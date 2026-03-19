"""Parse titles use case. Enriches paths with parsed title/season/year/resolution."""

from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.dto.parse import ParsedInfo, ParseInput, ParseResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.ports.filename_parser import FilenameParser


def make_execute(
    parser: FilenameParser,
) -> Callable[[ParseInput, object, Event], ParseResult]:
    """Create execute function with FilenameParser injected."""

    def execute(
        input_dto: ParseInput,
        progress_callback: object,
        cancel_token: Event,
    ) -> ParseResult:
        """Parse each path's filename; return ParsedInfo list in same order."""
        paths = input_dto.paths or []
        if cancel_token.is_set():
            return ParseResult(parsed=[])
        total = len(paths)
        if callable(progress_callback) and total:
            progress_callback(
                ProgressEvent(
                    stage="parse",
                    current=0,
                    total=total,
                    message="파일명 파싱 중...",
                    percent=0,
                )
            )
        parsed: list[ParsedInfo] = []
        for i, path in enumerate(paths):
            if cancel_token.is_set():
                return ParseResult(parsed=parsed)
            name = Path(path).name
            info = parser.parse(name)
            parsed.append(info)
            if callable(progress_callback) and total:
                pct = int((i + 1) * 100 / total) if total else 100
                progress_callback(
                    ProgressEvent(
                        stage="parse",
                        current=i + 1,
                        total=total,
                        message=f"파싱 중 {i + 1}/{total}",
                        percent=pct,
                        item_path=path,
                    )
                )
        return ParseResult(parsed=parsed)

    return execute
