from __future__ import annotations
import os
import platform
import subprocess
from typing import Optional

try:
    from plyer import notification  # type: ignore
except Exception:  # pragma: no cover
    notification = None  # type: ignore


def desktop_notify(title: str, message: str, timeout: int = 5) -> None:
    """Fire a desktop notification if possible, else print to console.
    On macOS, falls back to AppleScript if plyer isn't available.
    """
    # Try plyer first
    if notification is not None:
        try:
            notification.notify(title=title, message=message, timeout=timeout)
            return
        except Exception:
            pass

    # macOS fallback via AppleScript
    if platform.system() == "Darwin":
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False)
            return
        except Exception:
            pass

    # Final fallback
    print(f"[NOTIFY] {title}: {message}")


def play_sound() -> None:
    """Optional subtle sound cue; best-effort only."""
    try:
        if platform.system() == "Darwin":
            # Use built-in sound on macOS
            sound = "/System/Library/Sounds/Glass.aiff"
            if os.path.exists(sound):
                subprocess.run(["afplay", sound], check=False)
        else:
            # Terminal bell as last resort
            print("\a", end="")
    except Exception:
        pass
