import time
import requests
import uuid
import random
from celery.exceptions import MaxRetriesExceededError
from app.workers.celery_app import celery_app
from app.core.db import SessionLocal
from app.models.crm import Campaign, Communication, Customer, Segment, Order, Event, CustomerIntelligence, Opportunity
from app.services.segment_compiler import compile_segment
from app.services.heuristics import calculate_customer_intelligence
from app.services.opportunity_scanner import scan_opportunities
from sqlalchemy import func

@celery_app.task(bind=True, max_retries=3)
def dispatch_campaign_task(self, campaign_id_str: str):
    """
    Worker task to compile segment, create communication records, and dispatch messages.
    """
    db = SessionLocal()
    try:
        campaign_id = uuid.UUID(campaign_id_str)
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return f"Campaign {campaign_id_str} not found"
            
        campaign.status = "sending"
        db.commit()
        

        if campaign.segment_id:
            segment = db.query(Segment).filter(Segment.id == campaign.segment_id).first()
            if not segment:
                campaign.status = "failed"
                db.commit()
                return f"Segment not found for campaign {campaign_id_str}"

            from app.schemas.crm import SegmentDefinition
            definition = SegmentDefinition(**segment.definition_json)
            query = compile_segment(db, definition)
            customers = query.all()
        else:

            customers = db.query(Customer).all()
            
        if not customers:
            campaign.status = "completed"
            db.commit()
            return f"No customers in segment for campaign {campaign_id_str}"
            

        for customer in customers:

            idempotency_key = f"{campaign.id}:{customer.id}"
            existing_comm = db.query(Communication).filter(
                Communication.idempotency_key == idempotency_key
            ).first()
            
            if existing_comm:
                continue
                

            last_order = db.query(Order).filter(
                Order.customer_id == customer.id,
                Order.status == "completed"
            ).order_by(Order.created_at.desc()).first()
            
            last_item = "your recent item"
            if last_order and last_order.properties and "items" in last_order.properties:
                items = last_order.properties["items"]
                if items and isinstance(items, list):
                    last_item = items[0].get("name", "your recent item")
                    
            personalized_msg = campaign.message_template
            personalized_msg = personalized_msg.replace("{{first_name}}", customer.first_name)
            personalized_msg = personalized_msg.replace("{{last_name}}", customer.last_name)
            personalized_msg = personalized_msg.replace("{{last_purchased_item}}", last_item)
            
            comm = Communication(
                campaign_id=campaign.id,
                customer_id=customer.id,
                channel=campaign.channel,
                personalized_message=personalized_msg,
                status="sent",
                idempotency_key=idempotency_key
            )
            db.add(comm)
            db.flush()
            

            send_message_task.delay(str(comm.id))
            
        campaign.status = "completed"
        db.commit()
        return f"Dispatched campaign {campaign_id_str} to {len(customers)} customers"
        
    except Exception as exc:
        db.rollback()
        campaign = db.query(Campaign).filter(Campaign.id == uuid.UUID(campaign_id_str)).first()
        if campaign:
            campaign.status = "failed"
            db.commit()
        try:
            self.retry(exc=exc, countdown=10)
        except MaxRetriesExceededError:
            return f"Failed to dispatch campaign {campaign_id_str}: {exc}"
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=5)
def send_message_task(self, communication_id_str: str):
    """
    Calls the external/stubbed Channel Simulator service.
    """
    db = SessionLocal()
    try:
        comm_id = uuid.UUID(communication_id_str)
        comm = db.query(Communication).filter(Communication.id == comm_id).first()
        if not comm:
            return f"Communication {communication_id_str} not found"
            

        customer = db.query(Customer).filter(Customer.id == comm.customer_id).first()
        
        simulator_url = "http://localhost:8000/api/v1/channel-simulator/send"
        payload = {
            "communication_id": str(comm.id),
            "recipient_name": f"{customer.first_name} {customer.last_name}",
            "recipient_contact": customer.phone if comm.channel in ["WhatsApp", "SMS", "RCS"] else customer.email,
            "channel": comm.channel,
            "message": comm.personalized_message
        }
        
        try:
            response = requests.post(simulator_url, json=payload, timeout=5)
            if response.status_code == 202:
                return f"Sent communication {communication_id_str} to simulator"
        except requests.exceptions.RequestException:

            simulate_channel_events_task.delay(str(comm.id))
            return f"Server offline. Fallback: Direct simulation enqueued for {communication_id_str}"
            
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=5)
        except MaxRetriesExceededError:
            return f"Failed to send communication {communication_id_str} to simulator: {exc}"
    finally:
        db.close()

