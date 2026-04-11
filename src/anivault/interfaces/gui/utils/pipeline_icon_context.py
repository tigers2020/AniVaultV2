"""Pure helpers for icon-grid context menu (paths and TMDB URLs)."""

from __future__ import annotations

from pathlib import Path

from anivault.interfaces.gui.models.ui_rows import PipelineGroupRow


def open_location_directory_for_group(group: PipelineGroupRow) -> Path | None:
    """Return a directory Path to reveal in the file manager, or None if no file exists."""

    for member in group.members:
        p = Path(member.original_file)
        try:
            resolved = p.resolve()
        except OSError:
            resolved = p
        if resolved.is_file():
            return resolved.parent
    return None


def tmdb_tv_series_https_url(tmdb_series_id: str) -> str | None:
    """Return https://www.themoviedb.org/tv/{id} when id is a non-empty digit string."""

    tid = (tmdb_series_id or "").strip()
    if not tid or not tid.isdigit():
        return None
    return f"https://www.themoviedb.org/tv/{tid}"
