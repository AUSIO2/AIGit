import argparse
import sys
from .core import execute_prompt, init_aigit_dir

def main():
    parser = argparse.ArgumentParser(description="aigit - AI powered Git Assistant")
    parser.add_argument("prompt", nargs="*", help="Natural language description of your Git intent")
    parser.add_argument("--init", action="store_true", help="Initialize .aigit directory in the current repository")
    
    args = parser.parse_args()
    
    if args.init:
        init_aigit_dir()
        return 0
        
    if not args.prompt:
        parser.print_help()
        return 1
        
    user_prompt = " ".join(args.prompt)
    return execute_prompt(user_prompt)

if __name__ == "__main__":
    sys.exit(main())