@celery_app.task
def simulate_channel_events_task(communication_id_str: str):
    """
    Simulates the lifecycle of a message (Sent -> Delivered -> Opened -> Clicked -> Converted)
    and sends callback HTTP requests back to the CRM API.
    """
    comm_id = uuid.UUID(communication_id_str)
    db = SessionLocal()
    comm = db.query(Communication).filter(Communication.id == comm_id).first()
    if not comm:
        db.close()
        return f"Communication {communication_id_str} not found in simulator"
        
    channel = comm.channel
    customer_id = str(comm.customer_id)
    db.close()
    
    if channel == "WhatsApp":
        p_deliver, p_open, p_click, p_convert = 0.98, 0.85, 0.40, 0.12
    elif channel == "SMS":
        p_deliver, p_open, p_click, p_convert = 0.95, 0.90, 0.20, 0.05
    elif channel == "RCS":
        p_deliver, p_open, p_click, p_convert = 0.92, 0.75, 0.35, 0.08
    else:
        p_deliver, p_open, p_click, p_convert = 0.99, 0.30, 0.08, 0.03

    callback_url = "http://localhost:8000/api/v1/receipts/callback"
    
    def send_callback(event: str, properties: dict = {}):
        payload = {
            "communication_id": communication_id_str,
            "event_type": event,
            "properties": properties
        }
        try:
            requests.post(callback_url, json=payload, timeout=5)
        except requests.exceptions.RequestException:

            from app.services.receipt_service import process_receipt
            db_local = SessionLocal()
            try:
                from app.schemas.crm import WebhookCallback
                obj = WebhookCallback(communication_id=comm_id, event_type=event, properties=properties)
                process_receipt(db_local, obj)
            finally:
                db_local.close()


    send_callback("sent")
    time.sleep(1)
    

    if random.random() > p_deliver:
        send_callback("failed", {"reason": "Undeliverable number / Inbox full"})
        return f"Simulated failure for {communication_id_str}"
        
    send_callback("delivered")
    time.sleep(2)
    

    if random.random() > p_open:
        return f"Simulated stop at delivered for {communication_id_str}"
        
    send_callback("opened")
    time.sleep(2)
    

    if random.random() > p_click:
        return f"Simulated stop at opened for {communication_id_str}"
        
    send_callback("clicked")
    time.sleep(3)
    

    if random.random() > p_convert:
        return f"Simulated stop at clicked for {communication_id_str}"
        
    amount = float(round(random.uniform(20.0, 350.0), 2))
    categories = ["shoes", "electronics", "apparel", "beauty", "accessories"]
    category = random.choice(categories)
    
    order_properties = {
        "items": [{"name": f"Simulated {category.capitalize()} Item", "price": amount}],
        "category": category,
        "attributed_campaign_id": str(comm.campaign_id)
    }
    
    send_callback("converted", {
        "amount": amount,
        "category": category,
        "properties": order_properties
    })
    
    return f"Simulated complete conversion funnel for {communication_id_str}"

@celery_app.task
def recalculate_all_customer_intelligence_task():
    """
    Background batch job that recalculates risk, LTV, personas for all customers.
    """
    db = SessionLocal()
    try:
        customers = db.query(Customer).all()
        for cust in customers:
            orders = db.query(Order).filter(Order.customer_id == cust.id).all()
            comms = db.query(Communication).filter(Communication.customer_id == cust.id).all()
            
            intel_data = calculate_customer_intelligence(cust, orders, comms)
            
            intel = db.query(CustomerIntelligence).filter(
                CustomerIntelligence.customer_id == cust.id
            ).first()
            
            if not intel:
                intel = CustomerIntelligence(customer_id=cust.id, **intel_data)
                db.add(intel)
            else:
                for k, v in intel_data.items():
                    setattr(intel, k, v)
                    
        db.commit()
        return f"Recalculated intelligence profiles for {len(customers)} customers"
    except Exception as e:
        db.rollback()
        return f"Error in intelligence recalculation: {e}"
    finally:
        db.close()

@celery_app.task
def scan_opportunities_task():
    """
    Background batch job to audit database trends and surface growth opportunities.
    """
    db = SessionLocal()
    try:
        count = scan_opportunities(db)
        return f"Database audit complete. Surfaced {count} opportunities."
    except Exception as e:
        return f"Error scanning opportunities: {e}"
    finally:
        db.close()
