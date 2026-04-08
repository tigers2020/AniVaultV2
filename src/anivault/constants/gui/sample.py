"""Sample-panel copy and demo data constants."""

from __future__ import annotations

from typing import Final

SAMPLE_PANEL_WINDOW_TITLE: Final[str] = "AniVault V2 - Sample Panel"
SAMPLE_PANEL_TITLE: Final[str] = "AniVault Sample Panel"
SAMPLE_PANEL_SUBTITLE: Final[str] = (
    "기본 컴포넌트(Atoms/Molecules/Organisms) 조합과 레이아웃, margin/padding 감각 확인용 패널"
)

SAMPLE_PANEL_SECTION_ATOMS_NAME: Final[str] = "section_atoms"
SAMPLE_PANEL_SECTION_ATOMS_TITLE: Final[str] = "Atoms"
SAMPLE_PANEL_SECTION_ATOMS_NOTE: Final[str] = "기본 원자 컴포넌트의 스타일과 기본 간격 확인"
SAMPLE_PANEL_SECTION_MOLECULES_NAME: Final[str] = "section_molecules"
SAMPLE_PANEL_SECTION_MOLECULES_TITLE: Final[str] = "Molecules"
SAMPLE_PANEL_SECTION_MOLECULES_NOTE: Final[str] = "원자 조합 컴포넌트의 레이아웃과 패딩 확인"
SAMPLE_PANEL_SECTION_ORGANISMS_NAME: Final[str] = "section_organisms"
SAMPLE_PANEL_SECTION_ORGANISMS_TITLE: Final[str] = "Organisms"
SAMPLE_PANEL_SECTION_ORGANISMS_NOTE: Final[str] = (
    "상위 조합 컴포넌트의 카드/테이블/패널 레이아웃 확인"
)

SAMPLE_PANEL_ATOM_LABEL_DEFAULT: Final[str] = "Label default"
SAMPLE_PANEL_ATOM_LABEL_MUTED: Final[str] = "Label muted"
SAMPLE_PANEL_ATOM_LABEL_TITLE: Final[str] = "Label title"
SAMPLE_PANEL_ATOM_BUTTON_DEFAULT: Final[str] = "Default"
SAMPLE_PANEL_ATOM_BUTTON_PRIMARY: Final[str] = "Primary"
SAMPLE_PANEL_ATOM_BUTTON_SUCCESS: Final[str] = "Success"
SAMPLE_PANEL_ATOM_BUTTON_WARN: Final[str] = "Warn"
SAMPLE_PANEL_ATOM_BUTTON_DANGER: Final[str] = "Danger"
SAMPLE_PANEL_ATOM_INPUT_PLACEHOLDER: Final[str] = "placeholder"
SAMPLE_PANEL_ATOM_INPUT_TEXT: Final[str] = "sample text"
SAMPLE_PANEL_ATOM_COMBO_OPTIONS: Final[tuple[str, ...]] = (
    "Option A",
    "Option B",
    "Option C",
)
SAMPLE_PANEL_ATOM_PILL_BLUE: Final[str] = "Blue"
SAMPLE_PANEL_ATOM_PILL_GREEN: Final[str] = "Green"
SAMPLE_PANEL_ATOM_PILL_YELLOW: Final[str] = "Yellow"
SAMPLE_PANEL_ATOM_BADGE_TEXT: Final[str] = "A"
SAMPLE_PANEL_ATOM_TOGGLE_TEXT: Final[str] = "Toggle"

SAMPLE_PANEL_MOLECULE_HEADER_TITLE: Final[str] = "Panel Header"
SAMPLE_PANEL_MOLECULE_HEADER_DESCRIPTION: Final[str] = "설명 텍스트와 오른쪽 pill 확인"
SAMPLE_PANEL_MOLECULE_HEADER_PILL_TEXT: Final[str] = "Ready"
SAMPLE_PANEL_MOLECULE_FORM_LINE_LABEL: Final[str] = "Line Field"
SAMPLE_PANEL_MOLECULE_FORM_LINE_VALUE: Final[str] = "Sample"
SAMPLE_PANEL_MOLECULE_FORM_COMBO_LABEL: Final[str] = "Combo Field"
SAMPLE_PANEL_MOLECULE_FORM_COMBO_VALUE: Final[str] = "First"
SAMPLE_PANEL_MOLECULE_FORM_PATH_LABEL: Final[str] = "Path Field"
SAMPLE_PANEL_MOLECULE_FORM_PATH_VALUE: Final[str] = r"G:\Ani"
SAMPLE_PANEL_MOLECULE_PATH_SELECT_PLACEHOLDER: Final[str] = "폴더 선택 테스트"
SAMPLE_PANEL_MOLECULE_PATH_BOX_VALUE: Final[str] = (
    r"G:\AniSorted\FHD\2024\애니제목\Season01\ep01.mkv"
)
SAMPLE_PANEL_MOLECULE_NAV_ORGANIZER: Final[str] = "Organizer"
SAMPLE_PANEL_MOLECULE_NAV_SETTINGS: Final[str] = "Settings"
SAMPLE_PANEL_MOLECULE_STAT_TITLE: Final[str] = "Scanned Files"
SAMPLE_PANEL_MOLECULE_STAT_VALUE: Final[str] = "9,048"
SAMPLE_PANEL_MOLECULE_STEP_TITLE: Final[str] = "폴더 스캔"
SAMPLE_PANEL_MOLECULE_STEP_DESCRIPTION: Final[str] = "비디오 파일 수집"
SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_TITLE: Final[str] = "장송의 프리렌"
SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_META: Final[str] = "2023 · Season01 · FHD"
SAMPLE_PANEL_MOLECULE_POSTER_PRIMARY_PATH: Final[str] = r"G:\AniSorted\FHD\2023\장송의 프리렌"
SAMPLE_PANEL_MOLECULE_POSTER_SECONDARY_TITLE: Final[str] = "약사의 혼잣말"
SAMPLE_PANEL_MOLECULE_POSTER_SECONDARY_META: Final[str] = "2023 · Season01 · FHD"
SAMPLE_PANEL_ORGANISM_POSTER_GROUP_META_TEMPLATE: Final[str] = "{year} · S{season} · {resolution}"

SAMPLE_PANEL_ROW_1: Final[dict[str, str]] = {
    "original_file": "[SubsPlease] Frieren - 01 (1080p).mkv",
    "parsed_title": "Frieren",
    "parse_group": "frieren",
    "tmdb_korean_title_group": "장송의 프리렌",
    "tmdb_series_id": "",
    "tmdb_poster_path": "",
    "tmdb_backdrop_path": "",
    "year": "2023",
    "season": "01",
    "resolution": "FHD",
    "status": "Ready",
    "poster_url": "",
    "backdrop_url": "",
    "target_path": r"G:\AniSorted\FHD\2023\장송의 프리렌\Season01\ep01.mkv",
    "episode": "",
}
SAMPLE_PANEL_ROW_2: Final[dict[str, str]] = {
    "original_file": "[SubsPlease] Kusuriya - 03 (1080p).mkv",
    "parsed_title": "Kusuriya no Hitorigoto",
    "parse_group": "kusuriya",
    "tmdb_korean_title_group": "약사의 혼잣말",
    "tmdb_series_id": "",
    "tmdb_poster_path": "",
    "tmdb_backdrop_path": "",
    "year": "2023",
    "season": "01",
    "resolution": "FHD",
    "status": "Needs Review",
    "poster_url": "",
    "backdrop_url": "",
    "target_path": r"G:\AniSorted\FHD\2023\약사의 혼잣말\Season01\ep03.mkv",
    "episode": "",
}
