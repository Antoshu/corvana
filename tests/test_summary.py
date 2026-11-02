"""Summary-first tools (model/ground_truth.md section 13): the get_exposure summary shape, the unresolved block,
get_path and get_document as drill-downs, research ranked in SQL, and the nearest-match hint on unresolved refs."""
from __future__ import annotations

import pytest

import psycopg
from psycopg.rows import dict_row

from conftest import position
from kl import config, tools

CPL_IPO_DOC = 4                                  # research/2026-03-05_em-credit-internal_cpl-ipo.md


def test_summary_shape(bob_summary):
    assert isinstance(bob_summary, tools.ExposureSummary)
    for pe in bob_summary.positions:
        assert pe.position.instrument_id is not None and pe.exposed in ("yes", "unconfirmed", "no")
        for c in pe.channels:
            assert not hasattr(c, "hops") and not hasattr(c, "citations")        # no citations inside a channel
            assert len(c.edge_ids) == c.hop_count >= 1 and all(c.edge_ids)        # one edge id per hop
        for f in pe.flags:
            assert set(f.model_dump()) == {"kind", "message"}
    for d in bob_summary.research:
        assert not hasattr(d, "text") and d.about_on_path


def test_summary_edge_ids_are_citable(bob_summary):
    owns = next(c for c in position(bob_summary, "INS-1005").channels if c.key == "OWNS")
    assert owns.edge_ids == ["instruments:INS-1005:guarantor_id", "ownership:1"]


def test_summary_unresolved_block(bob_summary):
    assert [u.position.instrument_ref for u in bob_summary.unresolved] == ["XS2812345672", "XS2999887768"]
    assert {u.position.instrument_ref for u in bob_summary.unresolved}.isdisjoint(
        {pe.position.instrument_ref for pe in bob_summary.positions})
    assert all(u.flag_message.startswith("position EM_CREDIT/") for u in bob_summary.unresolved)
    assert tools.get_exposure("alice", config.TARGET_ISSUER).unresolved == []


def test_summary_is_smaller_than_full(bob_summary, bob_exposure):
    assert len(bob_summary.model_dump_json()) < len(bob_exposure.model_dump_json()) / 2
    assert bob_exposure.unresolved == bob_summary.unresolved
    assert [d.document_id for d in bob_exposure.research] == [d.document_id for d in bob_summary.research]


def test_get_path_matches_full(bob_exposure):
    full = next(c for c in position(bob_exposure, "INS-1005").channels if c.key == "OWNS")
    path = tools.get_path("bob", "INS-1005", config.TARGET_ISSUER, "OWNS")
    assert path.hops == full.hops and path.paths_considered == full.paths_considered == 4
    assert path.label == full.label and path.grade == "high"
    with pytest.raises(ValueError, match="no channel"):
        tools.get_path("bob", "INS-1005", config.TARGET_ISSUER, "GUARANTEED_BY")


def test_get_document_respects_rls():
    # an invisible document is indistinguishable from a missing one: both raise (documented in tools.get_document)
    assert tools.get_document("bob", CPL_IPO_DOC).visibility == "credit_internal"
    with pytest.raises(ValueError, match="does not exist or is not visible"):
        tools.get_document("alice", CPL_IPO_DOC)
    with pytest.raises(ValueError):
        tools.get_document("bob", 99999)


def test_get_documents_text_on_request():
    rows = tools.get_documents("bob", "ISS-0003")
    assert rows and all(isinstance(d, tools.DocumentSummary) and not hasattr(d, "text") for d in rows)
    with_text = tools.get_documents("bob", "ISS-0003", text=True)
    assert [d.document_id for d in with_text] == [d.document_id for d in rows]
    assert all(isinstance(d, tools.Document) and d.text for d in with_text)


def test_research_ranked_in_sql(bob_summary):
    order = [d.document_id for d in bob_summary.research]
    assert order.index(8) < order.index(1) and order.index(2) < order.index(1)
    counts = [len(d.about_on_path) for d in bob_summary.research]
    assert counts == sorted(counts, reverse=True)                         # most path entities first
    for a, b in zip(bob_summary.research, bob_summary.research[1:]):
        if len(a.about_on_path) == len(b.about_on_path):
            assert a.published_at >= b.published_at                      # then newest first
    assert len(tools.get_exposure("bob", config.TARGET_ISSUER, max_documents=2).research) == 2


