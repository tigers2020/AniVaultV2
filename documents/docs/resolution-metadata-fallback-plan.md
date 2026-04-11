# Resolution Metadata Fallback Plan

## Summary

Enable the existing scan resolution fallback by wiring parse-cache and ffprobe resolution probing into the organizer bootstrap path.

## Implementation Steps

1. Update `src/anivault/bootstrap/container.py`.
   - Instantiate `FfprobeStreamResolution`.
   - Pass `repos.parse_cache` into `make_scan_execute(...)`.
   - Pass the ffprobe-backed `resolution_probe` into both scan wiring branches.
2. Keep `src/anivault/application/use_cases/scan_library.py` unchanged.
   - Preserve the existing lookup order of cache, filename, then ffprobe.
   - Preserve the empty-string fallback when metadata probing is unavailable.
3. Extend `tests/unit/bootstrap/test_container_extra.py`.
   - Assert subtitle scan wiring passes `parse_cache` and `resolution_probe`.
   - Add a regression test for the default scan branch so both wiring paths are covered.

## Verification

- `pytest tests/unit/bootstrap/test_container_extra.py`
- `pytest tests/unit/adapters/media/test_ffprobe_stream_resolution.py`
- `pytest`
- `ruff check .`
- `mypy src`
- `black .`

## Assumptions

- The wrong Unknown result is caused by missing bootstrap wiring rather than a defect inside the ffprobe adapter.
- Subtitle-only scans can share the same scan wiring because the scan use case already limits metadata probing to video files.
