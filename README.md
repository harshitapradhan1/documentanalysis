# AI-Driven Document Processing System

This system processes documents in various formats (PDF, JSON, and email text) using AI-powered classification and specialized agents for each document type. The system maintains a shared memory for tracking document context and enables traceability across processing steps.

## Features

- Automatic document type detection and intent classification
- Specialized processing for JSON and email documents
- Shared memory for context tracking and traceability
- AI-powered analysis using Perplexity API
- Thread tracking for email conversations
- Standardized output format for downstream systems

## Prerequisites

- Python 3.8+
- Perplexity API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Perplexity API key:
```
PERPLEXITY_API_KEY=your-api-key-here
```

## Usage

The system can be used as a Python module or through the command line:

```python
from main import DocumentProcessor

# Initialize the processor
processor = DocumentProcessor()

# Process a document
result = processor.process_document(content, source_file_path)
print(result)
```

## System Components

### 1. Classifier Agent
- Detects document type based on file extension
- Uses Perplexity API to classify document intent
- Routes documents to appropriate specialized agents

### 2. JSON Agent
- Validates JSON against required fields
- Transforms JSON to standardized format
- Flags anomalies and missing fields

### 3. Email Agent
- Extracts email headers and content
- Analyzes email intent and urgency
- Tracks email threads
- Generates structured output

### 4. Shared Memory
- Stores document metadata and content
- Maintains context across processing steps
- Enables traceability and chaining

## Example Output

### JSON Document Processing
```json
{
    "status": "success",
    "classification": {
        "file_type": "JSON",
        "intent": "Invoice",
        "source": "example.json",
        "doc_id": "uuid-here"
    },
    "processing_result": {
        "standardized_content": {
            "type": "Invoice",
            "standardized_fields": {
                "document_id": "INV-001",
                "value": 1000.00,
                "timestamp": "2024-03-20"
            }
        },
        "validation": {
            "is_valid": true,
            "missing_fields": []
        }
    }
}
```

### Email Processing
```json
{
    "status": "success",
    "classification": {
        "file_type": "EMAIL",
        "intent": "Invoice",
        "source": "example.txt",
        "doc_id": "uuid-here"
    },
    "processing_result": {
        "headers": {
            "sender": "sender@example.com",
            "subject": "Invoice Payment Request"
        },
        "analysis": {
            "intent": "Invoice",
            "urgency": "Medium",
            "summary": "Payment request for recent services"
        },
        "thread_id": "THREAD-123"
    }
}
```

## Error Handling

The system includes comprehensive error handling for:
- Invalid file types
- Malformed JSON
- API failures
- Missing required fields

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. # document_analysis
