"""Gettext-style i18n helpers for the web UI."""
from __future__ import annotations

import json
import re
import struct
import subprocess
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent / "locale"
STATIC_LOCALE_DIR = Path(__file__).resolve().parent / "static" / "locale"
DOMAIN = "messages"
VALID_LOCALES = frozenset({"en", "nl", "brab"})
DEFAULT_LOCALE = "en"

_LOCALE_LABELS = {
    "en": "English",
    "nl": "Dutch",
    "brab": "Brabants",
}


def normalize_locale(locale: str | None) -> str:
    value = (locale or DEFAULT_LOCALE).strip().lower()
    return value if value in VALID_LOCALES else DEFAULT_LOCALE


def locale_label(locale: str) -> str:
    return _LOCALE_LABELS.get(normalize_locale(locale), locale)


def locale_html_lang(locale: str) -> str:
    normalized = normalize_locale(locale)
    if normalized == "brab":
        return "nl-BE"
    return normalized


def po_path(locale: str) -> Path:
    return LOCALE_DIR / normalize_locale(locale) / "LC_MESSAGES" / f"{DOMAIN}.po"


def mo_path(locale: str) -> Path:
    return LOCALE_DIR / normalize_locale(locale) / "LC_MESSAGES" / f"{DOMAIN}.mo"


def json_path(locale: str) -> Path:
    return STATIC_LOCALE_DIR / f"{normalize_locale(locale)}.json"


def parse_po(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    text = path.read_text(encoding="utf-8")
    entries: dict[str, str] = {}
    msgid: list[str] = []
    msgstr: list[str] = []
    state: str | None = None

    def flush() -> None:
        nonlocal msgid, msgstr, state
        if msgid:
            key = "".join(msgid)
            if key:
                entries[key] = "".join(msgstr) or key
        msgid = []
        msgstr = []
        state = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            flush()
            state = "msgid"
            msgid.append(_parse_po_string(line[6:].strip()))
            continue
        if line.startswith("msgstr "):
            state = "msgstr"
            msgstr.append(_parse_po_string(line[7:].strip()))
            continue
        if line.startswith('"') and state in {"msgid", "msgstr"}:
            chunk = _parse_po_string(line)
            if state == "msgid":
                msgid.append(chunk)
            else:
                msgstr.append(chunk)

    flush()
    return entries


def _parse_po_string(value: str) -> str:
    if not value:
        return ""
    if value[0] != '"':
        return value
    raw = value[1:-1]
    out: list[str] = []
    i = 0
    while i < len(raw):
        char = raw[i]
        if char != "\\":
            out.append(char)
            i += 1
            continue
        i += 1
        if i >= len(raw):
            break
        escaped = raw[i]
        if escaped == "n":
            out.append("\n")
        elif escaped == "t":
            out.append("\t")
        elif escaped == '"':
            out.append('"')
        elif escaped == "\\":
            out.append("\\")
        else:
            out.append(escaped)
        i += 1
    return "".join(out)


def load_catalog(locale: str | None = None) -> dict[str, str]:
    normalized = normalize_locale(locale)
    catalog = parse_po(po_path(DEFAULT_LOCALE))
    if normalized != DEFAULT_LOCALE:
        catalog.update(parse_po(po_path(normalized)))
    return catalog


def gettext(msgid: str, locale: str | None = None, **kwargs: object) -> str:
    catalog = load_catalog(locale)
    text = catalog.get(msgid, msgid)
    if kwargs:
        text = text.format(**kwargs)
    return text


def export_json(locale: str) -> None:
    catalog = load_catalog(locale)
    path = json_path(locale)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compile_mo(locale: str) -> None:
    po = po_path(locale)
    mo = mo_path(locale)
    mo.parent.mkdir(parents=True, exist_ok=True)

    msgfmt = _find_msgfmt()
    if msgfmt is not None:
        try:
            subprocess.run([msgfmt, "-o", str(mo), str(po)], check=True)
            return
        except subprocess.CalledProcessError:
            pass

    _write_mo_from_po(po, mo)


def compile_all_locales() -> None:
    for locale in sorted(VALID_LOCALES):
        compile_mo(locale)
        export_json(locale)


def _find_msgfmt() -> str | None:
    for candidate in ("msgfmt", "/opt/homebrew/bin/msgfmt", "/usr/local/bin/msgfmt"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True, check=True)
            return candidate
        except (OSError, subprocess.CalledProcessError):
            continue
    return None


def _write_mo_from_po(po_file: Path, mo_file: Path) -> None:
    catalog = parse_po(po_file)
    keys = sorted(catalog.keys())
    ids = b"\x00".join(key.encode("utf-8") for key in keys) + b"\x00"
    strs = b"\x00".join(catalog[key].encode("utf-8") for key in keys) + b"\x00"

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)

    output = struct.pack(
        "Iiiiiii",
        0x950412DE,
        0,
        len(keys),
        7 * 4,
        7 * 4 + 8 * len(keys),
        0,
        0,
    )

    for index, key in enumerate(keys):
        output += struct.pack("II", len(key.encode("utf-8")), keystart)
        keystart += len(key.encode("utf-8")) + 1

    for key in keys:
        value = catalog[key]
        output += struct.pack("II", len(value.encode("utf-8")), valuestart)
        valuestart += len(value.encode("utf-8")) + 1

    output += ids + strs
    mo_file.write_bytes(output)


if __name__ == "__main__":
    compile_all_locales()
