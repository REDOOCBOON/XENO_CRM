from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from app.models.crm import Customer, Order, Communication, Event

def calculate_customer_intelligence(customer: Customer, orders: List[Order], communications: List[Communication]) -> Dict[str, Any]:
    """
    Computes heuristic customer intelligence metrics based on purchase history, demographics and engagement.
    """
    now = datetime.utcnow()
    

    order_amounts = [float(o.amount) for o in orders if o.status == "completed"]
    total_spend = sum(order_amounts)
    order_count = len(order_amounts)
    avg_order_value = total_spend / order_count if order_count > 0 else 0.0
    

    tier = customer.properties.get("tier", "regular").lower()
    ltv_multiplier = 1.8 if tier == "vip" else (1.5 if tier == "premium" else 1.2)
    predicted_ltv = max(50.0, total_spend * ltv_multiplier)
    


    if order_count > 0:

        order_dates = sorted([o.created_at for o in orders])
        last_order_date = order_dates[-1]
        days_since_last = (now - last_order_date.replace(tzinfo=None)).days
        

        if order_count > 1:
            total_days_range = (order_dates[-1] - order_dates[0]).days
            avg_days_between = max(7, total_days_range / (order_count - 1))
        else:
            avg_days_between = 45
            

        churn_ratio = days_since_last / (avg_days_between * 2.0)
        churn_score = min(1.0, max(0.0, churn_ratio))
    else:

        days_since_created = (now - customer.created_at.replace(tzinfo=None)).days
        churn_score = min(1.0, max(0.3, days_since_created / 60.0))
        

    age = customer.properties.get("age", 30)
    location = customer.properties.get("location", "Mumbai")
    gender = customer.properties.get("gender", "female").lower()
    

    if age < 30:
        preferred_channel = "WhatsApp" if gender == "female" else "RCS"
    elif age > 45:
        preferred_channel = "Email"
    else:
        preferred_channel = "WhatsApp" if gender == "female" else "SMS"
        

    channel_success = {}
    for c in communications:
        if c.status in ["clicked", "converted"]:
            channel_success[c.channel] = channel_success.get(c.channel, 0) + (5 if c.status == "converted" else 1)
            
    if channel_success:
        preferred_channel = max(channel_success, key=channel_success.get)


    sent_count = len(communications)
    if sent_count > 0:
        clicks = sum(1 for c in communications if c.status in ["clicked", "converted"])
        opens = sum(1 for c in communications if c.status in ["opened", "clicked", "converted"])
        conversions = sum(1 for c in communications if c.status == "converted")
        

        engagement_weight = (opens * 1.0 + clicks * 2.0 + conversions * 5.0)
        engagement_score = min(1.0, engagement_weight / (sent_count * 3.0))
    else:
        engagement_score = 0.5
        

    purchase_frequency_score = min(1.0, order_count / 10.0)
    

    affinity_map = {}
    for o in orders:
        cat = o.properties.get("category", "general")
        affinity_map[cat] = affinity_map.get(cat, 0) + 1
    affinity_categories = sorted(affinity_map, key=affinity_map.get, reverse=True)[:3]
    if not affinity_categories:
        affinity_categories = ["apparel"]
        

    if churn_score >= 0.75:
        risk_classification = "High Churn Risk"
    elif churn_score >= 0.45:
        risk_classification = "Medium Churn Risk"
    elif order_count > 2 and avg_order_value > 200:
        risk_classification = "Active VIP"
    else:
        risk_classification = "Active Loyal"
        

    if risk_classification == "Active VIP":
        persona_summary = f"High-Value VIP {affinity_categories[0].capitalize()} Buyer"
    elif tier == "premium":
        persona_summary = f"Premium {location} Shopper"
    elif churn_score >= 0.75:
        persona_summary = f"Churning {affinity_categories[0].capitalize()} Customer"
    else:
        persona_summary = f"Regular {gender.capitalize()} Shopper"
        

    if risk_classification == "High Churn Risk":
        action_type = "discount"
        offer = "Offer 25% Churn Winback Discount"
        confidence = 0.85
    elif risk_classification == "Active VIP":
        action_type = "upsell"
        offer = "Invite to Exclusive Premium Product Drop"
        confidence = 0.92
    elif "shoes" in affinity_categories:
        action_type = "cross_sell"
        offer = "Offer 15% discount on Shoe Care accessories"
        confidence = 0.78
    else:
        action_type = "retarget"
        offer = "Promote new arrivals in " + affinity_categories[0].capitalize()
        confidence = 0.80
        
    next_best_action = {
        "type": action_type,
        "recommendation": offer,
        "confidence": confidence,
        "estimated_revenue_gain": float(round(avg_order_value * confidence, 2))
    }
    
    return {
        "churn_score": float(round(churn_score, 2)),
        "predicted_ltv": Decimal(str(round(predicted_ltv, 2))),
        "preferred_channel": preferred_channel,
        "purchase_frequency_score": float(round(purchase_frequency_score, 2)),
        "engagement_score": float(round(engagement_score, 2)),
        "affinity_categories": affinity_categories,
        "risk_classification": risk_classification,
        "persona_summary": persona_summary,
        "next_best_action": next_best_action
    }

