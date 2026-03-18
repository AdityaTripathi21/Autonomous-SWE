#!/usr/bin/env python3
"""
quit_listener.py – Simple REPL that exits when the user types 'quit'.

Usage:
    python -m src.main          # start interactive mode
    python -m src.main -h|--help
"""

import sys

def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(
            "Read lines from stdin until the word 'quit' is entered.\n"
            "Usage: quit_listener.py [-h|--help]"
        )
        return 0
    try:
        while True:
            line = input("> ")
            if line.strip().lower() == "quit":
                break
            print(f"You typed: {line}")
    except EOFError:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())