"""Ingest stress test: a scratch database rebuilt from the data pack on every run, the synthetic deliveries of
make_batches.py applied with the LLM off, and the fixed behaviours asserted. Marked `stress`, skipped by default:

    uv run pytest -m stress

The database is named by KL_STRESS_DB (default corvana_kl_stress; corvana_kl and the configured database are
refused), rebuilt at the start of the module and dropped at the end unless KL_STRESS_KEEP=1.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

from kl import config, ingest_update, load, tools, validate
from kl.load import InputError

from .make_batches import FOLDERS, MALFORMED, build_pack

pytestmark = pytest.mark.stress

DB = os.environ.get("KL_STRESS_DB", "corvana_kl_stress")
D27, D29, D30, D1110 = date(2026, 10, 27), date(2026, 10, 29), date(2026, 10, 30), date(2026, 11, 10)
BASE_FLAGS_27 = {"CONFLICT": 1, "CORROBORATED": 8, "STALE": 1, "SUPERSEDED": 2, "UNRESOLVED_REF": 2}


@dataclass
class Run:
    ok: bool
    entries: list[dict[str, Any]] = field(default_factory=list)
    text: str = ""
    error: str = ""
    rows_changed: bool = False


@pytest.fixture(scope="module")
def runs(tmp_path_factory) -> dict[str, Run]:
    if DB in ("corvana_kl", config.PG_DBNAME):
        pytest.fail(f"KL_STRESS_DB={DB!r} would overwrite the working database; use a scratch name")
    pack = build_pack(tmp_path_factory.mktemp("stress_pack"))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config, "PG_DBNAME", DB)
        mp.setattr(config, "PACK_DIR", pack)
        mp.setattr(load, "PACK", pack)
        mp.setattr(ingest_update, "PACK", pack)
        load.main()                                             # drop/create DB, base pack, roles (no LLM)
        out: dict[str, Run] = {}
        for name in FOLDERS:
            before = _counts()
            try:
                text, entries = ingest_update.ingest(pack / "updates" / name, llm=False)
                out[name] = Run(True, entries, text)
            except InputError as e:
                out[name] = Run(False, error=str(e))
            out[name].rows_changed = _counts() != before
        before = _counts()
        text, rerun = ingest_update.ingest(pack / "updates" / "2026-10-29", llm=False)
        out["rerun 2026-10-29"] = Run(True, rerun, text, rows_changed=_counts() != before)
        yield out
    if os.environ.get("KL_STRESS_KEEP") != "1":
        with psycopg.connect(config.admin_dsn("postgres"), autocommit=True) as c:
            c.execute(sql.SQL("drop database if exists {} with (force)").format(sql.Identifier(DB)))


@pytest.fixture(scope="module")
def stress_db(runs):
    """Point the tools at the stress database for one test (the runs fixture has already restored the config)."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config, "PG_DBNAME", DB)
        yield


def _counts() -> dict[str, int]:
    with psycopg.connect(config.admin_dsn()) as c:
        return load.counts(c)


def q(query: str, params: Any = ()) -> list[dict[str, Any]]:
    with psycopg.connect(config.admin_dsn(DB), row_factory=dict_row) as c:
        return c.execute(query, params).fetchall()


def kinds(as_of: date) -> dict[str, int]:
    return {r["kind"]: r["n"] for r in q("select kind, count(*) as n from data_quality(%s) group by 1", (as_of,))}


def entries(run: Run, action: str | None = None, table: str | None = None) -> list[dict[str, Any]]:
    return [e for e in run.entries if (action is None or e["action"] == action) and (table is None or e["table"] == table)]


# --- 1. known-at: a back-dated row delivered later does not change an earlier answer --------------------------------

def test_backdated_ownership_does_not_change_the_past(runs, stress_db):
    for user in ("alice", "bob"):
        cur = tools.get_statements(user, "ISS-0003", "OWNS", D27).current
        assert [(s.subject_id, s.value_num) for s in cur if s.subject_id == "ISS-0001"] == [("ISS-0001", 51)]
        later = tools.get_statements(user, "ISS-0003", "OWNS", D29).current
        assert [s.value_num for s in later if s.subject_id == "ISS-0001"] == [34]
    assert kinds(D27) == BASE_FLAGS_27                                  # the 2026-10-27 flags are the base pack's


def test_a_link_resolved_later_is_not_visible_before(runs, stress_db):
    issued = "select 1 from current_statements(%s) where edge_id = 'instruments:INS-1017:issuer_id'"
    assert q(issued, (D29,)) == [] and q(issued, (D30,)) != []


