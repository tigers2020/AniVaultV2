"""Scan library use case. Phase 1 will implement full logic."""

from threading import Event

from anivault.application.dto.scan import ScanInput, ScanResult


def execute(
    input_dto: ScanInput,
    progress_callback: object,
    cancel_token: Event,
) -> ScanResult:
    """
    Scan directory for media files. Phase 1: stub returns empty.
    progress_callback receives ProgressEvent. cancel_token.set() signals stop.
    """
    if cancel_token.is_set():
        return ScanResult(paths=[])
    # Stub: no actual scan; Phase 1 will wire FileRepository
    return ScanResult(paths=[])
