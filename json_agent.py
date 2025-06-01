import json
from typing import Dict, Any, List
from base_agent import BaseAgent
from shared_memory import DocumentMetadata

class JSONAgent(BaseAgent):
    def __init__(self, shared_memory):
        super().__init__(shared_memory)
        self.required_fields = {
            "Invoice": ["invoice_number", "amount", "date", "vendor"],
            "RFQ": ["request_id", "items", "deadline", "contact"],
            "Complaint": ["complaint_id", "description", "severity", "contact"],
            "Regulation": ["regulation_id", "title", "effective_date", "jurisdiction"]
        }

    def validate_json(self, content: Dict[str, Any], intent: str) -> List[str]:
        """Validate JSON against required fields for the given intent."""
        missing_fields = []
        required = self.required_fields.get(intent, [])
        
        for field in required:
            if field not in content:
                missing_fields.append(field)
        
        return missing_fields

    def standardize_json(self, content: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Transform JSON to a standardized format."""
        standardized = {
            "type": intent,
            "original_content": content,
            "standardized_fields": {}
        }
        
        # Map common fields to standardized names
        field_mapping = {
            "invoice_number": "document_id",
            "request_id": "document_id",
            "complaint_id": "document_id",
            "regulation_id": "document_id",
            "amount": "value",
            "date": "timestamp",
            "deadline": "due_date",
            "effective_date": "timestamp"
        }
        
        for old_field, new_field in field_mapping.items():
            if old_field in content:
                standardized["standardized_fields"][new_field] = content[old_field]
        
        return standardized

    def process(self, content: str, source: str) -> Dict[str, Any]:
        """Process JSON content and validate against schema."""
        try:
            # Parse JSON content
            if isinstance(content, str):
                json_content = json.loads(content)
            else:
                json_content = content
                
            # Get intent from metadata
            doc_id = self.generate_doc_id()
            metadata = self.store_initial_metadata(source, "JSON")
            intent = metadata.intent or "Other"
            
            # Validate and standardize
            missing_fields = self.validate_json(json_content, intent)
            standardized = self.standardize_json(json_content, intent)
            
            result = {
                "standardized_content": standardized,
                "validation": {
                    "is_valid": len(missing_fields) == 0,
                    "missing_fields": missing_fields
                },
                "doc_id": doc_id
            }
            
            self.log_to_memory(doc_id, result, metadata)
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}") 