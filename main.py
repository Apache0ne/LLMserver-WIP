# main.py

import threading
import argparse
from flask import Flask, request, jsonify

from conversation_manager import ConversationManager
from manager_instance import manager  # Import the shared manager instance
from console_commands import console_mode
from game_logic import initialize_game, process_game_turn

# Flask server configuration
FLASK_HOST = '127.0.0.1'  # Default host
FLASK_PORT = 5000         # Default port

app = Flask(__name__)

def create_route(route, methods, func, endpoint=None):
    endpoint = endpoint or f"{func.__name__}_{route}"
    @app.route(route, methods=methods, endpoint=endpoint)
    def wrapper():
        if request.method == 'GET':
            return jsonify(func())
        else:
            data = request.json or {}
            return jsonify(func(**data))
    return wrapper

# Register API routes
create_route('/create_context', ['POST'], manager.create_context)
create_route('/list_contexts', ['GET'], manager.list_contexts)
create_route('/delete_context', ['POST'], manager.delete_context)
create_route('/send_prompt', ['POST'], manager.send_prompt)
create_route('/copy_context', ['POST'], manager.copy_context)

@app.route('/list_models', methods=['GET'])
def list_models():
    service = request.args.get('service', '').lower()
    if service == 'ollama':
        models = manager.ollama_client.list_models()
    elif service == 'groq':
        models = manager.GROQ_MODELS
    elif service == 'cerebras':
        models = manager.cerebras_client.list_models()
    else:
        return jsonify({"error": "Invalid service specified"}), 400
    return jsonify({"models": models})

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    context_name = data.get('context_name')
    if not context_name or context_name not in manager.contexts:
        return jsonify({"error": "Invalid or missing context name"}), 400
    
    context = manager.contexts[context_name]
    initial_state = initialize_game(context)
    return jsonify({"initial_state": initial_state})

@app.route('/game_turn', methods=['POST'])
def game_turn():
    data = request.json
    context_name = data.get('context_name')
    user_input = data.get('user_input')
    
    if not context_name or context_name not in manager.contexts:
        return jsonify({"error": "Invalid or missing context name"}), 400
    if not user_input:
        return jsonify({"error": "Missing user input"}), 400
    
    context = manager.contexts[context_name]
    game_response = process_game_turn(context, user_input)
    return jsonify({"game_response": game_response})

def run_server():
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Conversation Manager and Game')
    parser.add_argument('--port', type=int, default=FLASK_PORT, help='Port number for the server')
    parser.add_argument('--host', type=str, default=FLASK_HOST, help='Host for the Flask server')
    args = parser.parse_args()

    FLASK_PORT = args.port
    FLASK_HOST = args.host

    # Start the Flask server in a separate thread
    flask_thread = threading.Thread(target=run_server, daemon=True)
    flask_thread.start()

    # Start the console mode
    console_mode()