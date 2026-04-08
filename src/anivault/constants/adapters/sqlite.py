"""SQLite adapter constants."""

from __future__ import annotations

from typing import Final

SQLITE_LOOKUP_CHUNK: Final[int] = 500
SQLITE_LIBRARY_INDEX_MARK_MISSING_INLINE_LIMIT: Final[int] = 500
SQLITE_LIBRARY_INDEX_EXISTING_LOOKUP_CHUNK: Final[int] = 500
SQLITE_TITLE_MATCH_FIND_SERIES_DEFAULT_LIMIT: Final[int] = 10
SQLITE_TITLE_MATCH_LOCAL_SEARCH_FETCH_LIMIT: Final[int] = 40
SQLITE_ERROR_DTO_JSON: Final[str] = "{}"
SQLITE_PARSE_STATUS_UNKNOWN_SOURCE: Final[str] = "unknown"
