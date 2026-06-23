from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, BinaryIO

class MetadataStore(ABC):
    @abstractmethod
    async def save_execution(self, execution_data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def update_execution(self, execution_id: str, update_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def add_step(self, execution_id: str, step_data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def update_step(self, step_id: str, update_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_executions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        pass

class DocumentStore(ABC):
    @abstractmethod
    async def upload(self, file_content: BinaryIO, filename: str, mime_type: str) -> str:
        pass

    @abstractmethod
    async def download(self, document_id: str) -> BinaryIO:
        pass

    @abstractmethod
    async def get_metadata(self, document_id: str) -> Dict[str, Any]:
        pass

class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, collection: str, points: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    async def search(self, collection: str, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        pass
