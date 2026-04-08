"""ffprobe_stream_resolution.py

ffprobe로 비디오 스트림 해상도를 조회해 표시용 라벨로 변환하는 어댑터.

Author: Pom Kim
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess

from anivault.application.ports.video_stream_resolution_port import VideoStreamResolutionPort
from anivault.domain.rules.resolution_from_filename import (
    resolution_label_from_stream_dimensions,
)

logger = logging.getLogger(__name__)


class FfprobeStreamResolution(VideoStreamResolutionPort):
    """ffprobe 기반 비디오 스트림 해상도 조회 구현체."""

    def __init__(self, timeout_seconds: float = 2.0) -> None:
        """어댑터를 초기화한다.

        Args:
            timeout_seconds: ffprobe 실행 제한 시간(초).

        Returns:
            None.
        """
        self._timeout_seconds = timeout_seconds

    def probe_display_resolution(self, path: str) -> str:
        """비디오 스트림의 width/height를 조회해 표시용 라벨로 변환한다.

        Args:
            self: 어댑터 인스턴스.
            path: 대상 비디오 파일 경로.

        Returns:
            720p/1080p 같은 라벨. 실패·미검출이면 빈 문자열.
        """
        exe = shutil.which("ffprobe")
        if not exe:
            return ""
        try:
            cp = subprocess.run(
                [
                    exe,
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "json",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as e:
            logger.debug("ffprobe 실행 실패 path=%s: %s", path, e)
            return ""
        if cp.returncode != 0:
            logger.debug(
                "ffprobe 비정상 종료 path=%s code=%s stderr=%s",
                path,
                cp.returncode,
                cp.stderr.strip(),
            )
            return ""
        return _resolution_from_ffprobe_json(cp.stdout)


def _resolution_from_ffprobe_json(raw: str) -> str:
    """ffprobe JSON 출력에서 표시용 해상도 라벨을 추출한다.

    Args:
        raw: ffprobe JSON 문자열.

    Returns:
        720p/1080p 같은 라벨 또는 빈 문자열.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    streams = data.get("streams")
    if not isinstance(streams, list) or not streams:
        return ""
    first = streams[0]
    if not isinstance(first, dict):
        return ""
    width = first.get("width")
    height = first.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        return ""
    return resolution_label_from_stream_dimensions(width, height)
