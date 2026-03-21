"""path_select_field.py

LineEdit + 폴더 찾아보기 버튼.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import Button, LineEdit


class PathSelectField(QWidget):
    """QFileDialog.getExistingDirectory로 경로를 고른다."""

    path_changed = Signal(str)

    def __init__(self, placeholder: str = "", parent=None):
        """편집란·찾아보기 버튼을 배치하고 시그널을 연결한다.

        Args:
            self: 이 위젯.
            placeholder: 빈 칸일 때 힌트.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._edit = LineEdit()
        self._edit.setPlaceholderText(placeholder or "폴더 경로")
        layout.addWidget(self._edit, 1)
        browse = Button("폴더 선택")
        browse.clicked.connect(self._on_browse)
        layout.addWidget(browse)
        self._edit.editingFinished.connect(lambda: self.path_changed.emit(self.path()))

    def _on_browse(self) -> None:
        """폴더 대화상자에서 선택한 경로를 반영한다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            self._edit.setText(path)
            self.path_changed.emit(path)

    def path(self) -> str:
        """편집란 텍스트를 앞뒤 공백 제거 후 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            경로 문자열.
        """
        return self._edit.text().strip()

    def set_path(self, path: str) -> None:
        """편집란에 경로를 설정한다.

        Args:
            self: 이 위젯.
            path: 경로 문자열.

        Returns:
            None.
        """
        self._edit.setText(path or "")
