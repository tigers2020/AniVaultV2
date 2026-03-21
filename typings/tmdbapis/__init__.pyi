"""Partial stubs for tmdbapis (no upstream py.typed)."""

from typing import Any

class TMDbAPIs:
    def __init__(
        self,
        apikey: str,
        session_id: str | None = None,
        v4_access_token: str | None = None,
        language: Any = None,
        session: Any = None,
    ) -> None: ...
    def tv_search(
        self,
        query: str,
        include_adult: bool | None = None,
        *,
        first_air_date_year: int | None = None,
    ) -> Any: ...
