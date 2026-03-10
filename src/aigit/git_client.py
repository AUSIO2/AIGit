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

    def execute_command(self, cmd: str) -> int:
        # Executes the user confirmed string command in the shell
        res = subprocess.run(cmd, shell=True)
        return res.returncode
