"""Expected state after `kl-update data/updates/2026-10-28` (tests/expected/update_2026-10-28.md).
Skipped until the delta is ingested; the extraction checks also need the LLM statements to exist."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import psycopg
import pytest

from conftest import by_exposed, channel_keys, position
from kl import config, tools
from kl.ingest_update import ingest

BATCH_DATE = date(2026, 10, 28)
NOTE = "updates/2026-10-28/research/2026-10-28_bank-b_corvana-downgrade.md"


def scalar(query: str) -> int:
    try:
        with psycopg.connect(config.admin_dsn(), connect_timeout=3) as conn:
            return conn.execute(query).fetchone()[0]
    except psycopg.Error:
        return 0


ingested = pytest.mark.skipif(scalar("select count(*) from ratings where action_date = '2026-10-28'") == 0,
                              reason="2026-10-28 delta not ingested; run `uv run kl-update data/updates/2026-10-28`")
pytestmark = ingested


@pytest.fixture(scope="module")
def bob_after() -> tools.ExposureReport:
    return tools.get_exposure("bob", "ISS-0001", BATCH_DATE, detail="full")


@pytest.mark.parametrize("user", ["alice", "bob", "carol"])
def test_corvana_downgraded(user):
    r = tools.get_ratings(user, "ISS-0001", BATCH_DATE)
    assert (r.current.rating, r.current.outlook, r.current.action_date) == ("B+", "Stable", BATCH_DATE)
    assert r.current.rank - r.history[1].rank == 1                        # one notch below BB-


def test_cnoc_followed():
    assert tools.get_ratings("bob", "ISS-0002", BATCH_DATE).current.rating == "B+"


def test_cdb_rating_lag(bob_after):
    flags = position(bob_after, "INS-1007").flags
    assert any(f.kind == "RATING_LAG" and f.subject == "ISS-0004|GUARANTEED_BY|ISS-0001|Agency A" for f in flags)


def test_new_cnoc_bond_resolves_like_the_old_one(bob_after):
    new = position(bob_after, "INS-1012")
    assert new.position.instrument_ref == "XS2999887768" and new.exposed == "yes"
    assert channel_keys(new) == channel_keys(position(bob_after, "INS-1005"))
    assert any(h.predicate == "GUARANTEED_BY" for c in new.channels for h in c.hops)


def test_only_one_unresolved_left(bob_after):
    assert by_exposed(bob_after)["unknown"] == {"XS2812345672"}


def test_second_run_is_a_noop():
    _text, entries = ingest(config.PACK_DIR / "updates" / "2026-10-28")
    assert entries and {e["action"] for e in entries} == {"SKIP"}


def test_note_stored_and_annotated():
    docs = [d for d in tools.get_documents("alice", as_of=BATCH_DATE) if d.source_file == NOTE]
    assert len(docs) == 1 and docs[0].visibility == "external" and docs[0].source_system == "ResearchHub"
    d = docs[0]
    assert {"ISS-0001", "ISS-0002", "ISS-0004", "ISS-0005"} <= set(d.about_issuers)
    if d.annotated_by == "LLM":
        assert d.summary and "downgrade" in d.topics
    else:
        assert d.summary is None and d.topics == []
    assert d in tools.get_documents("bob", "ISS-0004", as_of=BATCH_DATE)
    assert d in tools.get_documents("alice", "ISS-0001", as_of=BATCH_DATE)


def test_no_statements_extracted_from_the_delta():
    assert scalar("select count(*) from statements where method = 'LLM'") == 0
    assert scalar("select count(*) from statements where source_file like 'updates/%'") == 0
    bob = tools.get_statements("bob", "ISS-0005", "OWNS", BATCH_DATE)
    assert {s.source_file for s in bob.current + bob.other_sources} <= {"desk_notes/em-credit-desk-notes.md",
                                                                        "research/2023-10-02_bank-a_cortel-initiation.md"}


def test_data_quality_as_of_before_the_delta_is_unchanged():
    before = {(f.kind, f.subject) for f in tools.get_statements("bob", "ISS-0004", "GUARANTEED_BY", config.AS_OF).flags}
    assert not any(k == "RATING_LAG" for k, _ in before)
    assert by_exposed(tools.get_exposure("bob", "ISS-0001", config.AS_OF))["unknown"] == {"XS2812345672", "XS2999887768"}
