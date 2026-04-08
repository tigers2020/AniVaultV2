from __future__ import annotations

from threading import Event

from anivault.application.use_cases.rollback_plan import execute


def test_rollback_plan_returns_empty_dict_when_not_cancelled() -> None:
    assert execute(Event()) == {}


def test_rollback_plan_returns_empty_dict_when_cancelled() -> None:
    token = Event()
    token.set()

    assert execute(token) == {}
