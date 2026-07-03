from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from database import SessionLocal
from models import UserMemory
from services.vector_db import (
    embed_text,
    ensure_user_memories_collection,
    upsert_user_memory,
    delete_user_memory
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/tasks", tags=["internal"])

class SyncMemoryRequest(BaseModel):
    memory_id: str

@router.post("/sync-memory")
def sync_user_memory(request: SyncMemoryRequest):
    memory_id = request.memory_id
    db = SessionLocal()
    try:
        memory = db.query(UserMemory).filter_by(id=memory_id).first()
        if not memory:
            return {"memory_id": memory_id, "status": "missing"}

        point_id = str(memory.qdrant_point_id or memory.id)
        if not memory.is_active:
            delete_user_memory(point_id)
            if memory.qdrant_point_id:
                memory.qdrant_point_id = None
                db.commit()
            return {"memory_id": memory_id, "status": "deleted"}

        vector = embed_text(memory.text)
        ensure_user_memories_collection(vector_size=len(vector))

        payload = {
            "user_id": str(memory.user_id),
            "memory_id": str(memory.id),
            "memory_type": memory.memory_type,
            "source": memory.source,
            "source_object_type": memory.source_object_type,
            "source_object_id": memory.source_object_id,
            "confidence": float(memory.confidence),
            "importance": float(memory.importance),
            "is_core": memory.is_core,
            "is_active": memory.is_active,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
            "last_reinforced_at": memory.last_reinforced_at.isoformat() if memory.last_reinforced_at else None,
            "metadata": memory.metadata_ or {},
        }
        upsert_user_memory(point_id=point_id, vector=vector, payload=payload)

        if memory.qdrant_point_id != point_id:
            memory.qdrant_point_id = point_id
            db.commit()

        return {"memory_id": memory_id, "status": "synced", "vector_size": len(vector)}
    except Exception as e:
        logger.error(f"Error syncing memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
