"""Regression tests for the ingest stress-test findings (2026-11-02), on synthetic rows inside a transaction that is
rolled back, so they run with the regular suite. The end-to-end version is tests/stress (pytest -m stress)."""
from __future__ import annotations

from datetime import date, timedelta

import psycopg
import pytest
from psycopg.rows import dict_row

from kl import config
from kl.ingest_update import apply_level1_rows, reresolve
from kl.load import CHAT_LINE, InputError, interpret_note, parse_research
from kl.resolve import alias_patterns, document_scan_text, mention_ids, scan_mentions

D27, D29 = date(2026, 10, 27), date(2026, 10, 29)
CPL = "issuer|ISS-0001|OWNS|ISS-0003"


@pytest.fixture
def cur():
    conn = psycopg.connect(config.admin_dsn(), row_factory=dict_row)
    try:
        with conn.cursor() as c:
            yield c
    finally:
        conn.rollback()
        conn.close()


def backdated_stake(cur) -> None:
    """The tracker's 34% on CPL, dated 2026-10-15, delivered on 2026-10-29."""
    cur.execute("insert into ownership (ownership_id, owner, owner_id, owned_entity, owned_id, stake_pct, as_of_date, "
                "source, source_file, updated_on) values (-1, 'Republic of Corvana (MinFin)', 'ISS-0001', "
                "'Corvana Power & Light plc', 'ISS-0003', 34, '2026-10-15', 'placement notice', "
                "'updates/synthetic/ownership_delta.csv', %s)", (D29,))


def winner(cur, as_of: date) -> str:
    cur.execute("select num_key(value_num) as v from current_statements(%s) where link_key = %s and rn = 1", (as_of, CPL))
    return cur.fetchone()["v"]


def test_known_at_a_backdated_row_does_not_change_an_earlier_answer(cur):
    before = cur.execute("select kind, subject, edge_id, other_edge_id from data_quality(%s)", (D27,)).fetchall()
    backdated_stake(cur)
    assert winner(cur, D27) == "51" and winner(cur, D29) == "34"
    assert cur.execute("select kind, subject, edge_id, other_edge_id from data_quality(%s)", (D27,)).fetchall() == before


def test_known_by_reads_the_base_pack_before_its_load(cur):
    assert cur.execute("select known_by('2025-06-30') as d").fetchone()["d"] == config.AS_OF
    assert winner(cur, date(2025, 6, 30)) == "51"                    # the point-in-time question still answers


def test_same_source_update_is_superseded(cur):
    backdated_stake(cur)
    rows = cur.execute("select kind from link_quality(%s) where link_key = %s and winner_edge like 'ownership:%%' "
                       "and other_edge like 'ownership:%%'", (D29, CPL)).fetchall()
    assert [r["kind"] for r in rows] == ["SUPERSEDED"]


def test_positions_are_read_per_book(cur):
    cur.execute("insert into positions (book, instrument_ref, ref_type, quantity, notional_ccy, as_of_date, source_file, "
                "updated_on) values ('EM_CREDIT', 'INS-1007', 'INTERNAL', 1, 'USD', %s, 'updates/synthetic/p.csv', %s)",
                (D29, D29))
    rows = cur.execute("select book, as_of_date from positions_as_of(%s)", (D29,)).fetchall()
    assert {(r["book"], r["as_of_date"]) for r in rows} == {("EM_MACRO", D27), ("EM_CREDIT", D29)}
    assert cur.execute("select count(*) as n from positions_as_of(%s)", (D27,)).fetchone()["n"] == 14


def test_reresolution_fills_a_null_id_when_the_issuer_arrives(cur):
    entries = []
    row = {"instrument_id": "INS-9998", "isin": "XS0000000002", "ticker": "KESTRL 9 06/30/30",
           "description": "Synthetic 9% 2030", "instrument_type": "Corporate Bond", "issuer_name": "Kestrel Resources Ltd",
           "guarantor_name": None, "currency": "USD", "coupon": "9", "maturity": "2030-06-30",
           "underlying_curve": None, "source_system": "SecMaster"}
    apply_level1_rows(cur, entries, "instruments", [row], "updates/synthetic/instruments_delta.csv", D29)
    issuer = {"issuer_id": "ISS-9998", "legal_name": "Kestrel Resources Ltd", "short_name": "Kestrel", "lei": None,
              "country_of_incorporation": "QC", "issuer_type": "Corporate", "sector": "Materials",
              "source_system": "SecMaster", "last_updated": "2026-10-30"}
    apply_level1_rows(cur, entries, "issuers", [issuer], "updates/synthetic/issuers_delta.csv", date(2026, 10, 30))
    reresolve(cur, entries, date(2026, 10, 30))
    assert cur.execute("select issuer_id from instruments where instrument_id = 'INS-9998'").fetchone()["issuer_id"] == "ISS-9998"
    assert [e["action"] for e in entries if e["key"] == "INS-9998"] == ["AUTO", "AUTO"]
    flagged = "select 1 from data_quality(%s) where subject = 'instruments|INS-9998|issuer_name'"
    assert cur.execute(flagged, (D29,)).fetchall() and not cur.execute(flagged, (date(2026, 10, 30),)).fetchall()


