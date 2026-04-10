"""dry_run_dialog.py

Dialog for reviewing grouped dry-run move results.

Author: Pom Kim
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from anivault.constants.gui.components import (
    DRY_RUN_DIALOG_BUTTON_APPLY,
    DRY_RUN_DIALOG_BUTTON_CLOSE,
    DRY_RUN_DIALOG_HEADER_DESTINATION,
    DRY_RUN_DIALOG_HEADER_GROUP,
    DRY_RUN_DIALOG_HEADER_RESOLUTION,
    DRY_RUN_DIALOG_HEADER_SOURCE,
    DRY_RUN_DIALOG_TITLE,
)
from anivault.contracts.planning import PlanMovePreviewMeta
from anivault.domain.models.file_operation import FileOperation
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button

_GROUP_LABEL_DISPLAY_MAX_CHARS: int = 32


def _ellipsize_display(text: str, *, max_chars: int = _GROUP_LABEL_DISPLAY_MAX_CHARS) -> str:
    """Truncate for tree display; total length including ellipsis is at most max_chars."""
    stripped = (text or "").strip()
    if len(stripped) <= max_chars:
        return stripped
    if max_chars <= 3:
        return stripped[:max_chars]
    return stripped[: max_chars - 3] + "..."


def _format_group_resolution_summary(segments: set[str]) -> str:
    parts = sorted({s.strip() for s in segments if (s or "").strip()})
    return " / ".join(parts) if parts else "—"


def _format_folder_summary(paths: list[str]) -> str:
    uniq = sorted(set(paths))
    if not uniq:
        return "—"
    return " · ".join(uniq)


def _apply_folder_link_cell(
    item: QTreeWidgetItem,
    col: int,
    paths: list[str],
    *,
    openable: bool = True,
) -> None:
    """Show folder summary text. If openable, style as link and store paths for double-click."""
    display = _format_folder_summary(paths)
    item.setText(col, display)
    item.setData(col, Qt.ItemDataRole.UserRole, None)
    if not paths or display == "—":
        item.setToolTip(col, "")
        return
    item.setToolTip(col, "\n".join(paths))
    if not openable:
        return
    item.setData(col, Qt.ItemDataRole.UserRole, paths)
    item.setForeground(col, QBrush(QColor("#1a73e8")))
    font = QFont()
    font.setUnderline(True)
    item.setFont(col, font)


def _aggregate_group_summaries(
    moves: Sequence[FileOperation],
    move_preview: Sequence[PlanMovePreviewMeta],
) -> dict[tuple[str, str], dict[str, set[str]]]:
    group_agg: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"resolutions": set(), "src_dirs": set(), "dst_dirs": set()}
    )
    for move, preview in zip(moves, move_preview, strict=True):
        gid = (preview.group_key, preview.group_label)
        seg = (preview.resolution_segment or "").strip()
        if seg:
            group_agg[gid]["resolutions"].add(seg)
        group_agg[gid]["src_dirs"].add(str(Path(move.source_path).parent))
        group_agg[gid]["dst_dirs"].add(str(Path(move.destination_path).parent))
    return group_agg


def _fill_dry_run_tree(
    tree: QTreeWidget,
    moves: Sequence[FileOperation],
    move_preview: Sequence[PlanMovePreviewMeta],
    group_agg: dict[tuple[str, str], dict[str, set[str]]],
) -> None:
    groups: dict[tuple[str, str], QTreeWidgetItem] = {}
    resolutions: dict[tuple[str, str, str], QTreeWidgetItem] = {}

    for move, preview in zip(moves, move_preview, strict=True):
        group_id = (preview.group_key, preview.group_label)
        group_item = groups.get(group_id)
        if group_item is None:
            full_label = preview.group_label or ""
            display_label = _ellipsize_display(full_label)
            summary = group_agg[group_id]
            res_summary = _format_group_resolution_summary(summary["resolutions"])
            src_list = sorted(summary["src_dirs"])
            dst_list = sorted(summary["dst_dirs"])
            group_item = QTreeWidgetItem([display_label, res_summary, "", ""])
            _apply_folder_link_cell(group_item, 2, src_list, openable=True)
            _apply_folder_link_cell(group_item, 3, dst_list, openable=False)
            if display_label != full_label:
                group_item.setToolTip(0, full_label)
            tree.addTopLevelItem(group_item)
            groups[group_id] = group_item

        resolution_id = (*group_id, preview.resolution_segment)
        resolution_item = resolutions.get(resolution_id)
        if resolution_item is None:
            resolution_item = QTreeWidgetItem(["", preview.resolution_segment, "", ""])
            group_item.addChild(resolution_item)
            resolutions[resolution_id] = resolution_item

        resolution_item.addChild(QTreeWidgetItem(["", "", move.source_path, move.destination_path]))

    tree.resizeColumnToContents(0)
    tree.resizeColumnToContents(1)
    if tree.columnWidth(0) < 200:
        tree.setColumnWidth(0, 200)
    if tree.columnWidth(1) < 100:
        tree.setColumnWidth(1, 100)
    tree.collapseAll()


class _DryRunTreeWidget(QTreeWidget):
    """Top-level group row: double-click source folder cell opens first folder (dest is preview-only)."""

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        idx = self.indexAt(event.pos())
        if idx.isValid():
            item = self.itemFromIndex(idx)
            col = idx.column()
            if item is not None and self.indexOfTopLevelItem(item) >= 0 and col == 2:
                raw = item.data(col, Qt.ItemDataRole.UserRole)
                if isinstance(raw, list) and raw:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(raw[0])))
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)


class DryRunDialog(QDialog):
    """Dry Run result tree and apply button dialog."""

    apply_requested = Signal()

    def __init__(
        self,
        moves: tuple[FileOperation, ...] | list[FileOperation],
        move_preview: tuple[PlanMovePreviewMeta, ...] | list[PlanMovePreviewMeta],
        parent=None,
    ) -> None:
        super().__init__(parent)
        if len(moves) != len(move_preview):
            raise ValueError("DryRunDialog requires preview metadata for every move")

        self.setWindowTitle(DRY_RUN_DIALOG_TITLE)
        self.setMinimumSize(900, 480)
        self.setStyleSheet(theme.card_panel())

        layout = QVBoxLayout(self)
        self._tree = _DryRunTreeWidget()
        self._tree.setColumnCount(4)
        self._tree.setHeaderLabels(
            [
                DRY_RUN_DIALOG_HEADER_GROUP,
                DRY_RUN_DIALOG_HEADER_RESOLUTION,
                DRY_RUN_DIALOG_HEADER_SOURCE,
                DRY_RUN_DIALOG_HEADER_DESTINATION,
            ]
        )
        header = self._tree.header()
        header.setMinimumSectionSize(72)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        group_agg = _aggregate_group_summaries(moves, move_preview)
        _fill_dry_run_tree(self._tree, moves, move_preview, group_agg)
        layout.addWidget(self._tree)

        actions = QHBoxLayout()
        actions.addStretch(1)
        apply_btn = Button(DRY_RUN_DIALOG_BUTTON_APPLY, "primary")
        apply_btn.clicked.connect(self._on_apply_clicked)
        close_btn = Button(DRY_RUN_DIALOG_BUTTON_CLOSE, "default")
        close_btn.clicked.connect(self.reject)
        actions.addWidget(apply_btn)
        actions.addWidget(close_btn)
        layout.addLayout(actions)

    def _on_apply_clicked(self) -> None:
        self.apply_requested.emit()
