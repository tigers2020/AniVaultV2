"""plan_moves.py

매칭된 파일로부터 이동 계획을 구성한다. Phase 1/3 스텁은 빈 목록을 반환한다.

Author: Pom Kim
"""

from threading import Event


def execute(
    input_dto: object,
    progress_callback: object,
    cancel_token: Event,
) -> object:
    """이동 계획을 생성한다(스텁: 빈 리스트).

    Args:
        input_dto: 향후 PlanInput DTO. 현재는 미사용 객체.
        progress_callback: 향후 진행 콜백. 현재 무시.
        cancel_token: 설정 시 빈 리스트 반환.

    Returns:
        빈 list. Phase 3에서 실제 계획 구조로 대체 예정.
    """
    if cancel_token.is_set():
        return []
    return []
