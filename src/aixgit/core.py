import os
import re
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.syntax import Syntax

from .config import ConfigManager
from .git_client import GitClient
from .llm_client import LLMClient
import threading
import platform
import sys

console = Console()

def init_aixgit_dir():
    """Initializes the .aixgit directory in current repo."""
    git = GitClient()
    try:
        if not git.is_inside_work_tree():
            console.print("[yellow]Not inside a valid git repository.[/yellow]")
            if Prompt.ask("Do you want to run 'git init' now?", choices=["y", "n"], default="y") == "y":
                if git.git_init():
                    console.print("[green]Git repository initialized successfully.[/green]")
                else:
                    console.print("[red]Failed to initialize Git repository.[/red]")
                    return
            else:
                return
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    config = ConfigManager()
    
    if os.path.exists(config.aixgit_dir):
        console.print("[yellow]The .aixgit directory already exists.[/yellow]")
        return
        
    os.makedirs(config.aixgit_dir, exist_ok=True)
    
    # Interactive Configuration
    console.print("\n[bold cyan]Welcome to aixgit Setup![/bold cyan]")
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
    
    console.print(f"[green]Initialized empty aixgit directory in {config.aixgit_dir}[/green]")
    console.print("Please configure your API keys in [bold].aixgit/config.json[/bold]")
    console.print("You can also customize prompts in [bold].aixgit/prompts.json[/bold]")
    console.print("Remember to add [bold].aixgit/config.json[/bold] to your .gitignore!")


def run_doctor():
    """Diagnoses and fixes issues with the aixgit environment."""
    console.print(Panel("[bold cyan]🩺 aixgit Doctor - Diagnostic Tool[/bold cyan]", expand=False, border_style="cyan"))
    
    git = GitClient()
    config = ConfigManager()
    
    # 1. Git Installation
    try:
        git._run_git(["git", "--version"])
        console.print("[green]✔[/green] Git is installed and accessible.")
    except Exception:
        console.print("[red]✘[/red] Git is not found in PATH! Please install Git.")
        return

    # 2. Git Repository
    try:
        if git.is_inside_work_tree():
            console.print("[green]✔[/green] Inside a valid Git repository.")
        else:
            console.print("[yellow]![/yellow] Not inside a Git repository.")
            if Prompt.ask("Do you want to run 'git init' now?", choices=["y", "n"], default="y") == "y":
                if git.git_init():
                    console.print("[green]✔[/green] Git repository initialized.")
                else:
                    console.print("[red]✘[/red] Failed to initialize Git repository.")
                    return
            else:
                return
    except RuntimeError as e:
        console.print(f"[red]✘[/red] {e}")
        return

    # 3. .aixgit Directory
    if os.path.exists(config.aixgit_dir):
        console.print("[green]✔[/green] .aixgit directory exists.")
    else:
        console.print("[yellow]![/yellow] .aixgit directory is missing.")
        if Prompt.ask("Do you want to initialize .aixgit now?", choices=["y", "n"], default="y") == "y":
            init_aixgit_dir()
            # If init_aixgit_dir returns, it means it finished its own setup
            console.print("[green]✔[/green] .aixgit initialized.")
        else:
            return

    # 4. Configuration Validity
    if os.path.exists(config.config_file):
        if config.is_configured():
            console.print(f"[green]✔[/green] Configuration is valid (Model: {config.get_model()}).")
        else:
            console.print("[red]✘[/red] Configuration is incomplete (missing API key).")
            if Prompt.ask("Do you want to re-run setup to provide API keys?", choices=["y", "n"], default="y") == "y":
                init_aixgit_dir()
    else:
        console.print("[red]✘[/red] config.json is missing.")
        if Prompt.ask("Initialize default configuration?", choices=["y", "n"], default="y") == "y":
            init_aixgit_dir()

    # 5. Prompts
    if os.path.exists(config.prompts_file):
        console.print("[green]✔[/green] prompts.json exists.")
    else:
        console.print("[yellow]![/yellow] prompts.json is missing. Restoring defaults...")
        config.create_default_prompts()
        console.print("[green]✔[/green] prompts.json restored.")

    # 6. .gitignore Security Check
    gitignore_path = os.path.join(os.getcwd(), ".gitignore")
    is_ignored = False
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            lines = f.readlines()
            if any(".aixgit" in line and not line.strip().startswith("#") for line in lines):
                is_ignored = True
                
    if is_ignored:
        console.print("[green]✔[/green] .aixgit is ignored in .gitignore.")
    else:
        console.print("[yellow]![/yellow] [bold red]Security Warning:[/bold red] .aixgit/config.json is NOT in .gitignore!")
        if Prompt.ask("Do you want to add .aixgit/config.json to .gitignore?", choices=["y", "n"], default="y") == "y":
            mode = "a" if os.path.exists(gitignore_path) else "w"
            with open(gitignore_path, mode) as f:
                f.write("\n# aixgit config\n.aixgit/config.json\n")
            console.print("[green]✔[/green] Added to .gitignore.")

    console.print("\n[bold green]✨ All checks completed![/bold green]")


