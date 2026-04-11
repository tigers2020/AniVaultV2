# Benchmark Usage

AniVault benchmark tests measure elapsed time with `pytest-benchmark`.
They are not normal pass/fail unit tests, and they do not enforce fixed time thresholds.

## Setup

Install the dev dependencies first:

```powershell
pip install -e ".[dev]"
```

Benchmark samples are loaded from:

```text
docs/filenames.txt
```

The benchmark helper skips the first line when it is `collect_filenames.py`, then uses
100, 1,000, and 10,000 item slices from the remaining filename list.

## Run

Regular `pytest` excludes benchmark tests by default:

```powershell
pytest
```

Run the benchmark suite and print timing statistics:

```powershell
pytest -m benchmark tests/benchmarks
```

Each benchmark run also writes a human-readable Markdown report to:

```text
docs/benchmarks/benchmark-YYYYMMDD-HHMMSS.md
```

These reports use real millisecond values only. They intentionally omit pytest-benchmark's
ratio hints such as `>1000` and `inf`, because those hints compare each row against the
fastest row in the same console table and are not useful for cross-run comparison.

For a quicker local sanity check, reduce benchmark rounds:

```powershell
pytest -m benchmark tests/benchmarks --benchmark-max-time=0.05 --benchmark-min-rounds=1
```

Save benchmark results under `.benchmarks/`:

```powershell
pytest -m benchmark tests/benchmarks --benchmark-autosave
```

This is optional. The Markdown report in `docs/benchmarks/` is generated automatically
whenever benchmark fixture results exist.

## Covered Paths

Current timing benchmarks cover backend-only workflow paths:

- filename parsing with `AnitopyTitleParser`
- parse use case with `parse_titles.make_execute`
- scan use case with a fake file repository
- SQLite library index and parse cache upsert/read paths
- title group sync
- match use case with a fake metadata provider
- plan moves
- apply dry-run with operation log writing
- rollback stub
- cached TMDB hydrate with SQLite

GUI rendering and real TMDB network calls are intentionally excluded so timings stay
repeatable and do not depend on API keys, network latency, or desktop UI state.

## Reading Results

`pytest-benchmark` prints a table with columns such as `Min`, `Max`, `Mean`, `StdDev`,
`Median`, `IQR`, `OPS`, `Rounds`, and `Iterations`.

Use the generated Markdown report's `Mean ms`, `Median ms`, and `OPS` columns for a quick
comparison. When a previous auto-generated report exists, the new report also includes
`Prev Mean ms` and `Mean Delta`.

You can still use saved pytest-benchmark runs with `--benchmark-compare` when you want
pytest-benchmark's native comparison workflow.

Example:

```powershell
pytest -m benchmark tests/benchmarks --benchmark-autosave
pytest -m benchmark tests/benchmarks --benchmark-compare
```
