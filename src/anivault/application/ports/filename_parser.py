"""Port for filename parsers."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from anivault.domain.models import ParsedInfo


@runtime_checkable
class FilenameParser(Protocol):
    """Contract for extracting structured fields from a filename."""

    def parse(self, filename: str) -> "ParsedInfo": ...