def test_audit_column_change_is_skipped(cur):
    entries = []
    row = {"issuer_id": "ISS-0003", "legal_name": "Corvana Power & Light plc", "short_name": "CPL",
           "lei": "5493CPLPWR0000000204", "country_of_incorporation": "QC", "issuer_type": "Corporate",
           "sector": "Utilities", "source_system": "SecMaster", "last_updated": "2026-10-29"}
    apply_level1_rows(cur, entries, "issuers", [row], "updates/synthetic/issuers_delta.csv", D29)
    assert [e["action"] for e in entries if e["key"] == "ISS-0003"] == ["SKIP"]


def test_row_error_names_file_and_line(cur):
    row = {"entity": "Republic of Corvana", "agency": "Agency B", "rating": "B1", "outlook": "Negative",
           "action_date": "2026-11-02", "source": "RatingsFeed"}
    with pytest.raises(InputError, match=r"^updates/synthetic/ratings_delta\.csv:7: ratings row not applied"):
        apply_level1_rows(cur, [], "ratings", [row], "updates/synthetic/ratings_delta.csv", D29, lines=[7])


@pytest.mark.parametrize("note, predicates, refused", [
    ("Explicit sovereign guarantee on senior debt", ["GUARANTEED_BY"], False),
    ("Financing vehicle", ["FINANCING_VEHICLE_OF"], False),
    ("Sovereign guarantee withdrawn for new issuance from 2027", [], True),
    ("Guarantee no longer applies", [], False),                    # no curated phrase: nothing read, nothing refused
    ("Annual report 2019", [], False),
])
def test_ownership_note_rules(note, predicates, refused):
    found, why = interpret_note(note)
    assert [h["predicate"] for h in found] == predicates and bool(why) == refused


def test_chat_handle_with_a_dot():
    assert CHAT_LINE.match("[2026-10-29 10:40] j.s: CPL now 34%")[2] == "j.s"


def test_scan_reads_html_entities_and_dotted_abbreviations(cur):
    doc = {"title": "x", "text": "Corvana Power &amp; Light and C.N.O.C. widened."}
    found = mention_ids(scan_mentions(document_scan_text(doc), alias_patterns(cur)))
    assert {"ISS-0002", "ISS-0003"} <= set(found["about_issuers"])


def test_research_parse_errors_name_file_and_line(tmp_path):
    bad = tmp_path / "note.md"
    bad.write_text("---\ntitle: CNOC: capped\ndate: 2026-11-03\n---\n\nx\n", encoding="utf-8")
    with pytest.raises(InputError, match=r"note\.md:2: front matter is not valid YAML"):
        parse_research(bad)
    bad.write_text("---\ntitle: CDB\nsource: Bank A\ndate: 4 Nov 2026\n---\n\nx\n", encoding="utf-8")
    with pytest.raises(InputError, match=r"note\.md:4: date '4 Nov 2026' is not YYYY-MM-DD"):
        parse_research(bad)


def test_unknown_label_is_flagged(cur):
    # an explicit id: a rolled-back insert would still consume the sequence and shift the next real document's id
    cur.execute("insert into documents (document_id, source_system, source_file, kind, title, published_at, visibility, "
                "text, annotated_by, updated_on) values (-1, 'ResearchHub', 'updates/synthetic/research/x.md', "
                "'RESEARCH', 'x', %s, 'rates_internal', 'x', 'RULE', %s)", (D29, D29))
    kinds = {r["kind"] for r in cur.execute("select kind from data_quality(%s)", (D29,)).fetchall()}
    assert "UNKNOWN_LABEL" in kinds


# --- second review (2026-11-02): precedence on the walk, vehicle rule, guard, rating lag, hidden count, cap ---------

MERIDIAN_DESK = ("update statements set status = 'CONFIRMED' where subject_id = 'ISS-0008' "
                 "and predicate = 'COUNTRY_OF_RISK' and object_id = %s and method = %s")
MERIDIAN_PATHS = "select hop_grades from exposure_paths('issuer', 'ISS-0001', %s, p_start_ids => array['INS-1009'])"