# --- 2. positions per book ------------------------------------------------------------------------------------------

def test_one_book_delivery_keeps_the_other_book(runs, stress_db):
    def books(as_of: date) -> dict[str, set[date]]:
        out: dict[str, set[date]] = {}
        for p in tools.get_positions("carol", as_of):
            out.setdefault(p.book, set()).add(p.as_of_date)
        return out
    assert books(D29) == {"EM_MACRO": {D27}, "EM_CREDIT": {D29}}
    assert books(D30) == {"EM_MACRO": {D30}, "EM_CREDIT": {D29}}
    assert not any("closed UNRESOLVED_REF" in e["message"] for e in runs["2026-10-30"].entries)
    assert q("select 1 from data_quality(%s) where kind = 'UNRESOLVED_REF' and subject = 'EM_CREDIT|XS2812345672'",
             (D30,))


# --- 3. dependency order and re-resolution ----------------------------------------------------------------------------

def test_instrument_and_issuer_in_one_delivery_resolve(runs, stress_db):
    assert q("select issuer_id from instruments where instrument_id = 'INS-1013'") == [{"issuer_id": "ISS-0011"}]
    assert not any("UNRESOLVED_NAME" in e["message"] and e["key"] == "INS-1013" for e in runs["2026-10-29"].entries)
    assert q("select count(*) as n from instruments where instrument_id >= 'INS-5000' and issuer_id is null") == [{"n": 0}]


def test_an_issuer_arriving_later_resolves_the_waiting_instrument(runs, stress_db):
    assert q("select issuer_id from instruments where instrument_id = 'INS-1017'") == [{"issuer_id": "ISS-0013"}]
    assert [e["key"] for e in entries(runs["2026-10-30"], "AUTO", "instruments")] == ["INS-1017"]


# --- 4. an unresolved issuer is "cannot tell", never "no" -----------------------------------------------------------

def test_unresolved_issuer_goes_to_the_unresolved_block(runs, stress_db):
    report = tools.get_exposure("bob", "ISS-0001", D29)
    assert "INS-1015" not in {p.position.instrument_id for p in report.positions}
    [u] = [u for u in report.unresolved if u.position.instrument_ref == "XS3011223369"]
    assert "First Corvana Bank Ltd" in u.flag_message and "resolves to no issuer" in u.flag_message
    # INS-1017's issuer arrived on 10-30: as of 10-29 it is "cannot tell", as of 10-30 a resolved position
    assert "XS3011223385" in {u.position.instrument_ref for u in report.unresolved}
    later = tools.get_exposure("bob", "ISS-0001", D30)
    assert "INS-1017" in {p.position.instrument_id for p in later.positions}


# --- 5. ownership notes: curated phrases, negation guard ------------------------------------------------------------

def test_withdrawn_guarantee_gives_no_statement_and_is_reported(runs, stress_db):
    assert q("select 1 from statements where predicate = 'GUARANTEED_BY' "
             "and source_file = 'updates/2026-10-29/ownership_delta.csv'") == []
    assert any("withdrawn" in e["message"] for e in entries(runs["2026-10-29"], "DISCARD", "statements"))
    assert q("select object_id from statements where subject_id = 'ISS-0012' and predicate = 'FINANCING_VEHICLE_OF'") \
        == [{"object_id": "ISS-0009"}]


# --- 6. unknown label and book are flagged ----------------------------------------------------------------------------

def test_unknown_label_and_book_are_flagged(runs, stress_db):
    flags = {(r["kind"], r["subject"]) for r in q("select kind, subject from data_quality(%s)", (D29,))}
    assert ("UNKNOWN_BOOK", "book|EM_RATES") in flags
    assert any(k == "UNKNOWN_LABEL" and "rates-internal" in s for k, s in flags)
    opened = [e["message"] for e in entries(runs["2026-10-29"], "FLAG")]
    assert any(m.startswith("opened UNKNOWN_BOOK") for m in opened)
    assert any(m.startswith("opened UNKNOWN_LABEL") for m in opened)
    with psycopg.connect(config.admin_dsn(DB)) as c, c.cursor() as cur:
        assert any("EM_RATES" in m for m in validate.check_books(cur))
        assert any("rates_internal" in m for m in validate.check_visibility(cur))


# --- 7. the smaller items ---------------------------------------------------------------------------------------------

