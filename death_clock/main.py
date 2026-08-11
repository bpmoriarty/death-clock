"""
Death Clock — entry point.

This is what gets called when the app starts. It simply creates the App
object and runs it. All the real logic is in app.py.
"""

from .app import App


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
