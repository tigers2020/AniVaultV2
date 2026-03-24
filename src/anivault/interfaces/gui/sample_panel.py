"""sample_panel.py

Atoms/Molecules/Organisms 컴포넌트의 간격·레이아웃을 시각적으로 점검하는 샘플 패널 앱.

Author: Pom Kim
"""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui.components.atoms import (
    Badge,
    Button,
    ComboBox,
    Label,
    LineEdit,
    Pill,
    StepIndex,
    ViewToggleButton,
)
from anivault.interfaces.gui.components.molecules import (
    Brand,
    FormField,
    NavItem,
    PanelHeader,
    PathBox,
    PathSelectField,
    PosterCard,
    SettingsActionBar,
    StatCard,
    StepRow,
    ViewToggleBar,
)
from anivault.interfaces.gui.components.organisms import (
    AppearanceCard,
    ContentView,
    DetailsPane,
    ExecutionCard,
    FolderScanBar,
    FolderStructurePreview,
    LogList,
    ParseTmdbForm,
    PathRulesForm,
    PipelineTable,
    PosterGrid,
    PreviewPane,
    ScanBuildCard,
    SettingsActionsCard,
    Sidebar,
    StatsGrid,
    Topbar,
)
from anivault.interfaces.gui.models import PipelineRow, group_pipeline_rows
from anivault.interfaces.gui.theme import global_stylesheet
from anivault.interfaces.gui.themes import load_saved_theme


def _section_title(text: str, note: str) -> QWidget:
    """섹션 제목·설명·구분선을 담은 위젯을 만든다.

    Args:
        text: 섹션 제목.
        note: 부가 설명.

    Returns:
        구성된 QWidget.
    """
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    title = QLabel(text)
    desc = QLabel(note)
    desc.setWordWrap(True)
    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.HLine)

    layout.addWidget(title)
    layout.addWidget(desc)
    layout.addWidget(divider)
    return wrapper


def _add_section(layout: QVBoxLayout, name: str, title: str, note: str, widget: QWidget) -> None:
    """이름이 있는 프레임으로 섹션을 감싸 부모 수직 레이아웃에 추가한다.

    Args:
        layout: 루트 수직 레이아웃.
        name: objectName으로 쓸 식별자.
        title: 섹션 제목.
        note: 섹션 설명.
        widget: 섹션 본문 위젯.

    Returns:
        None.
    """
    section = QFrame()
    section.setObjectName(name)
    section_layout = QVBoxLayout(section)
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(10)
    section_layout.addWidget(_section_title(title, note))
    section_layout.addWidget(widget)
    layout.addWidget(section)


def _sample_rows() -> list[PipelineRow]:
    """데모용 파이프라인 행 두 건을 반환한다.

    Args:
        없음.

    Returns:
        PipelineRow 목록.
    """
    return [
        PipelineRow(
            original_file="[SubsPlease] Frieren - 01 (1080p).mkv",
            parsed_title="Frieren",
            parse_group="frieren",
            tmdb_korean_title_group="장송의 프리렌",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="2023",
            season="01",
            resolution="1080p",
            status="Ready",
            poster_url="",
            backdrop_url="",
            target_path=r"G:\AniSorted\1080p\2023\장송의 프리렌\Season01\ep01.mkv",
            episode="",
        ),
        PipelineRow(
            original_file="[SubsPlease] Kusuriya - 03 (1080p).mkv",
            parsed_title="Kusuriya no Hitorigoto",
            parse_group="kusuriya",
            tmdb_korean_title_group="약사의 혼잣말",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="2023",
            season="01",
            resolution="1080p",
            status="Needs Review",
            poster_url="",
            backdrop_url="",
            target_path=r"G:\AniSorted\1080p\2023\약사의 혼잣말\Season01\ep03.mkv",
            episode="",
        ),
    ]


