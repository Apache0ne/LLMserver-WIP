# game_logic.py

import json
from typing import Dict, Any
from manager_instance import manager  # Import the shared manager instance

def process_game_turn(context, user_input: str) -> str:
    # Add the user's input to the conversation history
    context.add_message("user", user_input)

    # Generate a response using the appropriate LLM client
    if context.service == 'groq':
        response = manager.groq_client.generate_response(context)
    elif context.service == 'ollama':
        response = manager.ollama_client.generate_response(context)
    elif context.service == 'cerebras':
        response = manager.cerebras_client.generate_response(context)
    else:
        return f"Error: Unknown service {context.service}"

    # Process the response
    try:
        game_state = parse_response(response)
        context.add_message("assistant", response)
        return format_game_output(game_state)
    except json.JSONDecodeError:
        return f"Error: Invalid response format. Raw response: {response}"

def parse_response(response: str) -> Dict[str, Any]:
    """Parse the JSON response from the LLM."""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # If the response isn't valid JSON, try to extract JSON from it
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != -1:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                raise ValueError("Could not parse response as JSON")
        else:
            raise ValueError("No JSON object found in response")

def format_game_output(game_state: Dict[str, Any]) -> str:
    """Format the game state into a user-friendly output."""
    output = []

    # Narration
    if "narration" in game_state:
        output.append(f"\nNarration: {game_state['narration']}")

    # Image details
    if "image" in game_state:
        output.append("\nImage Details:")
        image = game_state["image"]
        if "top" in image:
            output.append(f"Top Caption: {image['top']}")
        if "bottom" in image:
            output.append(f"Bottom Caption: {image['bottom']}")
        if "prompt" in image:
            output.append(f"Image Prompt: {image['prompt']}")

    # Available actions
    if "actions" in game_state and isinstance(game_state["actions"], list):
        output.append("\nAvailable Actions:")
        for i, action in enumerate(game_state["actions"], 1):
            if isinstance(action, dict) and "description" in action:
                output.append(f"{i}. {action['description']}")

    return "\n".join(output)

def initialize_game(context):
    """Initialize the game state."""
    system_message = {
        "role": "system",
        "content": """You are the game logic for an isekai anime-themed text-based adventure. Follow these guidelines:

1. Narration: Provide vivid, immersive descriptions of the current scene, maintaining consistent lore. Describe new characters, locations, or items in detail.

2. Rules: Enforce game rules strictly. Prevent cheating and unrealistic actions.

3. World: Set in an alternate fantasy realm where players embark on adventures, level up, and acquire items. Include an Adventurer's Guild for quests and shops with unique NPCs.

4. Image Generation: Create detailed prompts for Stable Diffusion, focusing on the most impactful visual moment of each scene.

5. Captions: Provide top and bottom captions for each scene, reflecting player actions and NPC responses or events.

6. Actions: Suggest four varied, interesting actions for the player to choose from.

IMPORTANT: Always respond in valid JSON format with the following structure:
{
    "narration": "Detailed narration of the current scene",
    "image": {
        "top": "Top caption for the scene",
        "bottom": "Bottom caption for the scene",
        "prompt": "Detailed image generation prompt"
    },
    "actions": [
        {"description": "Description of action 1"},
        {"description": "Description of action 2"},
        {"description": "Description of action 3"},
        {"description": "Description of action 4"}
    ]
}

Do not include any text outside of this JSON structure."""
    }
    context.add_message("system", system_message["content"])
    
    # Generate initial game state
    initial_prompt = "Start a new isekai anime-themed adventure game. Describe the opening scene where the player is transported to a fantasy world."
    return process_game_turn(context, initial_prompt)