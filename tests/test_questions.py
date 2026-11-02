"""Expected answers from tests/expected/*.md (base pack, before the 2026-10-28 update)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import psycopg
import pytest

from conftest import by_exposed, channel_keys, position
from kl import config, tools, validate

CPL_IPO = "research/2026-03-05_em-credit-internal_cpl-ipo.md"
MACRO_NOTE = "research/2026-08-21_macro-internal_cvd-reserves.md"
PIT = date(2025, 6, 30)
CURRENCY = "DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS"
CURVE = "PRICED_OFF>DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS"
COUNTRY = "COUNTRY_OF_RISK>SOVEREIGN_IS"


def owns_cpl(s: tools.StatementSet, rows: list[tools.Statement]) -> list[Decimal]:
    return sorted(r.value_num for r in rows if r.predicate == "OWNS" and r.object_id == "ISS-0003")


# --- alice_exposure.md -----------------------------------------------------------------------------------------

def test_alice_target_rating(alice_exposure):
    current = alice_exposure.target_rating.current
    assert (current.rating, current.outlook, current.action_date) == ("BB-", "Negative", date(2026, 9, 18))


def test_alice_exposed_sets(alice_exposure):
    assert by_exposed(alice_exposure) == {
        "yes": {"INS-1001", "INS-1004", "INS-2002", "INS-2003"},
        "unconfirmed": {"INS-1010"},
        "no": {"INS-1011"},
        "unknown": set(),
    }


def test_alice_cvgb_channels(alice_exposure):
    keys = channel_keys(position(alice_exposure, "INS-1004"))
    assert keys == {"ISSUED_BY": "high", CURRENCY: "high", CURVE: "high"}


def test_alice_cvgb_issued_by_is_inferred(alice_exposure):
    issued = next(c for c in position(alice_exposure, "INS-1004").channels if c.key == "ISSUED_BY")
    assert {c.status for c in issued.hops[0].citations} == {"INFERRED"}


def test_alice_derivatives(alice_exposure):
    assert channel_keys(position(alice_exposure, "INS-2002")) == {CURRENCY: "high"}
    assert channel_keys(position(alice_exposure, "INS-2003")) == {CURRENCY: "high", CURVE: "high"}


def test_alice_valdoria_correlation_only(alice_exposure):
    pe = position(alice_exposure, "INS-1010")
    assert pe.exposed == "unconfirmed"
    assert channel_keys(pe) == {"CORRELATED_WITH": "low"}
    assert "0.7" in pe.channels[0].label


def test_alice_research_visible(alice_exposure):
    files = {d.source_file for d in alice_exposure.research}
    assert MACRO_NOTE in files
    assert CPL_IPO not in files
    assert not any(f.startswith("desk_notes/") for f in files)


def test_alice_no_flags_required(alice_exposure):
    assert not [f for pe in alice_exposure.positions for f in pe.flags if f.kind in ("STALE", "CONFLICT")]


# --- bob_exposure.md -------------------------------------------------------------------------------------------

def test_bob_exposed_sets(bob_exposure):
    sets = by_exposed(bob_exposure)
    assert sets["yes"] == {"INS-1005", "INS-1006", "INS-1007", "INS-1008", "INS-2001"}
    assert sets["unconfirmed"] == {"INS-1009"}
    assert sets["no"] == set()
    assert sets["unknown"] == {"XS2812345672", "XS2999887768"}


def test_bob_cortel_channels(bob_exposure):
    pe = position(bob_exposure, "INS-1008")
    keys = channel_keys(pe)
    assert keys == {COUNTRY: "high", "OWNS": "low", "TRADES_AS_PROXY_FOR": "low"}
    owns = next(c for c in pe.channels if c.key == "OWNS")
    assert "20%" in owns.label
    assert {f.kind for f in pe.flags} == {"SUPERSEDED"}


def test_bob_cnoc_channels(bob_exposure):
    keys = channel_keys(position(bob_exposure, "INS-1005"))
    assert keys == {"OWNS": "high", "RATING_CAPPED_BY": "low", "TRADES_AS_PROXY_FOR": "low", COUNTRY: "high"}


def test_bob_cnoc_country_by_vehicle_rule(bob_exposure):
    cites = [c for ch in position(bob_exposure, "INS-1005").channels for h in ch.hops for c in h.citations]
    stmts = tools.get_statements("bob", "ISS-0007", "COUNTRY_OF_RISK")
    assert stmts.current[0].object_id == "QC" and "financing vehicle" in stmts.current[0].quote
    assert any(c.predicate == "OWNS" and c.status == "REFERENCE" and c.edge_id.startswith("ownership:") for c in cites)


def test_bob_cpl_stale_and_beta(bob_exposure):
    pe = position(bob_exposure, "INS-1006")
    keys = channel_keys(pe)
    assert keys["OWNS"] == "high" and keys["BETA_TO"] == "low"
    assert "51%" in next(c for c in pe.channels if c.key == "OWNS").label
    assert "STALE" in {f.kind for f in pe.flags}


def test_bob_cdb_guaranteed_and_corroborated(bob_exposure):
    pe = position(bob_exposure, "INS-1007")
    assert channel_keys(pe)["GUARANTEED_BY"] == "high"
    instrument_guarantee = next(c for c in pe.channels if c.key == "GUARANTEED_BY").hops[0]
    assert instrument_guarantee.citations[0].edge_id == "instruments:INS-1007:guarantor_id"
    assert instrument_guarantee.citations[0].status == "REFERENCE"
    corroborated = [f for f in pe.flags if f.kind == "CORROBORATED" and f.subject == "issuer|ISS-0004|GUARANTEED_BY|ISS-0001"]
    assert len(corroborated) == 3                                  # 4 sources: winner + 3 others


def test_bob_meridian_desk_view_only(bob_exposure):
    pe = position(bob_exposure, "INS-1009")
    assert pe.exposed == "unconfirmed"
    assert channel_keys(pe) == {COUNTRY: "low"}
    assert "CONFLICT" in {f.kind for f in pe.flags}


def test_bob_cds_sign_as_is(bob_exposure):
    pe = position(bob_exposure, "INS-2001")
    assert pe.position.quantity == Decimal("-20000000")
    assert channel_keys(pe) == {"REFERENCES_CREDIT": "high"}
    assert any("sign convention" in n for n in bob_exposure.notes)


def test_bob_unresolved_flagged(bob_exposure):
    # the two holdings the layer could not identify sit in their own block, not in the exposure table
    assert [u.position.instrument_ref for u in bob_exposure.unresolved] == ["XS2812345672", "XS2999887768"]
    assert not [pe for pe in bob_exposure.positions if pe.position.instrument_id is None]
    for u in bob_exposure.unresolved:
        assert u.position.instrument_id is None and "matches no instrument" in u.flag_message
        assert u.position.quantity > 0


def test_bob_research_visible(bob_exposure):
    files = {d.source_file for d in bob_exposure.research}
    assert CPL_IPO in files and "desk_notes/em-credit-desk-notes.md" in files
    assert MACRO_NOTE not in files


# --- pit_cpl.md ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("user", ["alice", "bob", "carol"])
def test_cpl_stake_2025(user):
    s = tools.get_statements(user, "ISS-0003", "OWNS", PIT)
    state = [r for r in s.current if r.subject_id == "ISS-0001"]
    assert [(r.value_num, r.status, r.as_of) for r in state] == [(Decimal(51), "REFERENCE", date(2023, 12, 31))]
    assert owns_cpl(s, s.other_sources) == [Decimal(51)]
    assert s.hidden_newer_count == 0
    assert not [f for f in s.flags if f.kind in ("STALE", "CONFLICT")]


def test_cpl_stake_now_alice():
    s = tools.get_statements("alice", "ISS-0003", "OWNS")
    state = [r for r in s.current if r.subject_id == "ISS-0001"]
    assert [(r.value_num, r.status) for r in state] == [(Decimal(51), "REFERENCE")]
    values = owns_cpl(s, s.current + s.other_sources)
    assert Decimal(34) not in values and Decimal(25) not in values
    assert s.hidden_newer_count == 1
    assert "STALE" not in {f.kind for f in s.flags}


@pytest.mark.parametrize("user", ["bob", "carol"])
def test_cpl_stake_now_entitled(user):
    s = tools.get_statements(user, "ISS-0003", "OWNS")
    state = [r for r in s.current if r.subject_id == "ISS-0001"]
    assert [(r.value_num, r.status) for r in state] == [(Decimal(51), "REFERENCE")]
    newer = [r for r in s.other_sources if r.value_num == 34]
    assert newer and newer[0].as_of == date(2026, 2, 24) and newer[0].visibility == "credit_internal"
    assert "sold down its stake from 51% to 34%" in newer[0].quote
    assert "STALE" in {f.kind for f in s.flags}
    assert s.hidden_newer_count == 0


# --- entitlement_negatives.md ----------------------------------------------------------------------------------

@pytest.mark.parametrize("user, books, n", [("alice", {"EM_MACRO"}, 6), ("bob", {"EM_CREDIT"}, 8),
                                            ("carol", {"EM_MACRO", "EM_CREDIT"}, 14)])
def test_positions_by_book(user, books, n):
    positions = tools.get_positions(user)
    assert len(positions) == n and {p.book for p in positions} == books


def test_alice_documents():
    files = {d.source_file for d in tools.get_documents("alice")}
    assert CPL_IPO not in files and not any(f.startswith("desk_notes/") for f in files)


def test_bob_documents():
    assert MACRO_NOTE not in {d.source_file for d in tools.get_documents("bob")}


def test_documents_about_cvgb_by_label():
    assert MACRO_NOTE not in {d.source_file for d in tools.get_documents("bob", "INS-1004")}
    # "the 2033" is a deliberately uncurated name, so the alias scan cannot tag INS-1004; INS-2003 is named outright
    alice = [d for d in tools.get_documents("alice", "INS-2003") if d.source_file == MACRO_NOTE]
    assert alice and "INS-2003" in alice[0].about_instruments and alice[0].visibility == "macro_internal"
    assert not [d for d in tools.get_documents("alice", "ISS-0003") if d.visibility == "credit_internal"]
    assert {d.source_file for d in tools.get_documents("alice", "INS-2003")} == {MACRO_NOTE}
    assert tools.get_documents("bob", "INS-2003") == []


def test_exposure_books(alice_exposure, bob_exposure):
    assert {pe.position.book for pe in alice_exposure.positions} == {"EM_MACRO"}
    assert {pe.position.book for pe in bob_exposure.positions + bob_exposure.unresolved} == {"EM_CREDIT"}


def test_reference_tables_identical():
    tables = ("issuers", "instruments", "curves", "ratings", "country", "rating_scale", "sources")
    digests = {}
    with tools.connect() as conn:
        for user in ("alice", "bob", "carol"):
            with tools.as_user(conn, user) as cur:
                digests[user] = [cur.execute(f"select md5(string_agg(t::text, ',' order by t::text)) as h "
                                             f"from {t} t").fetchone()["h"] for t in tables]
    assert digests["alice"] == digests["bob"] == digests["carol"]


def test_alice_sql_counts():
    with tools.connect() as conn, tools.as_user(conn, "alice") as cur:
        assert cur.execute("select count(*) as n from positions").fetchone()["n"] == 6
        assert cur.execute("select count(*) as n from documents "
                           "where visibility = 'credit_internal'").fetchone()["n"] == 0


def test_role_memberships_match_entitlements():
    with psycopg.connect(config.admin_dsn()) as conn, conn.cursor() as cur:
        assert validate.check_roles(cur) == []


def test_unknown_user_rejected():
    with pytest.raises(ValueError):
        tools.get_positions("mallory")


def test_unknown_entity_rejected():
    with pytest.raises(ValueError):
        tools.get_statements("bob", "ISS-9999")


def test_find_entity_kinds():
    assert [(m.entity_id, m.match_kind) for m in tools.find_entity("bob", "Republic of Corvana")] == [("ISS-0001", "exact")]
    assert tools.find_entity("bob", "XS2600112234")[0].match_kind == "identifier"
    assert {m.entity_id for m in tools.find_entity("bob", "CNOC")} == {"ISS-0002"}
    assert tools.find_entity("bob", "XS2812345672") == []
    assert config.AS_OF == date(2026, 10, 27)
