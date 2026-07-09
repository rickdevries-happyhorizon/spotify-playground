"""Install Python and optional system dependencies from the menu."""
from __future__ import annotations

import os
import shutil
import subprocess
import venv
from pathlib import Path

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
VENV_CANDIDATES = (".venv", "venv", "path/to/venv")

PYTHON_PACKAGES = (
    ("spotipy", "spotipy"),
    ("pymysql", "pymysql"),
    ("tqdm", "tqdm"),
    ("numbers_parser", "numbers-parser"),
    ("flask", "flask"),
    ("mutagen", "mutagen"),
    ("yt_dlp", "yt-dlp"),
)

SYSTEM_TOOLS = (
    ("brew", "Homebrew", "brew", []),
    ("ffmpeg", "ffmpeg", "brew", ["install", "ffmpeg"]),
    ("node", "Node.js", "brew", ["install", "node"]),
    ("mysql", "MySQL", "brew", ["install", "mysql"]),
)


def _find_venv_python() -> Path | None:
    for name in VENV_CANDIDATES:
        candidate = PROJECT_ROOT / name / "bin" / "python3"
        if candidate.is_file():
            return candidate
    return None


def _default_venv_python() -> Path:
    return PROJECT_ROOT / ".venv" / "bin" / "python3"


def _storage_backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "mysql").strip().lower()


def _uses_mysql() -> bool:
    return _storage_backend() not in ("txt", "text", "file")


def _run_command(
    command: list[str],
    *,
    label: str,
    cwd: Path | None = None,
) -> bool:
    print(f"\n{Colors.BRIGHT_CYAN}▶ {label}{Colors.RESET}")
    print(f"{Colors.DIM}  {' '.join(command)}{Colors.RESET}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            check=False,
        )
    except OSError as exc:
        print(f"{Colors.BRIGHT_RED}❌ Kon commando niet starten: {exc}{Colors.RESET}")
        return False

    if result.returncode != 0:
        print(f"{Colors.BRIGHT_RED}❌ Mislukt (exit code {result.returncode}){Colors.RESET}")
        return False

    print(f"{Colors.BRIGHT_GREEN}✅ Gelukt{Colors.RESET}")
    return True


