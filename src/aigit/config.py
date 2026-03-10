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
        
        # Self-healing: merge in any new keys from the canonical source template
        resource_path = os.path.join(os.path.dirname(__file__), "prompts.json")
        if os.path.exists(resource_path):
            try:
                with open(resource_path, "r", encoding="utf-8") as f:
                    canonical = json.load(f)
                updated = False
                for key, value in canonical.items():
                    if key not in self._prompts:
                        self._prompts[key] = value
                        updated = True
                if updated:
                    with open(self.prompts_file, "w", encoding="utf-8") as f:
                        json.dump(self._prompts, f, indent=4)
            except Exception:
                pass

    def create_default_config(self, custom_values: Dict[str, Any] = None):
        default_config = {
            "llm_provider": "openai",
            "api_base_url": "https://api.openai.com/v1",
            "api_key": "YOUR_API_KEY_HERE",
            "model": "gpt-4o-mini"
        }
        if custom_values:
            default_config.update(custom_values)
            
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        self._config = default_config

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
                "user_prompt_template_general": "Branch: {branch}\nStatus: {status}\nIntent: {prompt}",
                "user_prompt_template_commit": "Current branch: {branch}\nGit status:\n{status}\nGit Diff:\n{diff}\nUser intent: Create a commit. Info: {prompt}\nFocus on generating a highly descriptive and professional commit message based on the actual code changes (diff) and user intent. YOU MUST FOLLOW the Conventional Commits specification. The format should be `<type>(<scope>): <subject>`.\nAllowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.\nDetermine the `<scope>` based on the files modified (e.g., `core`, `config`, `cli`). Provide the exact bash git command(s), including `git add` if necessary."
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

    def get_exclude_patterns(self) -> list:
        """Returns user-defined extra diff exclude patterns from config.json."""
        return self._config.get("exclude_patterns", [])
