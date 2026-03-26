"""parse_signature.py

parse_input_signature: path_norm, size, mtime, PARSER_VERSION을 고정 구분자로 결합 후 SHA-1 hex.

Author: Pom Kim
"""

from __future__ import annotations

import hashlib

from anivault.domain.parsing.parser_version import PARSER_VERSION

# 단위 테스트·재현성용 고정 구분자(필드 값에 등장하지 않는 바이트 시퀀스).
_SIGNATURE_FIELD_SEP = "\x1e"


def compute_parse_input_signature(
    path_norm: str,
    size_bytes: int,
    mtime_ns: int,
) -> str:
    """파일 메타와 파서 파이프라인 버전으로 캐시 무효화용 서명을 만든다.

    Args:
        path_norm: 경로 정규화 키.
        size_bytes: 파일 크기(바이트).
        mtime_ns: 수정 시각(나노초).

    Returns:
        SHA-1 16진 문자열(소문자).
    """
    payload = _SIGNATURE_FIELD_SEP.join(
        (
            path_norm,
            str(size_bytes),
            str(mtime_ns),
            PARSER_VERSION,
        )
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
