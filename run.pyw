# Dependency-free bootstrap for .pyw associations and Start Death Clock.vbs.
# It checks the project environment and launches pythonw without mixing packages.

from death_clock.launcher import launch

if __name__ == "__main__":
    # 10 tells the Windows bootstrap that a friendly error was already shown.
    raise SystemExit(10 if launch() else 0)
