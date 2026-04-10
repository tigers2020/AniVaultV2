"""Progress contracts and helpers."""

from dataclasses import dataclass

from anivault.constants.application.progress import PROGRESS_PERCENT_MAX


@dataclass(slots=True)
class ProgressEvent:
    """Progress event emitted by long-running workflows."""

    stage: str
    current: int
    total: int
    message: str
    percent: int
    item_path: str | None = None


def progress_dialog_value_and_maximum(event: ProgressEvent) -> tuple[int | None, int]:
    """Convert a progress event into a QProgressBar-compatible value/maximum pair."""

    if event.total > 0:
        return event.current, event.total
    return None, PROGRESS_PERCENT_MAX
