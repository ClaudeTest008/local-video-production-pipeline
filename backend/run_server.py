"""Desktop entry point (PyInstaller). Data lives in the user's app-data dir —
never next to the installed binaries (Program Files is not writable)."""

import os
import sys


def _default_data_dir() -> str:
    if sys.platform == "win32":
        # Roaming AppData — NOT LocalAppData: the NSIS per-user install dir is
        # %LOCALAPPDATA%\LVPP Studio, and user data must survive uninstall.
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(base, "LVPP Studio")


data_dir = os.environ.get("LVPP_DATA_DIR", _default_data_dir())
os.makedirs(data_dir, exist_ok=True)
os.environ.setdefault(
    "LVPP_DATABASE_URL", "sqlite:///" + os.path.join(data_dir, "studio.db").replace("\\", "/")
)
os.environ.setdefault("LVPP_PROJECTS_ROOT", os.path.join(data_dir, "projects"))
os.environ.setdefault("LVPP_LOG_DIR", os.path.join(data_dir, "logs"))

import uvicorn  # noqa: E402

from app.main import app  # noqa: E402  (env must be set before app import)


def _watch_parent(pid: int) -> None:
    """Exit with the desktop shell even if it dies without cleanup (crash,
    force-kill). Windows: block on the process handle; elsewhere: poll."""
    import threading

    def waiter() -> None:
        if sys.platform == "win32":
            import ctypes

            SYNCHRONIZE = 0x00100000
            handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if handle:
                ctypes.windll.kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
                os._exit(0)
        else:
            import time

            while True:
                try:
                    os.kill(pid, 0)
                except OSError:
                    os._exit(0)
                time.sleep(2)

    threading.Thread(target=waiter, daemon=True, name="parent-watchdog").start()


if __name__ == "__main__":
    if "--parent-pid" in sys.argv:
        _watch_parent(int(sys.argv[sys.argv.index("--parent-pid") + 1]))
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("LVPP_PORT", "8321")))
