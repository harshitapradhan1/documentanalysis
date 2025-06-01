import os
import logging
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from document_processor import DocumentProcessor
from memory_storage import MemoryStorage
from dotenv import load_dotenv
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Configure CORS to allow all origins during development
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'.pdf', '.json', '.txt'}  # Updated to match frontend

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logger.info(f"Created upload directory: {UPLOAD_FOLDER}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize document processor with Perplexity API key
perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
if not perplexity_api_key:
    logger.error("PERPLEXITY_API_KEY environment variable is not set")
    raise ValueError("PERPLEXITY_API_KEY environment variable is not set")

try:
    document_processor = DocumentProcessor(perplexity_api_key)
    memory_storage = MemoryStorage()
    logger.info("DocumentProcessor and MemoryStorage initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler."""
    error_message = str(error)
    logger.error(f"Unhandled error: {error_message}\n{traceback.format_exc()}")
    memory_storage.add_log('error', error_message, {'traceback': traceback.format_exc()})
    return jsonify({
        'error': 'An unexpected error occurred',
        'details': error_message
    }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        stats = memory_storage.get_stats()
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "api_key_configured": bool(perplexity_api_key),
            "stats": stats
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        memory_storage.add_log('error', f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    doc_id = str(uuid.uuid4())
    file_extension = None
    file_path = None
    
    try:
        if 'file' not in request.files:
            error_msg = "No file part in request"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        file = request.files['file']
        if file.filename == '':
            error_msg = "No selected file"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        if not allowed_file(file.filename):
            error_msg = f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        # Save the file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        
        logger.info(f"File saved temporarily: {file_path}")

        # Extract text content
        text_content = document_processor.extract_text(file_path)
        logger.info(f"Extracted {len(text_content)} characters from file")
        
        # Process with Perplexity
        perplexity_response = document_processor.process_with_perplexity(text_content, file_extension)
        logger.info("Successfully processed with Perplexity")
        
        # Get agent-specific response
        agent_response = document_processor.get_agent_response(perplexity_response, file_extension)
        logger.info("Successfully received agent response")
        
        # Extract the final response content
        final_response = agent_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        analysis = perplexity_response.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Store the results
        result = {
            'message': 'File processed successfully',
            'analysis': analysis,
            'response': final_response,
            'doc_id': doc_id,
            'filename': filename,
            'file_extension': file_extension
        }
        
        memory_storage.store_document(doc_id, result)
        memory_storage.update_stats(file_extension, True)

        return jsonify(result)

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing file: {error_message}\n{traceback.format_exc()}")
        if file_extension:
            memory_storage.update_stats(file_extension, False)
        return jsonify({'error': error_message}), 500

    finally:
        # Clean up
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file: {str(e)}")

@app.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Retrieve a processed document by ID."""
    try:
        document = memory_storage.get_document(doc_id)
        if document:
            return jsonify(document)
        return jsonify({'error': 'Document not found'}), 404
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error retrieving document: {error_message}")
        memory_storage.add_log('error', f"Error retrieving document: {error_message}", {
            'doc_id': doc_id
        })
        return jsonify({'error': error_message}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve processing logs."""
    try:
        level = request.args.get('level')
        limit = int(request.args.get('limit', 100))
        logs = memory_storage.get_logs(level, limit)
        return jsonify(logs)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error retrieving logs: {error_message}")
        memory_storage.add_log('error', f"Error retrieving logs: {error_message}")
        return jsonify({'error': error_message}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Retrieve processing statistics."""
    try:
        stats = memory_storage.get_stats()
        return jsonify(stats)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error retrieving stats: {error_message}")
        memory_storage.add_log('error', f"Error retrieving stats: {error_message}")
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True, host='0.0.0.0', port=3001) 