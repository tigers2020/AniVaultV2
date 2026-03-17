"""Plan moves use case. Phase 1/3 will implement path building."""

from threading import Event


def execute(
    input_dto: object,
    progress_callback: object,
    cancel_token: Event,
) -> object:
    """
    Build move plan from matched files. Phase 1/3: stub returns empty list.
    """
    if cancel_token.is_set():
        return []
    return []
