"""filename_parser.py

파일명 파싱 포트. 유스케이스는 이 Protocol에만 의존하고 어댑터가 구현한다.

Author: Pom Kim
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from anivault.application.dto.parse import ParsedInfo


@runtime_checkable
class FilenameParser(Protocol):
    """파일명 파싱 계약. title, season, year, resolution 추출."""

    def parse(self, filename: str) -> "ParsedInfo":
        """파일명에서 제목·시즌·연도·해상도를 추출한다.

        Args:
            self: 파서 인스턴스.
            filename: 파싱할 파일명(경로 포함 가능).

        Returns:
            ParsedInfo. 예외 없이 항상 반환.
        """
        ...
