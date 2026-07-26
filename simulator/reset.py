"""Reset controls (docs demo runbook section 9).

Resets are always scoped to a single local run-output directory; this
module never touches shared/production data (there is none to touch --
the simulator only ever writes under the caller-supplied ``--out``
directory), matching the runbook rule "never truncate a shared or
production table... as part of reset".
"""
from __future__ import annotations

import shutil
from pathlib import Path


def reset_run_directory(out_dir: Path, *, keep_manifest_source: bool = True) -> list[str]:
    """Delete generated run artifacts under ``out_dir``.

    Returns the list of removed file/directory names. If
    ``keep_manifest_source`` is True, a checked-in scenario manifest (i.e.
    one that lives under ``simulator/manifests``) is never touched --
    this function only ever deletes files inside the run's own output
    directory.
    """
    removed: list[str] = []
    if not out_dir.exists():
        return removed
    for child in sorted(out_dir.iterdir()):
        removed.append(child.name)
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    return removed
