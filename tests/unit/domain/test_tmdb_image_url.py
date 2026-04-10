"""Tests for TMDB image CDN URL allowlisting."""

from __future__ import annotations

from anivault.domain.rules.tmdb_image_url import tmdb_backdrop_cdn_url, tmdb_poster_cdn_url


def test_poster_relative_path() -> None:
    assert tmdb_poster_cdn_url("/abc.jpg") == "https://image.tmdb.org/t/p/w342/abc.jpg"


def test_poster_https_tmdb_cdn_preserved() -> None:
    url = "https://image.tmdb.org/t/p/w500/z.jpg"
    assert tmdb_poster_cdn_url(url) == url


def test_poster_http_tmdb_cdn_upgraded() -> None:
    assert (
        tmdb_poster_cdn_url("http://image.tmdb.org/t/p/w500/z.jpg")
        == "https://image.tmdb.org/t/p/w500/z.jpg"
    )


def test_poster_protocol_relative_tmdb() -> None:
    assert (
        tmdb_poster_cdn_url("//image.tmdb.org/t/p/w342/x.png")
        == "https://image.tmdb.org/t/p/w342/x.png"
    )


def test_poster_arbitrary_https_rejected() -> None:
    assert tmdb_poster_cdn_url("https://evil.example/a.jpg") == ""


def test_poster_userinfo_rejected() -> None:
    assert tmdb_poster_cdn_url("https://user@image.tmdb.org/t/p/w342/x.jpg") == ""


def test_backdrop_same_allowlist() -> None:
    assert tmdb_backdrop_cdn_url("https://evil.example/b.jpg") == ""
    assert tmdb_backdrop_cdn_url("/bd.jpg") == "https://image.tmdb.org/t/p/w780/bd.jpg"
