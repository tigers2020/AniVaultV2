"""fs_operation_log.py

로컬 디스크에 operation log(JSON)를 저장·로드한다.

Author: Pom Kim
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from anivault.domain.models.file_operation import FileOperation, OperationType


class FsOperationLogRepository:
    """`{log_root}/.anivault/logs/organize{timestamp}.log` 에 JSON 배열을 쓴다."""

    def __init__(self, log_root: Path) -> None:
        """로그 루트(스캔 소스 또는 target_root 등 한 디렉터리)를 받는다.

        Args:
            self: 이 저장소.
            log_root: `.anivault/logs` 가 만들어질 기준 디렉터리.

        Returns:
            None.
        """
        self._log_root = log_root

    def save_plan(self, operations: list[object]) -> Path:
        """계획을 타임스탬프 로그 파일에 저장한다.

        Args:
            self: 이 저장소.
            operations: FileOperation 등 직렬화 가능한 작업 목록.

        Returns:
            생성된 로그 파일 경로.

        Raises:
            OSError: 쓰기 실패 시.
        """
        log_dir = self._log_root / ".anivault" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = log_dir / f"organize{ts}.log"
        payload: list[dict[str, Any]] = []
        for op in operations:
            if isinstance(op, FileOperation):
                payload.append(
                    {
                        "operation_type": op.operation_type.value,
                        "source_path": op.source_path,
                        "destination_path": op.destination_path,
                    }
                )
            elif isinstance(op, dict):
                payload.append(op)
            else:
                payload.append({"raw": repr(op)})
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_plan(self, log_path: Path) -> list[object]:
        """로그 파일에서 FileOperation 목록을 복원한다.

        Args:
            self: 이 저장소.
            log_path: 로그 파일 경로.

        Returns:
            FileOperation 리스트.

        Raises:
            OSError, json.JSONDecodeError: 파일 없음·손상 시.
        """
        raw = log_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("log payload must be a JSON array")
        out: list[FileOperation] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            ot = str(item.get("operation_type", "MOVE")).upper()
            op_type = OperationType.MOVE if ot == "MOVE" else OperationType.COPY
            out.append(
                FileOperation(
                    operation_type=op_type,
                    source_path=str(item.get("source_path", "")),
                    destination_path=str(item.get("destination_path", "")),
                )
            )
        return cast(list[object], out)
