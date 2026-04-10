"""Settings page composition for the GUI settings surface."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.organisms import (
    AppearanceCard,
    ParseTmdbForm,
    PathRulesForm,
    ScanBuildCard,
    SettingsActionsCard,
)
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.i18n import translate
from anivault.interfaces.gui.presenters import SettingsPresenter


class SettingsPage(QWidget):
    """Appearance, ScanBuild, PathRules, ParseTmdb, and actions."""

    def __init__(self, parent=None, presenter: SettingsPresenter | None = None):
        """Create the settings page and wire form widgets to the presenter."""
        super().__init__(parent)
        self._presenter = presenter if presenter is not None else SettingsPresenter(parent=self)
        if presenter is not None:
            self._presenter.setParent(self)

        scan_card = ScanBuildCard()
        scan_card.setObjectName("settings_scan_card")
        appearance_card = AppearanceCard()
        appearance_card.setObjectName("settings_appearance_card")
        appearance_card.theme_changed.connect(self._presenter.on_theme_changed)
        appearance_card.language_changed.connect(self._presenter.on_language_changed)
        path_rules_form = PathRulesForm()
        path_rules_form.setObjectName("settings_path_rules_card")
        parse_tmdb_form = ParseTmdbForm()
        parse_tmdb_form.setObjectName("settings_parse_tmdb_card")
        self._presenter.set_forms(path_rules_form, parse_tmdb_form, scan_card)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme.settings_page_section_gap_px())

        self._tabs = QTabWidget()
        self._tabs.setObjectName("settings_tabs")
        self._tabs.addTab(
            self._wrap_tab_content(scan_card, appearance_card),
            translate(K.SETTINGS_TAB_GENERAL),
        )
        self._tabs.addTab(
            self._wrap_tab_content(path_rules_form),
            translate(K.SETTINGS_TAB_PATHS),
        )
        self._tabs.addTab(
            self._wrap_tab_content(parse_tmdb_form),
            translate(K.SETTINGS_TAB_PARSE_TMDB),
        )
        layout.addWidget(self._tabs, 1)

        actions_card = SettingsActionsCard()
        actions_card.setObjectName("settings_actions_card")
        bar = actions_card.action_bar()
        bar.save_clicked.connect(self._presenter.on_save_clicked)
        bar.reset_clicked.connect(self._presenter.on_reset_clicked)
        bar.load_clicked.connect(self._presenter.on_load_clicked)
        layout.addWidget(actions_card)

    def retranslate_ui(self) -> None:
        """Refresh settings tab titles when UI language changes."""
        self._tabs.setTabText(0, translate(K.SETTINGS_TAB_GENERAL))
        self._tabs.setTabText(1, translate(K.SETTINGS_TAB_PATHS))
        self._tabs.setTabText(2, translate(K.SETTINGS_TAB_PARSE_TMDB))

    def _wrap_tab_content(self, *cards: QWidget) -> QScrollArea:
        """Put stacked cards in a scroll area with uniform tab insets."""
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        m = theme.settings_tab_content_margins_px()
        inner_layout.setContentsMargins(m, m, m, m)
        inner_layout.setSpacing(theme.settings_page_section_gap_px())
        for card in cards:
            inner_layout.addWidget(card)

        scroll = QScrollArea()
        scroll.setObjectName("settings_tab_scroll")
        scroll.setStyleSheet(theme.scroll_area_transparent())
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(inner)
        return scroll