def _check_python_packages(python_exe: Path) -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    for import_name, package_name in PYTHON_PACKAGES:
        if import_name == "pymysql" and not _uses_mysql():
            continue
        result = subprocess.run(
            [str(python_exe), "-c", f"import {import_name}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            missing.append((import_name, package_name))
    return missing


def _check_system_tools() -> list[tuple[str, str, list[str]]]:
    missing: list[tuple[str, str, list[str]]] = []
    for binary, label, installer, install_args in SYSTEM_TOOLS:
        if binary == "mysql" and not _uses_mysql():
            continue
        if shutil.which(binary):
            continue
        if installer == "brew" and not shutil.which("brew"):
            continue
        missing.append((label, installer, install_args))
    return missing


def _create_venv() -> Path:
    venv_dir = PROJECT_ROOT / ".venv"
    print(f"\n{Colors.BRIGHT_CYAN}Virtual environment aanmaken in {venv_dir}{Colors.RESET}")
    venv.create(venv_dir, with_pip=True)
    python_exe = venv_dir / "bin" / "python3"
    if not python_exe.is_file():
        raise RuntimeError("Virtual environment aangemaakt, maar python3 ontbreekt.")
    print(f"{Colors.BRIGHT_GREEN}✅ Virtual environment aangemaakt{Colors.RESET}")
    return python_exe


def _ensure_venv_python() -> Path | None:
    python_exe = _find_venv_python()
    if python_exe is not None:
        return python_exe

    create = input(
        f"\n{Colors.BRIGHT_CYAN}Geen virtual environment gevonden. "
        f"Aanmaken in .venv? (j/n): {Colors.RESET}"
    ).strip().lower()
    if create != "j":
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geannuleerd.{Colors.RESET}")
        return None

    try:
        return _create_venv()
    except Exception as exc:
        print(f"{Colors.BRIGHT_RED}❌ Kon virtual environment niet aanmaken: {exc}{Colors.RESET}")
        return None


def _install_python_packages(python_exe: Path) -> bool:
    if not REQUIREMENTS_FILE.is_file():
        print(f"{Colors.BRIGHT_RED}❌ requirements.txt niet gevonden: {REQUIREMENTS_FILE}{Colors.RESET}")
        return False

    ok = _run_command(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        label="pip upgraden",
    )
    if not ok:
        return False

    return _run_command(
        [str(python_exe), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        label="Python packages installeren uit requirements.txt",
    )


def _install_system_tools(missing: list[tuple[str, str, list[str]]]) -> int:
    installed = 0
    for label, installer, install_args in missing:
        if installer != "brew":
            continue

        confirm = input(
            f"\n{Colors.BRIGHT_CYAN}{label} installeren via Homebrew? (j/n): {Colors.RESET}"
        ).strip().lower()
        if confirm != "j":
            print(f"{Colors.DIM}Overgeslagen: {label}{Colors.RESET}")
            continue

        if _run_command(["brew"] + install_args, label=f"{label} installeren"):
            installed += 1

    return installed


def run_install_packages() -> None:
    """Interactive installer for Python and optional system dependencies."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📦  Packages installeren  📦{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")

    storage = _storage_backend()
    if storage in ("txt", "text", "file"):
        print(
            f"\n{Colors.DIM}Opslagmodus: tekstbestand ({storage}). "
            f"MySQL/pymysql is niet nodig.{Colors.RESET}"
        )
    else:
        print(f"\n{Colors.DIM}Opslagmodus: MySQL{Colors.RESET}")

    python_exe = _ensure_venv_python()
    if python_exe is None:
        return

    print(f"\n{Colors.BRIGHT_WHITE}Python:{Colors.RESET} {python_exe}")

    missing_python = _check_python_packages(python_exe)
    missing_system = _check_system_tools()

    if missing_python:
        print(f"\n{Colors.BRIGHT_YELLOW}Ontbrekende Python packages:{Colors.RESET}")
        for _, package_name in missing_python:
            print(f"  • {package_name}")
    else:
        print(f"\n{Colors.BRIGHT_GREEN}✅ Alle benodigde Python packages zijn al geïnstalleerd{Colors.RESET}")

    if missing_system:
        print(f"\n{Colors.BRIGHT_YELLOW}Ontbrekende systeemtools:{Colors.RESET}")
        for label, _, _ in missing_system:
            print(f"  • {label}")
    else:
        print(f"{Colors.BRIGHT_GREEN}✅ Alle benodigde systeemtools zijn aanwezig{Colors.RESET}")

    if not missing_python and not missing_system:
        play_action_done()
        print(f"\n{Colors.BRIGHT_GREEN}Niets te installeren.{Colors.RESET}")
        return

    proceed = input(
        f"\n{Colors.BRIGHT_CYAN}Installatie starten? (j/n): {Colors.RESET}"
    ).strip().lower()
    if proceed != "j":
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geannuleerd.{Colors.RESET}")
        return

    success = True
    if missing_python:
        success = _install_python_packages(python_exe) and success

    if missing_system:
        if not shutil.which("brew"):
            print(
                f"\n{Colors.BRIGHT_YELLOW}⚠️  Homebrew niet gevonden. "
                f"Installeer het eerst vanaf https://brew.sh{Colors.RESET}"
            )
            success = False
        else:
            _install_system_tools(missing_system)

    missing_python_after = _check_python_packages(python_exe)
    missing_system_after = _check_system_tools()

    print(f"\n{Colors.BRIGHT_WHITE}Resultaat:{Colors.RESET}")
    if not missing_python_after:
        print(f"  {Colors.BRIGHT_GREEN}✅ Python packages compleet{Colors.RESET}")
    else:
        print(f"  {Colors.BRIGHT_RED}❌ Nog ontbrekend: {', '.join(p for _, p in missing_python_after)}{Colors.RESET}")
        success = False

    if not missing_system_after:
        print(f"  {Colors.BRIGHT_GREEN}✅ Systeemtools compleet{Colors.RESET}")
    elif missing_system_after:
        labels = ", ".join(label for label, _, _ in missing_system_after)
        print(f"  {Colors.BRIGHT_YELLOW}⚠️  Nog ontbrekend: {labels}{Colors.RESET}")

    if success and not missing_python_after:
        play_action_done()
        print(
            f"\n{Colors.BRIGHT_GREEN}Klaar.{Colors.RESET} "
            f"Start de app met: {Colors.BRIGHT_CYAN}./run_sync.sh{Colors.RESET}"
        )
        if _uses_mysql() and shutil.which("mysql") and shutil.which("brew"):
            print(
                f"{Colors.DIM}Tip: start MySQL met "
                f"'brew services start mysql' en importeer schema.sql als dat nog niet is gedaan.{Colors.RESET}"
            )
        elif _uses_mysql():
            print(
                f"{Colors.DIM}Tip: installeer en start MySQL, importeer daarna schema.sql.{Colors.RESET}"
            )
        elif not (PROJECT_ROOT / "data" / "store.txt").is_file():
            print(
                f"{Colors.DIM}Tip: kopieer data/store.txt.example naar data/store.txt "
                f"voor tekstbestand-opslag.{Colors.RESET}"
            )
