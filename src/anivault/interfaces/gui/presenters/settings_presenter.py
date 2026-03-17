"""SettingsPresenter: orchestrates SettingsPage. Path/parse/TMDB rules, scan/build."""

from PySide6.QtCore import QObject


class SettingsPresenter(QObject):
    """Single orchestration for Settings page. Rules persistence, scan/build delegation."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def on_scan_clicked(self, path: str) -> None:
        """Handle scan from ScanBuildCard. Delegates to Organizer flow."""
        pass

    def on_parse_clicked(self) -> None:
        """Handle parse button."""
        pass

    def on_match_clicked(self) -> None:
        """Handle TMDB query button."""
        pass

    def on_build_plan_clicked(self) -> None:
        """Handle build move plan button."""
        pass
