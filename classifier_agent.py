import os
import json
import requests
from typing import Dict, Any, Tuple
from base_agent import BaseAgent
from shared_memory import DocumentMetadata

class ClassifierAgent(BaseAgent):
    def __init__(self, shared_memory):
        super().__init__(shared_memory)
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.api_url = "https://api.perplexity.ai/chat/completions"

    def detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension."""
        ext = file_path.lower().split('.')[-1]
        if ext == 'pdf':
            return 'PDF'
        elif ext == 'json':
            return 'JSON'
        elif ext == 'txt':
            return 'EMAIL'
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def classify_intent(self, content: str) -> str:
        """Use Perplexity API to classify document intent."""
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze the following content and classify its intent into one of these categories:
        - Invoice
        - RFQ (Request for Quote)
        - Complaint
        - Regulation
        - Other
        
        Content: {content[:1000]}  # Limit content length for API
        
        Respond with just the category name."""

        data = {
            "model": "mixtral-8x7b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            intent = response.json()['choices'][0]['message']['content'].strip()
            return intent
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "Other"

    def process(self, content: str, source: str) -> Dict[str, Any]:
        """Process the input and determine its type and intent."""
        file_type = self.detect_file_type(source)
        intent = self.classify_intent(content)
        
        doc_id = self.generate_doc_id()
        metadata = self.store_initial_metadata(source, file_type)
        metadata.intent = intent
        
        result = {
            "file_type": file_type,
            "intent": intent,
            "source": source,
            "doc_id": doc_id
        }
        
        self.log_to_memory(doc_id, result, metadata)
        return result 