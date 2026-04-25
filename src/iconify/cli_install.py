from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

APP_NAME = "Iconify"
COMMAND_NAME = "iconify"
SETTINGS_NAME = "settings.json"


def settings_path() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "Iconify" / SETTINGS_NAME


def load_settings() -> dict[str, Any]:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")


def set_cli_prompt_suppressed(value: bool) -> None:
    settings = load_settings()
    settings["suppress_cli_install_prompt"] = value
    save_settings(settings)


def cli_prompt_suppressed() -> bool:
    return bool(load_settings().get("suppress_cli_install_prompt"))


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False)) and Path(sys.executable).exists()


def app_source_dir() -> Path:
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def current_executable() -> Path:
    return Path(sys.executable).resolve() if is_frozen_app() else Path(sys.argv[0]).resolve()


def installed_app_dir() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Programs" / APP_NAME
    return Path.home() / ".local" / "share" / "iconify"


def cli_dir() -> Path:
    if platform.system() == "Windows":
        return installed_app_dir()
    return Path.home() / ".local" / "bin"


def cli_executable() -> Path:
    suffix = ".exe" if platform.system() == "Windows" else ""
    return cli_dir() / f"{COMMAND_NAME}{suffix}"


def found_cli() -> Path | None:
    found = shutil.which(COMMAND_NAME)
    return Path(found).resolve() if found else None


def cli_status() -> str:
    found = found_cli()
    if not found:
        return "Command line install not found."
    ok, message = test_cli()
    return f"Command line install found at {found}. {message if ok else 'Test failed: ' + message}"


def test_cli() -> tuple[bool, str]:
    found = found_cli()
    if not found:
        return False, "iconify is not on PATH."
    try:
        result = subprocess.run(
            [str(found), "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return False, str(exc)
    if result.returncode == 0 and "usage: iconify" in result.stdout:
        return True, "iconify --help completed successfully."
    output = (result.stderr or result.stdout or "no output").strip()
    return False, output


def install_cli() -> tuple[bool, str]:
    if not is_frozen_app():
        return False, "Build Iconify first, then run the packaged app to install the command."

    if platform.system() == "Windows":
        return _install_windows_cli()
    return _install_unix_cli()


def uninstall_cli() -> tuple[bool, str]:
    if platform.system() == "Windows":
        return _uninstall_windows_cli()
    return _uninstall_unix_cli()


def _install_windows_cli() -> tuple[bool, str]:
    source = app_source_dir()
    target = installed_app_dir()
    if source != target:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    _add_user_path(target)

    ok, message = test_cli()
    if ok:
        return True, f"Installed iconify to {target} and added it to your user PATH."
    return False, f"Installed files to {target}, but PATH test failed. Open a new terminal and try again. {message}"


def _install_unix_cli() -> tuple[bool, str]:
    source = app_source_dir()
    target = installed_app_dir()
    if source != target:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)

    bin_dir = cli_dir()
    bin_dir.mkdir(parents=True, exist_ok=True)
    link = cli_executable()
    executable = target / COMMAND_NAME
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(executable)
    _ensure_local_bin_profile()
    _add_process_path(str(bin_dir))

    ok, message = test_cli()
    if ok:
        return True, f"Installed iconify to {link}."
    return False, f"Installed {link}. Open a new terminal if PATH was just updated. {message}"


def _uninstall_windows_cli() -> tuple[bool, str]:
    target = installed_app_dir()
    _remove_user_path(target)
    _remove_process_path(str(target), separator=";")
    current_dir = app_source_dir()
    if target.exists() and target != current_dir:
        shutil.rmtree(target)
        return True, "Removed Iconify from your user PATH and deleted the installed command files."
    if target == current_dir:
        return True, "Removed Iconify from your user PATH. Close the app before deleting its install folder."
    return True, "Removed Iconify from your user PATH."


def _uninstall_unix_cli() -> tuple[bool, str]:
    link = cli_executable()
    if link.exists() or link.is_symlink():
        link.unlink()
    target = installed_app_dir()
    current_dir = app_source_dir()
    if target.exists() and target != current_dir:
        shutil.rmtree(target)
    return True, "Removed the iconify command line install."


def _add_user_path(path: Path) -> None:
    import winreg

    value = str(path)
    current = _read_user_path(winreg)
    parts = [part for part in current.split(";") if part]
    if value.lower() not in {part.lower() for part in parts}:
        parts.append(value)
        _write_user_path(winreg, ";".join(parts))
    _add_process_path(value, separator=";")


def _remove_user_path(path: Path) -> None:
    import winreg

    value = str(path).lower()
    parts = [part for part in _read_user_path(winreg).split(";") if part]
    kept = [part for part in parts if part.lower() != value]
    _write_user_path(winreg, ";".join(kept))


def _read_user_path(winreg: Any) -> str:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as key:
        try:
            value, _kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            return ""
    return value


def _write_user_path(winreg: Any, value: str) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, value)
    _broadcast_environment_change()


def _broadcast_environment_change() -> None:
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        hwnd_broadcast = 0xFFFF
        wm_settingchange = 0x001A
        ctypes.windll.user32.SendMessageTimeoutW(
            hwnd_broadcast,
            wm_settingchange,
            0,
            "Environment",
            0,
            5000,
            None,
        )
    except Exception:
        pass


def _ensure_local_bin_profile() -> None:
    profile = Path.home() / ".profile"
    export_line = 'export PATH="$HOME/.local/bin:$PATH"'
    try:
        text = profile.read_text(encoding="utf-8") if profile.exists() else ""
        if ".local/bin" not in text:
            profile.write_text(f"{text.rstrip()}\n\n{export_line}\n", encoding="utf-8")
    except OSError:
        pass


def _add_process_path(value: str, separator: str = os.pathsep) -> None:
    parts = [part for part in os.environ.get("PATH", "").split(separator) if part]
    if value.lower() not in {part.lower() for part in parts}:
        os.environ["PATH"] = separator.join([*parts, value])


def _remove_process_path(value: str, separator: str = os.pathsep) -> None:
    normalized = value.lower()
    parts = [part for part in os.environ.get("PATH", "").split(separator) if part]
    os.environ["PATH"] = separator.join(part for part in parts if part.lower() != normalized)
