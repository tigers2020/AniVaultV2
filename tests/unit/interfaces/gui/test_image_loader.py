from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.interfaces.gui.services import image_loader as image_loader_module
from anivault.interfaces.gui.services.image_loader import ImageLoader


class _LoadedSignal:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def emit(self, url: str, pixmap: object) -> None:
        self.calls.append((url, pixmap))


class _FakePixmap:
    def __init__(self, source: object = None, *, load_ok: bool = True, is_null: bool = False) -> None:
        self.source = source
        self._load_ok = load_ok
        self._is_null = is_null

    def isNull(self) -> bool:
        return self._is_null

    def loadFromData(self, data) -> bool:
        self.source = data
        return self._load_ok


class _Reply:
    __hash__ = object.__hash__

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)


def test_image_loader_load_paths_and_finished(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(image_loader_module, "QPixmap", _FakePixmap)
    loader = ImageLoader.__new__(ImageLoader)
    loader.loaded = _LoadedSignal()  # type: ignore[attr-defined]
    loader._cache = {}  # type: ignore[attr-defined]
    loader._pending = {}  # type: ignore[attr-defined]
    loader._inflight_urls = set()  # type: ignore[attr-defined]
    loader._nam = SimpleNamespace(get=lambda request: SimpleNamespace(request=request))  # type: ignore[attr-defined]

    loader.load("   ")  # type: ignore[attr-defined]
    assert loader.loaded.calls == []  # type: ignore[attr-defined]

    cached = _FakePixmap("cached")
    loader._cache["cached-url"] = cached  # type: ignore[attr-defined]
    loader.load("cached-url")  # type: ignore[attr-defined]
    assert loader.loaded.calls[-1] == ("cached-url", cached)  # type: ignore[attr-defined]

    local_file = tmp_path / "poster.jpg"
    local_file.write_text("poster", encoding="utf-8")
    assert loader._load_local(str(local_file)) is True  # type: ignore[attr-defined]
    assert loader.loaded.calls[-1][0] == str(local_file)  # type: ignore[attr-defined]

    monkeypatch.setattr(image_loader_module, "QUrl", lambda url: SimpleNamespace(toLocalFile=lambda: "F:/poster.jpg"))
    assert loader._load_local("file:///poster.jpg") is True  # type: ignore[attr-defined]
    assert loader._load_local("not-a-real-path") is False  # type: ignore[attr-defined]

    requests: list[object] = []
    loader._nam = SimpleNamespace(get=lambda request: requests.append(request) or _Reply())  # type: ignore[attr-defined]
    monkeypatch.setattr(image_loader_module, "QNetworkRequest", lambda url: SimpleNamespace(url=url))
    monkeypatch.setattr(image_loader_module, "QUrl", lambda url: f"url::{url}")
    loader._load_remote("http://image")  # type: ignore[attr-defined]
    loader._load_remote("http://image")  # type: ignore[attr-defined]
    loader._load_remote("ftp://image")  # type: ignore[attr-defined]
    assert len(requests) == 1

    reply = _Reply(
        error=lambda: image_loader_module.QNetworkReply.NetworkError.NoError,
        readAll=lambda: b"pixels",
        deleteLater=MagicMock(),
    )
    loader._pending = {reply: "http://image"}  # type: ignore[attr-defined]
    loader._inflight_urls = {"http://image"}  # type: ignore[attr-defined]
    loader._on_finished(reply)  # type: ignore[attr-defined]
    assert "http://image" in loader._cache  # type: ignore[attr-defined]
    assert loader.loaded.calls[-1][0] == "http://image"  # type: ignore[attr-defined]

    bad_reply = _Reply(
        error=lambda: object(),
        readAll=lambda: b"",
        deleteLater=MagicMock(),
    )
    loader._pending = {bad_reply: "http://bad"}  # type: ignore[attr-defined]
    loader._inflight_urls = {"http://bad"}  # type: ignore[attr-defined]
    loader._on_finished(bad_reply)  # type: ignore[attr-defined]
    assert loader.loaded.calls[-1][0] == "http://bad"  # type: ignore[attr-defined]
