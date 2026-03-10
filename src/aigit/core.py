import os
from rich.console import Console

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
    config.create_default_config()
    config.create_default_prompts()
    
    console.print(f"[green]Initialized empty aigit directory in {config.aigit_dir}[/green]")
    console.print("Please configure your API keys in [bold].aigit/config.json[/bold]")
    console.print("You can also customize prompts in [bold].aigit/prompts.json[/bold]")
    console.print("Remember to add [bold].aigit/config.json[/bold] to your .gitignore!")


def execute_prompt(prompt: str) -> int:
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

    with console.status("[cyan]Translating intent to Git commands using AI...[/cyan]", spinner="dots"):
        try:
            suggested_cmd = llm.generate_git_command(prompt, branch, status)
        except Exception as e:
            console.print(f"[red]Error communicating with LLM:[/red] {e}")
            return 1
            
    # Present suggestion to user
    console.print("")
    console.print("💡 [bold green]Suggested Command:[/bold green]")
    console.print(f"  [cyan]{suggested_cmd}[/cyan]")
    console.print("")
    
    try:
        confirm = console.input("Execute this command? \\[Y/n] ")
        if confirm.lower() in ('', 'y', 'yes'):
            return git.execute_command(suggested_cmd)
        else:
            console.print("Execution canceled.")
            return 0
    except KeyboardInterrupt:
        console.print("\nCanceled.")
        return 1
