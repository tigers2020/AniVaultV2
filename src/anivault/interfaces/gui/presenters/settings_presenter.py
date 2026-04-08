"""settings_presenter.py

설정 페이지: 경로·파서·TMDB·스캔/빌드·테마 저장.

Author: Pom Kim
"""

from typing import Any

from PySide6.QtCore import QObject

from anivault.bootstrap.env_file import read_tmdb_api_key, write_tmdb_api_key
from anivault.interfaces.gui.settings_storage import get_defaults, load_all, save_all
from anivault.interfaces.gui.themes import save_theme, set_current_theme


class SettingsPresenter(QObject):
    """폼 참조·자동 저장·기본값·테마 전환."""

    def __init__(self, parent: QObject | None = None) -> None:
        """폼 참조를 None으로 둔다.

        Args:
            self: 이 Presenter.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self._path_rules_form: Any = None
        self._parse_tmdb_form: Any = None
        self._scan_build_card: Any = None

    def set_forms(
        self,
        path_rules_form: Any,
        parse_tmdb_form: Any,
        scan_build_card: Any,
    ) -> None:
        """페이지가 만든 폼을 주입하고 로드·시그널을 연결한다.

        Args:
            self: 이 Presenter.
            path_rules_form: PathRulesForm.
            parse_tmdb_form: ParseTmdbForm.
            scan_build_card: ScanBuildCard.

        Returns:
            None.
        """
        self._path_rules_form = path_rules_form
        self._parse_tmdb_form = parse_tmdb_form
        self._scan_build_card = scan_build_card
        self._load_into_forms()
        if path_rules_form is not None:
            path_rules_form.settings_changed.connect(self._on_settings_changed)
        if parse_tmdb_form is not None:
            parse_tmdb_form.settings_changed.connect(self._on_settings_changed)
        if scan_build_card is not None:
            scan_build_card.settings_changed.connect(self._on_settings_changed)

    def _load_into_forms(self) -> None:
        """디스크 설정을 폼 위젯에 반영한다.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        data = load_all()
        if self._path_rules_form is not None and "path_rules" in data:
            self._path_rules_form.set_values(data["path_rules"])
        if self._parse_tmdb_form is not None and "parse_tmdb" in data:
            merged = dict(data["parse_tmdb"])
            merged["tmdb_api_key"] = read_tmdb_api_key()
            self._parse_tmdb_form.set_values(merged)
        if self._scan_build_card is not None and "scan_build" in data:
            self._scan_build_card.set_values(data["scan_build"])

    def _on_settings_changed(self) -> None:
        """폼 변경 시 병합 저장한다(API 키는 .env로 분리).

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        to_save: dict[str, Any] = {}
        if self._path_rules_form is not None:
            to_save["path_rules"] = self._path_rules_form.get_values()
        if self._parse_tmdb_form is not None:
            parse_vals = dict(self._parse_tmdb_form.get_values())
            api_key = parse_vals.pop("tmdb_api_key", "")
            to_save["parse_tmdb"] = parse_vals
            write_tmdb_api_key(api_key)
        if self._scan_build_card is not None:
            to_save["scan_build"] = self._scan_build_card.get_values()
        if to_save:
            save_all(to_save)

    def on_save_clicked(self) -> None:
        """Save 버튼: 현재 폼 값을 저장한다.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        self._on_settings_changed()

    def on_reset_clicked(self) -> None:
        """Reset: 기본값으로 폼만 채우고 파일은 저장하지 않는다.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        defaults = get_defaults()
        if self._path_rules_form is not None:
            self._path_rules_form.set_values(defaults["path_rules"])
        if self._parse_tmdb_form is not None:
            merged = dict(defaults["parse_tmdb"])
            merged["tmdb_api_key"] = read_tmdb_api_key()
            self._parse_tmdb_form.set_values(merged)
        if self._scan_build_card is not None:
            self._scan_build_card.set_values(defaults["scan_build"])

    def on_load_clicked(self) -> None:
        """Load: 파일에서 다시 읽어 폼에 넣는다.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        self._load_into_forms()

    def on_theme_changed(self, theme_name: str) -> None:
        """테마 콤보 변경: 즉시 적용·설정 파일에 이름 저장.

        Args:
            self: 이 Presenter.
            theme_name: dark | light 등.

        Returns:
            None.
        """
        set_current_theme(theme_name)
        save_theme(theme_name)

    def on_scan_clicked(self, path: str) -> None:
        """ScanBuildCard 스캔. Organizer 플로로 위임 예정.

        Args:
            self: 이 Presenter.
            path: 스캔 경로.

        Returns:
            None.
        """
        del path

    def on_parse_clicked(self) -> None:
        """Parse 버튼 스텁.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        pass

    def on_match_clicked(self) -> None:
        """TMDB 조회 버튼 스텁.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        pass

    def on_build_plan_clicked(self) -> None:
        """이동 계획 빌드 버튼 스텁.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        pass
