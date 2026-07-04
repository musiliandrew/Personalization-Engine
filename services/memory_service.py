import logging
from decimal import Decimal
from typing import Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from models import UserMemory, UserBehaviorEvent

logger = logging.getLogger(__name__)

def _field_source_id(object_id: str, field: str) -> str:
    return f"{object_id}:{field}"

def _schedule_memory_sync(memory_id: str) -> None:
    # TODO: trigger celery task here
    from worker import sync_user_memory_task
    try:
        sync_user_memory_task.delay(str(memory_id))
    except Exception as exc:
        logger.warning("UserMemory: failed to enqueue vector sync for %s: %s", memory_id, exc)

def upsert_memory(
    db: Session,
    *,
    user_id: int,
    memory_type: str,
    text: str,
    source: str,
    source_object_type: Optional[str] = None,
    source_object_id: Optional[str] = None,
    confidence: Decimal | float | str = Decimal("1.0"),
    importance: Decimal | float | str = Decimal("0.5"),
    is_core: bool = False,
    metadata: Optional[dict[str, Any]] = None,
) -> UserMemory:
    """Create or update a canonical memory, then schedule Vertex AI sync."""

    text = str(text or "").strip()
    if not text:
        raise ValueError("Memory text cannot be empty")

    memory = db.query(UserMemory).filter_by(
        user_id=user_id,
        memory_type=memory_type,
        source=source,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
    ).first()

    if memory:
        memory.text = text
        memory.confidence = Decimal(str(confidence))
        memory.importance = Decimal(str(importance))
        memory.is_core = is_core
        memory.is_active = True
        memory.last_reinforced_at = datetime.utcnow()
        memory.metadata_ = metadata or {}
    else:
        memory = UserMemory(
            user_id=user_id,
            memory_type=memory_type,
            text=text,
            source=source,
            source_object_type=source_object_type,
            source_object_id=source_object_id,
            confidence=Decimal(str(confidence)),
            importance=Decimal(str(importance)),
            is_core=is_core,
            is_active=True,
            last_reinforced_at=datetime.utcnow(),
            metadata_=metadata or {}
        )
        db.add(memory)
    
    db.commit()
    db.refresh(memory)
    
    _schedule_memory_sync(str(memory.id))
    return memory

def deactivate_memory(db: Session, memory: UserMemory) -> UserMemory:
    memory.is_active = False
    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    _schedule_memory_sync(str(memory.id))
    return memory

def deactivate_object_memories(
    db: Session,
    *,
    user_id: int,
    source: str,
    source_object_type: str,
    source_object_id: str,
) -> int:
    qs = db.query(UserMemory).filter_by(
        user_id=user_id,
        source=source,
        source_object_type=source_object_type,
        source_object_id=str(source_object_id),
        is_active=True,
    ).all()
    
    count = 0
    for memory in qs:
        deactivate_memory(db, memory)
        count += 1
    return count

def deactivate_field_memory(
    db: Session,
    *,
    user_id: int,
    source: str,
    source_object_type: str,
    object_id: str,
    field: str,
) -> int:
    return deactivate_object_memories(
        db=db,
        user_id=user_id,
        source=source,
        source_object_type=source_object_type,
        source_object_id=_field_source_id(str(object_id), field),
    )
