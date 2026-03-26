"""parser_version.py

파서·후처리·normalizer까지 포함한 파싱 파이프라인 버전. 서명·parse_cache에 단일 출처.

규칙이 바뀌면 값을 올려 캐시를 무효화한다(CHANGELOG에 기록).

Author: Pom Kim
"""

from typing import Final

PARSER_VERSION: Final[str] = "1"
