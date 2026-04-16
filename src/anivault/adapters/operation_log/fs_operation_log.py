"""fs_operation_log.py

로컬 디스크에 operation log(JSON)를 저장·로드한다.

기본 저장 위치: `~/.anivault/logs/organize{timestamp}.log`
테스트 격리가 필요하면 생성자의 `log_dir` 인자로 직접 지정한다.

Author: Pom Kim
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from anivault.adapters.persistence.sqlite.db_path import default_operation_logs_dir
from anivault.constants.adapters.operation_log import (
    OPERATION_LOG_DEFAULT_OPERATION_TYPE,
    OPERATION_LOG_FILENAME_PREFIX,
    OPERATION_LOG_FILENAME_SUFFIX,
    OPERATION_LOG_JSON_ARRAY_ERROR,
    OPERATION_LOG_KEY_DESTINATION_PATH,
    OPERATION_LOG_KEY_OPERATION_TYPE,
    OPERATION_LOG_KEY_RAW,
    OPERATION_LOG_KEY_SOURCE_PATH,
)
from anivault.domain.models.file_operation import FileOperation, OperationType


class FsOperationLogRepository:
    """`~/.anivault/logs/organize{timestamp}.log` 에 JSON 배열을 쓴다.

    기본 경로는 `default_operation_logs_dir()`(`~/.anivault/logs`)이며,
    테스트에서 격리가 필요할 때는 `log_dir` 인자로 임시 디렉터리를 지정한다.
    """

    def __init__(self, log_dir: Path | None = None) -> None:
        """로그 디렉터리를 설정한다.

        Args:
            log_dir: 로그 파일을 저장할 디렉터리. None이면 `default_operation_logs_dir()`.
        """
        self._log_dir = log_dir if log_dir is not None else default_operation_logs_dir()

    def save_plan(self, operations: list[object]) -> Path:
        """계획을 타임스탬프 로그 파일에 저장한다.

        Args:
            operations: FileOperation 등 직렬화 가능한 작업 목록.

        Returns:
            생성된 로그 파일 경로.

        Raises:
            OSError: 쓰기 실패 시.
        """
        self._log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self._log_dir / f"{OPERATION_LOG_FILENAME_PREFIX}{ts}{OPERATION_LOG_FILENAME_SUFFIX}"
        payload: list[dict[str, Any]] = []
        for op in operations:
            if isinstance(op, FileOperation):
                payload.append(
                    {
                        OPERATION_LOG_KEY_OPERATION_TYPE: op.operation_type.value,
                        OPERATION_LOG_KEY_SOURCE_PATH: op.source_path,
                        OPERATION_LOG_KEY_DESTINATION_PATH: op.destination_path,
                    }
                )
            elif isinstance(op, dict):
                payload.append(op)
            else:
                payload.append({OPERATION_LOG_KEY_RAW: repr(op)})
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_plan(self, log_path: Path) -> list[object]:
        """로그 파일에서 FileOperation 목록을 복원한다.

        Args:
            log_path: 로그 파일 경로.

        Returns:
            FileOperation 리스트.

        Raises:
            OSError, json.JSONDecodeError: 파일 없음·손상 시.
            ValueError: JSON 최상위가 배열이 아닐 때.
        """
        raw = log_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError(OPERATION_LOG_JSON_ARRAY_ERROR)
        out: list[object] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            ot = str(
                item.get(
                    OPERATION_LOG_KEY_OPERATION_TYPE,
                    OPERATION_LOG_DEFAULT_OPERATION_TYPE,
                )
            ).upper()
            op_type = (
                OperationType.MOVE
                if ot == OPERATION_LOG_DEFAULT_OPERATION_TYPE
                else OperationType.COPY
            )
            out.append(
                FileOperation(
                    operation_type=op_type,
                    source_path=str(item.get(OPERATION_LOG_KEY_SOURCE_PATH, "")),
                    destination_path=str(item.get(OPERATION_LOG_KEY_DESTINATION_PATH, "")),
                )
            )
        return out
