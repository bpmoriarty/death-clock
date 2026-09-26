"""Launch checks use mocks or unique native object names, never the live clock."""

import importlib
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock
from uuid import uuid4

import pytest

from death_clock import diagnostics, instance, launcher, startup
from death_clock.app import App


ROOT = Path(__file__).resolve().parent.parent


def child(code, *args, **kwargs):
    return subprocess.Popen([sys.executable, "-B", "-c", code, *args], cwd=ROOT,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, **kwargs)


def test_native_second_process_queues_show_then_exits():
    name = "Global\\DeathClock-test-" + uuid4().hex
    with instance.SingleInstance(name) as owner:
        assert owner.is_primary
        script = """
import sys
from death_clock.instance import SingleInstance
with SingleInstance(sys.argv[1]) as gate:
    assert not gate.is_primary
    gate.request_show()
    print('secondary exited')
"""
        process = child(script, name)
        out, err = process.communicate(timeout=10)
        assert process.returncode == 0, err
        assert out.strip() == "secondary exited"
        assert owner.take_show_request()  # request waited while UI was not polling
        assert not owner.take_show_request()
    with instance.SingleInstance(name) as next_owner:
        assert next_owner.is_primary


def test_native_crashed_owner_does_not_leave_a_stale_lock():
    name = "Global\\DeathClock-test-" + uuid4().hex
    script = """
import os, sys
from death_clock.instance import SingleInstance
gate = SingleInstance(sys.argv[1])
assert gate.is_primary
print('ready', flush=True)
input()
os._exit(0)
"""
    process = child(script, name)
    try:
        assert process.stdout.readline().strip() == "ready"
        with instance.SingleInstance(name) as observer:
            assert not observer.is_primary
            process.communicate("exit\n", timeout=10)
            # observer keeps the kernel object alive, testing WAIT_ABANDONED.
            with instance.SingleInstance(name) as replacement:
                assert replacement.is_primary
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_instance_identity_is_user_scoped_not_project_scoped(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user A"))
    first = instance.instance_name()
    monkeypatch.chdir(tmp_path)
    assert instance.instance_name() == first
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user B"))
    assert instance.instance_name() != first


def test_simultaneous_processes_have_exactly_one_owner():
    name = "Global\\DeathClock-test-" + uuid4().hex
    script = """
import sys
from death_clock.instance import SingleInstance
with SingleInstance(sys.argv[1]) as gate:
    if gate.is_primary:
        print('owner', flush=True)
        input()
        print(gate.take_show_request(), flush=True)
    else:
        gate.request_show()
        print('secondary', flush=True)
"""
    processes = [child(script, name), child(script, name)]
    try:
        roles = [p.stdout.readline().strip() for p in processes]
        assert sorted(roles) == ["owner", "secondary"]
        for process, role in zip(processes, roles):
            out, err = process.communicate("exit\n" if role == "owner" else None, timeout=10)
            assert process.returncode == 0, err
            if role == "owner":
                assert out.strip() == "True"
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)


@pytest.fixture
def runtime(tmp_path):
    project = tmp_path / "Project with spaces"
    scripts = project / ".venv" / "Scripts"
    scripts.mkdir(parents=True)
    for filename in ("python.exe", "pythonw.exe"):
        (scripts / filename).touch()
    return project


def test_launcher_uses_exact_project_interpreter_and_cwd(runtime, monkeypatch):
    run = Mock(return_value=SimpleNamespace(returncode=0))
    popen = Mock()
    monkeypatch.setattr(launcher.subprocess, "run", run)
    monkeypatch.setattr(launcher.subprocess, "Popen", popen)
    assert launcher.launch(runtime) == 0
    assert run.call_args.args[0][0] == str(runtime / ".venv/Scripts/python.exe")
    assert "-I" in run.call_args.args[0]
    assert popen.call_args.args[0] == [str(runtime / ".venv/Scripts/pythonw.exe"),
                                       "-B", "-m", "death_clock.main"]
    assert popen.call_args.kwargs["cwd"] == runtime
    assert popen.call_args.kwargs["creationflags"] == subprocess.CREATE_NO_WINDOW


