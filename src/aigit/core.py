import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.syntax import Syntax

from .config import ConfigManager
from .git_client import GitClient
from .llm_client import LLMClient

console = Console()

def init_aigit_dir():
    """Initializes the .aigit directory in current repo."""
    git = GitClient()
    if not git.is_inside_work_tree():
        console.print("[red]Error: Not inside a valid git repository.[/red]")
        return

    config = ConfigManager()
    
    if os.path.exists(config.aigit_dir):
        console.print("[yellow]The .aigit directory already exists.[/yellow]")
        return
        
    os.makedirs(config.aigit_dir, exist_ok=True)
    
    # Interactive Configuration
    console.print("\n[bold cyan]Welcome to aigit Setup![/bold cyan]")
    console.print("Let's configure your AI proxy parameters.\n")
    
    provider = Prompt.ask("LLM Provider", default="openai")
    api_base_url = Prompt.ask("API Base URL (Endpoint)", default="https://api.openai.com/v1")
    model = Prompt.ask("Model Name", default="gpt-4o-mini")
    api_key = Prompt.ask("API Key", password=True)
    
    custom_config = {
        "llm_provider": provider,
        "api_base_url": api_base_url,
        "model": model,
        "api_key": api_key if api_key else "YOUR_API_KEY_HERE"
    }

    config.create_default_config(custom_values=custom_config)
    config.create_default_prompts()
    
    console.print(f"[green]Initialized empty aigit directory in {config.aigit_dir}[/green]")
    console.print("Please configure your API keys in [bold].aigit/config.json[/bold]")
    console.print("You can also customize prompts in [bold].aigit/prompts.json[/bold]")
    console.print("Remember to add [bold].aigit/config.json[/bold] to your .gitignore!")


def execute_prompt(prompt: str, command_type: str = "general", explain: bool = False) -> int:
    config = ConfigManager()
    
    if not config.is_configured():
        console.print("[red]Error: aigit is not configured or missing API key.[/red]")
        console.print("Please run `aigit --init` and setup your API keys in .aigit/config.json")
        return 1

    git = GitClient()
    if not git.is_inside_work_tree():
        console.print("[red]Error: Not inside a valid git repository.[/red]")
        return 1

    llm = LLMClient(config)

    with console.status("[cyan]Gathering git context...[/cyan]", spinner="dots"):
        branch = git.get_current_branch()
        status = git.get_status()
        diff = git.get_git_diff(max_lines=2000)

    with console.status(f"[cyan]Translating {command_type} intent to Git commands using AI...[/cyan]", spinner="dots"):
        try:
            suggested_cmd, history = llm.generate_git_command(prompt, branch, status, diff, command_type)
        except Exception as e:
            console.print(f"[red]Error communicating with LLM:[/red] {e}")
            return 1
            
    if explain:
        with console.status("[cyan]Generating structural explanation...[/cyan]", spinner="dots"):
            try:
                explanation = llm.explain_git_command(history)
            except Exception as e:
                explanation = f"Failed to generate explanation: {e}"

    while True:
        # Format the command for better readability
        parts = []
        for c in suggested_cmd.split("&&"):
            c = c.strip()
            if c.startswith("git add "):
                tokens = c.split()
                if len(tokens) > 3:
                    formatted = "git add \\\n  " + " \\\n  ".join(tokens[2:])
                    parts.append(formatted)
                else:
                    parts.append(c)
            else:
                parts.append(c)
                
        display_cmd = "\n&& ".join(parts)

        # Present suggestion to user
        if explain:
            console.print("\n[bold yellow]🤖 AI Explanation:[/bold yellow]")
            console.print(Panel(explanation, expand=False, border_style="yellow"))
            
        console.print("\n💡 [bold green]Suggested Command:[/bold green]")
        syntax = Syntax(display_cmd, "bash", theme="monokai", word_wrap=True)
        console.print(Panel(syntax, expand=False, border_style="cyan"))
        console.print("")
        
        try:
            user_input = Prompt.ask("Execute? [Y/n] or Explain?[e] or type instructions to modify").strip()
            
            if user_input.lower() in ('y', 'yes', ''):
                console.print("\n[cyan]Executing...[/cyan]")
                exit_code = git.execute_command(suggested_cmd)
                if exit_code != 0:
                    console.print(f"[red]Command failed with exit code {exit_code}[/red]")
                else:
                    console.print("[green]Command executed successfully![/green]")
                return exit_code
            elif user_input.lower() in ('n', 'no', 'q', 'quit', 'exit'):
                console.print("[yellow]Execution canceled.[/yellow]")
                return 0
            elif any(token in user_input.lower().split() for token in ('-e', '--explain', 'explain')):
                with console.status("[cyan]Generating structural explanation...[/cyan]", spinner="dots"):
                    try:
                        explanation = llm.explain_git_command(history)
                        console.print("\n[bold yellow]🤖 AI Explanation:[/bold yellow]")
                        console.print(Panel(explanation, expand=False, border_style="yellow"))
                    except Exception as e:
                        console.print(f"[red]Failed to generate explanation:[/red] {e}")
                continue
            else:
                with console.status("[cyan]Refining command based on your instructions...[/cyan]", spinner="dots"):
                    try:
                        suggested_cmd, history = llm.refine_git_command(user_input, history)
                    except Exception as e:
                        console.print(f"[red]Error communicating with LLM:[/red] {e}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Canceled by user.[/yellow]")
            return 1
