import json
from openai import OpenAI
from app.core.config import settings
from app.schemas.crm import SegmentDefinition, ConditionNode
from app.services.segment_compiler import compile_segment
from app.services.heuristics import calculate_campaign_readiness, predict_campaign_performance
from app.models.crm import Customer, CustomerIntelligence, Segment, Campaign
from sqlalchemy.orm import Session
from sqlalchemy import func
import re
import uuid

class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def generate_segment_from_nl(self, prompt: str) -> dict:
        """
        Audience Agent: Translates natural language goal into AST JSON filters.
        """
        if not self.client:
            return self._mock_nl_segment(prompt)
            
        system_prompt = (
            "You are the Segmentation Agent for XenoPilot. Convert the user's audience description "
            "into a structured JSON filter AST matching the SegmentDefinition schema.\n"
            "Supported fields:\n"
            "  - 'customer.properties.tier' (premium, regular, vip)\n"
            "  - 'customer.properties.gender' (male, female)\n"
            "  - 'customer.total_spend' (Numeric)\n"
            "  - 'customer.order_count' (Integer)\n"
            "  - 'customer.last_order_date' (e.g. '30_days_ago', '60_days_ago', '90_days_ago')\n"
            "  - 'order.category' (e.g. 'shoes', 'electronics', 'apparel')\n"
            "Operators: 'equals', 'not_equals', 'greater_than', 'less_than', 'greater_than_or_equal', 'less_than_or_equal'\n\n"
            "Return ONLY raw JSON. Do not write markdown tags."
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in OpenAI call: {e}")
            return self._mock_nl_segment(prompt)

    def generate_campaign_proposal(self, goal: str, db: Session) -> dict:
        """
        Multi-Agent Orchestrator: Combines Audience, Messaging, Channel, and Prediction agents
        to formulate a campaign proposal from a marketer's goal.
        """

        segment_ast = self.generate_segment_from_nl(goal)
        definition = SegmentDefinition(**segment_ast)
        

        query = compile_segment(db, definition)
        customers = query.all()
        audience_size = len(customers)
        


        channel_counts = {}
        total_engagement = 0.0
        
        cust_ids = [c.id for c in customers]
        intel_records = db.query(CustomerIntelligence).filter(
            CustomerIntelligence.customer_id.in_(cust_ids)
        ).all() if cust_ids else []
        
        for intel in intel_records:
            channel_counts[intel.preferred_channel] = channel_counts.get(intel.preferred_channel, 0) + 1
            total_engagement += intel.engagement_score
            
        recommended_channel = "WhatsApp"
        if channel_counts:
            recommended_channel = max(channel_counts, key=channel_counts.get)
            
        avg_engagement = (total_engagement / len(intel_records)) if intel_records else 0.5
        match_count = channel_counts.get(recommended_channel, 0)
        match_pct = (match_count / audience_size) if audience_size > 0 else 1.0
        

        if self.client:
            copywriter_prompt = (
                f"You are the Messaging Copywriter Agent. Write a highly converting campaign copy template "
                f"targeting: '{goal}'. Channel selected: {recommended_channel}.\n"
                f"You MUST use merge tags: '{{{{first_name}}}}' and '{{{{last_purchased_item}}}}'.\n"
                f"Keep it concise. WhatsApp/SMS templates must be under 160 characters. Email can be up to 300 characters.\n"
                f"Return JSON with keys: 'template', 'reasoning'."
            )
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": copywriter_prompt},
                        {"role": "user", "content": f"Write message for goal: '{goal}'"}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                res = json.loads(response.choices[0].message.content)
                message_template = res.get("template", "")
                reasoning = res.get("reasoning", "")
            except Exception:
                message_template, reasoning = self._mock_message_template(goal, recommended_channel)
        else:
            message_template, reasoning = self._mock_message_template(goal, recommended_channel)


        readiness_score = calculate_campaign_readiness(message_template, recommended_channel, audience_size, match_pct)
        

        avg_order_val = 85.00
        
        predictions = predict_campaign_performance(
            channel=recommended_channel,
            segment_size=audience_size,
            avg_segment_engagement=avg_engagement,
            avg_order_value=avg_order_val,
            template=message_template
        )
        
        return {
            "goal": goal,
            "segment_ast": segment_ast,
            "audience_size": audience_size,
            "recommended_channel": recommended_channel,
            "message_template": message_template,
            "reasoning": reasoning,
            "readiness_score": readiness_score,
            "predictions": predictions
        }

    def generate_audience_recommendations(self) -> list:
        """
        AI Growth Advisor: Scans and generates marketing actions.
        """
        if not self.client:
            return self._mock_recommendations()
            
        system_prompt = (
            "You are the AI Growth Marketing Agent. Return 3 growth recommendations in JSON format "
            "with keys: 'title', 'description', 'suggested_nl_segment', 'suggested_channel', 'estimated_impact'."
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Fetch active opportunities"}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            if isinstance(data, dict) and "recommendations" in data:
                return data["recommendations"]
            return data
        except Exception:
            return self._mock_recommendations()

    def generate_performance_summary(self, campaign_name: str, metrics: dict) -> str:
        """
        Insights Agent: Evaluates campaign outcomes and returns markdown summaries.
        """
        if not self.client:
            return self._mock_performance_summary(campaign_name, metrics)
            
        system_prompt = (
            "You are the Insights Agent. Write a brief markdown summary analyzing campaign conversion rates, "
            "leakages, and one actionable takeaway."
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Campaign: {campaign_name}, Metrics: {metrics}"}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception:
            return self._mock_performance_summary(campaign_name, metrics)

    def _mock_nl_segment(self, prompt: str) -> dict:
        import re
        prompt_lower = prompt.lower()
        conditions = []
        

        if "inactive" in prompt_lower or "winback" in prompt_lower or "bring back" in prompt_lower or "haven't ordered" in prompt_lower:
            conditions.append({
                "field": "customer.last_order_date",
                "operator": "greater_than_or_equal",
                "value": "30_days_ago"
            })
            

        if "vip" in prompt_lower:
            conditions.append({
                "field": "customer.properties.tier",
                "operator": "equals",
                "value": "vip"
            })
        elif "premium" in prompt_lower:
            conditions.append({
                "field": "customer.properties.tier",
                "operator": "equals",
                "value": "premium"
            })
        elif "regular" in prompt_lower:
            conditions.append({
                "field": "customer.properties.tier",
                "operator": "equals",
                "value": "regular"
            })
            


        spend_more = re.search(r"spend(?:s)?\s*(?:more than|>|over|greater than)\s*(\d+)", prompt_lower)
        if spend_more:
            conditions.append({
                "field": "customer.total_spend",
                "operator": "greater_than",
                "value": float(spend_more.group(1))
            })
        else:
            spend_less = re.search(r"spend(?:s)?\s*(?:less than|<)\s*(\d+)", prompt_lower)
            if spend_less:
                conditions.append({
                    "field": "customer.total_spend",
                    "operator": "less_than",
                    "value": float(spend_less.group(1))
                })


        if "shoes" in prompt_lower:
            conditions.append({
                "field": "order.category",
                "operator": "equals",
                "value": "shoes"
            })
        elif "electronics" in prompt_lower:
            conditions.append({
                "field": "order.category",
                "operator": "equals",
                "value": "electronics"
            })
            
        if not conditions:
            conditions.append({
                "field": "customer.total_spend",
                "operator": "greater_than_or_equal",
                "value": 150.0
            })
            
        return {
            "conjunction": "AND",
            "conditions": conditions
        }


    def _mock_message_template(self, goal: str, channel: str) -> tuple:
        goal_lower = goal.lower()
        if "winback" in goal_lower or "inactive" in goal_lower or "bring back" in goal_lower:
            msg = "Hi {{first_name}}! We notice you haven't bought {{last_purchased_item}} in a while. Here is a special 20% discount code: WE_MISS_YOU."
            reasoning = "Win-back triggers rely on high incentive values. Email or WhatsApp is ideal."
        elif "upsell" in goal_lower or "premium" in goal_lower:
            msg = "Hello {{first_name}}! Upgrade to our Premium VIP Club today. Get free shipping and early access to drops. Tap here to join."
            reasoning = "Upselling highly active regular users works best on instant channels like WhatsApp."
        else:
            msg = "Hi {{first_name}}! Check out our new season arrivals. Get 10% off early bird discounts using SUMMER10."
            reasoning = "Generic promotions show peak response rates on conversational SMS."
        return msg, reasoning

    def _mock_recommendations(self) -> list:
        return [
            {
                "title": "Win-back Inactive VIPs",
                "description": "Premium tier customers who haven't ordered in over 30 days are at risk of churning. Win them back with an exclusive WhatsApp perk.",
                "suggested_nl_segment": "bring back inactive premium shoppers",
                "suggested_channel": "WhatsApp",
                "estimated_impact": "+18% Conversion"
            },
            {
                "title": "Re-engage Accessory Buyers",
                "description": "Customers who purchased shoes in the last 60 days but didn't look at socks or shoe care accessories. Upsell via an email recommendation flow.",
                "suggested_nl_segment": "customers who bought shoes in the last 60 days",
                "suggested_channel": "Email",
                "estimated_impact": "+$3,200 Revenue"
            }
        ]

    def _mock_performance_summary(self, campaign_name: str, metrics: dict) -> str:
        sent = metrics.get("sent", 0)
        delivered = metrics.get("delivered", 0)
        opened = metrics.get("opened", 0)
        clicked = metrics.get("clicked", 0)
        converted = metrics.get("converted", 0)
        revenue = metrics.get("revenue", 0.0)
        
        open_rate = (opened / delivered * 100) if delivered else 0
        click_rate = (clicked / opened * 100) if opened else 0
        conv_rate = (converted / clicked * 100) if clicked else 0
        
        return f"""
### Campaign Performance Report: **{campaign_name}**

**Overview:**
The campaign completed delivery successfully. Out of **{sent}** sent messages, **{delivered}** were delivered and **{converted}** shoppers converted directly, generating attributed sales of **${revenue:,.2f}**.

**Funnel Metrics:**
*   **Delivery Rate:** {((delivered / sent * 100) if sent else 0):.1f}%
*   **Open Rate:** {open_rate:.1f}%
*   **Click-Through Rate:** {click_rate:.1f}%
*   **Conversion Rate (on click):** {conv_rate:.1f}%

**Key Actionable Recommendation:**
For your next campaign, route SMS templates to WhatsApp to improve Click-to-Conversion metrics for the premium shoe buyers segment.
"""

ai_service = AIService()
