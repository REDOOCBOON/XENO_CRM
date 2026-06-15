from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
from decimal import Decimal

from app.core.db import get_db
from app.models.crm import Customer, Order, Segment, Campaign, Communication, Event, CustomerIntelligence, Opportunity
from app.schemas.crm import (
    CustomerCreate, CustomerResponse,
    OrderCreate, OrderResponse,
    SegmentCreate, SegmentResponse, SegmentDefinition,
    CampaignCreate, CampaignResponse,
    WebhookCallback, OpportunityResponse, CustomerIntelligenceResponse
)
from app.services.segment_compiler import compile_segment
from app.services.ai_service import ai_service
from app.services.receipt_service import process_receipt
from app.services.opportunity_scanner import scan_opportunities
from app.workers.tasks import (
    dispatch_campaign_task, 
    simulate_channel_events_task, 
    recalculate_all_customer_intelligence_task,
    scan_opportunities_task
)

router = APIRouter()


@router.get("/dashboard/kpis", tags=["Dashboard"])
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Returns marketing KPIs: Attributed Revenue, Campaign ROI, Channel Performance,
    Conversion Funnel, and Customer Re-activation rates.
    """

    attributed_orders = db.query(Order).filter(
        Order.properties["attributed_campaign_id"].astext != None
    ).all()
    total_attributed_revenue = sum(float(o.amount) for o in attributed_orders)
    

    total_revenue = sum(float(o.amount) for o in db.query(Order).all())
    

    campaigns = db.query(Campaign).all()
    campaign_count = len(campaigns)
    


    comms = db.query(Communication.channel, Communication.status).all()
    channel_stats = {}
    for channel, status in comms:
        if channel not in channel_stats:
            channel_stats[channel] = {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0, "failed": 0}
        
        channel_stats[channel]["sent"] += 1
        if status in channel_stats[channel]:
            channel_stats[channel][status] += 1
            

    channel_performance = []
    for chan, counts in channel_stats.items():
        sent = counts["sent"]

        delivered = counts["delivered"] + counts["opened"] + counts["clicked"] + counts["converted"]
        opened = counts["opened"] + counts["clicked"] + counts["converted"]
        clicked = counts["clicked"] + counts["converted"]
        converted = counts["converted"]
        
        open_rate = (opened / delivered * 100) if delivered else 0.0
        click_rate = (clicked / opened * 100) if opened else 0.0
        conv_rate = (converted / clicked * 100) if clicked else 0.0
        
        channel_performance.append({
            "channel": chan,
            "sent": sent,
            "open_rate": round(open_rate, 1),
            "click_rate": round(click_rate, 1),
            "conversion_rate": round(conv_rate, 1),
            "conversions": converted
        })


    total_comms = len(comms)
    status_counts = {"delivered": 0, "opened": 0, "clicked": 0, "converted": 0}
    for _, status in comms:
        if status in status_counts:
            status_counts[status] += 1
            
    funnel = {
        "sent": total_comms,
        "delivered": status_counts["delivered"] + status_counts["opened"] + status_counts["clicked"] + status_counts["converted"],
        "opened": status_counts["opened"] + status_counts["clicked"] + status_counts["converted"],
        "clicked": status_counts["clicked"] + status_counts["converted"],
        "converted": status_counts["converted"]
    }
    

    reactivated_count = db.query(Customer).join(CustomerIntelligence).filter(
        CustomerIntelligence.risk_classification == "High Churn Risk",
        Customer.orders.any(Order.properties["attributed_campaign_id"].astext != None)
    ).count()

    return {
        "attributed_revenue": total_attributed_revenue,
        "total_revenue": total_revenue,
        "campaign_count": campaign_count,
        "funnel": funnel,
        "channel_performance": channel_performance,
        "reactivated_customers": reactivated_count
    }



@router.post("/agent/goal", tags=["AI Marketing Agent"])
def parse_goal_proposal(payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    User submits goal -> AI analyzes database, compiles AST, routes channel, drafts message,
    and runs predictions, returning a complete Campaign Proposal for review.
    """
    goal = payload.get("goal")
    if not goal:
        raise HTTPException(status_code=400, detail="Goal prompt is required")
        
    proposal = ai_service.generate_campaign_proposal(goal, db)
    return proposal

