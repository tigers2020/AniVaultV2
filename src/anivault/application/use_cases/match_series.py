"""Match series use case. Phase 2 will implement TMDB matching."""

from threading import Event


def execute(
    input_dto: object,
    progress_callback: object,
    cancel_token: Event,
) -> object:
    """
    Match parsed files to TMDB series. Phase 2: stub returns empty dict.
    """
    if cancel_token.is_set():
        return {}
    return {}
