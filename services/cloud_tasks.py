import json
import os
import logging

try:
    from google.cloud import tasks_v2
except ImportError:
    tasks_v2 = None

logger = logging.getLogger(__name__)

def enqueue_task(endpoint: str, payload: dict) -> bool:
    """
    Enqueues an HTTP POST task to Google Cloud Tasks.
    
    endpoint: The relative path to hit (e.g. '/internal/tasks/sync-memory')
    payload: A dictionary containing the JSON payload for the POST request
    """
    project = os.getenv("GCP_PROJECT")
    location = os.getenv("GCP_LOCATION")
    queue = os.getenv("GCP_QUEUE_NAME")
    service_url = os.getenv("PERSONALIZATION_SERVICE_URL") # E.g. Cloud Run URL

    if not all([project, location, queue, service_url]):
        logger.warning(
            "Cloud Tasks env vars missing (GCP_PROJECT, GCP_LOCATION, GCP_QUEUE_NAME, PERSONALIZATION_SERVICE_URL). "
            f"Falling back to local mock for endpoint: {endpoint}"
        )
        logger.info(f"[MOCK ENQUEUE] Endpoint: {endpoint} | Payload: {payload}")
        return True

    if tasks_v2 is None:
        logger.error("google-cloud-tasks is not installed.")
        return False

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)

    url = f"{service_url.rstrip('/')}{endpoint}"
    
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }

    try:
        response = client.create_task(request={"parent": parent, "task": task})
        logger.debug(f"Created task {response.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create task in GCP: {e}")
        return False