@pytest.mark.parametrize("failure", [
    SimpleNamespace(returncode=1), OSError("denied"), subprocess.TimeoutExpired("python", 20),
])
def test_bad_runtime_reports_error_without_launching(runtime, monkeypatch, failure):
    probe = Mock()
    if isinstance(failure, Exception):
        probe.side_effect = failure
    else:
        probe.return_value = failure
    monkeypatch.setattr(launcher.subprocess, "run", probe)
    spawn = Mock()
    report = Mock()
    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    monkeypatch.setattr(launcher, "report_error", report)
    assert launcher.launch(runtime) == 1
    spawn.assert_not_called()
    report.assert_called_once()


def test_missing_runtime_does_not_fall_back_to_arbitrary_python(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "report_error", Mock())
    spawn = Mock()
    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    assert launcher.launch(tmp_path) == 1
    spawn.assert_not_called()


def test_diagnostic_log_omits_exception_values_and_source_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostics, "log_directory", lambda: tmp_path)
    try:
        raise ValueError("PRIVATE DOB OR TARGET 2099-01-01")
    except ValueError as error:
        path = diagnostics.record_error("startup", error)
    text = path.read_text()
    assert "ValueError" in text
    assert "PRIVATE" not in text and "2099" not in text
    assert "test_launching.py:" in text


def test_diagnostic_logs_rotate_and_fail_gracefully(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostics, "log_directory", lambda: tmp_path)
    path = tmp_path / "death-clock.log"
    path.write_text("x" * 32768)
    diagnostics.record_error("startup", RuntimeError())
    assert path.stat().st_size < 1024
    assert (tmp_path / "death-clock.previous.log").stat().st_size == 32768
    monkeypatch.setattr(diagnostics, "log_directory", lambda: path / "not-a-directory")
    assert diagnostics.record_error("startup", RuntimeError()) is None


def test_main_secondary_never_constructs_or_loads_app(monkeypatch):
    main = importlib.import_module("death_clock.main")
    gate = MagicMock()
    gate.__enter__.return_value = gate
    gate.is_primary = False
    monkeypatch.setattr(main, "SingleInstance", Mock(return_value=gate))
    app = Mock()
    monkeypatch.setattr("death_clock.app.App", app)
    assert main.main() == 0
    gate.request_show.assert_called_once()
    app.assert_not_called()
    gate.__exit__.assert_called_once()


def test_main_cleans_up_app_and_lock_after_failure(monkeypatch):
    main = importlib.import_module("death_clock.main")
    gate = MagicMock()
    gate.__enter__.return_value = gate
    gate.is_primary = True
    monkeypatch.setattr(main, "SingleInstance", Mock(return_value=gate))
    app = Mock()
    app.run.side_effect = RuntimeError("failure")
    monkeypatch.setattr("death_clock.app.App", Mock(return_value=app))
    monkeypatch.setattr(main, "report_error", Mock())
    assert main.main() == 1
    app.close.assert_called_once()
    gate.__exit__.assert_called_once()
    main.report_error.assert_called_once()


def test_repeat_launch_shows_hidden_widget_and_existing_settings():
    app = App.__new__(App)
    app.instance = Mock()
    app.instance.take_show_request.return_value = True
    app.widget = Mock()
    app.root = Mock()
    app._settings_window = Mock()
    app._poll_show_requests()
    app.widget.show.assert_called_once()
    app._settings_window.win.lift.assert_called_once()
    app.root.after.assert_called_once_with(250, app._poll_show_requests)


def test_repeat_launch_raises_first_run_form_without_widget():
    app = App.__new__(App)
    app.widget = None
    app._settings_window = Mock()
    app._show_widget()
    app._settings_window.win.deiconify.assert_called_once()
    app._settings_window.win.focus_force.assert_called_once()


def test_open_settings_reuses_existing_form(monkeypatch):
    app = App.__new__(App)
    app._settings_window = Mock()
    factory = Mock()
    monkeypatch.setattr("death_clock.app.SettingsWindow", factory)
    app._open_settings()
    factory.assert_not_called()
    app._settings_window.win.lift.assert_called_once()


def test_startup_quotes_space_paths_and_uses_checked_launcher(monkeypatch, tmp_path):
    folder = tmp_path / "Project with spaces"
    folder.mkdir()
    (folder / "Start Death Clock.vbs").touch()
    monkeypatch.setattr(startup, "_get_project_root", lambda: str(folder))
    command = startup._build_startup_command()
    assert '"' + str(folder / "Start Death Clock.vbs") + '"' in command
    assert "wscript.exe" in command and "//nologo" in command
    assert "pythonw.exe" not in command


