import subprocess
import psutil
from dataclasses import dataclass

# Processes that are not user facing and should be excluded
BACKGROUND_PROCESSES = [
    "bash", "sh", "zsh", "fish", "dash", "ksh",
    "python", "python3", "node", "ruby", "perl",
    "systemd", "dbus", "pulseaudio", "pipewire",
    "Xorg", "xwayland", "wayland",
    "kernel", "kworker", "kthread",
    "grep", "awk", "sed", "cat", "ls", "ps",
    "dconf", "gvfsd", "ibus", "fcitx",
    "at-spi", "gnome-shell-calendar",
    "xdg-permission-store", "xdg-document-portal", "xdg-desktop-portal",
    "swww-daemon", "swww", "hyprland"
]

BACKGROUND_KEYWORDS = [
    "daemon", "worker", "helper", "agent", "service",
    "broker", "watchdog", "monitor", "server",
    "dbus", "systemd", "kernel", "kworker",
    "gvfs", "ibus", "fcitx", "xdg",
    "swww", "xwayland", "hyprland", "sway", "compositor"
]

@dataclass
class AppInfo:
    pid: int
    name: str
    friendly_name: str
    cpu_percent: float
    memory_mb: float
    status: str

    def __str__(self):
        return (
            f"    {self.friendly_name} (PID {self.pid})\n"
            f"        CPU: {self.cpu_percent:.1f}% | "
            f"Memory: {self.memory_mb:.1f} MB | "
            f"Status: {self.status}"
        )

class ProcessManager:

    # Map raw process names to human-friendly display names
    FRIENDLY_NAMES : dict[str, str] = {
        "chrome": "Google Chrome",
        "google-chrome": "Google Chrome",
        "chromium": "Chromium",
        "chromium-browser": "Chromium",
        "firefox": "Firefox",
        "firefox-esr": "Firefox ESR",
        "brave": "Brave Browser",
        "opera": "Opera",
        "vivaldi": "Vivaldi",

        "kitty": "Kitty Terminal",
        "alacritty": "Alacritty Terminal",
        "gnome-terminal": "GNOME Terminal",
        "xterm": "XTerm",
        "konsole": "Konsole",
        "tilix": "Tilix",
        "wezterm": "WezTerm",
        "foot": "Foot Terminal",
        "urxvt": "URxvt Terminal",
        "rxvt": "Rxvt Terminal",
        "st": "st Terminal",
        "xfce4-terminal": "XFCE Terminal",

        "spotify": "Spotify",
        "vlc": "VLC Media Player",
        "mpv": "MPV Media Player",
        "rhythmbox": "Rhythmbox",
        "clementine": "Clementine",
        "audacious": "Audacious",
        "deadbeef": "DeaDBeeF",
        "cmus": "cmus",

        "code": "VS Code",
        "code-oss": "VS Code OSS",
        "codium": "VSCodium",
        "sublime_text": "Sublime Text",
        "atom": "Atom",
        "gedit": "Text Editor (gedit)",
        "kate": "Kate",
        "vim": "Vim",
        "nvim": "Neovim",
        "emacs": "Emacs",

        "nautilus": "Files (Nautilus)",
        "thunar": "Thunar File Manager",
        "dolphin": "Dolphin File Manager",
        "nemo": "Nemo File Manager",

        "slack": "Slack",
        "discord": "Discord",
        "telegram": "Telegram",
        "signal": "Signal",
        "thunderbird": "Thunderbird",
        "evolution": "Evolution Mail",

        "gimp": "GIMP",
        "inkscape": "Inkscape",
        "blender": "Blender",
        "obs": "OBS Studio",
        "krita": "Krita",

        "zoom": "Zoom",
        "teams": "Microsoft Teams",
        "skype": "Skype",

        "libreoffice": "LibreOffice",
        "soffice": "LibreOffice",
        "evince": "Document Viewer",
        "okular": "Okular PDF Viewer",

        "steam": "Steam",
        "lutris": "Lutris",
    }

    def get_friendly_name(self, raw_name : str) -> str | None:
        # Return a friendly display name, or None if the process
        # looks like a background task.
        lower = raw_name.lower()

        if lower in BACKGROUND_PROCESSES or any(kw in lower for kw in BACKGROUND_KEYWORDS):
            return None

        # Look up a curated friendly name, otherwise title-case the raw name
        return self.FRIENDLY_NAMES.get(lower) or self.FRIENDLY_NAMES.get(raw_name)

    def is_gui_process(self, proc : psutil.Process) -> bool:
        # Return true if the process has an open window
        # (holds a display connection).
        try:
            for conn in psutil.net_connections(kind = "unix"):
                if conn.pid != proc.pid:
                    continue

                path = conn.laddr or ""
                if isinstance(path, str) and ("wayland" in path.lower() or "x11" in path.lower()):
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            pass

        return False

    def has_open_window(self, pid : int) -> bool:
        # Check via 'xdotool' (if available) whether the PID owns any windows
        try:
            result = subprocess.run(
                ["xdotool", "search", "--pid", str(pid)],
                capture_output = True,
                timeout = 1
            )
            return bool(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_running_apps(self) -> list[AppInfo]:
        # Return a deduplicated list of user-facing applications currently running.
        # Each application appears only once even if it has multiple processes.
        apps : dict[str, AppInfo] = {}

        for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_info"]):
            try:
                raw_name = proc.info["name"] or ""
                friendly = self.get_friendly_name(raw_name)

                if not friendly:
                    lower = raw_name.lower()
                    if lower in BACKGROUND_PROCESSES or any(kw in lower for kw in BACKGROUND_KEYWORDS):
                        continue

                    if self.is_gui_process(proc) or self.has_open_window(proc.info["pid"]):
                        friendly = raw_name.replace("-", " ").replace("_", " ").title()
                    else:
                        continue

                mem_mb = (proc.info["memory_info"].rss / 1024 / 1024 if proc.info["memory_info"] else 0.0)
                cpu = proc.info["cpu_percent"] or 0.0
                status = proc.info["status"] or "unknown"

                if friendly not in apps or mem_mb > apps[friendly].memory_mb:
                    apps[friendly] = AppInfo(
                        pid = proc.info["pid"],
                        name = raw_name,
                        friendly_name = friendly,
                        cpu_percent = cpu,
                        memory_mb = mem_mb,
                        status = status
                    )
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue

        return sorted(apps.values(), key = lambda a: a.friendly_name.lower())

    def print_running_apps(self) -> None:
        # Prints a formatted list of running user-facing applications.
        apps = self.get_running_apps()
        if not apps:
            print("No user-facing applications detected.")
            return

        print(f"\n{'-' * 50}")
        print(f"   Running Applications ({len(apps)} found)")
        print(f"{'-' * 50}")
        for app in apps:
            print(app)
        print(f"{'-' * 50}\n")

if __name__ == "__main__":
    pm = ProcessManager()
    pm.print_running_apps()

