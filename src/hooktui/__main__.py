"""Entry point for `python -m hooktui`."""
from hooktui.app import HookTUIApp

def main():
    from hooktui.app import main as app_main
    app_main()

if __name__ == "__main__":
    main()
