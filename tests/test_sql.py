"""Direct SQL assertions, at least one per view and function in 020_logic.sql, against the base pack.
They run as the asking role where visibility matters (SET ROLE), as admin otherwise."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

from kl import config, validate

AS_OF = date(2026, 10, 27)


@pytest.fixture(scope="module")
def conn():
    with psycopg.connect(config.admin_dsn(), row_factory=dict_row) as c:
        yield c


def q(conn, query: str, params=(), role: str | None = None):
    with conn.cursor() as cur:
        if role:
            cur.execute(sql.SQL("set role {}").format(sql.Identifier(role)))
        try:
            return cur.execute(query, params).fetchall()
        finally:
            if role:
                cur.execute("reset role")


def test_alias_resolves_ministry_of_finance(conn):
    rows = q(conn, "select entity_type, entity_id, name_column from alias where lower(alias) = lower(%s)",
             ("Corvana Ministry of Finance",))
    assert [(r["entity_type"], r["entity_id"], r["name_column"]) for r in rows] == [("issuer", "ISS-0001", "aliases")]
    assert q(conn, "select entity_type, lower(alias) from alias group by 1, 2 having count(distinct entity_id) > 1") == []


def test_source_tier(conn):
    tiers = {r["source_id"]: r["tier"] for r in q(conn, "select * from source_tier")}
    assert tiers["SecMaster"] == 3 and tiers["OwnershipTracker"] == 2 and tiers["ResearchHub"] == 1
    assert tiers["DeskNotes"] == 1 and tiers["Curated"] == 3


def test_position_resolved(conn):
    rows = {r["instrument_ref"]: r["instrument_id"] for r in q(conn, "select * from position_resolved")}
    assert rows["CVD IRS 5Y"] == "INS-2003" and rows["INS-1007"] == "INS-1007" and rows["XS2812345671"] == "INS-1001"
    assert rows["XS2812345672"] is None
    assert rows["XS2999887768"] in (None, "INS-1012")               # INS-1012 arrives with the 2026-10-28 delta


def test_rating_current(conn):
    rows = {r["issuer_id"]: r for r in q(conn, "select * from rating_current")}
    latest = q(conn, "select action_date from ratings where issuer_id = 'ISS-0001' order by action_date desc limit 1")[0]
    assert rows["ISS-0001"]["action_date"] == latest["action_date"]
    if latest["action_date"] == date(2026, 9, 18):                   # base pack
        assert (rows["ISS-0001"]["rating"], rows["ISS-0001"]["outlook"], rows["ISS-0001"]["rank"]) == ("BB-", "Negative", 13)
    else:                                                            # after the 2026-10-28 delta
        assert (rows["ISS-0001"]["rating"], rows["ISS-0001"]["outlook"], rows["ISS-0001"]["rank"]) == ("B+", "Stable", 14)


def test_edges_issued_by_status(conn):
    rows = {r["edge_id"]: r for r in q(conn, "select * from edges where predicate in ('ISSUED_BY', 'REFERENCES_CREDIT')")}
    inferred = rows["instruments:INS-1003:issuer_id"]
    assert (inferred["status"], inferred["quote"], inferred["object_id"]) == ("INFERRED", "Corvana Ministry of Finance", "ISS-0001")
    assert rows["instruments:INS-1001:issuer_id"]["status"] == "REFERENCE"
    assert rows["instruments:INS-2001:issuer_id"]["predicate"] == "REFERENCES_CREDIT"
    assert rows["instruments:INS-1005:issuer_id"]["object_id"] == "ISS-0007"


def test_edges_level1_projection(conn):
    preds = {r["predicate"]: r["n"] for r in q(conn, "select predicate, count(*) as n from edges "
                                                    "where statement_id is null and as_of <= %s group by 1", (AS_OF,))}
    assert preds == {"ISSUED_BY": 11, "REFERENCES_CREDIT": 1, "GUARANTEED_BY": 2, "OWNS": 4, "DENOMINATED_IN": 17,
                     "PRICED_OFF": 3, "CURRENCY_OF": 4, "SOVEREIGN_IS": 2}
    owns = q(conn, "select * from edges where edge_id = 'ownership:3'")[0]
    assert (owns["subject_id"], owns["object_id"], owns["value_num"], owns["as_of"], owns["status"], owns["tier"]) == \
        ("ISS-0001", "ISS-0003", Decimal("51.00"), date(2023, 12, 31), "REFERENCE", 2)
    assert q(conn, "select 1 from edges where status = 'REFERENCE' and statement_id is not null") == []


def test_current_statements_cpl_stake_for_carol(conn):
    rows = q(conn, "select edge_id, rn, value_num, status, visibility from current_statements(%s) "
                   "where link_key = 'issuer|ISS-0001|OWNS|ISS-0003' order by rn", (AS_OF,), role="carol")
    assert [(r["edge_id"], r["rn"], int(r["value_num"]), r["status"]) for r in rows] == [
        ("ownership:3", 1, 51, "REFERENCE"), ("stmt:21", 2, 34, "PROPOSED"), ("stmt:17", 3, 51, "PROPOSED")]
    # alice cannot see the credit_internal row at all
    alice = q(conn, "select edge_id from current_statements(%s) where link_key = 'issuer|ISS-0001|OWNS|ISS-0003'",
              (AS_OF,), role="alice")
    assert {r["edge_id"] for r in alice} == {"ownership:3", "stmt:17"}


def test_link_quality_stale_on_cpl_stake(conn):
    rows = q(conn, "select kind, winner_edge, other_edge from link_quality(%s) "
                   "where link_key = 'issuer|ISS-0001|OWNS|ISS-0003' order by kind", (AS_OF,), role="bob")
    assert [(r["kind"], r["winner_edge"], r["other_edge"]) for r in rows] == [
        ("CORROBORATED", "ownership:3", "stmt:17"), ("STALE", "ownership:3", "stmt:21")]
    assert q(conn, "select 1 from link_quality(%s) where link_key = 'issuer|ISS-0001|OWNS|ISS-0003' and kind = 'STALE'",
             (AS_OF,), role="alice") == []


def test_data_quality_as_of(conn):
    rows = q(conn, "select kind, subject from data_quality(%s)", (AS_OF,))
    kinds = {(r["kind"], r["subject"]) for r in rows}
    assert ("UNRESOLVED_REF", "EM_CREDIT|XS2812345672") in kinds and ("UNRESOLVED_REF", "EM_CREDIT|XS2999887768") in kinds
    assert sum(k == "UNRESOLVED_REF" for k, _ in kinds) == 2
    assert ("CONFLICT", "issuer|ISS-0008|COUNTRY_OF_RISK|") in kinds
    assert not any(k in ("UNRESOLVED_NAME", "RATING_LAG", "UNLABELLED_DOCUMENT") for k, _ in kinds)
    # the view is the function at today's date
    assert {r["kind"] for r in q(conn, "select kind from data_quality")} >= {"UNRESOLVED_REF", "CONFLICT", "STALE"}


def test_exposure_paths_curve_channel(conn):
    rows = q(conn, "select predicates, hop_grades from exposure_paths('issuer', 'ISS-0001', %s) "
                   "where start_id = 'INS-2003' order by predicates", (AS_OF,), role="alice")
    assert [r["predicates"] for r in rows] == [["DENOMINATED_IN", "CURRENCY_OF", "SOVEREIGN_IS"],
                                              ["PRICED_OFF", "DENOMINATED_IN", "CURRENCY_OF", "SOVEREIGN_IS"]]
    assert all(set(r["hop_grades"]) == {"high"} for r in rows)
    # a research-only hop is low, and bob's credit_internal beta path is invisible to alice
    cpl = q(conn, "select predicates, hop_grades from exposure_paths('issuer', 'ISS-0001', %s) where start_id = 'INS-1006'",
            (AS_OF,), role="alice")
    assert ["ISSUED_BY", "BETA_TO"] not in [r["predicates"] for r in cpl]


def test_hidden_newer_count(conn):
    args = ("issuer", "ISS-0001", "OWNS", "ISS-0003", date(2023, 12, 31), AS_OF)
    assert q(conn, "select hidden_newer_count(%s, %s, %s, %s, %s, %s) as n", args, role="alice")[0]["n"] == 1
    assert q(conn, "select hidden_newer_count(%s, %s, %s, %s, %s, %s) as n", args, role="bob")[0]["n"] == 0


def test_num_key(conn):
    assert [r["k"] for r in q(conn, "select num_key(51.00) as k union all select num_key(51.0000) "
                                    "union all select num_key(0.7000) union all select num_key(null)")] == ["51", "51", "0.7", ""]


def test_rls_counts_as_alice(conn):
    assert q(conn, "select count(*) as n from positions", role="alice")[0]["n"] == 6
    assert q(conn, "select count(*) as n from documents where visibility = 'credit_internal'", role="alice")[0]["n"] == 0
    assert q(conn, "select count(*) as n from statements where visibility = 'credit_internal'", role="alice")[0]["n"] == 0


def test_validator_is_clean():
    with psycopg.connect(config.admin_dsn()) as c, c.cursor() as cur:
        failures = {name: errs for name, errs in validate.run_checks(cur).items() if errs}
    assert failures == {}
