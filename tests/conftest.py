"""Shared fixtures. Tests hit the real corvana_kl database through kl.tools; they skip if it is not reachable."""
from __future__ import annotations

import psycopg
import pytest

from kl import config, tools


@pytest.fixture(scope="session", autouse=True)
def database() -> None:
    try:
        with psycopg.connect(config.admin_dsn(), connect_timeout=3) as conn:
            conn.execute("select 1 from statements limit 1")
    except psycopg.Error as e:
        pytest.skip(f"corvana_kl not reachable or not loaded ({e.__class__.__name__}: {e}); run `uv run kl-load`")


@pytest.fixture(scope="session")
def alice_exposure() -> tools.ExposureReport:
    return tools.get_exposure("alice", config.TARGET_ISSUER, detail="full")


@pytest.fixture(scope="session")
def bob_exposure() -> tools.ExposureReport:
    return tools.get_exposure("bob", config.TARGET_ISSUER, detail="full")


@pytest.fixture(scope="session")
def bob_summary() -> tools.ExposureSummary:
    return tools.get_exposure("bob", config.TARGET_ISSUER)


def by_exposed(report: tools.ExposureReport | tools.ExposureSummary) -> dict[str, set[str]]:
    """{verdict: instrument ids}; the unresolved block's holdings are 'unknown', keyed by their OMS ref."""
    out: dict[str, set[str]] = {"yes": set(), "unconfirmed": set(), "no": set(), "unknown": set()}
    for pe in report.positions:
        out[pe.exposed].add(pe.position.instrument_id)
    for u in report.unresolved:
        out["unknown"].add(u.position.instrument_ref)
    return out


def position(report: tools.ExposureReport, instrument_id: str) -> tools.PositionExposure:
    return next(pe for pe in report.positions if pe.position.instrument_id == instrument_id)


def channel_keys(pe: tools.PositionExposure) -> dict[str, str]:
    """{channel key: grade}."""
    return {c.key: c.grade for c in pe.channels}
