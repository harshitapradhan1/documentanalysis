from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DocumentMetadata:
    source: str
    file_type: str
    timestamp: datetime
    intent: Optional[str] = None
    thread_id: Optional[str] = None

class SharedMemory:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._metadata: Dict[str, DocumentMetadata] = {}

    def store_document(self, doc_id: str, content: Dict[str, Any], metadata: DocumentMetadata) -> None:
        """Store document content and its metadata."""
        self._store[doc_id] = content
        self._metadata[doc_id] = metadata

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document content by ID."""
        return self._store.get(doc_id)

    def get_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Retrieve document metadata by ID."""
        return self._metadata.get(doc_id)

    def update_document(self, doc_id: str, content: Dict[str, Any]) -> None:
        """Update existing document content."""
        if doc_id in self._store:
            self._store[doc_id].update(content)

    def update_metadata(self, doc_id: str, metadata: DocumentMetadata) -> None:
        """Update existing document metadata."""
        if doc_id in self._metadata:
            self._metadata[doc_id] = metadata

    def get_thread_documents(self, thread_id: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all documents belonging to a specific thread."""
        return {
            doc_id: content
            for doc_id, content in self._store.items()
            if self._metadata[doc_id].thread_id == thread_id
        }

    def store_perplexity_response(self, response: Dict[str, Any], thread_id: str) -> str:
        """Store a Perplexity response and return its entry ID."""
        entry_id = f"perp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{len(self._store)}"
        self._store[entry_id] = response
        self._metadata[entry_id] = DocumentMetadata(
            source="perplexity_api",
            file_type="api_response",
            timestamp=datetime.now(),
            thread_id=thread_id
        )
        return entry_id

    def get_perplexity_response(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Perplexity response by entry ID."""
        return self._store.get(entry_id)

    def get_thread_responses(self, thread_id: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all Perplexity responses for a specific thread."""
        return {
            doc_id: content
            for doc_id, content in self._store.items()
            if self._metadata[doc_id].source == "perplexity_api" and self._metadata[doc_id].thread_id == thread_id
        }

    def update_perplexity_response(self, entry_id: str, response: Dict[str, Any]) -> None:
        """Update an existing Perplexity response."""
        if entry_id in self._store:
            self._store[entry_id] = response
            self._metadata[entry_id] = DocumentMetadata(
                source="perplexity_api",
                file_type="api_response",
                timestamp=datetime.now(),
                thread_id=self._metadata[entry_id].thread_id
            )

    def delete_perplexity_response(self, entry_id: str) -> None:
        """Delete a Perplexity response."""
        if entry_id in self._store:
            del self._store[entry_id]
            del self._metadata[entry_id]

    def search_responses(self, thread_id: str, model: str, min_confidence: float) -> Dict[str, Dict[str, Any]]:
        """Search for Perplexity responses based on thread ID, model, and minimum confidence."""
        return {
            doc_id: content
            for doc_id, content in self._store.items()
            if self._metadata[doc_id].source == "perplexity_api" and
               self._metadata[doc_id].thread_id == thread_id and
               self._metadata[doc_id].file_type == "api_response" and
               content.get("model") == model and
               content.get("confidence", 0.0) >= min_confidence
        } 