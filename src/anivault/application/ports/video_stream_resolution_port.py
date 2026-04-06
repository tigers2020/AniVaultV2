"""video_stream_resolution_port.py

비디오 파일 메타데이터에서 표시용 해상도 라벨을 조회하는 포트.

Author: Pom Kim
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class VideoStreamResolutionPort(Protocol):
    """비디오 스트림 해상도 조회 계약."""

    def probe_display_resolution(self, path: str) -> str:
        """파일 메타데이터에서 표시용 해상도 라벨을 조회한다.

        Args:
            self: 포트 구현체 인스턴스.
            path: 비디오 파일 절대/상대 경로.

        Returns:
            720p/1080p 같은 라벨. 조회 실패 또는 미검출이면 빈 문자열.
        """
        ...