def test_registry_operations_close_handles_even_on_failure(monkeypatch):
    handle = MagicMock()
    monkeypatch.setattr(startup.winreg, "OpenKey", Mock(return_value=handle))
    monkeypatch.setattr(startup, "_build_startup_command", lambda: "checked launcher")
    monkeypatch.setattr(startup.winreg, "SetValueEx", Mock(side_effect=OSError))
    with pytest.raises(OSError):
        startup.add_to_startup()
    handle.__exit__.assert_called_once()


def test_background_tray_failure_is_reported(monkeypatch):
    app = App.__new__(App)
    app.tray_icon = Mock()
    app.tray_icon.run.side_effect = OSError("private error data")
    report = Mock()
    monkeypatch.setattr("death_clock.app.report_error", report)
    app._run_tray()
    assert report.call_args.args[0] == "system tray"


def test_close_destroys_root_even_when_tray_stop_fails():
    app = App.__new__(App)
    app.root = Mock()
    app.tray_icon = Mock()
    app.tray_icon.stop.side_effect = OSError()
    with pytest.raises(OSError):
        app.close()
    app.root.destroy.assert_called_once()


def run_vbs(path, *args, env=None):
    host = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/cscript.exe"
    return subprocess.run([str(host), "//nologo", "//T:10", str(path), *args],
                          capture_output=True, text=True, timeout=15, env=env,
                          creationflags=subprocess.CREATE_NO_WINDOW)


@pytest.mark.parametrize("filename", ["Start Death Clock.vbs", "Create Desktop Shortcut.vbs"])
def test_windows_scripts_compile_without_executing_actions(tmp_path, filename):
    source = (ROOT / filename).read_text()
    # WSH parses the entire file before executing this early exit.
    assert source.count("Option Explicit") == 1
    source = source.replace("Option Explicit", "Option Explicit\nWScript.Quit 0", 1)
    path = tmp_path / filename
    path.write_text(source)
    result = run_vbs(path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_windows_bootstrap_reports_missing_runtime_in_isolated_folder(tmp_path):
    folder = tmp_path / "Project with spaces"
    folder.mkdir()
    path = folder / "Start Death Clock.vbs"
    # Replace only dialogs with console messages; no interactive prompts in tests.
    path.write_text((ROOT / path.name).read_text().replace("MsgBox ", "WScript.Echo "))
    local = tmp_path / "local"
    local.mkdir()
    result = run_vbs(path, env={**os.environ, "LOCALAPPDATA": str(local)})
    assert result.returncode == 1
    log = local / "DeathClock/logs/bootstrap.log"
    assert "bootstrap: RuntimeUnavailable" in log.read_text()
    assert not (folder / "settings.json").exists()


def test_shortcut_targets_checked_bootstrap_with_space_paths(tmp_path):
    folder = tmp_path / "Project with spaces"
    folder.mkdir()
    path = folder / "Start Death Clock.vbs"
    desktop = tmp_path / "Fake desktop"
    desktop.mkdir()
    source = (ROOT / path.name).read_text()
    lookup = 'shell.SpecialFolders("Desktop")'
    assert source.count(lookup) == 1
    # Redirect only the destination; exercise real Windows .lnk creation.
    source = source.replace(lookup, '"' + str(desktop).replace('"', '""') + '"')
    source = source.replace("MsgBox ", "WScript.Echo ")
    path.write_text(source)
    result = run_vbs(path, "/shortcut")
    assert result.returncode == 0, result.stdout + result.stderr
    shortcut = desktop / "Death Clock.lnk"
    assert shortcut.exists()
    inspector = tmp_path / "read shortcut.vbs"
    inspector.write_text('Set s = CreateObject("WScript.Shell")\n'
                         'Set link = s.CreateShortcut(WScript.Arguments(0))\n'
                         'WScript.Echo link.TargetPath\n'
                         'WScript.Echo link.Arguments\n'
                         'WScript.Echo link.WorkingDirectory\n')
    result = run_vbs(inspector, str(shortcut))
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert lines[0].lower().endswith(r"system32\wscript.exe")
    assert lines[1] == '//nologo "' + str(path) + '"'
    assert lines[2] == str(folder)
