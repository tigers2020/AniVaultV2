"""apply_plan.py

계획에 따라 파일을 이동한다. Phase 3 스텁은 빈 결과를 반환한다.

Author: Pom Kim
"""

from threading import Event


def execute(
    cancel_token: Event,
) -> object:
    """계획을 적용한다(스텁: 빈 dict).

    Args:
        cancel_token: 설정 시 빈 dict 반환.

    Returns:
        빈 dict. Phase 3에서 실제 적용 결과로 대체 예정.
    """
    if cancel_token.is_set():
        return {}
    return {}
