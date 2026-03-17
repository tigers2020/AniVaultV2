"""Rollback plan use case. Phase 3 will implement undo."""

from threading import Event


def execute(
    input_dto: object,
    progress_callback: object,
    cancel_token: Event,
) -> object:
    """
    Undo last apply. Phase 3: stub returns empty result.
    """
    if cancel_token.is_set():
        return {}
    return {}
