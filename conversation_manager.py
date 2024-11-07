# conversation_manager.py

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from game_settings import get_default_settings
from api_clients import GroqClientWrapper, OllamaClientWrapper, CerebrasClientWrapper
from tinydb import TinyDB, Query

@dataclass
class ConversationContext:
    name: str
    service: str
    model: str
    system_prompt: str
    settings: Any
    history: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "service": self.service,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "settings": self.settings.__dict__ if hasattr(self.settings, '__dict__') else self.settings,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        settings = get_default_settings(data["service"])
        for key, value in data["settings"].items():
            setattr(settings, key, value)
        return cls(
            name=data["name"],
            service=data["service"],
            model=data["model"],
            system_prompt=data["system_prompt"],
            settings=settings,
            history=data.get("history", [])
        )

class ConversationManager:
    def __init__(self, groq_api_key: Optional[str] = None, ollama_host: str = 'http://localhost', ollama_port: int = 11434, cerebras_api_key: Optional[str] = None):
        self.contexts: Dict[str, ConversationContext] = {}
        self.groq_client = GroqClientWrapper(api_key=groq_api_key)
        self.ollama_client = OllamaClientWrapper(host=ollama_host, port=ollama_port)
        self.cerebras_client = CerebrasClientWrapper(api_key=cerebras_api_key)
        self.db = TinyDB('all_contexts.json')
        self.autosave_enabled = True
        self.load_all_contexts_from_db()

    def load_all_contexts_from_db(self):
        self.contexts = {}
        for record in self.db.all():
            try:
                context = ConversationContext.from_dict(record)
                self.contexts[context.name] = context
            except Exception as e:
                print(f"Error loading context: {e}")

    def autosave(self, context: ConversationContext):
        if not self.autosave_enabled:
            return
        Context = Query()
        self.db.upsert(context.to_dict(), Context.name == context.name)

    def create_context(self, name: str, service: str, model: str, system_prompt: str, settings: Any) -> Dict[str, Any]:
        if name in self.contexts:
            return {"success": False, "message": f"Context '{name}' already exists."}

        context = ConversationContext(name, service, model, system_prompt, settings)
        context.add_message("system", system_prompt)
        self.contexts[name] = context
        self.autosave(context)
        return {"success": True, "message": f"Context '{name}' created successfully."}

    def list_contexts(self) -> Dict[str, Any]:
        return {
            "success": True,
            "contexts": [
                {
                    "name": ctx.name,
                    "service": ctx.service,
                    "model": ctx.model,
                    "system_prompt": ctx.system_prompt[:50] + '...' if len(ctx.system_prompt) > 50 else ctx.system_prompt
                } for ctx in self.contexts.values()
            ]
        }

    def delete_context(self, name: str) -> Dict[str, Any]:
        if self.contexts.pop(name, None):
            Context = Query()
            self.db.remove(Context.name == name)
            return {"success": True, "message": f"Context '{name}' deleted."}
        return {"success": False, "message": f"Context '{name}' does not exist."}

    def send_prompt(self, name: str, prompt: str) -> Dict[str, Any]:
        if name not in self.contexts:
            return {"success": False, "message": f"Context '{name}' does not exist.", "response": None}

        context = self.contexts[name]
        context.add_message("user", prompt)
        
        if context.service == 'groq':
            response = self.groq_client.generate_response(context)
        elif context.service == 'ollama':
            response = self.ollama_client.generate_response(context)
        elif context.service == 'cerebras':
            response = self.cerebras_client.generate_response(context)
        else:
            return {"success": False, "message": f"Unknown service: {context.service}", "response": None}

        if response:
            context.add_message("assistant", response)
            self.autosave(context)
            return {"success": True, "response": response}
        return {"success": False, "message": "Failed to get a response.", "response": None}

    def copy_context(self, source_name: str, new_name: str, num_messages: Optional[int] = None) -> Dict[str, Any]:
        if source_name not in self.contexts:
            return {"success": False, "message": f"Source context '{source_name}' does not exist."}
        if new_name in self.contexts:
            return {"success": False, "message": f"Context '{new_name}' already exists."}

        source_context = self.contexts[source_name]
        new_context = ConversationContext(
            name=new_name,
            service=source_context.service,
            model=source_context.model,
            system_prompt=source_context.system_prompt,
            settings=source_context.settings,
            history=list(source_context.history)
        )

        if num_messages is not None:
            new_context.history = [new_context.history[0]] + new_context.history[-num_messages:]

        self.contexts[new_name] = new_context
        self.autosave(new_context)
        return {"success": True, "message": f"Context '{new_name}' copied from '{source_name}'."}