def test_walk_base_pack_keeps_unconfirmed_desk_view(cur):
    """No confirmation: the desk's QC still walks as a low-grade channel beside the GB rule row (expected answers)."""
    grades = [r["hop_grades"] for r in cur.execute(MERIDIAN_PATHS, (D27,)).fetchall()]
    assert grades and all("low" in g for g in grades)
    proxy = cur.execute("select hop_grades from exposure_paths('issuer', 'ISS-0001', %s, p_start_ids => array['INS-1008']) "
                        "where predicates = array['ISSUED_BY', 'TRADES_AS_PROXY_FOR']", (D27,)).fetchall()
    assert [r["hop_grades"] for r in proxy] == [["high", "low"]]                 # the desk row wins, low grade


def test_walk_confirmed_gb_drops_the_superseded_desk_path(cur):
    assert cur.execute(MERIDIAN_DESK, ("GB", "RULE")).rowcount == 1
    assert cur.execute(MERIDIAN_PATHS, (D27,)).fetchall() == []                  # INS-1009 reads "no"


def test_walk_confirmed_qc_is_high(cur):
    assert cur.execute(MERIDIAN_DESK, ("QC", "MANUAL")).rowcount == 1
    grades = [r["hop_grades"] for r in cur.execute(MERIDIAN_PATHS, (D27,)).fetchall()]
    assert grades and all(set(g) == {"high"} for g in grades)


def test_guard_compares_with_the_winner_only(cur):
    from kl.ingest_update import add_statements
    from kl.load import statement
    cur.execute(MERIDIAN_DESK, ("QC", "MANUAL"))
    row = statement(subject_type="issuer", subject_id="ISS-0008", predicate="COUNTRY_OF_RISK", object_type="country",
                    object_id="QC", as_of=D29, source_system="SecMaster", source_file="updates/synthetic/x.csv",
                    status="INFERRED", quote="synthetic rule row agreeing with the confirmed QC", updated_on=D29)
    entries = []
    assert add_statements(cur, entries, [row], D29) == 1 and not [e for e in entries if e["action"] == "DISCARD"]


def _vehicle_rows(cur, as_of: date) -> list[str]:
    cur.execute("select object_id from current_statements(%s, 'issuer|ISS-0099|COUNTRY_OF_RISK|') order by rn", (as_of,))
    return [r["object_id"] for r in cur.fetchall()]


VEHICLE_ISSUER = {"issuer_id": "ISS-0099", "legal_name": "CNOC Treasury B.V.", "short_name": "CNOC Treasury",
                  "lei": None, "country_of_incorporation": "NL", "issuer_type": "Corporate", "sector": "Energy",
                  "source_system": "SecMaster", "last_updated": "2026-10-29"}
VEHICLE_NOTE = {"owner": "Corvana National Oil Company", "owned_entity": "CNOC Treasury B.V.", "stake_pct": "100",
                "as_of_date": "2026-10-30", "source": "prospectus", "notes": "Financing vehicle"}


def test_vehicle_and_issuer_in_one_batch_take_the_parents_country(cur):
    from kl.ingest_update import derive_country_of_risk
    entries = []
    apply_level1_rows(cur, entries, "issuers", [VEHICLE_ISSUER], "updates/synthetic/issuers_delta.csv", D29)
    apply_level1_rows(cur, entries, "ownership", [VEHICLE_NOTE], "updates/synthetic/ownership_delta.csv", D29)
    reresolve(cur, entries, D29)
    derive_country_of_risk(cur, entries, D29)
    assert _vehicle_rows(cur, D29) == ["QC"]                                     # never NL


def test_vehicle_note_arriving_later_supersedes_the_default(cur):
    from kl.ingest_update import derive_country_of_risk
    entries, d30 = [], date(2026, 10, 30)
    apply_level1_rows(cur, entries, "issuers", [VEHICLE_ISSUER], "updates/synthetic/issuers_delta.csv", D29)
    derive_country_of_risk(cur, entries, D29)
    assert _vehicle_rows(cur, D29) == ["NL"]
    apply_level1_rows(cur, entries, "ownership", [VEHICLE_NOTE], "updates/synthetic/ownership_delta.csv", d30)
    derive_country_of_risk(cur, entries, d30)
    assert _vehicle_rows(cur, d30) == ["QC", "NL"] and _vehicle_rows(cur, D29) == ["NL"]
    kinds = cur.execute("select kind from link_quality(%s) where link_key = 'issuer|ISS-0099|COUNTRY_OF_RISK|'",
                        (d30,)).fetchall()
    assert [k["kind"] for k in kinds] == ["SUPERSEDED"]


