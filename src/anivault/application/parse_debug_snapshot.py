"""parse_debug_snapshot.py

스캔·파싱 직후 상태를 JSON으로 내보내 디버깅한다.

Author: Pom Kim
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from anivault.application.dto.parse import ParsedInfo

logger = logging.getLogger(__name__)


def build_parse_debug_snapshot(
    *,
    working_directory: str,
    paths: list[str],
    parsed_infos: list[ParsedInfo],
    merged_row_dicts: list[dict[str, Any]],
) -> dict[str, Any]:
    """파일 경로·파서 출력·파이프라인 행(병합 후)을 한 문서로 묶는다.

    Args:
        working_directory: 앱이 기준으로 삼는 작업 디렉터리(보통 ``Path.cwd()``).
        paths: ``original_file`` 경로(파싱 결과와 동일 순서).
        parsed_infos: ``ParseResult.parsed``와 동일 순서.
        merged_row_dicts: 병합된 ``PipelineRow``를 ``asdict`` 등으로 만든 딕셔너리 목록.

    Returns:
        JSON 직렬화 가능한 스냅샷 딕셔너리.
    """
    entries: list[dict[str, Any]] = []
    n = len(paths)
    for i in range(n):
        p = paths[i]
        path_obj = Path(p)
        parsed = parsed_infos[i] if i < len(parsed_infos) else None
        row_d = merged_row_dicts[i] if i < len(merged_row_dicts) else None
        entries.append(
            {
                "index": i,
                "original_file": p,
                "stem": path_obj.stem,
                "parent": str(path_obj.parent),
                "parsed_info": asdict(parsed) if parsed is not None else None,
                "pipeline_row": row_d,
            }
        )
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "working_directory": working_directory,
        "file_count": n,
        "entries": entries,
    }


def write_parse_debug_json(path: Path, snapshot: dict[str, Any]) -> None:
    """UTF-8로 JSON 파일을 쓴다(부모 디렉터리가 없으면 만든다).

    Args:
        path: 저장 경로.
        snapshot: ``build_parse_debug_snapshot`` 결과.

    Returns:
        None.

    Raises:
        OSError: 쓰기 실패 시.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def try_write_parse_debug_json(path: Path, snapshot: dict[str, Any]) -> bool:
    """쓰기 실패 시 로그만 남기고 False를 반환한다.

    Args:
        path: 저장 경로.
        snapshot: ``build_parse_debug_snapshot`` 결과.

    Returns:
        성공하면 True, 예외 시 False.
    """
    try:
        write_parse_debug_json(path, snapshot)
    except OSError:
        logger.exception("parse debug JSON write failed: %s", path)
        return False
    return True
