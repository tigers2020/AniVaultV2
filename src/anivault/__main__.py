"""Entry point for `python -m anivault`. Delegates to CLI."""

from anivault.interfaces.cli.main import run

if __name__ == "__main__":
    run()