def _atoms_preview() -> QWidget:
    """Atom 컴포넌트 미리보기 위젯을 구성한다.

    Args:
        없음.

    Returns:
        프리뷰 QFrame.
    """
    box = QFrame()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    labels = QWidget()
    labels_layout = QHBoxLayout(labels)
    labels_layout.setContentsMargins(0, 0, 0, 0)
    labels_layout.setSpacing(10)
    labels_layout.addWidget(Label("Label default"))
    labels_layout.addWidget(Label("Label muted", "muted"))
    labels_layout.addWidget(Label("Label title", "title"))
    layout.addWidget(labels)

    buttons = QWidget()
    buttons_layout = QHBoxLayout(buttons)
    buttons_layout.setContentsMargins(0, 0, 0, 0)
    buttons_layout.setSpacing(10)
    buttons_layout.addWidget(Button("Default"))
    buttons_layout.addWidget(Button("Primary", "primary"))
    buttons_layout.addWidget(Button("Success", "success"))
    buttons_layout.addWidget(Button("Warn", "warn"))
    buttons_layout.addWidget(Button("Danger", "danger"))
    layout.addWidget(buttons)

    inputs = QWidget()
    inputs_layout = QHBoxLayout(inputs)
    inputs_layout.setContentsMargins(0, 0, 0, 0)
    inputs_layout.setSpacing(10)
    line = LineEdit("placeholder")
    line.setText("sample text")
    combo = ComboBox()
    combo.addItems(["Option A", "Option B", "Option C"])
    inputs_layout.addWidget(line, 1)
    inputs_layout.addWidget(combo, 1)
    layout.addWidget(inputs)

    chips = QWidget()
    chips_layout = QHBoxLayout(chips)
    chips_layout.setContentsMargins(0, 0, 0, 0)
    chips_layout.setSpacing(10)
    chips_layout.addWidget(Pill("Blue", "blue"))
    chips_layout.addWidget(Pill("Green", "green"))
    chips_layout.addWidget(Pill("Yellow", "yellow"))
    chips_layout.addWidget(Badge("A"))
    chips_layout.addWidget(StepIndex(3))
    chips_layout.addWidget(ViewToggleButton("Toggle", checked=True))
    chips_layout.addStretch(1)
    layout.addWidget(chips)
    return box


def _molecules_preview() -> QWidget:
    """Molecule 컴포넌트 미리보기 위젯을 구성한다.

    Args:
        없음.

    Returns:
        프리뷰 QFrame.
    """
    box = QFrame()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    layout.addWidget(Brand())
    layout.addWidget(
        PanelHeader("Panel Header", "설명 텍스트와 오른쪽 pill 확인", "Ready", "green")
    )

    forms = QWidget()
    forms_layout = QGridLayout(forms)
    forms_layout.setContentsMargins(0, 0, 0, 0)
    forms_layout.setHorizontalSpacing(14)
    forms_layout.setVerticalSpacing(10)
    forms_layout.addWidget(FormField("Line Field", "line", "Sample"), 0, 0)
    forms_layout.addWidget(FormField("Combo Field", "combo", "First"), 0, 1)
    forms_layout.addWidget(FormField("Path Field", "path", r"G:\Ani"), 1, 0)
    forms_layout.addWidget(PathSelectField("폴더 선택 테스트"), 1, 1)
    layout.addWidget(forms)

    layout.addWidget(PathBox(r"G:\AniSorted\1080p\2024\애니제목\Season01\ep01.mkv"))

    toggles = QWidget()
    toggles_layout = QHBoxLayout(toggles)
    toggles_layout.setContentsMargins(0, 0, 0, 0)
    toggles_layout.setSpacing(10)
    toggles_layout.addWidget(NavItem("Organizer", "organizer"))
    toggles_layout.addWidget(NavItem("Settings", "settings"))
    toggles_layout.addWidget(ViewToggleBar(), 1)
    layout.addWidget(toggles)

    layout.addWidget(SettingsActionBar())
    layout.addWidget(StatCard("Scanned Files", "9,048"))
    layout.addWidget(StepRow(1, "폴더 스캔", "비디오 파일 수집"))

    posters = QWidget()
    posters_layout = QHBoxLayout(posters)
    posters_layout.setContentsMargins(0, 0, 0, 0)
    posters_layout.setSpacing(10)
    posters_layout.addWidget(
        PosterCard(
            title="장송의 프리렌",
            meta="2023 • Season01 • 1080p",
            path=r"G:\AniSorted\1080p\2023\장송의 프리렌",
            variant="poster",
        ),
        1,
    )
    posters_layout.addWidget(
        PosterCard(
            title="약사의 혼잣말",
            meta="2023 • Season01 • 1080p",
            path="",
            variant="compact",
        ),
        1,
    )
    layout.addWidget(posters)
    return box