def test_delta_desk_notes_keep_the_desk_label_and_dotted_handles(runs, stress_db):
    rows = q("select author, visibility, published_at from documents "
             "where source_file = 'updates/2026-10-29/desk_notes/em-credit-desk-notes.md' order by published_at")
    assert [r["author"] for r in rows] == ["dk", "j.s", "dk"]
    assert {r["visibility"] for r in rows} == {"credit_internal"}


def test_resent_note_is_not_stored_twice(runs, stress_db):
    assert q("select count(*) as n from documents where title = 'Corvana cut to B+ - what next'") == [{"n": 1}]
    assert any("re-sent" in e["message"] for e in entries(runs["2026-10-30"], "SKIP", "documents"))


def test_same_source_update_is_superseded_not_conflict(runs, stress_db):
    rows = q("select kind, other_edge from link_quality(%s) where link_key = 'issuer|ISS-0001|OWNS|ISS-0003' "
             "and winner_edge like 'ownership:%%' and other_edge like 'ownership:%%'", (D29,))
    assert [r["kind"] for r in rows] == ["SUPERSEDED"]


def test_audit_and_dropped_column_changes(runs, stress_db):
    run = runs["2026-10-29"]
    assert [e["action"] for e in run.entries if e["key"] == "ISS-0003"] == ["SKIP"]       # last_updated only
    assert [e["action"] for e in run.entries if e["key"] == "INS-1006"] == ["DISCARD"]    # a real name change
    notes = [e for e in entries(run, "SKIP") if e["message"].startswith("ignored column change")]
    assert {e["table"] for e in notes} == {"instruments", "issuers"}


@pytest.mark.parametrize("folder", list(MALFORMED))
def test_malformed_files_name_file_and_line_and_roll_back(runs, stress_db, folder):
    run, expected = runs[folder], MALFORMED[folder]
    if expected is None:                                         # BOM + CRLF: an Excel export is accepted
        assert run.ok and q("select issuer_id from instruments where instrument_id = 'INS-1016'") == [
            {"issuer_id": "ISS-0001"}]
        return
    file, line = expected
    assert not run.ok and not run.rows_changed
    assert run.error.startswith(f"updates/{folder}/{file}" + (f":{line}:" if line else ":")), run.error


def test_scan_reads_entities_and_dotted_names(runs, stress_db):
    [doc] = q("select about_issuers from documents where title = 'Credit compendium'")
    assert {"ISS-0002", "ISS-0003"} <= set(doc["about_issuers"])


def test_shared_descriptions_are_not_aliases(runs, stress_db):
    with psycopg.connect(config.admin_dsn(DB)) as c, c.cursor() as cur:
        assert validate.check_aliases(cur, validate.entity_ids(cur)) == []


def test_exposure_summary_is_capped(runs, stress_db):
    full = tools.get_exposure("carol", "ISS-0001", D1110, detail="full")
    summary = tools.get_exposure("carol", "ISS-0001", D1110)
    assert len(full.positions) > 200
    assert len(summary.positions) == 200 and summary.positions_omitted == len(full.positions) - 200
    order = {"yes": 0, "unconfirmed": 1, "no": 2}
    rank = lambda p: (order[p.exposed], -abs(p.position.quantity))                      # noqa: E731
    kept = {(p.position.book, p.position.instrument_ref) for p in summary.positions}
    worst_kept = max(rank(p) for p in full.positions if (p.position.book, p.position.instrument_ref) in kept)
    assert all(rank(p) >= worst_kept for p in full.positions if (p.position.book, p.position.instrument_ref) not in kept)
    assert len(summary.unresolved) == len(full.unresolved)                               # never omitted


def test_rerun_is_a_noop(runs):
    """Nothing applied; the batch's contradictions are reported again (no bookkeeping tables, by design)."""
    run = runs["rerun 2026-10-29"]
    assert not run.rows_changed and {e["action"] for e in run.entries} <= {"SKIP", "DISCARD"}
    assert {e["key"] for e in entries(run, "DISCARD")} == {"INS-1006", "Republic of Corvana|Agency A|2026-10-28"}


def test_validator_on_the_stress_database(runs, stress_db):
    """Only the deliberate defects remain: an unentitled book and label, unlabelled notes, one unresolved name."""
    with psycopg.connect(config.admin_dsn(DB)) as c, c.cursor() as cur:
        failures = {k.split(".")[0]: v for k, v in validate.run_checks(cur).items() if v}
    assert set(failures) <= {"3", "8", "12"}, failures              # check 6 (two positions files per book) is clean
    assert failures["3"] == ["instruments INS-1015 issuer_name 'First Corvana Bank Ltd' resolves to no issuer"]
