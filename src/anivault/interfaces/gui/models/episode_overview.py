"""View models and mapping helpers for episode overview dialog."""

from __future__ import annotations

from dataclasses import dataclass

from anivault.contracts.tmdb import TvSeasonOverview
from anivault.interfaces.gui.models.episode_parsing import extract_episode_numbers
from anivault.interfaces.gui.models.ui_rows import PipelineGroupRow


@dataclass(frozen=True, slots=True)
class EpisodeSlotViewModel:
    """GUI-ready episode slot state."""

    number: int
    title: str
    image_url: str
    file_path: str | None
    missing: bool


def build_episode_slot_view_models(
    group: PipelineGroupRow,
    overview: TvSeasonOverview,
) -> list[EpisodeSlotViewModel]:
    """Build episode slot view models from TMDB season data and local files."""

    file_by_episode: dict[int, str] = {}
    for member in sorted(group.members, key=lambda item: item.original_file):
        for episode_number in extract_episode_numbers(member.episode):
            if episode_number > 0 and episode_number not in file_by_episode:
                file_by_episode[episode_number] = member.original_file

    slots: list[EpisodeSlotViewModel] = []
    for episode in overview.episodes:
        file_path = file_by_episode.get(episode.number)
        slots.append(
            EpisodeSlotViewModel(
                number=episode.number,
                title=(episode.name or "").strip(),
                image_url=(episode.still_url or "").strip(),
                file_path=file_path,
                missing=file_path is None,
            )
        )
    return slots