def _organisms_preview() -> QWidget:
    """Organism 컴포넌트 미리보기 위젯을 구성한다.

    Args:
        없음.

    Returns:
        프리뷰 QFrame.
    """
    box = QFrame()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(14)

    rows = _sample_rows()
    groups = group_pipeline_rows(rows)

    content = ContentView()
    content.set_rows(groups)
    content.setFixedHeight(360)

    details = DetailsPane()
    details.set_row(groups[0])
    details.setFixedHeight(240)

    preview = PreviewPane()
    preview.set_row(groups[0])
    preview.setFixedHeight(260)

    pipeline = PipelineTable(show_header=True)
    pipeline.set_rows(groups)
    pipeline.setFixedHeight(300)

    poster_grid = PosterGrid(show_header=True)
    poster_grid.set_cards(
        [
            PosterCard(
                title=g.tmdb_korean_title_group,
                meta=f"{g.year} • S{g.season} • {g.resolution}",
                path=g.target_path,
            )
            for g in groups
        ]
    )
    poster_grid.setFixedHeight(420)

    layout.addWidget(Sidebar())
    layout.addWidget(Topbar())
    layout.addWidget(FolderScanBar())
    layout.addWidget(StatsGrid())
    layout.addWidget(ScanBuildCard())
    layout.addWidget(FolderStructurePreview())
    layout.addWidget(ExecutionCard())
    layout.addWidget(LogList())
    layout.addWidget(SettingsActionsCard())
    layout.addWidget(AppearanceCard())
    layout.addWidget(PathRulesForm())
    layout.addWidget(ParseTmdbForm())
    layout.addWidget(pipeline)
    layout.addWidget(content)
    layout.addWidget(details)
    layout.addWidget(preview)
    layout.addWidget(poster_grid)
    return box


def build_sample_panel_widget() -> QWidget:
    """Atom/Molecule/Organism 프리뷰가 담긴 스크롤 가능한 루트 위젯을 만든다.

    Args:
        없음.

    Returns:
        구성된 QWidget.
    """
    root = QWidget()
    root_layout = QVBoxLayout(root)
    root_layout.setContentsMargins(20, 20, 20, 20)
    root_layout.setSpacing(16)

    title = QLabel("AniVault Sample Panel")
    subtitle = QLabel(
        "기본 컴포넌트(Atoms/Molecules/Organisms) 디자인, 레이아웃, margin/padding 점검용 화면"
    )
    subtitle.setWordWrap(True)
    root_layout.addWidget(title)
    root_layout.addWidget(subtitle)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    root_layout.addWidget(scroll, 1)

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(8, 8, 8, 8)
    content_layout.setSpacing(24)
    scroll.setWidget(content)

    _add_section(
        content_layout,
        "section_atoms",
        "Atoms",
        "기본 원자 컴포넌트의 스타일과 기본 간격 확인",
        _atoms_preview(),
    )
    _add_section(
        content_layout,
        "section_molecules",
        "Molecules",
        "원자 조합 컴포넌트의 레이아웃과 패딩 확인",
        _molecules_preview(),
    )
    _add_section(
        content_layout,
        "section_organisms",
        "Organisms",
        "상위 조합 컴포넌트의 카드/테이블/패널 레이아웃 확인",
        _organisms_preview(),
    )
    content_layout.addStretch(1)

    return root


class SamplePanelWindow(QMainWindow):
    """샘플 패널을 중앙 위젯으로 두는 메인 윈도우."""

    def __init__(self, parent=None) -> None:
        """창 제목·크기·중앙 위젯을 초기화한다.

        Args:
            self: 이 윈도우 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setWindowTitle("AniVault V2 - Sample Panel")
        self.resize(1520, 980)
        self.setMinimumSize(1280, 800)
        self.setCentralWidget(build_sample_panel_widget())


def run() -> None:
    """테마·스타일을 적용한 뒤 샘플 패널 QApplication을 실행한다.

    Args:
        없음.

    Returns:
        None.
    """
    load_saved_theme()
    app = QApplication(sys.argv)
    app.setStyleSheet(global_stylesheet())
    window = SamplePanelWindow()
    window.show()
    sys.exit(app.exec())
