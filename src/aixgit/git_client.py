import subprocess
import os
import platform

class GitClient:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    def _run_git(self, args: list, check: bool = False, text: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Helper to run git commands with OS-specific settings."""
        try:
            return subprocess.run(
                args,
                shell=self.is_windows,
                capture_output=capture_output,
                check=check,
                text=text
            )
        except OSError as e:
            # Handle case where 'git' is not in PATH
            if e.errno == 2: # File not found
                raise RuntimeError("Git command not found. Please ensure Git is installed and in your PATH.") from e
            raise

    def is_inside_work_tree(self) -> bool:
        try:
            self._run_git(["git", "rev-parse", "--is-inside-work-tree"], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> str:
        res = self._run_git(["git", "branch", "--show-current"], check=False)
        return res.stdout.strip()

    def get_status(self) -> str:
        res = self._run_git(["git", "status", "-s"], check=False)
        return res.stdout.strip()
        
    def get_git_diff(self, max_lines: int = 2000, exclude_patterns: list = None) -> str:
        """Gets both staged and unstaged git diffs, excluding configured noise files."""
        # Build git pathspec exclusion args: ':(exclude)pattern'
        pathspec = []
        if exclude_patterns:
            pathspec = ["--"] + [f":(exclude){p}" for p in exclude_patterns]

        staged = self._run_git(["git", "diff", "--cached"] + pathspec, check=False).stdout
        unstaged = self._run_git(["git", "diff"] + pathspec, check=False).stdout
        
        combined_diff = staged + "\n" + unstaged
        lines = combined_diff.split('\n')
        
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f"\n... (diff truncated after {max_lines} lines) ..."
        return combined_diff.strip()

    def get_recent_commits(self, limit: int = 10) -> str:
        """Gets recent commit history with subject and body for style analysis."""
        try:
            res = self._run_git(["git", "log", f"-n{limit}", "--pretty=format:%s%n%b%n---"], check=False)
            return res.stdout.strip()
        except Exception:
            return ""

    def git_init(self) -> bool:
        """Initializes a new git repository in the current directory."""
        try:
            self._run_git(["git", "init"], check=True)
            return True
        except (subprocess.CalledProcessError, RuntimeError):
            return False

    def execute_command(self, cmd: str) -> tuple[int, str]:
        """Executes the user confirmed string command in the shell. Returns (exit_code, stderr)."""
        res = subprocess.run(cmd, shell=True, capture_output=False, stderr=subprocess.PIPE, text=True)
        return res.returncode, res.stderr.strip()
