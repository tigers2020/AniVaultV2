"""Port: filename parsing. Use cases depend on this; adapters implement it."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from anivault.application.dto.parse import ParsedInfo


@runtime_checkable
class FilenameParser(Protocol):
    """파일명 파싱 계약. title, season, year, resolution 추출."""

    def parse(self, filename: str) -> "ParsedInfo":
        """파일명에서 제목·시즌·연도·해상도 추출. 예외 없이 ParsedInfo 반환."""
        ...
