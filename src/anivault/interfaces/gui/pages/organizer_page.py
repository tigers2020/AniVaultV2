"""Organizer page: StatsGrid + PipelineResultPanel (organisms only)."""

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.organisms import PipelineResultPanel, StatsGrid
from anivault.interfaces.gui.models import PipelineRow

STATUS_TMDB_MATCHED = "TMDB Matched"


def _sample_rows() -> list[PipelineRow]:
    return [
        PipelineRow(
            original_file="[SubsPlease] Sousou no Frieren - 01 (1080p).mkv",
            parsed_title="Sousou no Frieren",
            parse_group="Sousou no Frieren",
            tmdb_korean_title_group="장송의 프리렌",
            year="2023",
            season="Season01",
            resolution="1080p",
            status=STATUS_TMDB_MATCHED,
            poster_url="https://image.tmdb.org/t/p/w342/4KzSmKGY2FX6HPHk3rX4WQkB7VL.jpg",
            target_path=r"G:\AniSorted\1080p\2023\장송의 프리렌\Season01\[SubsPlease] Sousou no Frieren - 01 (1080p).mkv",
        ),
        PipelineRow(
            original_file="[Erai-raws] Kusuriya no Hitorigoto - 12 [1080p].mkv",
            parsed_title="Kusuriya no Hitorigoto",
            parse_group="Kusuriya no Hitorigoto",
            tmdb_korean_title_group="약사의 혼잣말",
            year="2023",
            season="Season01",
            resolution="1080p",
            status=STATUS_TMDB_MATCHED,
            poster_url="https://image.tmdb.org/t/p/w342/k5SJCke8KXz3Qw2dOjPyfzmZR8z.jpg",
            target_path=r"G:\AniSorted\1080p\2023\약사의 혼잣말\Season01\[Erai-raws] Kusuriya no Hitorigoto - 12 [1080p].mkv",
        ),
        PipelineRow(
            original_file="One Piece 1089 WEBRip 720p.avi",
            parsed_title="One Piece",
            parse_group="One Piece",
            tmdb_korean_title_group="원피스",
            year="1999",
            season="Season01",
            resolution="720p",
            status=STATUS_TMDB_MATCHED,
            poster_url="https://image.tmdb.org/t/p/w342/cMD9Ygz11zjJzAovURpO75Qg7rT.jpg",
            target_path=r"G:\AniSorted\720p\1999\원피스\Season01\One Piece 1089 WEBRip 720p.avi",
        ),
        PipelineRow(
            original_file="Random_File_Final_v2.avi",
            parsed_title="Unknown",
            parse_group="Unknown",
            tmdb_korean_title_group="Needs_Review",
            year="Unknown",
            season="Season00",
            resolution="Unknown",
            status="Manual Review",
            poster_url="",
            target_path=r"G:\AniSorted\Unknown\Unknown\Needs_Review\Season00\Random_File_Final_v2.avi",
        ),
    ]


class OrganizerPage(QWidget):
    """Organizer: stats + pipeline table + poster grid (organisms only)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(StatsGrid())
        panel = PipelineResultPanel()
        panel.set_rows(_sample_rows())
        content_layout.addWidget(panel)
        scroll.setWidget(content)
        layout.addWidget(scroll)
