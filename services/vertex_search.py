import os
import logging
from typing import List, Dict, Any, Optional

from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

logger = logging.getLogger(__name__)

VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_INDEX_ENDPOINT_ID = os.getenv("VERTEX_INDEX_ENDPOINT_ID")
VERTEX_DEPLOYED_INDEX_ID = os.getenv("VERTEX_DEPLOYED_INDEX_ID")

class VertexSearchError(Exception):
    pass

def _get_index_endpoint():
    if not VERTEX_PROJECT_ID or not VERTEX_INDEX_ENDPOINT_ID or not VERTEX_DEPLOYED_INDEX_ID:
        logger.warning("Vertex AI variables not fully configured. Using mock endpoint.")
        return None
        
    aiplatform.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)
    
    return aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=VERTEX_INDEX_ENDPOINT_ID
    )

def embed_text(text: str) -> List[float]:
    """Uses Vertex AI to generate text embeddings"""
    if not VERTEX_PROJECT_ID:
        # Mock embedding of 768 dims if no GCP set up
        return [0.01] * 768
        
    import vertexai
    vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)
    
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embeddings = model.get_embeddings([text])
    return embeddings[0].values

def upsert_datapoints(points: List[Dict[str, Any]]):
    """
    Push vectors to Vertex AI Vector Search.
    `points` should be a list of dictionaries with 'id' and 'embedding'.
    Example: [{"id": "user-123-mem-456", "embedding": [0.1, 0.2, ...]}]
    """
    endpoint = _get_index_endpoint()
    if not endpoint:
        logger.info(f"Mock upsert: {len(points)} points")
        return
        
    formatted_points = []
    for point in points:
        formatted_points.append(
            aiplatform.matching_engine.matching_engine_index_endpoint.IndexDatapoint(
                datapoint_id=point["id"],
                feature_vector=point["embedding"]
            )
        )
        
    try:
        endpoint.upsert_datapoints(
            deployed_index_id=VERTEX_DEPLOYED_INDEX_ID,
            datapoints=formatted_points
        )
    except Exception as e:
        logger.error(f"Failed to upsert to Vertex AI: {e}")
        raise VertexSearchError(f"Upsert failed: {e}")

def find_neighbors(vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Find nearest neighbors for a given vector.
    """
    endpoint = _get_index_endpoint()
    if not endpoint:
        logger.info("Mock find_neighbors")
        return []
        
    try:
        response = endpoint.find_neighbors(
            deployed_index_id=VERTEX_DEPLOYED_INDEX_ID,
            queries=[vector],
            num_neighbors=top_k
        )
        
        results = []
        if response and len(response) > 0:
            for neighbor in response[0]:
                results.append({
                    "id": neighbor.id,
                    "distance": neighbor.distance
                })
        return results
    except Exception as e:
        logger.error(f"Failed to query Vertex AI: {e}")
        raise VertexSearchError(f"Query failed: {e}")
