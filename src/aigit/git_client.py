import subprocess

class GitClient:
    def is_inside_work_tree(self) -> bool:
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> str:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout.strip()

    def get_status(self) -> str:
        res = subprocess.run(
            ["git", "status", "-s"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout.strip()
        
    def get_git_diff(self, max_lines: int = 2000, exclude_patterns: list = None) -> str:
        """Gets both staged and unstaged git diffs, excluding configured noise files."""
        # Build git pathspec exclusion args: ':(exclude)pattern'
        pathspec = []
        if exclude_patterns:
            pathspec = ["--"] + [f":(exclude){p}" for p in exclude_patterns]

        staged = subprocess.run(
            ["git", "diff", "--cached"] + pathspec,
            capture_output=True,
            text=True,
            check=False
        ).stdout
            
        unstaged = subprocess.run(
            ["git", "diff"] + pathspec,
            capture_output=True,
            text=True,
            check=False
        ).stdout
        
        combined_diff = staged + "\n" + unstaged
        lines = combined_diff.split('\n')
        
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f"\n... (diff truncated after {max_lines} lines) ..."
        return combined_diff.strip()

    def get_recent_commits(self, limit: int = 10) -> str:
        """Gets recent commit history with subject and body for style analysis."""
        try:
            res = subprocess.run(
                ["git", "log", f"-n{limit}", "--pretty=format:%s%n%b%n---"],
                capture_output=True,
                text=True,
                check=False
            )
            return res.stdout.strip()
        except Exception:
            return ""

    def execute_command(self, cmd: str) -> tuple[int, str]:
        """Executes the user confirmed string command in the shell. Returns (exit_code, stderr)."""
        res = subprocess.run(cmd, shell=True, capture_output=False, stderr=subprocess.PIPE, text=True)
        return res.returncode, res.stderr.strip()