def test_unresolved_nearest_match_hint():
    with tools.connect() as conn, tools.as_user(conn, "bob") as cur:
        cur.execute("select subject, message from data_quality(%s) where kind = 'UNRESOLVED_REF'", (config.AS_OF,))
        msgs = {r["subject"]: r["message"] for r in cur.fetchall()}
    assert msgs["EM_CREDIT|XS2812345672"].endswith("nearest known ISIN XS2812345671 (INS-1001); not applied")
    assert "nearest" not in msgs["EM_CREDIT|XS2999887768"]               # INS-1012 is not known before the delta
    # never resolved by the hint
    assert not [p for p in tools.get_positions("bob") if p.instrument_ref == "XS2812345672" and p.instrument_id]


def test_confirmed_desk_row_overrides_inferred_reference(bob_exposure):
    """A person's CONFIRMED outranks REFERENCE/INFERRED and settles the link (losers SUPERSEDED, never CONFLICT);
    without one, reference data keeps winning (CPL 51 vs 34). One transaction: the update as admin, the reads as
    bob, rolled back at the end."""
    base_counts = {"CONFLICT": 1, "CORROBORATED": 8, "STALE": 1, "SUPERSEDED": 2, "UNRESOLVED_REF": 2}
    with psycopg.connect(config.admin_dsn(), row_factory=dict_row) as conn:
        try:
            with conn.cursor() as admin:
                counts = admin.execute("select kind, count(*)::int as n from data_quality(%s) group by 1",
                                       (config.AS_OF,)).fetchall()
                assert {r["kind"]: r["n"] for r in counts} == base_counts
                n = admin.execute("update statements set status = 'CONFIRMED' where subject_id = 'ISS-0008' "
                                  "and predicate = 'COUNTRY_OF_RISK' and object_id = 'QC' "
                                  "and source_system = 'DeskNotes'").rowcount
                assert n == 1
            with tools.as_user(conn, "bob") as cur:
                rows = cur.execute("select rn, object_id, status, edge_id from current_statements(%s) "
                                   "where subject_id = 'ISS-0008' and predicate = 'COUNTRY_OF_RISK' order by rn",
                                   (config.AS_OF,)).fetchall()
                assert [(r["object_id"], r["status"]) for r in rows] == [("QC", "CONFIRMED"), ("GB", "INFERRED")]
                lq = cur.execute("select kind, winner_edge, other_edge from link_quality(%s) "
                                 "where link_key = 'issuer|ISS-0008|COUNTRY_OF_RISK|'", (config.AS_OF,)).fetchall()
                assert [(q["kind"], q["winner_edge"], q["other_edge"]) for q in lq] == [
                    ("SUPERSEDED", rows[0]["edge_id"], rows[1]["edge_id"])]         # a person settled the link
                assert not [q for q in lq if q["kind"] == "CONFLICT"]
                report, _ = tools._exposure(cur, "bob", config.TARGET_ISSUER, config.AS_OF, 10)
            pe = position(report, "INS-1009")
            assert pe.exposed == "yes"
            country = next(c for c in pe.channels if c.key == "COUNTRY_OF_RISK>SOVEREIGN_IS")
            assert country.grade == "high" and country.hops[1].grade == "high"
            assert {c.status for c in country.hops[1].citations} == {"CONFIRMED"}   # the GB row is another hop, off the path
        finally:
            conn.rollback()
        with conn.cursor() as admin:
            counts = admin.execute("select kind, count(*)::int as n from data_quality(%s) group by 1",
                                   (config.AS_OF,)).fetchall()
            assert {r["kind"]: r["n"] for r in counts} == base_counts         # rolled back: counts as before
    # base-pack precedence unchanged: Meridian stays unconfirmed, the tracker's 51 still beats the IPO note's 34
    assert position(bob_exposure, "INS-1009").exposed == "unconfirmed"
    s = tools.get_statements("bob", "ISS-0003", "OWNS")
    assert [(r.value_num, r.status) for r in s.current if r.subject_id == "ISS-0001"] == [(51, "REFERENCE")]
    assert 34 in {r.value_num for r in s.other_sources}
