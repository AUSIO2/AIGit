# aigit
A context-aware AI CLI proxy for Git. Converts natural language to Git commands seamlessly, acting as a smart wrapper around Git.

## Installation
```bash
# Clone the repository and install it locally
pip install -e .
```

## Basic Usage
```bash
# In any Git repository, initialize aigit:
aigit --init

# This creates a `.aigit` directory in the repository.
# You must edit `.aigit/config.json` to insert your OpenAI/Anthropic keys.
# Remember to add `.aigit` (or at least `.aigit/config.json`) to your `.gitignore`.

# Once configured:
aigit "Fix the login bug and push to main"
```
