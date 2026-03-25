# src/main.py
import sys

def add(a, b):
    """Return the sum of a and b as float."""
    return a + b

def sub(a, b):
    """Return the difference of a and b as float."""
    return a - b

def mul(a, b):
    """Return the product of a and b as float."""
    return a * b

def div(a, b):
    """Return the division of a by b as float.

    Raises ZeroDivisionError if b is zero.
    """
    if b == 0:
        raise ZeroDivisionError
    return a / b

def print_help():
    """Print usage instructions."""
    help_text = """Available commands:
  add a b   or  + a b   → a + b
  sub a b   or  - a b   → a - b
  mul a b   or  * a b   → a * b
  div a b   or  / a b   → a / b   (division by zero not allowed)
Special commands:
  help (h)   – show this help
  quit (q)   – exit the program
Examples:
  > add 2 3
  5.0
  > / 10 2
  5.0"""
    print(help_text)

def print_error(message):
    """Print an error message prefixed with 'Error:'."""
    print(f"Error: {message}")

def parse_input(line):
    """Normalize input line and split into command and arguments.

    Returns a tuple (cmd, args) where cmd is lower‑cased command string
    and args is a list of remaining tokens.
    """
    tokens = line.strip().split()
    if not tokens:
        return "", []
    cmd = tokens[0].lower()
    args = tokens[1:]
    return cmd, args

def execute_command(cmd, args):
    """Execute a parsed command with arguments.

    Prints result or error messages directly.
    """
    arithmetic_ops = {
        "add": add, "+": add,
        "sub": sub, "-": sub,
        "mul": mul, "*": mul,
        "div": div, "/": div,
    }
    if cmd in ("help", "h"):
        print_help()
        return
    if cmd in ("quit", "exit", "q"):
        print("Good‑bye!")
        sys.exit(0)
    if cmd not in arithmetic_ops:
        print_error("Unknown command")
        return
    if len(args) != 2:
        print_error("Expected two arguments")
        return
    try:
        a = float(args[0])
        b = float(args[1])
    except ValueError:
        print_error("Non-numeric argument")
        return
    try:
        result = arithmetic_ops[cmd](a, b)
    except ZeroDivisionError:
        print_error("Division by zero")
        return
    except Exception:
        print_error("Internal error")
        return
    print(result)

def repl_loop():
    """Read‑Eval‑Print loop for the calculator."""
    while True:
        try:
            line = input("calc> ")
        except EOFError:
            print("\nGood‑bye!")
            break
        cmd, args = parse_input(line)
        if not cmd:
            continue
        execute_command(cmd, args)

def main():
    """Entry point for the calculator script."""
    print('Welcome to Python Calculator! Type "help" for usage.')
    repl_loop()

if __name__ == "__main__":
    main()
