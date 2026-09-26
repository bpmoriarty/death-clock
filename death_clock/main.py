"""
Death Clock — entry point.

Owns the single-instance lifetime, imports the UI only for the primary process,
and reports startup failures even if the UI dependencies cannot load.
"""

from .diagnostics import report_error
from .instance import SingleInstance


def main():
    # Acquire before importing the UI or reading settings. A repeat launch does
    # nothing except queue a reveal request and exit.
    try:
        with SingleInstance() as instance:
            if not instance.is_primary:
                instance.request_show()
                return 0
            from .app import App
            app = App(instance=instance)
            try:
                app.run()
            finally:
                app.close()
        return 0
    except Exception as error:
        report_error("application startup", error,
                     "Death Clock could not run. Close any older clock instance normally, "
                     "then try again. If this repeats, follow launch troubleshooting in README.md. "
                     "Your saved target has not been recalculated.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
