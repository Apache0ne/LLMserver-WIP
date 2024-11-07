# game_settings.py

class CerebrasSettings:
    def __init__(self):
        self.stream = False
        self.use_tools = False
        self.temperature = 0.7
        self.max_tokens = 150
        self.top_p = 1.0
        self.tools = []  # List to store tool configurations

    def add_tool(self, tool):
        self.tools.append(tool)

class GroqSettings:
    def __init__(self):
        self.stream = False
        self.temperature = 0.7
        self.max_tokens = 150
        self.top_p = 1.0
        self.response_format = None  # Can be set to {"type": "json_object"} for JSON mode

class OllamaSettings:
    def __init__(self):
        self.stream = False
        self.num_predict = 128  # Similar to max_tokens
        self.temperature = 0.7
        self.top_k = 40
        self.top_p = 0.9
        self.repeat_penalty = 1.1

def get_default_settings(service):
    if service == 'cerebras':
        return CerebrasSettings()
    elif service == 'groq':
        return GroqSettings()
    elif service == 'ollama':
        return OllamaSettings()
    else:
        raise ValueError(f"Unknown service: {service}")