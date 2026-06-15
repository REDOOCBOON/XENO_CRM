import uuid
from sqlalchemy import Column, String, ForeignKey, Numeric, Integer, DateTime, JSON, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    properties = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="customer", cascade="all, delete-orphan")
    intelligence = relationship("CustomerIntelligence", back_populates="customer", uselist=False, cascade="all, delete-orphan")

class CustomerIntelligence(Base):
    __tablename__ = "customer_intelligence"
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    churn_score = Column(Float, default=0.0, nullable=False)
    predicted_ltv = Column(Numeric(10, 2), default=0.0, nullable=False)
    preferred_channel = Column(String(50), default="WhatsApp", nullable=False)
    purchase_frequency_score = Column(Float, default=0.0, nullable=False)
    engagement_score = Column(Float, default=0.0, nullable=False)
    affinity_categories = Column(JSONB, default=[], nullable=False)
    risk_classification = Column(String(50), default="Active", nullable=False)
    persona_summary = Column(String(255), default="Regular Buyer", nullable=False)
    next_best_action = Column(JSONB, default={}, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    customer = relationship("Customer", back_populates="intelligence")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    item_count = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="completed")
    properties = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    customer = relationship("Customer", back_populates="orders")

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    definition_json = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    campaigns = relationship("Campaign", back_populates="segment")

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="SET NULL"), nullable=True)
    message_template = Column(String, nullable=False)
    channel = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    goal = Column(String(255), nullable=True)
    readiness_score = Column(Integer, default=100, nullable=False)
    predicted_metrics = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    segment = relationship("Segment", back_populates="campaigns")
    communications = relationship("Communication", back_populates="campaign", cascade="all, delete-orphan")

class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)
    personalized_message = Column(String, nullable=False)
    status = Column(String(50), nullable=False, default="sent")
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    customer = relationship("Customer", back_populates="communications")
    campaign = relationship("Campaign", back_populates="communications")
    events = relationship("Event", back_populates="communication", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    communication_id = Column(UUID(as_uuid=True), ForeignKey("communications.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    properties = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    communication = relationship("Communication", back_populates="events")

class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    type = Column(String(100), nullable=False)
    audience_size = Column(Integer, nullable=False, default=0)
    expected_revenue_impact = Column(Numeric(10, 2), nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    suggested_segment_nl = Column(String(255), nullable=False)
    suggested_channel = Column(String(50), nullable=False, default="WhatsApp")
    suggested_message = Column(String, nullable=False)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
