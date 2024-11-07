# console_commands.py

import os
from manager_instance import manager
from game_settings import get_default_settings
from game_logic import initialize_game, process_game_turn

def display_menu():
    menu = f"""
=== Conversation Manager ===
1. Create Context
2. List Contexts
3. Delete Context
4. Send Prompt
5. Copy Context
6. Toggle Autosave (Currently: {'Enabled' if manager.autosave_enabled else 'Disabled'})
7. Start Game
8. Exit
=============================
"""
    print(menu)

def get_system_prompt():
    system_prompt = input("Enter system prompt (leave blank for default or provide a file name): ").strip()
    if system_prompt:
        if os.path.isfile(system_prompt):
            with open(system_prompt, 'r') as f:
                system_prompt = f.read()
                print("[Info] System prompt loaded from file.")
        else:
            pass  # Use the input as the system prompt
    else:
        system_prompt = "You are a helpful assistant."
    return system_prompt

def configure_llm_settings(service):
    settings = get_default_settings(service)
    
    if service == 'cerebras':
        settings.stream = input("Enable streaming? (y/n): ").lower() == 'y'
        settings.use_tools = input("Enable tools? (y/n): ").lower() == 'y'
        if settings.use_tools:
            # Add logic to configure tools
            pass
        settings.temperature = float(input(f"Enter temperature (default: {settings.temperature}): ") or settings.temperature)
        settings.max_tokens = int(input(f"Enter max tokens (default: {settings.max_tokens}): ") or settings.max_tokens)
        settings.top_p = float(input(f"Enter top_p (default: {settings.top_p}): ") or settings.top_p)
    
    elif service == 'groq':
        settings.stream = input("Enable streaming? (y/n): ").lower() == 'y'
        settings.temperature = float(input(f"Enter temperature (default: {settings.temperature}): ") or settings.temperature)
        settings.max_tokens = int(input(f"Enter max tokens (default: {settings.max_tokens}): ") or settings.max_tokens)
        settings.top_p = float(input(f"Enter top_p (default: {settings.top_p}): ") or settings.top_p)
        json_mode = input("Enable JSON mode? (y/n): ").lower() == 'y'
        if json_mode:
            settings.response_format = {"type": "json_object"}
    
    elif service == 'ollama':
        settings.stream = input("Enable streaming? (y/n): ").lower() == 'y'
        settings.num_predict = int(input(f"Enter num_predict (default: {settings.num_predict}): ") or settings.num_predict)
        settings.temperature = float(input(f"Enter temperature (default: {settings.temperature}): ") or settings.temperature)
        settings.top_k = int(input(f"Enter top_k (default: {settings.top_k}): ") or settings.top_k)
        settings.top_p = float(input(f"Enter top_p (default: {settings.top_p}): ") or settings.top_p)
        settings.repeat_penalty = float(input(f"Enter repeat_penalty (default: {settings.repeat_penalty}): ") or settings.repeat_penalty)
    
    return settings

