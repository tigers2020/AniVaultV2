"""Operation-log adapter constants."""

from __future__ import annotations

from typing import Final

OPERATION_LOG_DIRNAME_ROOT: Final[str] = ".anivault"
OPERATION_LOG_DIRNAME_LOGS: Final[str] = "logs"
OPERATION_LOG_FILENAME_PREFIX: Final[str] = "organize"
OPERATION_LOG_FILENAME_SUFFIX: Final[str] = ".log"

OPERATION_LOG_KEY_OPERATION_TYPE: Final[str] = "operation_type"
OPERATION_LOG_KEY_SOURCE_PATH: Final[str] = "source_path"
OPERATION_LOG_KEY_DESTINATION_PATH: Final[str] = "destination_path"
OPERATION_LOG_KEY_RAW: Final[str] = "raw"

OPERATION_LOG_DEFAULT_OPERATION_TYPE: Final[str] = "MOVE"
OPERATION_LOG_JSON_ARRAY_ERROR: Final[str] = "log payload must be a JSON array"
