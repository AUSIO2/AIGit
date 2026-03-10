import os
import json
from typing import Any, Dict

class ConfigManager:
    def __init__(self):
        self.aigit_dir = os.path.join(os.getcwd(), ".aigit")
        self.config_file = os.path.join(self.aigit_dir, "config.json")
        self.prompts_file = os.path.join(self.aigit_dir, "prompts.json")
        self._config: Dict[str, Any] = {}
        self._prompts: Dict[str, str] = {}
        if os.path.exists(self.config_file):
            self.load()
        if os.path.exists(self.prompts_file):
            self.load_prompts()

    def load(self):
        with open(self.config_file, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def load_prompts(self):
        with open(self.prompts_file, "r", encoding="utf-8") as f:
            self._prompts = json.load(f)

    def create_default_config(self):
        default_config = {
            "llm_provider": "openai",
            "api_key": "YOUR_API_KEY_HERE",
            "model": "gpt-4o-mini"
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)

    def create_default_prompts(self):
        # Load from internal package resource
        resource_path = os.path.join(os.path.dirname(__file__), "prompts.json")
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                default_prompts = json.load(f)
        except Exception:
            # Fallback if resource is missing
            default_prompts = {
                "system_prompt": "You are a Git assistant. Return only valid git commands.",
                "user_prompt_template": "Branch: {branch}\nStatus: {status}\nIntent: {prompt}"
            }

        with open(self.prompts_file, "w", encoding="utf-8") as f:
            json.dump(default_prompts, f, indent=4)
        self._prompts = default_prompts

    def is_configured(self) -> bool:
        return os.path.exists(self.config_file) and self._config.get("api_key") != "YOUR_API_KEY_HERE"

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def get_prompt(self, key: str, default: str = "") -> str:
        return self._prompts.get(key, default)
