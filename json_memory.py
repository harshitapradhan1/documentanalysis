import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import hashlib

class JsonMemory:
    def __init__(self, base_dir: str = "perplexity_responses"):
        """Initialize the JSON memory storage.
        
        Args:
            base_dir (str): Base directory to store response files
        """
        self.base_dir = base_dir
        self._ensure_base_dir_exists()

    def _ensure_base_dir_exists(self):
        """Ensure the base directory exists."""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _get_query_file_path(self, query: str) -> str:
        """Generate a file path for a specific query.
        
        Args:
            query (str): The query string
            
        Returns:
            str: Path to the query's JSON file
        """
        # Create a hash of the query to use as filename
        query_hash = hashlib.md5(query.encode()).hexdigest()[:10]
        timestamp = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.base_dir, f"query_{timestamp}_{query_hash}.json")

    def _ensure_query_file_exists(self, query: str) -> str:
        """Ensure the query's JSON file exists with proper structure.
        
        Args:
            query (str): The query string
            
        Returns:
            str: Path to the query's JSON file
        """
        file_path = self._get_query_file_path(query)
        if not os.path.exists(file_path):
            initial_data = {
                "query": query,
                "responses": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self._write_data(file_path, initial_data)
        return file_path

    def _read_data(self, file_path: str) -> Dict:
        """Read data from the storage file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            Dict: The stored data
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "responses": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }

    def _write_data(self, file_path: str, data: Dict):
        """Write data to the storage file.
        
        Args:
            file_path (str): Path to the JSON file
            data (Dict): Data to write
        """
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def store_perplexity_response(self, 
                                query: str,
                                response: Dict[str, Any],
                                thread_id: Optional[str] = None) -> str:
        """Store a Perplexity API response in the memory.
        
        Args:
            query (str): The original query
            response (Dict[str, Any]): The raw response from Perplexity API
            thread_id (Optional[str]): Thread or conversation ID
            
        Returns:
            str: Entry ID
        """
        file_path = self._ensure_query_file_exists(query)
        data = self._read_data(file_path)
        
        # Generate entry ID
        entry_id = f"perp_{int(time.time())}_{len(data['responses'])}"
        
        # Extract relevant information from the response
        entry = {
            "source": "perplexity_api",
            "type": "api_response",
            "timestamp": datetime.now().isoformat(),
            "extracted_values": {
                "model": response.get("model", "unknown"),
                "response_text": response.get("text", ""),
                "confidence": response.get("confidence", 0.0),
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "raw_response": response  # Store the complete response for reference
            },
            "thread_id": thread_id
        }
        
        data["responses"][entry_id] = entry
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        self._write_data(file_path, data)
        return entry_id

    def get_perplexity_response(self, query: str, entry_id: str) -> Optional[Dict]:
        """Retrieve a Perplexity response by its ID.
        
        Args:
            query (str): The original query
            entry_id (str): ID of the response to retrieve
            
        Returns:
            Optional[Dict]: The response if found, None otherwise
        """
        file_path = self._get_query_file_path(query)
        if not os.path.exists(file_path):
            return None
        data = self._read_data(file_path)
        return data["responses"].get(entry_id)

    def get_thread_responses(self, query: str, thread_id: str) -> List[Dict]:
        """Retrieve all Perplexity responses for a specific thread.
        
        Args:
            query (str): The original query
            thread_id (str): Thread ID to retrieve responses for
            
        Returns:
            List[Dict]: List of responses for the thread
        """
        file_path = self._get_query_file_path(query)
        if not os.path.exists(file_path):
            return []
        data = self._read_data(file_path)
        return [
            entry for entry in data["responses"].values()
            if entry.get("thread_id") == thread_id
        ]

    def update_perplexity_response(self, 
                                 query: str,
                                 entry_id: str, 
                                 updates: Dict[str, Any]) -> bool:
        """Update an existing Perplexity response.
        
        Args:
            query (str): The original query
            entry_id (str): ID of the response to update
            updates (Dict[str, Any]): Updates to apply
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        file_path = self._get_query_file_path(query)
        if not os.path.exists(file_path):
            return False
            
        data = self._read_data(file_path)
        if entry_id not in data["responses"]:
            return False
            
        entry = data["responses"][entry_id]
        entry["extracted_values"].update(updates)
        entry["timestamp"] = datetime.now().isoformat()
        
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        self._write_data(file_path, data)
        return True

    def delete_perplexity_response(self, query: str, entry_id: str) -> bool:
        """Delete a Perplexity response.
        
        Args:
            query (str): The original query
            entry_id (str): ID of the response to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        file_path = self._get_query_file_path(query)
        if not os.path.exists(file_path):
            return False
            
        data = self._read_data(file_path)
        if entry_id not in data["responses"]:
            return False
            
        del data["responses"][entry_id]
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        self._write_data(file_path, data)
        return True

    def search_responses(self, 
                        query: str,
                        thread_id: Optional[str] = None,
                        model: Optional[str] = None,
                        min_confidence: Optional[float] = None) -> List[Dict]:
        """Search for Perplexity responses matching specific criteria.
        
        Args:
            query (str): The original query
            thread_id (Optional[str]): Thread ID to filter by
            model (Optional[str]): Model name to filter by
            min_confidence (Optional[float]): Minimum confidence score
            
        Returns:
            List[Dict]: List of matching responses
        """
        file_path = self._get_query_file_path(query)
        if not os.path.exists(file_path):
            return []
            
        data = self._read_data(file_path)
        responses = data["responses"].values()
        
        matches = []
        for response in responses:
            if thread_id and response.get("thread_id") != thread_id:
                continue
            if model and response["extracted_values"].get("model") != model:
                continue
            if min_confidence is not None and response["extracted_values"].get("confidence", 0) < min_confidence:
                continue
            matches.append(response)
            
        return matches

    def clear_query_responses(self, query: str):
        """Clear all responses for a specific query.
        
        Args:
            query (str): The query to clear responses for
        """
        file_path = self._get_query_file_path(query)
        if os.path.exists(file_path):
            initial_data = {
                "query": query,
                "responses": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self._write_data(file_path, initial_data) 