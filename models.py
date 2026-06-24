import uuid
from decimal import Decimal
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, Boolean, Numeric, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class UserMemory(Base):
    __tablename__ = "user_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, index=True, nullable=False) # Maps to auth_user.id
    memory_type = Column(String(40), nullable=False)
    text = Column(Text, nullable=False)
    source = Column(String(80), nullable=True)
    source_object_type = Column(String(100), nullable=True)
    source_object_id = Column(String(100), nullable=True)
    confidence = Column(Numeric(4, 3), default=1)
    importance = Column(Numeric(4, 3), default=0.5)
    is_core = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    last_reinforced_at = Column(DateTime(timezone=True), nullable=True)
    qdrant_point_id = Column(String(100), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class UserBehaviorEvent(Base):
    __tablename__ = "user_behavior_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    object_type = Column(String(80), nullable=True)
    object_id = Column(String(100), nullable=True)
    event_value = Column(Numeric(8, 3), nullable=True)
    context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class UserTrait(Base):
    __tablename__ = "user_traits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, index=True, nullable=False)
    trait_key = Column(String(100), nullable=False)
    trait_value = Column(String(255), nullable=False)
    confidence = Column(Numeric(4, 3), default=0.5)
    evidence_count = Column(Integer, default=1)
    last_evidence_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
