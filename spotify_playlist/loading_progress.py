"""Terminal progress helpers for long-running operations."""

from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

try:
    from tqdm import tqdm as _tqdm_real
except ImportError:
    _tqdm_real = None


def _tqdm_write(s: str, file: Any = None, end: str = "\n") -> None:
    print(s, file=file if file is not None else sys.stdout, end=end)


def _tqdm_fallback(iterable: Any = None, **kwargs: Any) -> Any:
    if iterable is None:
        raise TypeError("tqdm() fallback requires an iterable")
    return iterable


_tqdm_fallback.write = _tqdm_write  # type: ignore[attr-defined]

tqdm = _tqdm_real if _tqdm_real is not None else _tqdm_fallback


def _indeterminate_loop_tqdm(pbar: Any, stop: threading.Event) -> None:
    while not stop.is_set():
        for i in range(0, 101, 2):
            if stop.is_set():
                return
            pbar.n = i
            pbar.refresh()
            time.sleep(0.006)
        for i in range(100, -1, -2):
            if stop.is_set():
                return
            pbar.n = i
            pbar.refresh()
            time.sleep(0.006)


def _indeterminate_loop_stdlib(description: str, stop: threading.Event, file: Any) -> None:
    width = 28
    pos = 0
    direction = 1
    while not stop.is_set():
        fill = max(0, min(width, int((pos / 100.0) * width)))
        bar = "█" * fill + "░" * (width - fill)
        line = f"\r{description} |{bar}| "
        file.write(line)
        file.flush()
        pos += 3 * direction
        if pos >= 100:
            pos = 100
            direction = -1
        elif pos <= 0:
            pos = 0
            direction = 1
        time.sleep(0.02)
    # clear line
    clear = "\r" + " " * min(120, len(description) + width + 8) + "\r"
    file.write(clear)
    file.flush()


@contextmanager
def loading_bar(description: str = "Laden...") -> Iterator[None]:
    """Show an indeterminate progress bar on stderr while the block runs."""
    stop = threading.Event()

    if _tqdm_real is not None:
        pbar = _tqdm_real(
            total=100,
            desc=description,
            bar_format="{l_bar}{bar}| {desc}",
            leave=False,
            file=sys.stderr,
            dynamic_ncols=True,
        )
        worker = threading.Thread(target=_indeterminate_loop_tqdm, args=(pbar, stop), daemon=True)
        worker.start()
        try:
            yield
        finally:
            stop.set()
            worker.join(timeout=3.0)
            pbar.close()
    else:
        worker = threading.Thread(
            target=_indeterminate_loop_stdlib,
            args=(description, stop, sys.stderr),
            daemon=True,
        )
        worker.start()
        try:
            yield
        finally:
            stop.set()
            worker.join(timeout=3.0)
