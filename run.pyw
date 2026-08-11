# run.pyw — Death Clock launcher
#
# This file uses the .pyw extension so Windows opens it with pythonw.exe,
# which suppresses the console window. Only the GUI widget will appear.
#
# To run manually during development, use:
#   uv run python -m death_clock.main
#
# This file is also the target registered in the Windows startup registry.

import sys
import os

# Make sure Python can find the death_clock package regardless of
# where the working directory is when this script runs (e.g. at Windows boot,
# the working directory might be C:\Windows\System32, not our project folder).
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Also inject the .venv site-packages so installed libraries (customtkinter, etc.)
# are available when running via pythonw.exe directly (not via `uv run`).
venv_site = os.path.join(project_dir, ".venv", "Lib", "site-packages")
if os.path.isdir(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

from death_clock.main import main

main()
