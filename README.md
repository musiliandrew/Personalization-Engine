# CareerScoper Personalization System

The Personalization System is a **standalone FastAPI microservice** that powers the dynamic, user-specific data layers of the CareerScoper platform. It manages user memories, vector embeddings, and aggregates complex personalized data structures (like the Mission Control Dashboard and Company Intelligence Roadmaps).

## Architecture Overview
This microservice operates independently of the main API gateway, specifically handling heavy analytical and vector operations that would otherwise block the primary application layer.

1. **Vector Search Integration:** Natively interfaces with Google Cloud Vertex AI Vector Search to embed, store, and query user memories, skills, and semantic job requirements.
2. **Asynchronous ORM Parsing:** Reads directly from the shared PostgreSQL database (using Django ORM in a FastAPI `run_in_threadpool`) to rapidly assemble massive, personalized JSON dashboard objects without hitting HTTP bottlenecks.
3. **Event-Driven Memory Sync:** Listens for webhook triggers (via Google Cloud Tasks) when a user's profile updates, automatically recalculating their capabilities and syncing their context to the Vector Database.

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

- **`GET /dashboard/mission-control/{user_id}`**: Retrieves the unified Mission Control payload containing recent applications, job matches, and upcoming events.
- **`GET /dashboard/company-intelligence/{user_id}/{company_id}`**: Assembles a dynamic Company Intelligence Roadmap, comparing user skills to company tech stacks and recent news.
- **`GET /dashboard/recommended-jobs/{user_id}`**: Performs a semantic search against the Vertex AI Vector Database to return jobs matching the user's implicit profile.
- **`POST /internal/tasks/sync-memory`**: Internal webhook designed for Google Cloud Tasks. Syncs user updates into the canonical Memory Graph and Vector Index.