def test_rating_lag_is_per_agency(cur):
    when = date(2026, 12, 1)
    for agency in ("Agency T", "Agency U"):
        cur.execute("insert into rating_scale (agency, rating, rank, updated_on) "
                    "select %s, rating, rank, updated_on from rating_scale where agency = 'Agency A'", (agency,))
    rows = [("Corvana Development Bank", "ISS-0004", "Agency T", "BBB", when),   # T: CDB above the sovereign
            ("Republic of Corvana", "ISS-0001", "Agency T", "BB", when),
            ("Corvana Development Bank", "ISS-0004", "Agency U", "BB", when + timedelta(days=1)),  # U: level, latest
            ("Republic of Corvana", "ISS-0001", "Agency U", "BB", when + timedelta(days=1))]
    for entity, issuer, agency, rating, day in rows:
        cur.execute("insert into ratings (entity, issuer_id, agency, rating, outlook, action_date, source, source_file, "
                    "updated_on) values (%s, %s, %s, %s, 'Stable', %s, 'RatingsFeed', 'updates/synthetic/r.csv', %s)",
                    (entity, issuer, agency, rating, day, when))
    subjects = {r["subject"] for r in cur.execute("select subject from data_quality(%s) where kind = 'RATING_LAG'",
                                                  (when + timedelta(days=2),)).fetchall()}
    assert "ISS-0004|GUARANTEED_BY|ISS-0001|Agency T" in subjects
    assert "ISS-0004|GUARANTEED_BY|ISS-0001|Agency U" not in subjects


def test_hidden_newer_count_takes_the_asker_from_the_session():
    from kl import tools
    args = ("issuer", "ISS-0001", "OWNS", "ISS-0003", date(2023, 12, 31), D27)
    with psycopg.connect(config.admin_dsn(), row_factory=dict_row, autocommit=True) as conn:
        counts = {}
        for user in ("alice", "bob"):
            with tools.as_user(conn, user) as c:
                counts[user] = c.execute("select hidden_newer_count(%s, %s, %s, %s, %s, %s) as n", args).fetchone()["n"]
        assert counts == {"alice": 1, "bob": 0}
        with tools.as_user(conn, "alice") as c:
            with pytest.raises(psycopg.errors.UndefinedFunction):                 # no p_user parameter any more
                c.execute("select hidden_newer_count(%s, %s, %s, %s, %s, %s, 'bob') as n", args)
            # the asker is the SET ROLE value, read inside the definer function. Note: the tools connect as a
            # superuser, and SET ROLE is checked against the session user, so raw SQL in a tools session could
            # still SET ROLE bob; only a non-superuser application role (TODO "Identity from the session") closes it.
            assert c.execute("select current_setting('role') as r").fetchone()["r"] == "alice"
    s = tools.get_statements("alice", "ISS-0003", "OWNS", D27)
    assert s.hidden_newer_count == 1 and tools.get_statements("bob", "ISS-0003", "OWNS", D27).hidden_newer_count == 0


def test_summary_cap_ranks_exposed_first():
    from decimal import Decimal
    from kl import tools

    def pe(ref: str, qty: int, exposed: str) -> tools.PositionExposure:
        pos = tools.Position(book="SYN", instrument_ref=ref, ref_type="INTERNAL", quantity=Decimal(qty),
                             notional_ccy="USD", as_of_date=D27, instrument_id=ref, description=None,
                             instrument_type=None, resolution_note="synthetic")
        return tools.PositionExposure(position=pos, exposed=exposed, channels=[], flags=[])
    positions = [pe("A", 900, "no"), pe("B", -5, "yes"), pe("C", 50, "unconfirmed"), pe("D", 800, "no"),
                 pe("E", 1, "yes")]
    unresolved = [tools.Unresolved(position=positions[0].position, flag_message="synthetic")]
    target = tools.EntityMatch(entity_type="issuer", entity_id="ISS-0001", name="Republic of Corvana",
                               matched_alias="ISS-0001", match_kind="exact")
    report = tools.ExposureReport(user="carol", as_of=D27, target=target, target_rating=None, positions=positions,
                                  unresolved=unresolved, research=[], notes=[])
    s = tools._summarise(report, {}, 4)
    assert [p.position.instrument_ref for p in s.positions] == ["A", "B", "C", "E"]   # report order kept
    assert s.positions_omitted == 1 and len(s.unresolved) == 1                         # D (no, smaller) omitted
    with pytest.raises(ValueError, match="max_positions"):
        tools.get_exposure("carol", "ISS-0001", max_positions=-1)
