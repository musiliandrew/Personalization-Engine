from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CareerScoper Personalization Engine")

class WebhookPayload(BaseModel):
    event_type: str
    object_type: str
    object_id: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/webhooks/profile_updated")
def profile_updated_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    logger.info(f"Received webhook: {payload.event_type} for {payload.object_type} {payload.object_id}")
    # TODO: Add logic to fetch profile and sync memories
    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