def calculate_campaign_readiness(template: str, channel: str, segment_size: int, preferred_channel_match_pct: float) -> int:
    """
    Computes a Readiness Score (0-100) before a campaign launches.
    Readiness Score = (40% audience quality) + (20% deliverability) + (20% channel match) + (20% campaign relevance)
    """


    if segment_size == 0:
        audience_quality = 0
    elif segment_size < 5:
        audience_quality = 70
    else:
        audience_quality = 100
        

    deliverability = 100
    spam_words = ["free", "cash", "winner", "urgent", "credit", "gift card", "guaranteed", "loan"]
    template_lower = template.lower()
    matches = sum(1 for w in spam_words if w in template_lower)
    
    if matches > 0:
        deliverability = max(50, 100 - (matches * 15))
        

    if channel == "SMS" and len(template) > 160:
        deliverability = max(40, deliverability - 20)



    channel_match = preferred_channel_match_pct * 100
    


    relevance = 60
    if "{{first_name}}" in template:
        relevance += 20
    if "{{last_purchased_item}}" in template:
        relevance += 20
        

    score = (audience_quality * 0.4) + (deliverability * 0.2) + (channel_match * 0.2) + (relevance * 0.2)
    return int(round(score))

def predict_campaign_performance(channel: str, segment_size: int, avg_segment_engagement: float, avg_order_value: float, template: str) -> Dict[str, Any]:
    """
    Predicts funnel response metrics (Open rate, click rate, conversion rate, spam risk, and revenue impact).
    """

    if channel == "WhatsApp":
        base_open, base_click, base_conv = 0.90, 0.35, 0.08
        spam_risk = "Low"
        deliv_risk = "Low"
    elif channel == "SMS":
        base_open, base_click, base_conv = 0.95, 0.15, 0.04
        spam_risk = "Medium"
        deliv_risk = "Low"
    elif channel == "RCS":
        base_open, base_click, base_conv = 0.82, 0.28, 0.06
        spam_risk = "Low"
        deliv_risk = "Medium"
    else:
        base_open, base_click, base_conv = 0.24, 0.06, 0.02
        spam_risk = "Low"
        deliv_risk = "Low"


    engagement_factor = avg_segment_engagement / 0.5
    predicted_open = min(0.99, base_open * engagement_factor)
    

    personalization_bonus = 1.0
    if "{{first_name}}" in template:
        personalization_bonus += 0.15
    if "{{last_purchased_item}}" in template:
        personalization_bonus += 0.20
        
    predicted_click = min(0.95, base_click * engagement_factor * personalization_bonus)
    predicted_conv = min(0.90, base_conv * engagement_factor * personalization_bonus)
    

    conversions = segment_size * predicted_open * predicted_click * predicted_conv
    revenue_impact = conversions * avg_order_value
    

    spam_words = ["free", "cash", "winner", "urgent"]
    if any(w in template.lower() for w in spam_words):
        spam_risk = "High"
        
    return {
        "open_rate": float(round(predicted_open * 100, 1)),
        "click_rate": float(round(predicted_click * 100, 1)),
        "conversion_rate": float(round(predicted_conv * 100, 1)),
        "revenue_impact": float(round(revenue_impact, 2)),
        "spam_risk": spam_risk,
        "deliverability_risk": deliv_risk
    }
