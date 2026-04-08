"""Media adapter constants."""

from __future__ import annotations

from typing import Final

FFPROBE_EXECUTABLE: Final[str] = "ffprobe"
FFPROBE_TIMEOUT_SECONDS: Final[float] = 2.0
FFPROBE_LOG_LEVEL_FLAG: Final[str] = "-v"
FFPROBE_LOG_LEVEL_ERROR: Final[str] = "error"
FFPROBE_SELECT_STREAMS_FLAG: Final[str] = "-select_streams"
FFPROBE_PRIMARY_VIDEO_STREAM: Final[str] = "v:0"
FFPROBE_SHOW_ENTRIES_FLAG: Final[str] = "-show_entries"
FFPROBE_STREAM_DIMENSIONS_ENTRIES: Final[str] = "stream=width,height"
FFPROBE_OUTPUT_FORMAT_FLAG: Final[str] = "-of"
FFPROBE_OUTPUT_FORMAT_JSON: Final[str] = "json"
