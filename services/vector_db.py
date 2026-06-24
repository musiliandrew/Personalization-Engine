import os
import logging
from typing import Any, Dict, Iterable, List
import requests

logger = logging.getLogger(__name__)

LEGACY_VECTOR_VALUE = os.getenv("CAREERSCOPE_VECTOR_API")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL") or (
    LEGACY_VECTOR_VALUE if LEGACY_VECTOR_VALUE and LEGACY_VECTOR_VALUE.startswith(("http://", "https://")) else None
)
QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or (
    LEGACY_VECTOR_VALUE if LEGACY_VECTOR_VALUE and not LEGACY_VECTOR_VALUE.startswith(("http://", "https://")) else None
)
USER_MEMORIES_COLLECTION = os.getenv("QDRANT_USER_MEMORIES_COLLECTION", "user_memories")

class VectorDBError(RuntimeError):
    pass

def _require_env(name: str, value: str | None):
    if not value:
        raise VectorDBError(f"Missing required environment variable: {name}")

def embed_text(text: str) -> List[float]:
    _require_env("EMBEDDING_API_URL", EMBEDDING_API_URL)
    try:
        resp = requests.post(
            EMBEDDING_API_URL.rstrip("/") + "/embed",
            json={"text": text},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        emb = data.get("embedding")
        if not isinstance(emb, list):
            raise VectorDBError("Vector API did not return 'embedding' list")
        return [float(x) for x in emb]
    except Exception as exc:
        logger.error("VectorDB.embed_text failed: %s", exc)
        raise

def _qdrant_url(path: str) -> str:
    _require_env("QDRANT_ENDPOINT", QDRANT_ENDPOINT)
    base = QDRANT_ENDPOINT.rstrip("/")
    return f"{base}{path}"

def _qdrant_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if QDRANT_API_KEY:
        headers["api-key"] = QDRANT_API_KEY
    return headers

def ensure_user_memories_collection(vector_size: int, distance: str = "Cosine") -> None:
    url = _qdrant_url(f"/collections/{USER_MEMORIES_COLLECTION}")
    try:
        r = requests.get(url, headers=_qdrant_headers(), timeout=5)
        if r.status_code == 200:
            return
    except Exception:
        pass
    payload = {
        "vectors": {
            "size": vector_size,
            "distance": distance,
        }
    }
    resp = requests.put(url, headers=_qdrant_headers(), json=payload, timeout=10)
    if resp.status_code not in (200, 201):
        raise VectorDBError(f"Failed to create Qdrant collection: {resp.text}")

def upsert_user_memory(point_id: str, vector: List[float], payload: Dict[str, Any]) -> None:
    url = _qdrant_url(f"/collections/{USER_MEMORIES_COLLECTION}/points")
    point = {
        "id": point_id,
        "vector": vector,
        "payload": payload,
    }
    resp = requests.put(url, headers=_qdrant_headers(), json={"points": [point]}, timeout=20)
    if resp.status_code not in (200, 202):
        raise VectorDBError(f"Failed to upsert user memory vector: {resp.text}")

def delete_user_memory(point_id: str) -> None:
    url = _qdrant_url(f"/collections/{USER_MEMORIES_COLLECTION}/points/delete")
    resp = requests.post(
        url,
        headers=_qdrant_headers(),
        json={"points": [point_id]},
        timeout=15,
    )
    if resp.status_code not in (200, 202):
        raise VectorDBError(f"Failed to delete user memory vector: {resp.text}")
