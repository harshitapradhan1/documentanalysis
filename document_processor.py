import os
import json
import logging
import requests
from typing import Tuple, Dict, Any
import PyPDF2
import docx
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, api_key: str):
        """Initialize the document processor with API key."""
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.json'}

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate file type and existence."""
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.allowed_extensions:
            return False, f"Unsupported file type. Allowed types: {', '.join(self.allowed_extensions)}"
        
        return True, ""

    def extract_text(self, file_path: str) -> str:
        """Extract text content from different file types."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.doc', '.docx']:
                return self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                return self._extract_from_txt(file_path)
            elif file_extension == '.json':
                return self._extract_from_json(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise

    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise

    def _extract_from_json(self, file_path: str) -> str:
        """Extract text from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error extracting text from JSON: {str(e)}")
            raise

    def _truncate_text(self, text: str, max_length: int = 4000) -> str:
        """Truncate text to a maximum length."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "... [content truncated]"

    def process_with_perplexity(self, text_content: str, file_extension: str) -> Dict[str, Any]:
        """Process text content with Perplexity API using Sonar model."""
        try:
            # Truncate content if too long
            text_content = self._truncate_text(text_content)
            
            # Prepare the prompt based on file type
            if file_extension == '.json':
                prompt = f"""Analyze this JSON document and provide a detailed summary in a clean, structured format without markdown:

                Document Structure:
                - Describe the overall structure and organization
                - List the main components and their purposes
                - Explain the data types used
                - Describe relationships between components
                - Explain the likely purpose of this JSON

                Document content:
                {text_content}"""
            else:
                prompt = f"""Analyze this document and provide a comprehensive summary in a clean, structured format without markdown:

                Main Topics:
                - List and explain the main topics covered
                - Highlight key themes and subjects
                - Note any recurring elements

                Key Points:
                - Extract and summarize the most important points
                - Include specific details and numbers
                - Note any critical information

                Document Type:
                - Identify the type of document
                - Explain its format and structure
                - Note any standard elements

                Purpose:
                - Explain the main purpose of the document
                - Describe its intended audience
                - Note any specific goals

                Important Details:
                - List critical information and data points
                - Note any deadlines or dates
                - Highlight any requirements or conditions

                Document content:
                {text_content}"""

            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a document analysis expert. Provide clear, structured analysis without markdown formatting. Use simple bullet points and clear sections."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            logger.info("Sending request to Perplexity API")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout
            )
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            response_data = response.json()
            if 'error' in response_data:
                raise Exception(f"API error: {response_data['error']}")
            
            logger.info("Successfully received response from Perplexity API")
            return response_data

        except requests.exceptions.Timeout:
            logger.error("Request to Perplexity API timed out")
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error processing with Perplexity: {str(e)}")
            raise Exception(f"Error processing with Perplexity: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in process_with_perplexity: {str(e)}")
            raise

    def get_agent_response(self, perplexity_response: Dict[str, Any], file_extension: str) -> Dict[str, Any]:
        """Get agent-specific response based on the initial analysis."""
        try:
            analysis = perplexity_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not analysis:
                raise ValueError("No analysis content found in Perplexity response")
            
            # Prepare the follow-up prompt based on file type
            if file_extension == '.json':
                prompt = f"""Based on this JSON analysis, provide specific recommendations in a clean, structured format without markdown:

                Data Structure Improvements:
                - List specific structural improvements
                - Suggest optimizations
                - Note any redundancies

                Validation Needs:
                - Identify required validations
                - Suggest validation rules
                - Note any data constraints

                Integration Suggestions:
                - List potential integration points
                - Suggest integration methods
                - Note any dependencies

                Best Practices:
                - List recommended practices
                - Suggest improvements
                - Note any standards to follow

                Security Considerations:
                - List security concerns
                - Suggest security measures
                - Note any vulnerabilities

                Analysis:
                {analysis}"""
            else:
                prompt = f"""Based on this document analysis, provide actionable insights in a clean, structured format without markdown:

                Key Takeaways:
                - List the most important findings
                - Highlight critical points
                - Note any surprises or concerns

                Action Items:
                - List specific actions needed
                - Assign priorities
                - Note any dependencies

                Recommendations:
                - List specific recommendations
                - Explain their benefits
                - Note implementation considerations

                Next Steps:
                - List immediate next steps
                - Suggest a timeline
                - Note any prerequisites

                Additional Considerations:
                - List important factors to consider
                - Note potential challenges
                - Suggest risk mitigation strategies

                Analysis:
                {analysis}"""

            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert document analyst providing actionable insights and recommendations. Use simple bullet points and clear sections without markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            logger.info("Sending follow-up request to Perplexity API")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout
            )
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            response_data = response.json()
            if 'error' in response_data:
                raise Exception(f"API error: {response_data['error']}")
            
            logger.info("Successfully received follow-up response from Perplexity API")
            return response_data

        except requests.exceptions.Timeout:
            logger.error("Request to Perplexity API timed out")
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting agent response: {str(e)}")
            raise Exception(f"Error getting agent response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_agent_response: {str(e)}")
            raise 