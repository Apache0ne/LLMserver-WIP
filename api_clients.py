# api_clients.py

from typing import Dict, Any
from groq import Groq
from ollama import Client as OllamaClient
from cerebras.cloud.sdk import Cerebras

class GroqClientWrapper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.groq_client = Groq(api_key=api_key)
    
    def generate_response(self, context) -> str:
        if not self.api_key:
            raise ValueError("Groq API key not set.")
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=context.history,
                model=context.model,
                temperature=context.settings.temperature,
                max_tokens=context.settings.max_tokens,
                top_p=context.settings.top_p,
                stream=context.settings.stream,
                response_format=context.settings.response_format
            )
            if context.settings.stream:
                response_text = ""
                for chunk in chat_completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content
                        print(content, end='', flush=True)
                print()
                return response_text
            else:
                return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"[DEBUG] Error calling Groq API: {e}")
            return f"Groq Error: {e}"

class OllamaClientWrapper:
    def __init__(self, host: str = 'http://localhost', port: int = 11434):
        self.host = host
        self.port = port
        self.ollama_client = OllamaClient(host=f'{host}:{port}')
    
    def generate_response(self, context) -> str:
        try:
            response_text = ""
            if context.settings.stream:
                for chunk in self.ollama_client.chat(
                    model=context.model,
                    messages=context.history,
                    stream=True,
                    options={
                        "num_predict": context.settings.num_predict,
                        "temperature": context.settings.temperature,
                        "top_k": context.settings.top_k,
                        "top_p": context.settings.top_p,
                        "repeat_penalty": context.settings.repeat_penalty
                    }
                ):
                    content = chunk['message']['content']
                    response_text += content
                    print(content, end='', flush=True)
                print()
            else:
                response = self.ollama_client.chat(
                    model=context.model,
                    messages=context.history,
                    options={
                        "num_predict": context.settings.num_predict,
                        "temperature": context.settings.temperature,
                        "top_k": context.settings.top_k,
                        "top_p": context.settings.top_p,
                        "repeat_penalty": context.settings.repeat_penalty
                    }
                )
                response_text = response['message']['content']
            return response_text
        except Exception as e:
            print(f"[DEBUG] Ollama Error: {e}")
            return f"Ollama Error: {e}"
    
    def list_models(self) -> Dict[str, Any]:
        try:
            return self.ollama_client.list()
        except Exception as e:
            print(f"[DEBUG] Ollama Error when listing models: {e}")
            return {}

class CerebrasClientWrapper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cerebras_client = Cerebras(api_key=api_key)
    
    def generate_response(self, context) -> str:
        if not self.api_key:
            raise ValueError("Cerebras API key not set.")
        try:
            response = self.cerebras_client.chat.completions.create(
                messages=context.history,
                model=context.model,
                temperature=context.settings.temperature,
                max_tokens=context.settings.max_tokens,
                top_p=context.settings.top_p,
                stream=context.settings.stream,
                tools=context.settings.tools if context.settings.use_tools else None
            )
            if context.settings.stream:
                response_text = ""
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content
                        print(content, end='', flush=True)
                print()
                return response_text
            else:
                return response.choices[0].message.content
        except Exception as e:
            print(f"[DEBUG] Error calling Cerebras API: {e}")
            return f"Cerebras Error: {e}"
    
    def list_models(self) -> list:
        try:
            models = self.cerebras_client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            print(f"[DEBUG] Cerebras Error when listing models: {e}")
            return []