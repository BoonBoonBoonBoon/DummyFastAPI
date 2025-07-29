from fastapi import FastAPI
# Import Qdrant client

import os
from qdrant_client import QdrantClient
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
