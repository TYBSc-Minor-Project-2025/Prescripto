
# filepath: /Users/anuragbhosale/Desktop/Projects/Prescripto/src/notify.py
"""
notify.py
Cross-platform desktop notifications for Prescripto.

Tries, in order:
- macOS: pync (Notification Center) or AppleScript
- Linux: notify-send
- Windows: win10toast
"""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pync  # macOS Notification Center
except ImportError:
    pync = None  # type: ignore

try:
    from win10toast import ToastNotifier  # Windows 10 notifications
except ImportError:
    ToastNotifier = None  # type: ignore


@dataclass
class Notification:
    title: str
    message: str
    subtitle: str = ""


def _notify_macos(n: Notification) -> bool:
    # Prefer pync if available
    if pync is not None:
        try:
            pync.notify(
                n.message,
                title=n.title,
                subtitle=n.subtitle or "",
            )
            return True
        except Exception as e:
            logger.error("macOS pync notify failed: %s", e, exc_info=True)

    # Fallback: AppleScript via osascript
    script = f'display notification "{n.message}" with title "{n.title}"'
    if n.subtitle:
        script = (
            f'display notification "{n.message}" with title '
            f'"{n.title}" subtitle "{n.subtitle}"'
        )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except Exception as e:
        logger.error("macOS AppleScript notify failed: %s", e, exc_info=True)
        return False


def _notify_linux(n: Notification) -> bool:
    # Uses `notify-send` (libnotify)
    try:
        cmd = ["notify-send", n.title, n.message]
        if n.subtitle:
            cmd.append(f"({n.subtitle})")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        logger.error("Linux notify-send failed: %s", e, exc_info=True)
        return False


def _notify_windows(n: Notification) -> bool:
    if ToastNotifier is None:
        logger.warning("win10toast not installed; cannot show Windows toast.")
        return False

    try:
        toaster = ToastNotifier()
        toaster.show_toast(
            n.title,
            f"{n.subtitle}\n{n.message}" if n.subtitle else n.message,
            duration=5,
            threaded=True,
        )
        return True
    except Exception as e:
        logger.error("Windows toast notification failed: %s", e, exc_info=True)
        return False


def desktop_notify(title: str, message: str, subtitle: str = "") -> bool:
    """
    Try to show a desktop notification; return True on success, False otherwise.
    """
    n = Notification(title=title, message=message, subtitle=subtitle)
    system = platform.system().lower()
    logger.info("Sending notification on %s: %s", system, n)

    if system == "darwin":
        return _notify_macos(n)
    if system == "linux":
        return _notify_linux(n)
    if system == "windows":
        return _notify_windows(n)

    logger.warning("Unsupported platform for notifications: %s", system)
    return False