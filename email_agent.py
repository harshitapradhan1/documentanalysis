import re
import os
import requests
from typing import Dict, Any, Tuple
from base_agent import BaseAgent
from shared_memory import DocumentMetadata

class EmailAgent(BaseAgent):
    def __init__(self, shared_memory):
        super().__init__(shared_memory)
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.api_url = "https://api.perplexity.ai/chat/completions"

    def extract_email_headers(self, content: str) -> Dict[str, str]:
        """Extract basic email headers using regex patterns."""
        headers = {}
        
        # Extract sender
        sender_match = re.search(r'From:\s*(.*?)(?:\n|$)', content)
        if sender_match:
            headers['sender'] = sender_match.group(1).strip()
            
        # Extract subject
        subject_match = re.search(r'Subject:\s*(.*?)(?:\n|$)', content)
        if subject_match:
            headers['subject'] = subject_match.group(1).strip()
            
        return headers

    def analyze_email_content(self, content: str) -> Dict[str, Any]:
        """Use Perplexity API to analyze email content."""
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze this email content and extract:
        1. Intent (Invoice, RFQ, Complaint, Regulation, Other)
        2. Urgency level (High, Medium, Low)
        3. A brief summary (max 2 sentences)
        
        Email content:
        {content[:1000]}  # Limit content length for API
        
        Respond in JSON format with keys: intent, urgency, summary"""
        
        data = {
            "model": "mixtral-8x7b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            analysis = response.json()['choices'][0]['message']['content']
            return eval(analysis)  # Convert string JSON to dict
        except Exception as e:
            print(f"Error analyzing email content: {e}")
            return {
                "intent": "Other",
                "urgency": "Medium",
                "summary": "Failed to analyze email content"
            }

    def extract_thread_id(self, content: str) -> str:
        """Extract or generate thread ID from email content."""
        # Look for common email thread identifiers
        thread_match = re.search(r'Thread-Id:\s*(.*?)(?:\n|$)', content)
        if thread_match:
            return thread_match.group(1).strip()
        
        # If no thread ID found, generate one based on subject
        subject_match = re.search(r'Subject:\s*(.*?)(?:\n|$)', content)
        if subject_match:
            subject = subject_match.group(1).strip()
            return f"thread_{hash(subject)}"
        
        return self.generate_doc_id()

    def process(self, content: str, source: str) -> Dict[str, Any]:
        """Process email content and extract structured information."""
        # Extract basic headers
        headers = self.extract_email_headers(content)
        
        # Analyze content using Perplexity
        analysis = self.analyze_email_content(content)
        
        # Generate or extract thread ID
        thread_id = self.extract_thread_id(content)
        
        # Create document ID and metadata
        doc_id = self.generate_doc_id()
        metadata = self.store_initial_metadata(source, "EMAIL")
        metadata.intent = analysis['intent']
        metadata.thread_id = thread_id
        
        result = {
            "headers": headers,
            "analysis": analysis,
            "thread_id": thread_id,
            "doc_id": doc_id
        }
        
        self.log_to_memory(doc_id, result, metadata)
        return result 