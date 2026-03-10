# aixgit
A context-aware AI CLI proxy for Git. Converts natural language to Git commands seamlessly, acting as a smart wrapper around Git.

## Installation
```bash
# Clone the repository and install it locally
pip install -e .
```

## Basic Usage
```bash
# In any Git repository, initialize aixgit:
aixgit --init

# This creates a `.aixgit` directory in the repository. (Note: we should probably consider if the config dir needs renaming too, but keeping .aixgit for now)
# You must edit `.aixgit/config.json` to insert your OpenAI/Anthropic keys.
# Remember to add `.aixgit` (or at least `.aixgit/config.json`) to your `.gitignore`.

# Once configured:
aixgit "Fix the login bug and push to main"
```

## Troubleshooting (Windows)
If you get a `command not found` error after installation:
1. Ensure your Python `Scripts` directory is in your system **PATH**.
2. Alternatively, use `python -m aixgit` instead of `aixgit`.
3. Try restarting your terminal.
