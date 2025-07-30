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
from dotenv import load_dotenv

# Load environment variables from .env if present (for local dev)
load_dotenv()

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

def search_client():
    """
    Searches for points in the 'client_001_memory' collection where metadata 'client_id' == 123.
    After fetching, combines the payloads, measures token count, and trims context for LLM use.
    """
    try:
        result = qdrant_client.scroll(
            collection_name="client_001_memory",
            scroll_filter={
                "must": [
                    {"key": "client_id", "match": {"value": 123}}
                ]
            },
            limit=10
        )
        points, _ = result
        # Extract text fields from payloads (customize as needed)
        payload_texts = []
        for point in points:
            payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
            # Combine all string values in the payload
            text = " ".join(str(v) for v in payload.values() if isinstance(v, (str, int, float)))
            payload_texts.append(text)
        context, token_count = prepare_context_for_llm(payload_texts)
        return {
            "points": points,
            "context": context,
            "token_count": token_count
        }
    except Exception as e:
        return {"error": str(e)}


# Endpoint to search for a specific client_id and lead_id
from fastapi import Query

@app.get("/search-client-lead")
def search_client_lead(client_id: int = Query(...), lead_id: str = Query(...)):
    """
    Searches for points in the 'client_001_memory' collection where metadata 'client_id' and 'lead_id' match the given values.
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
            limit=10
        )
        points, _ = result
        return {"points": points}
    except Exception as e:
        return {"error": str(e)}