@router.post("/agent/goal/execute", tags=["AI Marketing Agent"])
def execute_goal_campaign(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Executes the campaign proposed by the AI Campaign Agent.
    Creates segment and campaign records in DB, then triggers Celery dispatch.
    """
    goal = payload.get("goal", "Growth Campaign")
    name = payload.get("name", "XenoPilot Campaign")
    segment_ast = payload.get("segment_ast")
    channel = payload.get("channel", "WhatsApp")
    message_template = payload.get("message_template")
    readiness_score = payload.get("readiness_score", 100)
    predictions = payload.get("predictions", {})
    autonomous = payload.get("autonomous", False)
    
    if not segment_ast or not message_template:
        raise HTTPException(status_code=400, detail="segment_ast and message_template are required")
        

    segment = Segment(
        name=f"Auto Segment: {name}",
        description=f"Generated by AI Campaign Agent for goal: {goal}",
        definition_json=segment_ast
    )
    db.add(segment)
    db.flush()
    

    campaign = Campaign(
        name=name,
        segment_id=segment.id,
        message_template=message_template,
        channel=channel,
        status="sending" if not autonomous else "sending",
        goal=goal,
        readiness_score=readiness_score,
        predicted_metrics=predictions
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    

    dispatch_campaign_task.delay(str(campaign.id))
    
    return {
        "message": "Campaign successfully launched" if not autonomous else "Autonomous mode: Campaign executed",
        "campaign_id": str(campaign.id),
        "segment_id": str(segment.id)
    }



@router.get("/opportunities", response_model=List[OpportunityResponse], tags=["AI Marketing Agent"])
def list_opportunities(db: Session = Depends(get_db)):
    """
    Returns active surfaced revenue opportunities.
    """
    return db.query(Opportunity).filter(Opportunity.status == "active").order_by(Opportunity.expected_revenue_impact.desc()).all()

@router.post("/opportunities/scan", tags=["AI Marketing Agent"])
def run_opportunities_scan(db: Session = Depends(get_db)):
    """
    Audits the database and refreshes the proactive growth feed.
    """
    count = scan_opportunities(db)
    return {"message": f"Scan completed. Surfaced {count} opportunities."}

@router.post("/opportunities/{id}/execute", tags=["AI Marketing Agent"])
def execute_opportunity(id: str, db: Session = Depends(get_db)):
    """
    Launches a campaign directly from an Opportunity card in one click.
    """
    opp_uuid = uuid.UUID(id)
    opp = db.query(Opportunity).filter(Opportunity.id == opp_uuid).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        

    segment_ast = ai_service.generate_segment_from_nl(opp.suggested_segment_nl)
    

    segment = Segment(
        name=f"Segment: {opp.title}",
        description=opp.description,
        definition_json=segment_ast
    )
    db.add(segment)
    db.flush()
    

    campaign = Campaign(
        name=opp.title,
        segment_id=segment.id,
        message_template=opp.suggested_message,
        channel=opp.suggested_channel,
        status="sending",
        goal=opp.title,
        readiness_score=int(opp.confidence_score * 100),
        predicted_metrics={
            "open_rate": 85.0, "click_rate": 25.0, "conversion_rate": 5.0,
            "revenue_impact": float(opp.expected_revenue_impact), "spam_risk": "Low", "deliverability_risk": "Low"
        }
    )
    db.add(campaign)
    opp.status = "executed"
    db.commit()
    

    dispatch_campaign_task.delay(str(campaign.id))
    return {"message": "Opportunity campaign dispatched", "campaign_id": str(campaign.id)}



@router.get("/customers/{id}/intelligence", response_model=CustomerIntelligenceResponse, tags=["Customer Intelligence"])
def get_customer_intelligence(id: str, db: Session = Depends(get_db)):
    cust_uuid = uuid.UUID(id)
    intel = db.query(CustomerIntelligence).filter(CustomerIntelligence.customer_id == cust_uuid).first()
    if not intel:
        raise HTTPException(status_code=404, detail="Customer intelligence profile not found")
    return intel

@router.post("/customers/intelligence/recalculate", tags=["Customer Intelligence"])
def trigger_intelligence_recalculation(background_tasks: BackgroundTasks):
    """
    Triggers recalculation for all customer profiles in background.
    """
    recalculate_all_customer_intelligence_task.delay()
    return {"message": "Customer intelligence profiling job enqueued"}



@router.post("/receipts/callback", tags=["CRM Core"])
def receipts_callback(callback: WebhookCallback, db: Session = Depends(get_db)):
    """
    Receives state events from simulated messaging channels.
    """
    comm = process_receipt(db, callback)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return {"status": "Success", "communication_id": str(comm.id), "comm_status": comm.status}

@router.post("/channel-simulator/send", status_code=202, tags=["Channel Simulator"])
def channel_simulator_send(payload: Dict[str, Any]):
    """
    Exposes simulated Channel send API endpoint. Triggered by worker dispatch.
    """
    comm_id = payload.get("communication_id")
    if not comm_id:
        raise HTTPException(status_code=400, detail="communication_id required")
    simulate_channel_events_task.delay(comm_id)
    return {"status": "Accepted", "details": "Simulation events enqueued"}



@router.post("/customers", response_model=CustomerResponse, tags=["CRM Core"])
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_cust = db.query(Customer).filter(Customer.email == customer.email).first()
    if db_cust:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_cust = Customer(**customer.model_dump())
    db.add(db_cust)
    db.commit()
    db.refresh(db_cust)
    return db_cust

@router.get("/customers", response_model=List[CustomerResponse], tags=["CRM Core"])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.created_at.desc()).limit(100).all()

@router.post("/orders", response_model=OrderResponse, tags=["CRM Core"])
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/orders", response_model=List[OrderResponse], tags=["CRM Core"])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.created_at.desc()).limit(100).all()

@router.post("/segments", response_model=SegmentResponse, tags=["CRM Segments"])
def create_segment(segment: SegmentCreate, db: Session = Depends(get_db)):
    db_seg = Segment(
        name=segment.name,
        description=segment.description,
        definition_json=segment.definition_json.model_dump()
    )
    db.add(db_seg)
    db.commit()
    db.refresh(db_seg)
    return db_seg

@router.get("/segments", response_model=List[SegmentResponse], tags=["CRM Segments"])
def list_segments(db: Session = Depends(get_db)):
    return db.query(Segment).order_by(Segment.created_at.desc()).all()

@router.post("/segments/nlp", tags=["CRM Segments"])
def parse_nlp_segment(payload: Dict[str, str], db: Session = Depends(get_db)):
    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    ast = ai_service.generate_segment_from_nl(prompt)
    return ast

@router.post("/segments/preview", tags=["CRM Segments"])
def preview_segment_endpoint(definition: SegmentDefinition, db: Session = Depends(get_db)):
    query = compile_segment(db, definition)
    customers = query.all()

    return [
        {
            "id": str(c.id),
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "properties": c.properties,
            "created_at": c.created_at.isoformat()
        } for c in customers
    ]

@router.get("/campaigns", response_model=List[CampaignResponse], tags=["CRM Campaigns"])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.created_at.desc()).all()

@router.post("/campaigns", response_model=CampaignResponse, tags=["CRM Campaigns"])
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    segment_size = 0
    match_pct = 1.0
    if campaign.segment_id:
        segment = db.query(Segment).filter(Segment.id == campaign.segment_id).first()
        if segment:
            definition = SegmentDefinition(**segment.definition_json)
            query = compile_segment(db, definition)
            segment_size = query.count()
            
    from app.services.heuristics import calculate_campaign_readiness, predict_campaign_performance
    readiness = calculate_campaign_readiness(campaign.message_template, campaign.channel, segment_size, match_pct)
    predictions = predict_campaign_performance(
        channel=campaign.channel,
        segment_size=segment_size,
        avg_segment_engagement=0.7,
        avg_order_value=85.00,
        template=campaign.message_template
    )
    
    db_campaign = Campaign(
        name=campaign.name,
        segment_id=campaign.segment_id,
        message_template=campaign.message_template,
        channel=campaign.channel,
        status="draft",
        goal=campaign.goal,
        readiness_score=readiness,
        predicted_metrics=predictions
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.post("/campaigns/{id}/send", tags=["CRM Campaigns"])
def send_campaign_endpoint(id: str, db: Session = Depends(get_db)):
    camp_uuid = uuid.UUID(id)
    campaign = db.query(Campaign).filter(Campaign.id == camp_uuid).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    campaign.status = "sending"
    db.commit()
    
    dispatch_campaign_task.delay(id)
    return {"message": "Campaign sending process started", "campaign_id": id}

@router.post("/campaigns/nlp-content", tags=["CRM Campaigns"])
def generate_nlp_campaign_content(payload: Dict[str, str]):
    import json
    name = payload.get("name", "")
    audience_description = payload.get("audience_description", "")
    goal = payload.get("goal", "")
    
    if not audience_description or not goal:
        raise HTTPException(status_code=400, detail="audience_description and goal are required")
        
    template, reasoning = ai_service._mock_message_template(goal, "WhatsApp")
    if ai_service.client:
        copywriter_prompt = (
            f"You are the Messaging Copywriter Agent. Write a highly converting campaign copy template for campaign '{name}' "
            f"targeting: '{goal}' with audience: '{audience_description}'.\n"
            f"You MUST use merge tags: '{{{{first_name}}}}' and '{{{{last_purchased_item}}}}'.\n"
            f"Keep it concise. WhatsApp/SMS templates must be under 160 characters. Email can be up to 300 characters.\n"
            f"Return JSON with keys: 'template', 'reasoning'."
        )
        try:
            response = ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": copywriter_prompt},
                    {"role": "user", "content": f"Generate template"}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            res = json.loads(response.choices[0].message.content)
            template = res.get("template", template)
            reasoning = res.get("reasoning", reasoning)
        except Exception as e:
            print(f"Error calling OpenAI copywriting: {e}")
            
    return {"template": template, "reasoning": reasoning}

@router.get("/ai/recommendations", tags=["AI Marketing Agent"])
def get_ai_recommendations_endpoint():
    recommendations = ai_service.generate_audience_recommendations()
    return recommendations


@router.get("/campaigns/{campaign_id}/analytics", tags=["CRM Campaigns"])
def get_campaign_analytics(campaign_id: str, db: Session = Depends(get_db)):
    camp_uuid = uuid.UUID(campaign_id)
    campaign = db.query(Campaign).filter(Campaign.id == camp_uuid).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    comms = db.query(Communication).filter(Communication.campaign_id == camp_uuid).all()
    total = len(comms)
    
    stats = {"sent": 0, "delivered": 0, "failed": 0, "opened": 0, "clicked": 0, "converted": 0}
    for c in comms:
        status = c.status
        if status in stats:
            stats[status] += 1
            
    funnel = {
        "sent": total,
        "delivered": stats.get("delivered", 0) + stats.get("opened", 0) + stats.get("clicked", 0) + stats.get("converted", 0),
        "failed": stats.get("failed", 0),
        "opened": stats.get("opened", 0) + stats.get("clicked", 0) + stats.get("converted", 0),
        "clicked": stats.get("clicked", 0) + stats.get("converted", 0),
        "converted": stats.get("converted", 0)
    }
    
    attributed_orders = db.query(Order).filter(
        Order.properties["attributed_campaign_id"].astext == campaign_id
    ).all()
    total_revenue = sum(float(o.amount) for o in attributed_orders)
    
    ai_report = ai_service.generate_performance_summary(campaign.name, {
        "sent": funnel["sent"],
        "delivered": funnel["delivered"],
        "opened": funnel["opened"],
        "clicked": funnel["clicked"],
        "converted": funnel["converted"],
        "revenue": total_revenue
    })
    
    return {
        "campaign_id": campaign_id,
        "name": campaign.name,
        "channel": campaign.channel,
        "status": campaign.status,
        "funnel": funnel,
        "revenue": total_revenue,
        "ai_report": ai_report
    }



@router.post("/admin/seed-mock-data", tags=["Admin Utils"])
def seed_mock_data(db: Session = Depends(get_db)):

    db.query(Opportunity).delete()
    db.query(Event).delete()
    db.query(Communication).delete()
    db.query(Campaign).delete()
    db.query(Segment).delete()
    db.query(Order).delete()
    db.query(CustomerIntelligence).delete()
    db.query(Customer).delete()
    db.commit()
    

    customers_data = [
        {"first_name": "Aarav", "last_name": "Sharma", "email": "aarav.sharma@example.com", "phone": "+919876543200", "properties": {"tier": "premium", "gender": "male", "age": 28, "location": "Mumbai"}},
        {"first_name": "Diya", "last_name": "Patel", "email": "diya.patel@example.com", "phone": "+919876543201", "properties": {"tier": "premium", "gender": "female", "age": 32, "location": "Delhi"}},
        {"first_name": "Aditya", "last_name": "Verma", "email": "aditya.verma@example.com", "phone": "+919876543202", "properties": {"tier": "vip", "gender": "male", "age": 45, "location": "Bangalore"}},
        {"first_name": "Ananya", "last_name": "Iyer", "email": "ananya.iyer@example.com", "phone": "+919876543203", "properties": {"tier": "regular", "gender": "female", "age": 24, "location": "Chennai"}},
        {"first_name": "Kabir", "last_name": "Singh", "email": "kabir.singh@example.com", "phone": "+919876543204", "properties": {"tier": "regular", "gender": "male", "age": 30, "location": "Pune"}},
        {"first_name": "Meera", "last_name": "Nair", "email": "meera.nair@example.com", "phone": "+919876543205", "properties": {"tier": "vip", "gender": "female", "age": 39, "location": "Hyderabad"}},
        {"first_name": "Vivaan", "last_name": "Reddy", "email": "vivaan.reddy@example.com", "phone": "+919876543206", "properties": {"tier": "regular", "gender": "male", "age": 22, "location": "Hyderabad"}},
        {"first_name": "Isha", "last_name": "Gupta", "email": "isha.gupta@example.com", "phone": "+919876543207", "properties": {"tier": "regular", "gender": "female", "age": 27, "location": "Kolkata"}},
        {"first_name": "Rohan", "last_name": "Joshi", "email": "rohan.joshi@example.com", "phone": "+919876543208", "properties": {"tier": "premium", "gender": "male", "age": 35, "location": "Ahmedabad"}},
        {"first_name": "Sanya", "last_name": "Malhotra", "email": "sanya.malhotra@example.com", "phone": "+919876543209", "properties": {"tier": "vip", "gender": "female", "age": 31, "location": "Mumbai"}}
    ]
    
    customers_objs = []
    for c in customers_data:
        cust = Customer(**c)
        db.add(cust)
        customers_objs.append(cust)
    db.commit()
    

    import random
    from datetime import datetime, timedelta
    
    categories = ["shoes", "electronics", "apparel", "beauty", "accessories"]
    
    for cust in customers_objs:
        order_count = random.randint(1, 4)
        for _ in range(order_count):
            amount = float(round(random.uniform(15.0, 450.0), 2))
            category = random.choice(categories)

            days_ago = random.randint(5, 90)
            order_date = datetime.now() - timedelta(days=days_ago)
            
            order = Order(
                customer_id=cust.id,
                amount=amount,
                item_count=random.randint(1, 3),
                status="completed",
                properties={"items": [{"name": f"Stylish {category.capitalize()}", "price": amount}], "category": category},
                created_at=order_date
            )
            db.add(order)
    db.commit()
    


    from app.services.heuristics import calculate_customer_intelligence
    for cust in customers_objs:
        orders = db.query(Order).filter(Order.customer_id == cust.id).all()
        comms = db.query(Communication).filter(Communication.customer_id == cust.id).all()
        
        intel_data = calculate_customer_intelligence(cust, orders, comms)
        intel = CustomerIntelligence(customer_id=cust.id, **intel_data)
        db.add(intel)
    db.commit()
    

    scan_opportunities(db)
    
    return {"message": "Database successfully populated with seed intelligence data", "customers_count": len(customers_objs)}
