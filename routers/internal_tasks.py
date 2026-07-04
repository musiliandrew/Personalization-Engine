from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from database import SessionLocal
from models import UserMemory
from services.vertex_search import (
    embed_text,
    upsert_datapoints
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
            # Vertex deletion not fully implemented in stub, normally you'd push a delete op
            # upsert_datapoints([{"id": point_id, "embedding": []}]) # Not correct for delete
            if memory.qdrant_point_id:
                memory.qdrant_point_id = None
                db.commit()
            return {"memory_id": memory_id, "status": "deleted"}

        vector = embed_text(memory.text)

        payload = {
            "id": point_id,
            "embedding": vector
            # Vertex AI currently only supports filtering via Restricts, so we'd push metadata as tokens
        }
        upsert_datapoints([payload])

        if memory.qdrant_point_id != point_id:
            memory.qdrant_point_id = point_id
            db.commit()

        return {"memory_id": memory_id, "status": "synced", "vector_size": len(vector)}
    except Exception as e:
        logger.error(f"Error syncing memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
