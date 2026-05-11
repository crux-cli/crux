"""Append-only TSV history log of harness activations.

Each row is ``<iso8601>\\t<previous_ref>\\t<new_ref>``. The log is bounded
to ``MAX_ENTRIES`` rows. ``pop_previous`` returns the most recent row's
``previous_ref`` (the harness that was active before the latest activation).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

MAX_ENTRIES = 100


def append(history_file: Path, prev: str | None, new: str) -> None:
    """Append an activation row, trimming the file to MAX_ENTRIES."""
    history_file.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = read_all(history_file)
    rows.append((ts, prev or "", new))
    rows = rows[-MAX_ENTRIES:]
    history_file.write_text("".join(f"{r[0]}\t{r[1]}\t{r[2]}\n" for r in rows))


def read_all(history_file: Path) -> list[tuple[str, str, str]]:
    """Return all rows as ``(timestamp, prev, new)`` tuples."""
    if not history_file.exists():
        return []
    rows: list[tuple[str, str, str]] = []
    for raw in history_file.read_text().splitlines():
        parts = raw.split("\t")
        if len(parts) >= 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def pop_previous(history_file: Path) -> str | None:
    """Return the ``previous_ref`` of the most recent activation, or None."""
    rows = read_all(history_file)
    if not rows:
        return None
    return rows[-1][1] or None
