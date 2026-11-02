"""The ingest rules on synthetic input, inside a transaction that is rolled back: a level-1 row whose key exists
with a changed value is discarded and logged; a reference-grade statement contradicting an existing one on its
link is discarded and logged. Neither needs the delta to have been applied."""
from __future__ import annotations

from datetime import date

import psycopg
import pytest

from kl import config
from kl.ingest_update import add_statements, apply_level1_rows, same
from kl.load import statement

BATCH = date(2026, 10, 28)


@pytest.fixture
def cur():
    conn = psycopg.connect(config.admin_dsn())
    try:
        with conn.cursor() as c:
            yield c
    finally:
        conn.rollback()
        conn.close()


def test_changed_existing_key_is_discarded(cur):
    before = cur.execute("select description, issuer_id from instruments where instrument_id = 'INS-1001'").fetchone()
    row = {"instrument_id": "INS-1001", "isin": "XS2812345671", "ticker": "CORVAN 6.5 03/15/30",
           "description": "Republic of Corvana 6.5% 2030 (restated)", "instrument_type": "Sovereign Bond",
           "issuer_name": "Republic of Corvana", "guarantor_name": None, "currency": "USD", "coupon": "6.5",
           "maturity": "2030-03-15", "underlying_curve": None, "source_system": "SecMaster"}
    entries = []
    apply_level1_rows(cur, entries, "instruments", [row], "updates/synthetic/instruments_delta.csv", BATCH)
    entries = [e for e in entries if e["key"] == "INS-1001"]          # the row's own entry; the file note is separate
    assert [e["action"] for e in entries] == ["DISCARD"]
    assert "description" in entries[0]["message"] and "not applied" in entries[0]["message"]
    assert cur.execute("select description, issuer_id from instruments where instrument_id = 'INS-1001'").fetchone() == before


def test_identical_existing_key_is_skipped(cur):
    row = {"instrument_id": "INS-1001", "isin": "XS2812345671", "ticker": "CORVAN 6.5 03/15/30",
           "description": "Republic of Corvana 6.5% 2030", "instrument_type": "Sovereign Bond",
           "issuer_name": "Republic of Corvana", "guarantor_name": None, "currency": "USD", "coupon": "6.5",
           "maturity": "2030-03-15", "underlying_curve": None, "source_system": "SecMaster"}
    entries = []
    apply_level1_rows(cur, entries, "instruments", [row], "updates/synthetic/instruments_delta.csv", BATCH)
    assert [e["action"] for e in entries if e["key"] == "INS-1001"] == ["SKIP"]
    # coupon and maturity are dropped columns: noted once per file, never compared
    assert [e["message"].split(":")[0] for e in entries if e["key"] != "INS-1001"] == ["ignored column change"]


def test_new_key_is_applied_with_resolution(cur):
    row = {"instrument_id": "INS-9999", "isin": "XS0000000001", "ticker": "CORVAN 9 01/01/40",
           "description": "Synthetic 9% 2040", "instrument_type": "Sovereign Bond", "issuer_name": "Rep. of Corvana",
           "guarantor_name": "Nobody Known Ltd", "currency": "USD", "coupon": "9", "maturity": "2040-01-01",
           "underlying_curve": None, "source_system": "SecMaster"}
    entries = []
    apply_level1_rows(cur, entries, "instruments", [row], "updates/synthetic/instruments_delta.csv", BATCH)
    assert [e["action"] for e in entries] == ["AUTO"] and "UNRESOLVED_NAME on guarantor_id" in entries[0]["message"]
    got = cur.execute("select issuer_id, guarantor_id from instruments where instrument_id = 'INS-9999'").fetchone()
    assert got == ("ISS-0001", None)
    flags = cur.execute("select subject from data_quality(%s) where kind = 'UNRESOLVED_NAME'", (BATCH,)).fetchall()
    assert ("instruments|INS-9999|guarantor_name",) in flags
    assert cur.execute("select status from edges where edge_id = 'instruments:INS-9999:issuer_id'").fetchone() == ("INFERRED",)


def test_contradicting_reference_statement_is_discarded(cur):
    n_before = cur.execute("select count(*) from statements").fetchone()[0]
    row = statement(subject_type="issuer", subject_id="ISS-0008", predicate="COUNTRY_OF_RISK", object_type="country",
                    object_id="QC", as_of=BATCH, source_system="SecMaster", source_file="updates/synthetic/issuers_delta.csv",
                    status="INFERRED", quote="synthetic rule row that contradicts the GB rule row", updated_on=BATCH)
    entries = []
    assert add_statements(cur, entries, [row], BATCH) == 0
    assert [e["action"] for e in entries] == ["DISCARD"] and "stmt:" in entries[0]["message"]
    assert cur.execute("select count(*) from statements").fetchone()[0] == n_before


def test_agreeing_reference_statement_is_applied(cur):
    row = statement(subject_type="issuer", subject_id="ISS-0008", predicate="COUNTRY_OF_RISK", object_type="country",
                    object_id="GB", as_of=BATCH, source_system="SecMaster", source_file="updates/synthetic/issuers_delta.csv",
                    status="INFERRED", quote="synthetic rule row that agrees with the GB rule row", updated_on=BATCH)
    entries = []
    assert add_statements(cur, entries, [row], BATCH) == 1 and entries == []


def test_same():
    from decimal import Decimal
    assert same(Decimal("6.5"), "6.50") and same(date(2030, 3, 15), "2030-03-15") and same(None, None)
    assert not same("a", "b") and not same(None, "x")


def test_alias_scan_longest_first(cur):
    from kl.resolve import alias_patterns, rule_annotation
    patterns = alias_patterns(cur)
    scan = rule_annotation("Corvana Telecommunications (CorTel) reported.", patterns)
    assert scan["about_issuers"] == ["ISS-0005"]                       # "Corvana" inside the longer name does not tag ISS-0001
    scan = rule_annotation("Corvana and CorTel: the Republic of Corvana owns CorTel.", patterns)
    assert scan["about_issuers"] == ["ISS-0001", "ISS-0005"]           # a free-standing "Corvana" still does
    scan = rule_annotation("Nothing here.", patterns)
    assert all(v == [] for v in scan.values())
    scan = rule_annotation("remember CDB 27s are guaranteed", patterns)
    assert scan["about_issuers"] == ["ISS-0004"] and scan["about_instruments"] == ["INS-1007"]   # types scanned independently
