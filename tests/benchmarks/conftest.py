from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "docs" / "benchmarks"
REPORT_PREFIX = "benchmark-"
REPORT_MARKER_START = "<!-- ANIVAULT_BENCHMARK_JSON"
REPORT_MARKER_END = "-->"


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    del exitstatus
    benchmark_session = getattr(session.config, "_benchmarksession", None)
    if benchmark_session is None:
        return

    benchmark_rows = [_benchmark_to_row(bench) for bench in benchmark_session.benchmarks if bench]
    if not benchmark_rows:
        return

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    previous = _load_previous_report()
    report_path = _next_report_path(datetime.now())
    report_path.write_text(
        _render_report(benchmark_rows, previous),
        encoding="utf-8",
    )


def _benchmark_to_row(bench: Any) -> dict[str, object]:
    stats = bench.stats
    params = dict(bench.params or {})
    return {
        "fullname": str(bench.fullname),
        "benchmark": _base_benchmark_name(str(bench.name)),
        "sample": _sample_label(params, bench.param),
        "mean_ms": float(stats.mean) * 1_000,
        "median_ms": float(stats.median) * 1_000,
        "min_ms": float(stats.min) * 1_000,
        "max_ms": float(stats.max) * 1_000,
        "stddev_ms": float(stats.stddev) * 1_000,
        "ops": float(stats.ops),
        "rounds": int(stats.rounds),
        "iterations": int(bench.iterations),
    }


def _base_benchmark_name(name: str) -> str:
    return name.split("[", 1)[0]


def _sample_label(params: dict[str, object], fallback: object) -> str:
    if "sample_size" in params:
        return str(params["sample_size"])
    if "cancelled" in params:
        return f"cancelled={params['cancelled']}"
    if fallback is not None:
        return str(fallback)
    return "-"


def _next_report_path(now: datetime) -> Path:
    stem = now.strftime(f"{REPORT_PREFIX}%Y%m%d-%H%M%S")
    candidate = REPORT_DIR / f"{stem}.md"
    index = 2
    while candidate.exists():
        candidate = REPORT_DIR / f"{stem}-{index:02d}.md"
        index += 1
    return candidate


def _load_previous_report() -> dict[str, float]:
    for path in sorted(REPORT_DIR.glob(f"{REPORT_PREFIX}*.md"), reverse=True):
        payload = _extract_report_payload(path)
        if payload is None:
            continue
        rows = payload.get("benchmarks")
        if not isinstance(rows, list):
            continue
        previous: dict[str, float] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            fullname = row.get("fullname")
            mean_ms = row.get("mean_ms")
            if isinstance(fullname, str) and isinstance(mean_ms, int | float):
                previous[fullname] = float(mean_ms)
        if previous:
            return previous
    return {}


def _extract_report_payload(path: Path) -> dict[str, object] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    start = text.find(REPORT_MARKER_START)
    if start < 0:
        return None
    json_start = start + len(REPORT_MARKER_START)
    end = text.find(REPORT_MARKER_END, json_start)
    if end < 0:
        return None
    raw = text[json_start:end].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _render_report(rows: list[dict[str, object]], previous: dict[str, float]) -> str:
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    has_previous = bool(previous)
    lines = [
        "# AniVault Benchmark Report",
        "",
        f"- Generated: `{generated_at}`",
        f"- Command: `{_command_line()}`",
        f"- Python: `{platform.python_implementation()} {platform.python_version()}`",
        f"- Platform: `{platform.platform()}`",
        f"- Git: `{_git_summary()}`",
        f"- Benchmarks: `{len(rows)}`",
        "",
        "## Results",
        "",
        _table_header(has_previous),
        _table_separator(has_previous),
    ]
    sorted_rows = sorted(rows, key=lambda row: (str(row["benchmark"]), str(row["sample"])))
    for row in sorted_rows:
        lines.append(_table_row(row, previous, has_previous))
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Times are real elapsed timings rendered in milliseconds.",
            "- The pytest-benchmark console table may show ratio hints such as `>1000` or `inf`; this report omits those ratio hints on purpose.",
            "- `Mean Delta` compares this run against the previous auto-generated `benchmark-*.md` report when available.",
            "",
            REPORT_MARKER_START,
            json.dumps(
                {"generated_at": generated_at, "benchmarks": sorted_rows},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            REPORT_MARKER_END,
            "",
        ]
    )
    return "\n".join(lines)


def _table_header(has_previous: bool) -> str:
    columns = [
        "Benchmark",
        "Sample",
        "Mean ms",
        "Median ms",
        "Min ms",
        "Max ms",
        "StdDev ms",
        "OPS",
        "Rounds",
        "Iterations",
    ]
    if has_previous:
        columns.extend(["Prev Mean ms", "Mean Delta"])
    return "| " + " | ".join(columns) + " |"


def _table_separator(has_previous: bool) -> str:
    columns = 10 + (2 if has_previous else 0)
    return "| " + " | ".join(["---"] * columns) + " |"


def _table_row(
    row: dict[str, object],
    previous: dict[str, float],
    has_previous: bool,
) -> str:
    values = [
        str(row["benchmark"]),
        str(row["sample"]),
        _fmt_ms(row["mean_ms"]),
        _fmt_ms(row["median_ms"]),
        _fmt_ms(row["min_ms"]),
        _fmt_ms(row["max_ms"]),
        _fmt_ms(row["stddev_ms"]),
        _fmt_ops(row["ops"]),
        str(row["rounds"]),
        str(row["iterations"]),
    ]
    if has_previous:
        prev = previous.get(str(row["fullname"]))
        values.extend([_fmt_ms(prev), _fmt_delta(row["mean_ms"], prev)])
    return "| " + " | ".join(values) + " |"


def _fmt_ms(value: object) -> str:
    if not isinstance(value, int | float):
        return "-"
    numeric = float(value)
    if abs(numeric) < 1:
        return f"{numeric:.6f}"
    if abs(numeric) < 1_000:
        return f"{numeric:.3f}"
    return f"{numeric:.1f}"


def _fmt_ops(value: object) -> str:
    if not isinstance(value, int | float):
        return "-"
    return f"{float(value):.3f}"


def _fmt_delta(current: object, previous: float | None) -> str:
    if not isinstance(current, int | float) or previous is None or previous == 0:
        return "-"
    delta = (float(current) - previous) / previous * 100
    return f"{delta:+.2f}%"


def _command_line() -> str:
    return " ".join(sys.argv)


def _git_summary() -> str:
    commit = _git_output("rev-parse", "--short", "HEAD")
    if not commit:
        return "unknown"
    dirty = "dirty" if _git_output("status", "--porcelain") else "clean"
    return f"{commit} ({dirty})"


def _git_output(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()
