import json
import requests
from .config import ConfigManager

class LLMClient:
    def __init__(self, config: ConfigManager):
        self.config = config

    def generate_git_command(self, prompt: str, branch: str, status: str, diff: str, recent_commits: str, project_context: str, command_type: str = "general") -> tuple[str, list]:
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
            
        format_kwargs = {
            "branch": branch,
            "status": status,
            "diff": diff,
            "prompt": prompt,
            "recent_commits": recent_commits,
            "project_context": project_context
        }
        
        try:
            user_prompt = user_template.format(**format_kwargs)
        except KeyError:
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

    def explain_git_command(self, history: list, extra_prompt: str = "") -> str:
        """Asks the LLM to explain the generated git command using the current conversation history.
        If extra_prompt is given, the AI also answers that specific question in context."""
        api_key = self.config.get("api_key")
        base_url = self.config.get("api_base_url", "https://api.openai.com/v1")
        model = self.config.get("model", "gpt-4o-mini")
        provider = self.config.get("llm_provider", "openai")
        
        explain_prompt = self.config.get_prompt("user_prompt_template_explain")
        if not explain_prompt:
            explain_prompt = "Please explain the command you just generated concisely."
        
        if extra_prompt.strip():
            explain_prompt = f"{explain_prompt}\n\nThe user also has a specific question: {extra_prompt.strip()}\nPlease answer this question in the context of the command above."
            
        messages = list(history)
        messages.append({"role": "user", "content": explain_prompt})
        
        if provider == "openai":
            return self._call_openai(api_key, base_url, model, messages)
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

    def update_project_context(self, command: str, diff: str) -> None:
        """Asks the LLM to summarize the action and appends it to the project context memory file."""
        import os
        
        api_key = self.config.get("api_key")
        base_url = self.config.get("api_base_url", "https://api.openai.com/v1")
        model = self.config.get("model", "gpt-4o-mini")
        provider = self.config.get("llm_provider", "openai")
        
        update_prompt_template = self.config.get_prompt("user_prompt_template_context_update")
        if not update_prompt_template:
            return  # Fail silently if template is missing to avoid crashing post-execution
            
        user_prompt = update_prompt_template.format(command=command, diff=diff)
        
        messages = [
            {"role": "system", "content": "You are a concise recorder of architectural choices."},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            if provider == "openai":
                summary_bullet = self._call_openai(api_key, base_url, model, messages)
            else:
                return
                
            context_file = os.path.join(self.config.aigit_dir, "PROJECT_CONTEXT.md")
            lines = []
            if os.path.exists(context_file):
                with open(context_file, "r") as f:
                    lines = f.readlines()
            
            # Keep only the last 50 entries to avoid bloat
            if len(lines) > 50:
                lines = lines[-50:]
                
            lines.append(summary_bullet.strip() + "\n")
            
            with open(context_file, "w") as f:
                f.writelines(lines)
                
        except Exception:
            pass # Fail silently as this is a background optimization task
