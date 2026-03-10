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
        
    def get_git_diff(self, max_lines: int = 2000) -> str:
        """Gets both staged and unstaged git diffs, truncated to max_lines."""
        staged = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=False
        ).stdout
            
        unstaged = subprocess.run(
            ["git", "diff"],
            capture_output=True,
            text=True,
            check=False
        ).stdout
        
        combined_diff = staged + "\n" + unstaged
        lines = combined_diff.split('\n')
        
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f"\n... (diff truncated after {max_lines} lines) ..."
        return combined_diff.strip()

    def get_recent_commits(self, limit: int = 5) -> str:
        """Gets recent commit history formatted as oneline."""
        try:
            res = subprocess.run(
                ["git", "log", f"-n", str(limit), "--oneline"],
                capture_output=True,
                text=True,
                check=False
            )
            return res.stdout.strip()
        except Exception:
            return ""

    def execute_command(self, cmd: str) -> int:
        # Executes the user confirmed string command in the shell
        res = subprocess.run(cmd, shell=True)
        return res.returncode
