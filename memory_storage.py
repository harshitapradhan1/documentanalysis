import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

logger = logging.getLogger(__name__)

class MemoryStorage:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoryStorage, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        """Initialize the storage with empty structures."""
        self._storage = {
            'documents': {},  # Store document processing results
            'logs': [],      # Store processing logs
            'stats': {       # Store processing statistics
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'by_type': {}
            }
        }
        logger.info("Memory storage initialized")

    def store_document(self, doc_id: str, content: Dict[str, Any]) -> None:
        """Store document processing results."""
        with self._lock:
            self._storage['documents'][doc_id] = {
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            logger.info(f"Stored document {doc_id}")

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document processing results."""
        with self._lock:
            return self._storage['documents'].get(doc_id)

    def add_log(self, level: str, message: str, context: Dict[str, Any] = None) -> None:
        """Add a log entry with context."""
        with self._lock:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'context': context or {}
            }
            self._storage['logs'].append(log_entry)
            logger.info(f"Added log entry: {message}")

    def get_logs(self, level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve logs with optional filtering."""
        with self._lock:
            logs = self._storage['logs']
            if level:
                logs = [log for log in logs if log['level'] == level]
            return logs[-limit:]

    def update_stats(self, doc_type: str, success: bool) -> None:
        """Update processing statistics."""
        with self._lock:
            self._storage['stats']['total_processed'] += 1
            if success:
                self._storage['stats']['successful'] += 1
            else:
                self._storage['stats']['failed'] += 1
            
            if doc_type not in self._storage['stats']['by_type']:
                self._storage['stats']['by_type'][doc_type] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0
                }
            
            self._storage['stats']['by_type'][doc_type]['total'] += 1
            if success:
                self._storage['stats']['by_type'][doc_type]['successful'] += 1
            else:
                self._storage['stats']['by_type'][doc_type]['failed'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        with self._lock:
            return self._storage['stats']

    def clear_old_logs(self, days: int = 7) -> None:
        """Clear logs older than specified days."""
        with self._lock:
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            self._storage['logs'] = [
                log for log in self._storage['logs']
                if datetime.fromisoformat(log['timestamp']).timestamp() > cutoff
            ]
            logger.info(f"Cleared logs older than {days} days")

    def export_data(self) -> Dict[str, Any]:
        """Export all stored data."""
        with self._lock:
            return self._storage.copy()

    def import_data(self, data: Dict[str, Any]) -> None:
        """Import data into storage."""
        with self._lock:
            self._storage = data
            logger.info("Imported data into storage")

    def clear_all(self) -> None:
        """Clear all stored data."""
        with self._lock:
            self._initialize()
            logger.info("Cleared all stored data") 