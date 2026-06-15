from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class CustomerIntelligenceBase(BaseModel):
    churn_score: float
    predicted_ltv: Decimal
    preferred_channel: str
    purchase_frequency_score: float
    engagement_score: float
    affinity_categories: List[str]
    risk_classification: str
    persona_summary: str
    next_best_action: Dict[str, Any]

class CustomerIntelligenceResponse(CustomerIntelligenceBase):
    customer_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    intelligence: Optional[CustomerIntelligenceResponse] = None

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_id: UUID
    amount: Decimal
    item_count: int = 1
    status: str = "completed"
    properties: Dict[str, Any] = Field(default_factory=dict)

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ConditionNode(BaseModel):
    field: str
    operator: str
    value: Any

class SegmentDefinition(BaseModel):
    conjunction: str = "AND"
    conditions: List[ConditionNode]


class SegmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    definition_json: SegmentDefinition

class SegmentCreate(SegmentBase):
    pass

class SegmentResponse(SegmentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignBase(BaseModel):
    name: str
    segment_id: Optional[UUID] = None
    message_template: str
    channel: str
    goal: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(CampaignBase):
    id: UUID
    status: str
    goal: Optional[str] = None
    readiness_score: int
    predicted_metrics: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class CommunicationResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    customer_id: UUID
    channel: str
    personalized_message: str
    status: str
    sent_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookCallback(BaseModel):
    communication_id: UUID
    event_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class OpportunityResponse(BaseModel):
    id: UUID
    title: str
    description: str
    type: str
    audience_size: int
    expected_revenue_impact: Decimal
    confidence_score: float
    suggested_segment_nl: str
    suggested_channel: str
    suggested_message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
