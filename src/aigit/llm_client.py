import json
import requests
from .config import ConfigManager

class LLMClient:
    def __init__(self, config: ConfigManager):
        self.config = config

    def generate_git_command(self, prompt: str, branch: str, status: str, diff: str, command_type: str = "general") -> tuple[str, list]:
        api_key = self.config.get("api_key")
        base_url = self.config.get("api_base_url", "https://api.openai.com/v1")
        model = self.config.get("model", "gpt-4o-mini")
        provider = self.config.get("llm_provider", "openai")
        
        system_prompt = self.config.get_prompt("system_prompt")
        
        # Try to find specific template, fallback to general
        template_key = f"user_prompt_template_{command_type}"
        user_template = self.config.get_prompt(template_key)
        if not user_template:
            user_template = self.config.get_prompt("user_prompt_template_general")
            
        user_prompt = user_template.format(branch=branch, status=status, diff=diff, prompt=prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if provider == "openai":
            cmd = self._call_openai(api_key, base_url, model, messages)
            messages.append({"role": "assistant", "content": cmd}) # Store AI response
            return cmd, messages
        else:
            raise NotImplementedError(f"Provider {provider} not currently implemented.")

    def refine_git_command(self, instruction: str, history: list) -> tuple[str, list]:
        """Sends user feedback to the LLM to refine the previous git command."""
        api_key = self.config.get("api_key")
        base_url = self.config.get("api_base_url", "https://api.openai.com/v1")
        model = self.config.get("model", "gpt-4o-mini")
        provider = self.config.get("llm_provider", "openai")
        
        messages = list(history) # Copy to avoid mutating on failure
        messages.append({"role": "user", "content": instruction})
        
        if provider == "openai":
            cmd = self._call_openai(api_key, base_url, model, messages)
            messages.append({"role": "assistant", "content": cmd})
            return cmd, messages
        else:
            raise NotImplementedError(f"Provider {provider} not currently implemented.")

    def _call_openai(self, api_key: str, base_url: str, model: str, messages: list) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.1
        }
        
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        response = requests.post(
            endpoint,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API Error ({response.status_code}): {response.text}")
            
        result = response.json()
        content = result.get("choices", [])[0].get("message", {}).get("content", "")
        return content.strip().strip('`').strip() # Remove any potentially leaked markdown formatting
