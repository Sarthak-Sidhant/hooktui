"""Entry point for `python -m hooktui`."""
from hooktui.app import HookTUIApp

def main():
    app = HookTUIApp()
    app.run()

if __name__ == "__main__":
    main()
