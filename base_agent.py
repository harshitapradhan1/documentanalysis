from abc import ABC, abstractmethod
from typing import Dict, Any
from shared_memory import SharedMemory, DocumentMetadata
from datetime import datetime
import uuid

class BaseAgent(ABC):
    def __init__(self, shared_memory: SharedMemory):
        self.shared_memory = shared_memory

    def generate_doc_id(self) -> str:
        """Generate a unique document ID."""
        return str(uuid.uuid4())

    def store_initial_metadata(self, source: str, file_type: str) -> DocumentMetadata:
        """Create and store initial document metadata."""
        metadata = DocumentMetadata(
            source=source,
            file_type=file_type,
            timestamp=datetime.utcnow()
        )
        return metadata

    @abstractmethod
    def process(self, content: Any, source: str) -> Dict[str, Any]:
        """Process the input content and return structured data."""
        pass

    def log_to_memory(self, doc_id: str, content: Dict[str, Any], metadata: DocumentMetadata) -> None:
        """Log processed content and metadata to shared memory."""
        self.shared_memory.store_document(doc_id, content, metadata) 