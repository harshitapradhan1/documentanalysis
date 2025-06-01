from json_memory import JsonMemory

# Initialize the memory
memory = JsonMemory()

# Test query and response
test_query = "What is the capital of France?"
test_response = {
    "model": "sonar-medium",
    "text": "The capital of France is Paris.",
    "confidence": 0.95,
    "usage": {"total_tokens": 150}
}

# Store the response
entry_id = memory.store_perplexity_response(
    query=test_query,
    response=test_response,
    thread_id="test_conversation"
)

print(f"Stored response with ID: {entry_id}")
print(f"JSON file created in: {memory.base_dir}") 