from typing import Any, Dict, List
from qdrant_client import QdrantClient
from core.storage.base import VectorStore
from core.config import settings

class QdrantVectorStore(VectorStore):
    def __init__(self, url: str = settings.qdrant_url, api_key: str = settings.qdrant_api_key):
        self.url = url
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = QdrantClient(url=self.url, api_key=self.api_key)
        return self._client

    async def upsert(self, collection: str, points: List[Dict[str, Any]]) -> None:
        print(f"Upserting {len(points)} points to collection {collection}...")

    async def search(self, collection: str, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        print(f"Searching collection {collection} with vector...")
        return []
