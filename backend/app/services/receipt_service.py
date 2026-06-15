from sqlalchemy.orm import Session
from app.models.crm import Communication, Event, Order, Customer
from app.schemas.crm import WebhookCallback
import uuid

STATUS_RANKS = {
    "failed": -1,
    "sent": 1,
    "delivered": 2,
    "opened": 3,
    "clicked": 4,
    "converted": 5
}

def process_receipt(db: Session, callback: WebhookCallback):
    """
    Processes a webhook callback from the Channel Simulator, updates status using a state machine rank filter,
    inserts an event log, and creates simulated attributed orders.
    """
    comm = db.query(Communication).filter(Communication.id == callback.communication_id).first()
    if not comm:
        return None
        
    current_status = comm.status
    new_status = callback.event_type
    
    current_rank = STATUS_RANKS.get(current_status, 0)
    new_rank = STATUS_RANKS.get(new_status, 0)
    


    if current_status != "failed":
        if new_status == "failed" or new_rank > current_rank:
            comm.status = new_status
            

    event = Event(
        communication_id=comm.id,
        event_type=new_status,
        properties=callback.properties
    )
    db.add(event)
    

    if new_status == "converted":
        amount = callback.properties.get("amount", 50.00)
        category = callback.properties.get("category", "general")
        properties = callback.properties.get("properties", {})
        
        order = Order(
            customer_id=comm.customer_id,
            amount=amount,
            item_count=1,
            status="completed",
            properties=properties
        )
        db.add(order)
        
    db.commit()
    db.refresh(comm)
    return comm
