from sqlalchemy.orm import Session
from app.models.crm import Customer, CustomerIntelligence, Order, Opportunity
from app.services.heuristics import predict_campaign_performance
from decimal import Decimal
import uuid

def scan_opportunities(db: Session) -> int:
    """
    Scans the database, runs heuristic rule checks to identify opportunities,
    and inserts active opportunities into the table.
    Returns the count of created opportunities.
    """

    db.query(Opportunity).filter(Opportunity.status == "active").delete()
    db.commit()
    
    created_count = 0
    


    inactive_vips = db.query(Customer).join(CustomerIntelligence).filter(
        CustomerIntelligence.churn_score >= 0.75,
        CustomerIntelligence.predicted_ltv >= 150
    ).all()
    
    if len(inactive_vips) >= 1:
        avg_ltv = sum(float(c.intelligence.predicted_ltv) for c in inactive_vips) / len(inactive_vips)
        expected_impact = len(inactive_vips) * 0.12 * avg_ltv * 0.25
        
        opp = Opportunity(
            title="Win-back Dormant High-Value VIPs",
            description=f"AI detected {len(inactive_vips)} VIP customers at extreme risk of churning. They have not made purchases in over 60 days.",
            type="Winback",
            audience_size=len(inactive_vips),
            expected_revenue_impact=Decimal(str(round(expected_impact, 2))),
            confidence_score=0.85,
            suggested_segment_nl="bring back inactive premium shoppers",
            suggested_channel="WhatsApp",
            suggested_message="Hi {{first_name}}! We miss you. Here is an exclusive VIP discount code for 20% off your next purchase: WE_MISS_YOU. Grab it now!",
            status="active"
        )
        db.add(opp)
        created_count += 1




    shoes_cust_ids = db.query(Order.customer_id).filter(
        Order.properties["category"].astext == "shoes"
    ).distinct().all()
    shoes_cust_ids = [c[0] for c in shoes_cust_ids]
    

    acc_cust_ids = db.query(Order.customer_id).filter(
        Order.properties["category"].astext == "accessories"
    ).distinct().all()
    acc_cust_ids = [c[0] for c in acc_cust_ids]
    
    cross_sell_targets = [cid for cid in shoes_cust_ids if cid not in acc_cust_ids]
    
    if len(cross_sell_targets) >= 1:

        targets = db.query(Customer).filter(Customer.id.in_(cross_sell_targets)).all()
        avg_spend = sum(float(c.intelligence.predicted_ltv) for c in targets if c.intelligence) / len(targets)
        expected_impact = len(targets) * 0.08 * 35.0
        
        opp = Opportunity(
            title="Cross-Sell Accessories to Shoe Buyers",
            description=f"AI audited purchasing trends and identified {len(targets)} shoppers who bought footwear but have never explored shoe care accessories.",
            type="Cross Sell",
            audience_size=len(targets),
            expected_revenue_impact=Decimal(str(round(expected_impact, 2))),
            confidence_score=0.74,
            suggested_segment_nl="customers who bought shoes in the last 60 days",
            suggested_channel="Email",
            suggested_message="Hi {{first_name}}! Keep your recently purchased footwear looking brand new with our premium shoe care kits. Take 15% off shoe accessories today!",
            status="active"
        )
        db.add(opp)
        created_count += 1
        


    upsell_candidates = db.query(Customer).join(CustomerIntelligence).filter(
        CustomerIntelligence.engagement_score >= 0.6,
        Customer.properties["tier"].astext == "regular"
    ).all()
    
    if len(upsell_candidates) >= 1:
        avg_ltv = sum(float(c.intelligence.predicted_ltv) for c in upsell_candidates) / len(upsell_candidates)
        expected_impact = len(upsell_candidates) * 0.15 * 50.0
        
        opp = Opportunity(
            title="Convert Highly Engaged Shoppers to Premium Tier",
            description=f"Identified {len(upsell_candidates)} regular shoppers with extremely high interaction logs. Propose a Premium loyalty upgrade offer.",
            type="Upsell",
            audience_size=len(upsell_candidates),
            expected_revenue_impact=Decimal(str(round(expected_impact, 2))),
            confidence_score=0.90,
            suggested_segment_nl="regular shoppers with high engagement score",
            suggested_channel="WhatsApp",
            suggested_message="Hey {{first_name}}! You are one of our top shoppers. Upgrade to our Premium Tier loyalty club today for early access to sales and a $10 welcome gift!",
            status="active"
        )
        db.add(opp)
        created_count += 1
        
    db.commit()
    return created_count
