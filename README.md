# Vector Personalization System

A **standalone FastAPI microservice** designed to power dynamic, user-specific data aggregation and semantic vector capabilities. It manages memory graphs, vector embeddings, and aggregates complex personalized data structures on demand.

## Architecture Overview
This microservice isolates heavy analytical queries and vector operations from generic HTTP web servers, acting as an intelligent aggregation layer.

1. **Vector Search Integration:** Natively interfaces with Google Cloud Vertex AI Vector Search to embed, store, and query arbitrary semantic relationships (e.g. user memories or skills to external requirements).
2. **Asynchronous Aggregation:** Reads directly from PostgreSQL using a thread-pool architecture to rapidly assemble massive, personalized JSON payloads without blocking standard async event loops.
3. **Event-Driven Syncing:** Listens for external webhook triggers (e.g., via Google Cloud Tasks) to automatically recalculate dynamic state and sync context to the Vector Database.

## Running Locally

1. Create a virtual environment: `python -m venv env`
2. Activate it: `source env/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables (requires `DATABASE_URL` and `VERTEX_PROJECT_ID`):
   ```bash
   cp .env.example .env
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload --port 8001
   ```

## Key API Endpoints

- **`GET /dashboard/mission-control/{user_id}`**: Retrieves a unified, personalized payload containing aggregated metrics and recent relevant entities.
- **`GET /dashboard/recommended-jobs/{user_id}`**: Performs a semantic search against the Vertex AI Vector Database to return entities matching the user's implicit profile vector.
- **`POST /internal/tasks/sync-memory`**: Internal webhook designed for Google Cloud Tasks. Syncs payload updates into the canonical Memory Graph and Vector Index.