def select_model(service):
    if service == 'ollama':
        models = manager.ollama_client.list_models()
        if not models:
            print("[Error] No Ollama models available.")
            return None
        print("\nAvailable Ollama Models:")
        for idx, model in enumerate(models, start=1):
            print(f"{idx}. {model['name']}")
    elif service == 'groq':
        models = manager.GROQ_MODELS
        print("\nAvailable Groq Models:")
        for idx, model in enumerate(models, start=1):
            print(f"{idx}. {model}")
    elif service == 'cerebras':
        models = manager.cerebras_client.list_models()
        if not models:
            print("[Error] No Cerebras models available.")
            return None
        print("\nAvailable Cerebras Models:")
        for idx, model in enumerate(models, start=1):
            print(f"{idx}. {model}")
    
    while True:
        choice = input("Enter the model number: ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(models):
                return models[index]['name'] if service == 'ollama' else models[index]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def create_context_console():
    name = input("Enter context name: ").strip()
    if not name:
        print("[Error] Context name cannot be empty.")
        return

    service = input("Enter service (Groq, Ollama, or Cerebras): ").strip().lower()
    if service not in ['groq', 'ollama', 'cerebras']:
        print("[Error] Invalid service. Choose Groq, Ollama, or Cerebras.")
        return

    model = select_model(service)
    if not model:
        return

    system_prompt = get_system_prompt()
    settings = configure_llm_settings(service)

    result = manager.create_context(name, service, model, system_prompt, settings)
    print(result["message"])
    if result["success"]:
        start_game = input("Do you want to start the game now? (y/n): ").lower() == 'y'
        if start_game:
            start_game_console(name)

def list_contexts_console():
    result = manager.list_contexts()
    if not result["contexts"]:
        print("[Info] No contexts available.")
    else:
        print("\n--- Available Contexts ---")
        for ctx in result["contexts"]:
            print(f"Name: {ctx['name']} | Service: {ctx['service']} | Model: {ctx['model']}")
            print(f"System Prompt: {ctx['system_prompt']}\n")
        print("--------------------------")

def delete_context_console():
    name = input("Enter context name to delete: ").strip()
    if not name:
        print("[Error] Context name cannot be empty.")
        return
    result = manager.delete_context(name)
    print(result["message"])

def send_prompt_console():
    name = input("Enter context name: ").strip()
    if not name:
        print("[Error] Context name cannot be empty.")
        return
    if name not in manager.contexts:
        print(f"[Error] Context '{name}' does not exist.")
        return
    send_prompt_loop(name)

def send_prompt_loop(name: str):
    context = manager.contexts[name]
    while True:
        prompt = input("Enter your prompt (or type 'exit' to return to main menu): ").strip()
        if prompt.lower() == 'exit':
            break
        if not prompt:
            print("[Error] Prompt cannot be empty.")
            continue
        result = manager.send_prompt(name, prompt)
        if result["success"]:
            print(f"\n[Assistant] {result['response']}\n")
        else:
            print(f"[Error] {result['message']}")

def copy_context_console():
    source_name = input("Enter the name of the context to copy from: ").strip()
    new_name = input("Enter the new context name: ").strip()
    num_messages_input = input("Enter the number of recent messages to keep (leave blank to keep all): ").strip()
    num_messages = int(num_messages_input) if num_messages_input.isdigit() else None
    result = manager.copy_context(source_name, new_name, num_messages)
    print(result["message"])

def toggle_autosave_console():
    manager.autosave_enabled = not manager.autosave_enabled
    status = "Enabled" if manager.autosave_enabled else "Disabled"
    print(f"Autosave has been {status}.")

def start_game_console(name: str = None):
    if name is None:
        name = input("Enter the name of the context to use for the game: ").strip()
    if name not in manager.contexts:
        print(f"[Error] Context '{name}' does not exist.")
        return
    start_game_loop(name)

def start_game_loop(name: str):
    context = manager.contexts[name]
    print(f"\nStarting game with context: {name}")
    print("Type 'exit' at any time to end the game.")
    
    # Initialize the game
    game_state = initialize_game(context)
    print(game_state)
    
    while True:
        user_input = input("\nYour action: ").strip()
        if user_input.lower() == 'exit':
            print("Ending game. Returning to main menu.")
            break
        
        game_response = process_game_turn(context, user_input)
        print(game_response)

def exit_console():
    print("Exiting Conversation Manager. Goodbye!")
    exit()

def console_mode():
    options = {
        '1': create_context_console,
        '2': list_contexts_console,
        '3': delete_context_console,
        '4': send_prompt_console,
        '5': copy_context_console,
        '6': toggle_autosave_console,
        '7': start_game_console,
        '8': exit_console
    }

    while True:
        display_menu()
        choice = input("Select an option (1-8): ").strip()
        action = options.get(choice, lambda: print("[Error] Invalid option. Please select a number between 1 and 8."))
        action()

if __name__ == "__main__":
    console_mode()