# manager_instance.py

import os
from dotenv import load_dotenv
from conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost')
OLLAMA_PORT = int(os.getenv('OLLAMA_PORT', 11434))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# Create a shared instance of ConversationManager
manager = ConversationManager(
    groq_api_key=GROQ_API_KEY,
    ollama_host=OLLAMA_HOST,
    ollama_port=OLLAMA_PORT,
    cerebras_api_key=CEREBRAS_API_KEY
)

# List of available Groq models
manager.GROQ_MODELS = [
    'llama3-groq-70b-8192-tool-use-preview',
    'llama3-groq-8b-8192-tool-use-preview',
    'llama-3.1-70b-versatile',
    'llama-3.1-8b-instant',
    'llama-3.2-1b-preview',
    'llama-3.2-3b-preview',
    'llama3-70b-8192',
    'llama3-8b-8192',
]

# Verify API keys and connections
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY is not set. Groq functionality may be limited.")

if not CEREBRAS_API_KEY:
    print("Warning: CEREBRAS_API_KEY is not set. Cerebras functionality may be limited.")

try:
    ollama_models = manager.ollama_client.list_models()
    print(f"Successfully connected to Ollama. Available models: {len(ollama_models)}")
except Exception as e:
    print(f"Warning: Could not connect to Ollama server. Error: {e}")

print("ConversationManager instance created and configured.")