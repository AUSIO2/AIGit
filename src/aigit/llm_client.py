import json
import requests
from .config import ConfigManager

class LLMClient:
    def __init__(self, config: ConfigManager):
        self.config = config

    def generate_git_command(self, prompt: str, branch: str, status: str) -> str:
        api_key = self.config.get("api_key")
        model = self.config.get("model", "gpt-4o-mini")
        provider = self.config.get("llm_provider", "openai")
        
        system_prompt = self.config.get_prompt("system_prompt")
        user_template = self.config.get_prompt("user_prompt_template")
        user_prompt = user_template.format(branch=branch, status=status, prompt=prompt)

        if provider == "openai":
            return self._call_openai(api_key, model, system_prompt, user_prompt)
        else:
            raise NotImplementedError(f"Provider {provider} not currently implemented.")

    def _call_openai(self, api_key: str, model: str, sys_prompt: str, usr_prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt}
            ],
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API Error ({response.status_code}): {response.text}")
            
        result = response.json()
        content = result.get("choices", [])[0].get("message", {}).get("content", "")
        return content.strip().strip('`').strip() # Remove any potentially leaked markdown formatting
