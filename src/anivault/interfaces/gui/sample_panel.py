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

from anivault.constants.gui.sample import (
    SAMPLE_PANEL_ATOM_BADGE_TEXT,
    SAMPLE_PANEL_ATOM_BUTTON_DANGER,
    SAMPLE_PANEL_ATOM_BUTTON_DEFAULT,
    SAMPLE_PANEL_ATOM_BUTTON_PRIMARY,
    SAMPLE_PANEL_ATOM_BUTTON_SUCCESS,
    SAMPLE_PANEL_ATOM_BUTTON_WARN,
    SAMPLE_PANEL_ATOM_COMBO_OPTIONS,
    SAMPLE_PANEL_ATOM_INPUT_PLACEHOLDER,
    SAMPLE_PANEL_ATOM_INPUT_TEXT,
    SAMPLE_PANEL_ATOM_LABEL_DEFAULT,
    SAMPLE_PANEL_ATOM_LABEL_MUTED,
    SAMPLE_PANEL_ATOM_LABEL_TITLE,
    SAMPLE_PANEL_ATOM_PILL_BLUE,
    SAMPLE_PANEL_ATOM_PILL_GREEN,
    SAMPLE_PANEL_ATOM_PILL_YELLOW,
    SAMPLE_PANEL_ATOM_TOGGLE_TEXT,
    SAMPLE_PANEL_MOLECULE_FORM_COMBO_LABEL,
    SAMPLE_PANEL_MOLECULE_FORM_COMBO_VALUE,
    SAMPLE_PANEL_MOLECULE_FORM_LINE_LABEL,
    SAMPLE_PANEL_MOLECULE_FORM_LINE_VALUE,
    SAMPLE_PANEL_MOLECULE_FORM_PATH_LABEL,
    SAMPLE_PANEL_MOLECULE_FORM_PATH_VALUE,
    SAMPLE_PANEL_MOLECULE_HEADER_DESCRIPTION,
    SAMPLE_PANEL_MOLECULE_HEADER_PILL_TEXT,
    SAMPLE_PANEL_MOLECULE_HEADER_TITLE,
    SAMPLE_PANEL_MOLECULE_NAV_ORGANIZER,
    SAMPLE_PANEL_MOLECULE_NAV_SETTINGS,
    SAMPLE_PANEL_MOLECULE_PATH_BOX_VALUE,
    SAMPLE_PANEL_MOLECULE_PATH_SELECT_PLACEHOLDER,
    SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_META,
    SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_PATH,
    SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_TITLE,
    SAMPLE_PANEL_MOLECULE_POSTER_SECONDARY_META,
    SAMPLE_PANEL_MOLECULE_POSTER_SECONDARY_TITLE,
    SAMPLE_PANEL_MOLECULE_STAT_TITLE,
    SAMPLE_PANEL_MOLECULE_STAT_VALUE,
    SAMPLE_PANEL_MOLECULE_STEP_DESCRIPTION,
    SAMPLE_PANEL_MOLECULE_STEP_TITLE,
    SAMPLE_PANEL_ROW_1,
    SAMPLE_PANEL_ROW_2,
    SAMPLE_PANEL_ORGANISM_POSTER_GROUP_META_TEMPLATE,
    SAMPLE_PANEL_SECTION_ATOMS_NAME,
    SAMPLE_PANEL_SECTION_ATOMS_NOTE,
    SAMPLE_PANEL_SECTION_ATOMS_TITLE,
    SAMPLE_PANEL_SECTION_MOLECULES_NAME,
    SAMPLE_PANEL_SECTION_MOLECULES_NOTE,
    SAMPLE_PANEL_SECTION_MOLECULES_TITLE,
    SAMPLE_PANEL_SECTION_ORGANISMS_NAME,
    SAMPLE_PANEL_SECTION_ORGANISMS_NOTE,
    SAMPLE_PANEL_SECTION_ORGANISMS_TITLE,
    SAMPLE_PANEL_SUBTITLE,
    SAMPLE_PANEL_TITLE,
    SAMPLE_PANEL_WINDOW_TITLE,
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
    """섹션 제목·설명·구분선을 담은 위젯을 만든다."""
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
    """이름이 붙은 프레임으로 섹션을 감싼 뒤 부모 레이아웃에 추가한다."""
    section = QFrame()
    section.setObjectName(name)
    section_layout = QVBoxLayout(section)
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(10)
    section_layout.addWidget(_section_title(title, note))
    section_layout.addWidget(widget)
    layout.addWidget(section)


def _sample_rows() -> list[PipelineRow]:
    """데모용 파이프라인 샘플 행을 반환한다."""
    return [
        PipelineRow(**SAMPLE_PANEL_ROW_1),
        PipelineRow(**SAMPLE_PANEL_ROW_2),
    ]


def _atoms_preview() -> QWidget:
    """Atom 컴포넌트 미리보기 위젯을 구성한다."""
    box = QFrame()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    labels = QWidget()
    labels_layout = QHBoxLayout(labels)
    labels_layout.setContentsMargins(0, 0, 0, 0)
    labels_layout.setSpacing(10)
    labels_layout.addWidget(Label(SAMPLE_PANEL_ATOM_LABEL_DEFAULT))
    labels_layout.addWidget(Label(SAMPLE_PANEL_ATOM_LABEL_MUTED, "muted"))
    labels_layout.addWidget(Label(SAMPLE_PANEL_ATOM_LABEL_TITLE, "title"))
    layout.addWidget(labels)

    buttons = QWidget()
    buttons_layout = QHBoxLayout(buttons)
    buttons_layout.setContentsMargins(0, 0, 0, 0)
    buttons_layout.setSpacing(10)
    buttons_layout.addWidget(Button(SAMPLE_PANEL_ATOM_BUTTON_DEFAULT))
    buttons_layout.addWidget(Button(SAMPLE_PANEL_ATOM_BUTTON_PRIMARY, "primary"))
    buttons_layout.addWidget(Button(SAMPLE_PANEL_ATOM_BUTTON_SUCCESS, "success"))
    buttons_layout.addWidget(Button(SAMPLE_PANEL_ATOM_BUTTON_WARN, "warn"))
    buttons_layout.addWidget(Button(SAMPLE_PANEL_ATOM_BUTTON_DANGER, "danger"))
    layout.addWidget(buttons)

    inputs = QWidget()
    inputs_layout = QHBoxLayout(inputs)
    inputs_layout.setContentsMargins(0, 0, 0, 0)
    inputs_layout.setSpacing(10)
    line = LineEdit(SAMPLE_PANEL_ATOM_INPUT_PLACEHOLDER)
    line.setText(SAMPLE_PANEL_ATOM_INPUT_TEXT)
    combo = ComboBox()
    combo.addItems(list(SAMPLE_PANEL_ATOM_COMBO_OPTIONS))
    inputs_layout.addWidget(line, 1)
    inputs_layout.addWidget(combo, 1)
    layout.addWidget(inputs)

    chips = QWidget()
    chips_layout = QHBoxLayout(chips)
    chips_layout.setContentsMargins(0, 0, 0, 0)
    chips_layout.setSpacing(10)
    chips_layout.addWidget(Pill(SAMPLE_PANEL_ATOM_PILL_BLUE, "blue"))
    chips_layout.addWidget(Pill(SAMPLE_PANEL_ATOM_PILL_GREEN, "green"))
    chips_layout.addWidget(Pill(SAMPLE_PANEL_ATOM_PILL_YELLOW, "yellow"))
    chips_layout.addWidget(Badge(SAMPLE_PANEL_ATOM_BADGE_TEXT))
    chips_layout.addWidget(StepIndex(3))
    chips_layout.addWidget(ViewToggleButton(SAMPLE_PANEL_ATOM_TOGGLE_TEXT, checked=True))
    chips_layout.addStretch(1)
    layout.addWidget(chips)
    return box


def _molecules_preview() -> QWidget:
    """Molecule 컴포넌트 미리보기 위젯을 구성한다."""
    box = QFrame()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    layout.addWidget(Brand())
    layout.addWidget(
        PanelHeader(
            SAMPLE_PANEL_MOLECULE_HEADER_TITLE,
            SAMPLE_PANEL_MOLECULE_HEADER_DESCRIPTION,
            SAMPLE_PANEL_MOLECULE_HEADER_PILL_TEXT,
            "green",
        )
    )

    forms = QWidget()
    forms_layout = QGridLayout(forms)
    forms_layout.setContentsMargins(0, 0, 0, 0)
    forms_layout.setHorizontalSpacing(14)
    forms_layout.setVerticalSpacing(10)
    forms_layout.addWidget(
        FormField(
            SAMPLE_PANEL_MOLECULE_FORM_LINE_LABEL,
            "line",
            SAMPLE_PANEL_MOLECULE_FORM_LINE_VALUE,
        ),
        0,
        0,
    )
    forms_layout.addWidget(
        FormField(
            SAMPLE_PANEL_MOLECULE_FORM_COMBO_LABEL,
            "combo",
            SAMPLE_PANEL_MOLECULE_FORM_COMBO_VALUE,
        ),
        0,
        1,
    )
    forms_layout.addWidget(
        FormField(
            SAMPLE_PANEL_MOLECULE_FORM_PATH_LABEL,
            "path",
            SAMPLE_PANEL_MOLECULE_FORM_PATH_VALUE,
        ),
        1,
        0,
    )
    forms_layout.addWidget(PathSelectField(SAMPLE_PANEL_MOLECULE_PATH_SELECT_PLACEHOLDER), 1, 1)
    layout.addWidget(forms)

    layout.addWidget(PathBox(SAMPLE_PANEL_MOLECULE_PATH_BOX_VALUE))

    toggles = QWidget()
    toggles_layout = QHBoxLayout(toggles)
    toggles_layout.setContentsMargins(0, 0, 0, 0)
    toggles_layout.setSpacing(10)
    toggles_layout.addWidget(NavItem(SAMPLE_PANEL_MOLECULE_NAV_ORGANIZER, "organizer"))
    toggles_layout.addWidget(NavItem(SAMPLE_PANEL_MOLECULE_NAV_SETTINGS, "settings"))
    toggles_layout.addWidget(ViewToggleBar(), 1)
    layout.addWidget(toggles)

    layout.addWidget(SettingsActionBar())
    layout.addWidget(StatCard(SAMPLE_PANEL_MOLECULE_STAT_TITLE, SAMPLE_PANEL_MOLECULE_STAT_VALUE))
    layout.addWidget(
        StepRow(1, SAMPLE_PANEL_MOLECULE_STEP_TITLE, SAMPLE_PANEL_MOLECULE_STEP_DESCRIPTION)
    )

    posters = QWidget()
    posters_layout = QHBoxLayout(posters)
    posters_layout.setContentsMargins(0, 0, 0, 0)
    posters_layout.setSpacing(10)
    posters_layout.addWidget(
        PosterCard(
            title=SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_TITLE,
            meta=SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_META,
            path=SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_PATH,
            variant="poster",
        ),
        1,
    )
    posters_layout.addWidget(
        PosterCard(
            title=SAMPLE_PANEL_MOLECULE_POSTER_SECONDARY_TITLE,
            meta=SAMPLE_PANEL_MOLECULE_POSTER_SECONDARY_META,
            path="",
            variant="compact",
        ),
        1,
    )
    layout.addWidget(posters)
    return box


def _organisms_preview() -> QWidget:
    """Organism 컴포넌트 미리보기 위젯을 구성한다."""
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

    pipeline = PipelineTable(show_header=True)
    pipeline.set_rows(groups)
    pipeline.setFixedHeight(300)

    poster_grid = PosterGrid(show_header=True)
    poster_grid.set_cards(
        [
            PosterCard(
                title=g.tmdb_korean_title_group,
                meta=SAMPLE_PANEL_ORGANISM_POSTER_GROUP_META_TEMPLATE.format(
                    year=g.year,
                    season=g.season,
                    resolution=g.resolution,
                ),
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
    layout.addWidget(poster_grid)
    return box


def build_sample_panel_widget() -> QWidget:
    """Atom/Molecule/Organism 프리뷰가 담긴 스크롤 가능한 루트 위젯을 만든다."""
    root = QWidget()
    root_layout = QVBoxLayout(root)
    root_layout.setContentsMargins(20, 20, 20, 20)
    root_layout.setSpacing(16)

    title = QLabel(SAMPLE_PANEL_TITLE)
    subtitle = QLabel(SAMPLE_PANEL_SUBTITLE)
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
        SAMPLE_PANEL_SECTION_ATOMS_NAME,
        SAMPLE_PANEL_SECTION_ATOMS_TITLE,
        SAMPLE_PANEL_SECTION_ATOMS_NOTE,
        _atoms_preview(),
    )
    _add_section(
        content_layout,
        SAMPLE_PANEL_SECTION_MOLECULES_NAME,
        SAMPLE_PANEL_SECTION_MOLECULES_TITLE,
        SAMPLE_PANEL_SECTION_MOLECULES_NOTE,
        _molecules_preview(),
    )
    _add_section(
        content_layout,
        SAMPLE_PANEL_SECTION_ORGANISMS_NAME,
        SAMPLE_PANEL_SECTION_ORGANISMS_TITLE,
        SAMPLE_PANEL_SECTION_ORGANISMS_NOTE,
        _organisms_preview(),
    )
    content_layout.addStretch(1)

    return root


class SamplePanelWindow(QMainWindow):
    """샘플 패널을 중앙 위젯으로 두는 메인 윈도우."""

    def __init__(self, parent=None) -> None:
        """창 제목·크기·중앙 위젯을 초기화한다."""
        super().__init__(parent)
        self.setWindowTitle(SAMPLE_PANEL_WINDOW_TITLE)
        self.resize(1520, 980)
        self.setMinimumSize(1280, 800)
        self.setCentralWidget(build_sample_panel_widget())


def run() -> None:
    """테마·스타일시트를 적용한 뒤 샘플 패널 QApplication을 실행한다."""
    load_saved_theme()
    app = QApplication(sys.argv)
    app.setStyleSheet(global_stylesheet())
    window = SamplePanelWindow()
    window.show()
    sys.exit(app.exec())
