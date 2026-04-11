# AniVault V2 App Summary PDF Research

## Purpose

This note captures repo-backed evidence for a one-page app summary PDF. Claims below are limited to what was found in this repository on 2026-04-08.

## Confirmed from repo

- App type: AniVault V2 is a GUI-only Qt desktop app.
  - Evidence: `src/anivault/__main__.py` runs the GUI entrypoint.
  - Evidence: `src/anivault/interfaces/gui/main.py` creates `QApplication` and `MainWindow`.
  - Evidence: `pyproject.toml` depends on `PySide6` and exposes `anivault.interfaces.gui.main:run`.
- Core workflow implemented in code:
  - Scan library files: `src/anivault/application/use_cases/scan_library.py`
  - Parse titles from filenames: `src/anivault/application/use_cases/parse_titles.py`
  - Match series against TMDB: `src/anivault/application/use_cases/match_series.py`
  - Build move plans: `src/anivault/application/use_cases/plan_moves.py`
  - Apply plans and write logs: `src/anivault/application/use_cases/apply_plan.py`
- Rollback status:
  - There is no `rollback_plan` use case module in the current tree; rollback is not implemented end-to-end.
  - `apply_plan` writes an operation log via `OperationLogRepository.save_plan`; `load_plan` exists on the port for a future rollback flow but is not called from application code yet.
  - SQLite organize-plan persistence includes `load_plan` / `mark_plan_rolled_back` on the adapter; those entry points are not invoked from application code yet.
- Architecture shape:
  - GUI creates pages and presenters: `src/anivault/interfaces/gui/app.py`
  - Bootstrap wires use cases and adapters: `src/anivault/bootstrap/container.py`
  - Filesystem adapter: `src/anivault/adapters/fs`
  - TMDB metadata adapter: `src/anivault/adapters/metadata/tmdb`
  - SQLite repositories: `src/anivault/adapters/persistence/sqlite`
  - Operation log adapter: `src/anivault/adapters/operation_log`
- Run/install evidence:
  - Install: `pip install -e .` in `README.md`
  - Run: `python -m anivault` in `README.md` and `src/anivault/__main__.py`
  - TMDB key is read from `.env`: `README.md`, `src/anivault/bootstrap/env_file.py`

## Repo-backed inference

- Primary user: desktop end users organizing a local anime library.
  - Basis: `pyproject.toml` classifier `Intended Audience :: End Users/Desktop`
  - Basis: repository workflow centers on scanning, matching, and reorganizing local media files.

## Not found in repo

- No explicit named end-user persona for the app.
- No complete rollback implementation.
- No Poppler / `pdftoppm` tool available in this environment for image-based PDF review.
