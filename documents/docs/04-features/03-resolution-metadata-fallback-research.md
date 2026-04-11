# Resolution Metadata Fallback Research

## Goal

Fix the scan pipeline so files without a resolution token in the filename use video metadata before ending up as Unknown.

## Findings

- The scan use case already has the intended resolution lookup order.
  - [`scan_library._resolve_resolution_for_scanned_path`](/F:/Python_Projects/AniVault_V2/src/anivault/application/use_cases/scan_library.py) checks parse-cache first when indexed metadata is available.
  - It then tries `resolution_from_filename(path_str)`.
  - If that is empty and the scanned item is classified as video, it calls `resolution_probe.probe_display_resolution(path_str)`.
- The ffprobe adapter for metadata lookup already exists.
  - [`FfprobeStreamResolution`](/F:/Python_Projects/AniVault_V2/src/anivault/adapters/media/ffprobe_stream_resolution.py) returns a normalized display label such as `HD`, `FHD`, or `UHD`.
  - When `ffprobe` is missing or probing fails, it safely returns an empty string.
- The missing piece is dependency wiring in the GUI bootstrap layer.
  - [`_create_organizer_page`](/F:/Python_Projects/AniVault_V2/src/anivault/bootstrap/container.py) currently creates `scan_execute` with only `library_index`.
  - Because `parse_cache` and `resolution_probe` are not injected there, the scan path never reaches cache-backed resolution reuse or ffprobe fallback in normal app execution.

## Expected Behavior

- If the filename contains a usable resolution token, keep using that value.
- If the filename does not contain a resolution token and the item is a video file, probe metadata through ffprobe.
- If ffprobe is unavailable or probing fails, keep the resolution empty so the existing Unknown folder behavior still applies later in planning.
