from fastapi import FastAPI, Request
from pydantic import BaseModel
import logging

from routers import internal_tasks
from services.cloud_tasks import enqueue_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CareerScoper Personalization Engine")

# Include the internal tasks router
app.include_router(internal_tasks.router)

class WebhookPayload(BaseModel):
    event_type: str
    object_type: str
    object_id: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/webhooks/profile_updated")
def profile_updated_webhook(payload: WebhookPayload):
    logger.info(f"Received webhook: {payload.event_type} for {payload.object_type} {payload.object_id}")
    
    # Delegate the heavy lifting to Cloud Tasks
    # This replaces the old Celery sync_user_memory_task.delay(memory_id) call
    # Here, we assume object_id is the memory_id we want to sync
    enqueue_task(
        endpoint="/internal/tasks/sync-memory",
        payload={"memory_id": payload.object_id}
    )
    
    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