def execute_prompt(prompt: str, command_type: str = "general", explain: str | None = None) -> int:
    config = ConfigManager()
    
    if not config.is_configured():
        console.print("[red]Error: aixgit is not configured or missing API key.[/red]")
        console.print("Please run `aixgit --init` and setup your API keys in .aixgit/config.json")
        return 1

    git = GitClient()
    try:
        if not git.is_inside_work_tree():
            console.print("[red]Error: Not inside a valid git repository.[/red]")
            return 1
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    llm = LLMClient(config)

    with console.status("[cyan]Gathering git context...[/cyan]", spinner="dots"):
        branch = git.get_current_branch()
        status = git.get_status()
        extra_exclude = config.get_exclude_patterns()
        diff = git.get_git_diff(max_lines=2000, exclude_patterns=extra_exclude)
        recent_commits = git.get_recent_commits(limit=5)
        
        project_context = ""
        context_file = os.path.join(config.aixgit_dir, "PROJECT_CONTEXT.md")
        if os.path.exists(context_file):
            try:
                with open(context_file, "r") as f:
                    project_context = f.read()
            except Exception:
                pass

    with console.status(f"[cyan]Translating {command_type} intent to Git commands using AI...[/cyan]", spinner="dots"):
        try:
            suggested_cmd, history = llm.generate_git_command(
                prompt, branch, status, diff, recent_commits, 
                project_context, platform.system(), command_type
            )
        except Exception as e:
            console.print(f"[red]Error communicating with LLM:[/red] {e}")
            return 1
            
    if explain is not None:
        with console.status("[cyan]Generating structural explanation...[/cyan]", spinner="dots"):
            try:
                explanation = llm.explain_git_command(history, extra_prompt=explain)
            except Exception as e:
                explanation = f"Failed to generate explanation: {e}"

    while True:
        # Format the command for better readability
        is_windows = platform.system() == "Windows"
        line_cont = "^" if is_windows else "\\"
        
        parts = []
        for c in suggested_cmd.split("&&"):
            c = c.strip()
            if c.startswith("git add "):
                tokens = c.split()
                if len(tokens) > 3:
                    formatted = f"git add {line_cont}\n  " + f" {line_cont}\n  ".join(tokens[2:])
                    parts.append(formatted)
                else:
                    parts.append(c)
            else:
                parts.append(c)
                
        display_cmd = "\n&& ".join(parts)

        # Present suggestion to user
        if explain is not None:
            console.print("\n[bold yellow]🤖 AI Explanation:[/bold yellow]")
            console.print(Panel(explanation, expand=False, border_style="yellow"))
            
        console.print("\n💡 [bold green]Suggested Command:[/bold green]")
        syntax = Syntax(display_cmd, "bash", theme="monokai", word_wrap=True)
        console.print(Panel(syntax, expand=False, border_style="cyan"))
        console.print("")
        
        try:
            user_input = Prompt.ask("Execute? [Y/n] or Explain? \\[e] or type instructions to modify").strip()
            
            if user_input.lower() in ('y', 'yes', ''):
                console.print("\n[cyan]Executing...[/cyan]")
                exit_code, stderr = git.execute_command(suggested_cmd)
                if exit_code != 0:
                    console.print(f"[red]Command failed with exit code {exit_code}[/red]")
                    if stderr:
                        console.print(Panel(stderr, title="Error Output", border_style="red"))
                    
                    if config.get_auto_debug():
                        console.print("\n[bold cyan]🔍 Command failed. Triggering auto-debug...[/bold cyan]")
                        try:
                            suggested_cmd, history = llm.debug_failed_command(suggested_cmd, stderr, history, platform.system())
                            # Update explain status so the loop shows the new command
                            explain = None 
                            continue # Loop back to show the suggested fix
                        except Exception as e:
                            console.print(f"[red]Auto-debug failed:[/red] {e}")
                    return exit_code
                else:
                    console.print("[green]Command executed successfully![/green]")
                    # Fire-and-forget background thread to update project context
                    threading.Thread(target=llm.update_project_context, args=(suggested_cmd, diff), daemon=False).start()
                return exit_code
            elif user_input.lower() in ('n', 'no', 'q', 'quit', 'exit'):
                console.print("[yellow]Execution canceled.[/yellow]")
                return 0
            elif user_input.strip().lower() in ('e', 'explain') or re.match(r'^e[: ].+', user_input.strip(), re.IGNORECASE) or re.match(r'^explain[: ].+', user_input.strip(), re.IGNORECASE):
                # Extract optional extra question after 'e:' / 'e ' / 'explain:' / 'explain '
                extra_match = re.match(r'^(?:e|explain)[: ]\s*(.+)', user_input.strip(), re.IGNORECASE)
                extra_prompt = extra_match.group(1).strip() if extra_match else ""
                with console.status("[cyan]Generating structural explanation...[/cyan]", spinner="dots"):
                    try:
                        explanation = llm.explain_git_command(history, extra_prompt=extra_prompt)
                        console.print("\n[bold yellow]🤖 AI Explanation:[/bold yellow]")
                        console.print(Panel(explanation, expand=False, border_style="yellow"))
                    except Exception as e:
                        console.print(f"[red]Failed to generate explanation:[/red] {e}")
                continue
            else:
                with console.status("[cyan]Refining command based on your instructions...[/cyan]", spinner="dots"):
                    try:
                        refine_instruction = (
                            f"[Note: the previous command was NOT executed. "
                            f"Adjust the command to ALSO satisfy this additional requirement, "
                            f"while PRESERVING the original intent and all previously selected files/operations. "
                            f"Treat this as an ADDITIVE adjustment, NOT a replacement of the original command. "
                            f"Do NOT drop the original command's purpose or file selections unless the user explicitly says so.] "
                            f"{user_input}"
                        )
                        suggested_cmd, history = llm.refine_git_command(refine_instruction, history)
                    except Exception as e:
                        console.print(f"[red]Error communicating with LLM:[/red] {e}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Canceled by user.[/yellow]")
            return 1
