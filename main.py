import os
from dotenv import load_dotenv
from shared_memory import SharedMemory
from classifier_agent import ClassifierAgent
from json_agent import JSONAgent
from email_agent import EmailAgent

class DocumentProcessor:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize shared memory
        self.shared_memory = SharedMemory()
        
        # Initialize agents
        self.classifier = ClassifierAgent(self.shared_memory)
        self.json_agent = JSONAgent(self.shared_memory)
        self.email_agent = EmailAgent(self.shared_memory)

    def process_document(self, content: str, source: str) -> dict:
        """Process a document through the system."""
        try:
            # First, classify the document
            classification = self.classifier.process(content, source)
            
            # Route to appropriate agent based on file type
            if classification["file_type"] == "JSON":
                result = self.json_agent.process(content, source)
            elif classification["file_type"] == "EMAIL":
                result = self.email_agent.process(content, source)
            else:
                raise ValueError(f"Unsupported file type: {classification['file_type']}")
            
            return {
                "status": "success",
                "classification": classification,
                "processing_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

def main():
    # Example usage
    processor = DocumentProcessor()
    
    # Example JSON document
    json_content = """
    {
        "invoice_number": "INV-001",
        "amount": 1000.00,
        "date": "2024-03-20",
        "vendor": "Example Corp"
    }
    """
    
    # Example email content
    email_content = """
    From: sender@example.com
    Subject: Invoice Payment Request
    Thread-Id: THREAD-123
    
    Dear Sir/Madam,
    
    Please find attached the invoice for our recent services.
    Payment is due within 30 days.
    
    Best regards,
    John Doe
    """
    
    # Process documents
    print("\nProcessing JSON document:")
    json_result = processor.process_document(json_content, "example.json")
    print(json_result)
    
    print("\nProcessing email document:")
    email_result = processor.process_document(email_content, "example.txt")
    print(email_result)

if __name__ == "__main__":
    main() 