import json
import os
import requests
from cerebras.cloud.sdk import Cerebras, CerebrasError

# Read config file
with open('config.json') as f:
    data = json.load(f)
    token = data.get("TOKEN")

# Use environment variables if not in config
if not token:
    token = os.environ.get("CEREBRAS_API_KEY")

cclient = Cerebras(api_key=token)

conversation = [
    {"role": "system", "content": """You are the game logic for an isekai anime-themed text-based adventure. Follow these guidelines:

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

Do not include any text outside of this JSON structure."""}
]

def get_user_float_input(prompt, default):
    while True:
        user_input = input(f"{prompt} (default: {default}): ")
        if user_input == "":
            return default
        try:
            return float(user_input)
        except ValueError:
            print("Please enter a valid number.")

def get_user_int_input(prompt, default):
    while True:
        user_input = input(f"{prompt} (default: {default}): ")
        if user_input == "":
            return default
        try:
            return int(user_input)
        except ValueError:
            print("Please enter a valid integer.")

def perform_math_operation(operation, x, y):
    print(f"Performing math operation: {operation} with {x} and {y}")
    try:
        if operation == "add":
            return x + y
        elif operation == "subtract":
            return x - y
        elif operation == "multiply":
            return x * y
        elif operation == "divide":
            if y == 0:
                return "Error: Division by zero"
            return x / y
        else:
            return f"Error: Unknown operation '{operation}'"
    except Exception as e:
        return f"Error: {str(e)}"

math_tool = {
    "type": "function",
    "function": {
        "name": "perform_math_operation",
        "description": "Perform a basic math operation",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The math operation to perform",
                },
                "x": {
                    "type": "number",
                    "description": "The first number",
                },
                "y": {
                    "type": "number",
                    "description": "The second number",
                },
            },
            "required": ["operation", "x", "y"],
        },
    }
}

try:
    # List available models
    models = cclient.models.list()
    model_ids = [model.id for model in models.data]
    
    # Display models with numbers
    print("Available models:")
    for i, model in enumerate(model_ids, 1):
        print(f"{i}. {model}")

    # Let user choose a model by number
    while True:
        choice = input(f"Choose a model number (1-{len(model_ids)}, default: 1): ")
        if choice == "":
            chosen_model = model_ids[0]
            break
        try:
            choice = int(choice)
            if 1 <= choice <= len(model_ids):
                chosen_model = model_ids[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(model_ids)}.")
        except ValueError:
            print("Please enter a valid number.")

    print(f"\nSelected model: {chosen_model}")

    # Get user preferences for parameters
    temperature = get_user_float_input("Enter temperature (0.0 to 1.0)", 0.7)
    max_tokens = get_user_int_input("Enter max_tokens", 150)
    top_p = get_user_float_input("Enter top_p (0.0 to 1.0)", 1.0)

    print(f"\nUsing model: {chosen_model}")
    print(f"Parameters: temperature={temperature}, max_tokens={max_tokens}, top_p={top_p}\n")

    user_input = None
    game_running = True
    game_started = False

    print("\nType 'Start the game' to begin or 'exit' to quit.")

    while game_running:
        if not game_started:
            user_input = input("\nWhat would you like to do? ").strip().lower()
            
            if user_input in ['exit', 'quit', 'bye', 'end']:
                print("Exiting the game.")
                game_running = False
                break

            if user_input != "start the game":
                print("Please type 'Start the game' to begin or 'exit' to quit.")
                continue
            else:
                game_started = True

        try:
            if game_started and user_input:
                conversation.append({"role": "user", "content": user_input})

            response = cclient.chat.completions.create(
                messages=conversation,
                model=chosen_model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                tools=[math_tool],
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message
            
            print("Debug - Raw AI response:")
            print(assistant_message.content)

            try:
                # First, try to parse the entire response as JSON
                response_content = json.loads(assistant_message.content)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the response
                try:
                    json_start = assistant_message.content.find('{')
                    json_end = assistant_message.content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = assistant_message.content[json_start:json_end]
                        response_content = json.loads(json_str)
                    else:
                        raise ValueError("No JSON object found in the response")
                except (json.JSONDecodeError, ValueError):
                    print("Error: Unable to parse JSON response. Displaying raw content.")
                    print(assistant_message.content)
                    response_content = {}

            # Print narration
            narration = response_content.get("narration", "No narration provided.")
            print("\nNarration:")
            print(narration)

            # Print image details (if available)
            image_data = response_content.get("image", {})
            if image_data:
                print("\nImage Details:")
                print(f"Top Caption: {image_data.get('top', 'N/A')}")
                print(f"Bottom Caption: {image_data.get('bottom', 'N/A')}")
                print(f"Image Prompt: {image_data.get('prompt', 'N/A')}")
            else:
                print("\nNo image details provided.")

            # Print actions
            actions = response_content.get("actions", [])
            if actions and isinstance(actions, list):
                print("\nAvailable Actions:")
                for i, action in enumerate(actions, 1):
                    if isinstance(action, dict):
                        print(f"{i}. {action.get('description', 'No description')}")
                
                # Let user choose an action
                while True:
                    action_choice = input("\nChoose an action (1-4) or type your own action: ")
                    if action_choice.lower() in ['exit', 'quit', 'bye', 'end']:
                        print("Exiting the game.")
                        game_running = False
                        break
                    try:
                        action_index = int(action_choice) - 1
                        if 0 <= action_index < len(actions):
                            chosen_action = actions[action_index]
                            user_input = chosen_action.get('description', 'Chosen action')
                            print(f"\nYou chose: {user_input}")
                            break
                        else:
                            print("Invalid action number. Please try again.")
                    except ValueError:
                        # If the input is not a number, treat it as a custom action
                        user_input = action_choice
                        print(f"\nYou chose a custom action: {user_input}")
                        break
            else:
                print("\nNo actions provided.")
                user_input = input("What would you like to do? ")

            if game_running:
                conversation.append({"role": "assistant", "content": assistant_message.content})

                # Print usage information
                print(f"\nTokens used: {response.usage.total_tokens}")

        except CerebrasError as e:
            print(f"An error occurred with Cerebras API: {e}")
            user_input = input("An error occurred. What would you like to do next? ")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print(f"Error details: {str(e)}")
            user_input = input("An error occurred. What would you like to do next? ")

except CerebrasError as e:
    print(f"An error occurred while setting up the client: {e}")

print("Chat ended.")