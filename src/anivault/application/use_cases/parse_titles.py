"""parse_titles.py

FilenameParser로 각 경로의 파일명을 파싱해 제목·시즌·연도·해상도를 채운다.

Author: Pom Kim
"""

from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.dto.parse import ParsedInfo, ParseInput, ParseResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.ports.filename_parser import FilenameParser
from anivault.domain.rules.anime_title_refine import apply_anime_title_refine
from anivault.domain.rules.parent_folder_title import augment_parsed_info_with_parent_folder


def make_execute(
    parser: FilenameParser,
) -> Callable[[ParseInput, object, Event], ParseResult]:
    """FilenameParser가 주입된 파싱 실행 함수를 만든다.

    Args:
        parser: 파일명 파싱 포트.

    Returns:
        (ParseInput, progress_callback, cancel_token) -> ParseResult 클로저.
    """

    def execute(
        input_dto: ParseInput,
        progress_callback: object,
        cancel_token: Event,
    ) -> ParseResult:
        """경로 순서대로 파일명을 파싱한 ParsedInfo 목록을 반환한다.

        Args:
            input_dto: 파싱할 경로 목록.
            progress_callback: ProgressEvent를 받는 콜백. 없으면 무시.
            cancel_token: 설정 시 지금까지 파싱분만 반환.

        Returns:
            입력 순서와 동일한 parsed 리스트.
        """
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
            stem = Path(path).stem
            info = parser.parse(name)
            info = apply_anime_title_refine(stem, info)
            info = augment_parsed_info_with_parent_folder(path, info)
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
