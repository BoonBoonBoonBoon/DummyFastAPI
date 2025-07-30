# Utility function to measure token size and trim/chunk context using tiktoken
def prepare_context_for_llm(texts, model="gpt-4-turbo", max_tokens=8000):
    """
    Combine texts, measure token count, and trim/chunk to fit max_tokens.
    Returns the combined context and the token count.
    """
    enc = tiktoken.encoding_for_model(model)
    combined = "\n".join(texts)
    tokens = enc.encode(combined)
    if len(tokens) > max_tokens:
        # Trim to max_tokens
        tokens = tokens[:max_tokens]
        combined = enc.decode(tokens)
    return combined, len(tokens)
from fastapi import FastAPI
# Import Qdrant client

import os
from qdrant_client import QdrantClient
import tiktoken
import logging
from dotenv import load_dotenv

# Load environment variables from .env if present (for local dev)
load_dotenv()


# Set up basic logging
logging.basicConfig(level=logging.INFO)
app = FastAPI()

# Connect to Qdrant cloud using your endpoint and API key
# The QdrantClient object allows you to interact with your Qdrant cluster (search, insert, etc.)
# Get Qdrant credentials from environment variables
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)
# Now you can use qdrant_client in your endpoints to interact with your Qdrant collection

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Railway! Qdrant is connected."}


# Endpoint to list all Qdrant collections
@app.get("/collections")
def list_collections():
    """
    Returns a list of all collections in the connected Qdrant cluster.
    If there is an error, returns the error message for debugging.
    """
    try:
        collections = qdrant_client.get_collections()
        return collections
    except Exception as e:
        return {"error": str(e)}


# Endpoint to create indexes for client_id and lead_id
@app.post("/create-indexes")
def create_indexes():
    """
    Creates indexes for 'client_id' (integer) and 'lead_id' (keyword) in the 'client_001_memory' collection.
    """
    try:
        qdrant_client.create_payload_index(
            collection_name="client_001_memory",
            field_name="client_id",
            field_schema="integer"
        )
        qdrant_client.create_payload_index(
            collection_name="client_001_memory",
            field_name="lead_id",
            field_schema="keyword"
        )
        return {"status": "Indexes created for client_id and lead_id."}
    except Exception as e:
        return {"error": str(e)}


# Endpoint to search for client 123 in 'client_001_memory' collection by metadata tag 'client_id'
@app.get("/search-client")

from fastapi import Query

@app.get("/search-client")
def search_client(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    max_tokens: int = Query(8000, ge=100, le=32000),
    model: str = Query("gpt-4-turbo"),
    include_fields: str = Query("summary,text", description="Comma-separated fields to include in context")
):
    """
    Searches for points in the 'client_001_memory' collection where metadata 'client_id' == 123.
    Uses the 'summary' field from each payload if present, otherwise falls back to 'text'.
    Sorts by timestamp descending to prioritize recent emails.
    """
    try:
        result = qdrant_client.scroll(
            collection_name="client_001_memory",
            scroll_filter={
                "must": [
                    {"key": "client_id", "match": {"value": 123}}
                ]
            },
            limit=limit + offset
        )
        points, _ = result
        if not points:
            return {
                "points": [],
                "context": "",
                "token_count": 0,
                "message": "No results found."
            }
        # Sort points by timestamp descending (most recent first)
        def get_timestamp(point):
            payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
            return payload.get('timestamp', '')
        points_sorted = sorted(points, key=get_timestamp, reverse=True)
        # Pagination
        paged_points = points_sorted[offset:offset+limit]
        # Field selection
        fields = [f.strip() for f in include_fields.split(",") if f.strip()]
        payload_texts = []
        for point in paged_points:
            payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
            for field in fields:
                if field in payload:
                    payload_texts.append(str(payload[field]))
                    break
        context, token_count = prepare_context_for_llm(payload_texts, model=model, max_tokens=max_tokens)
        serializable_points = []
        for point in paged_points:
            if hasattr(point, 'id') and hasattr(point, 'payload'):
                serializable_points.append({"id": point.id, "payload": point.payload})
            else:
                serializable_points.append(point)
        return {
            "points": serializable_points,
            "context": context,
            "token_count": token_count,
            "limit": limit,
            "offset": offset,
            "fields": fields,
            "model": model,
            "max_tokens": max_tokens
        }
    except Exception as e:
        logging.error(f"/search-client error: {e}")
        return {
            "points": [],
            "context": "",
            "token_count": 0,
            "error": str(e)
        }


# Endpoint to search for a specific client_id and lead_id
from fastapi import Query

@app.get("/search-client-lead")
@app.get("/search-client-lead")
def search_client_lead(
    client_id: int = Query(...),
    lead_id: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    max_tokens: int = Query(8000, ge=100, le=32000),
    model: str = Query("gpt-4-turbo"),
    include_fields: str = Query("summary,text", description="Comma-separated fields to include in context")
):
    """
    Searches for points in the 'client_001_memory' collection where metadata 'client_id' and 'lead_id' match the given values.
    Uses the 'summary' field from each payload if present, otherwise falls back to 'text'.
    Sorts by timestamp descending to prioritize recent emails.
    Returns points, context, and token count.
    Supports pagination, field selection, and token/model parameters.
    """
    try:
        result = qdrant_client.scroll(
            collection_name="client_001_memory",
            scroll_filter={
                "must": [
                    {"key": "client_id", "match": {"value": client_id}},
                    {"key": "lead_id", "match": {"value": lead_id}}
                ]
            },
            limit=limit + offset
        )
        points, _ = result
        if not points:
            return {
                "points": [],
                "context": "",
                "token_count": 0,
                "message": "No results found."
            }
        # Sort points by timestamp descending (most recent first)
        def get_timestamp(point):
            payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
            return payload.get('timestamp', '')
        points_sorted = sorted(points, key=get_timestamp, reverse=True)
        # Pagination
        paged_points = points_sorted[offset:offset+limit]
        # Field selection
        fields = [f.strip() for f in include_fields.split(",") if f.strip()]
        payload_texts = []
        for point in paged_points:
            payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
            for field in fields:
                if field in payload:
                    payload_texts.append(str(payload[field]))
                    break
        context, token_count = prepare_context_for_llm(payload_texts, model=model, max_tokens=max_tokens)
        serializable_points = []
        for point in paged_points:
            if hasattr(point, 'id') and hasattr(point, 'payload'):
                serializable_points.append({"id": point.id, "payload": point.payload})
            else:
                serializable_points.append(point)
        return {
            "points": serializable_points,
            "context": context,
            "token_count": token_count,
            "limit": limit,
            "offset": offset,
            "fields": fields,
            "model": model,
            "max_tokens": max_tokens
        }
    except Exception as e:
        logging.error(f"/search-client-lead error: {e}")
        return {
            "points": [],
            "context": "",
            "token_count": 0,
            "error": str(e)
        }
