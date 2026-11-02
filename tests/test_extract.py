"""The deterministic half of the grounded annotation (ground / apply_annotation on hand-made model output) and,
marked experimental, the relationship-extraction checks. Runs inside a transaction that is rolled back."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import psycopg
import pytest
from psycopg.rows import dict_row

from kl import config
from kl.extract import (AddedMention, Annotation, MentionChoice, ProposedStatement, apply_annotation, build_prompt,
                        candidate_types, check_and_insert, clean_topics, ground, mentions_of, predicate_defs)

MACRO_NOTE = "research/2026-08-21_macro-internal_cvd-reserves.md"
DELTA_NOTE = "updates/2026-10-28/research/2026-10-28_bank-b_corvana-downgrade.md"


@pytest.fixture
def conn():
    c = psycopg.connect(config.admin_dsn())
    try:
        yield c
    finally:
        c.rollback()
        c.close()


def load_doc(conn, source_file: str, skip_hint: str):
    with conn.cursor(row_factory=dict_row) as dcur:
        doc = dcur.execute("select * from documents where source_file = %s", (source_file,)).fetchone()
    if doc is None:
        pytest.skip(skip_hint)
    return doc


def mention(mentions, text: str):
    return next(m for m in mentions if m["text"].lower() == text.lower())


def test_macro_note_mentions_are_grounded(conn):
    doc = load_doc(conn, MACRO_NOTE, "run kl-load")
    with conn.cursor() as cur:
        mentions = mentions_of(cur, doc)
        prompt = build_prompt(cur, doc)
    corvana = mention(mentions, "Corvana")                           # "central bank of Corvana": country or issuer
    assert {i for _, i in corvana["candidates"]} == {"QC", "ISS-0001"}
    assert mention(mentions, "3M NDFs")["candidates"] == [("instrument", "INS-2002")]
    assert mention(mentions, "CVD govt curve")["candidates"] == [("curve", "CVD-GOVT")]
    assert "the 2033" not in {m["text"] for m in mentions}             # no alias: only the model can add it
    assert f"[{corvana['no']}] span \"Corvana\"" in prompt and "KNOWN ENTITIES" in prompt and "summary" in prompt


def test_unambiguous_kept_ambiguous_below_threshold_dropped(conn):
    doc = load_doc(conn, MACRO_NOTE, "run kl-load")
    with conn.cursor() as cur:
        mentions = mentions_of(cur, doc)
        corvana = mention(mentions, "Corvana")
        # the model answers nothing about the unambiguous mentions and is unsure about "Corvana"
        annotation = Annotation(mentions=[MentionChoice(mention_no=corvana["no"], entity_id="ISS-0001", confidence=0.3)],
                                added=[], topics=["fx"], summary="x")
        r = ground(cur, doc, annotation, threshold=0.5)
    assert set(r["about"]["about_instruments"]) >= {"INS-2002", "INS-2003"}       # unambiguous, always kept
    assert r["about"]["about_curves"] == ["CVD-GOVT"]
    entry = next(m for m in r["mentions"] if m["no"] == corvana["no"])
    assert not entry["kept"] and "below threshold" in entry["reason"]
    assert r["counts"]["llm_only"] == 0


def test_ambiguous_choice_above_threshold_and_added_mentions(conn):
    doc = load_doc(conn, MACRO_NOTE, "run kl-load")
    with conn.cursor() as cur:
        mentions = mentions_of(cur, doc)
        corvana = mention(mentions, "Corvana")
        annotation = Annotation(
            mentions=[MentionChoice(mention_no=corvana["no"], entity_id="ISS-0001", confidence=0.9)],
            added=[AddedMention(entity_id="INS-1004", text="the 2033", confidence=0.9),            # verbatim, known
                   AddedMention(entity_id="INS-1003", text="the 2028 bond", confidence=0.9),       # not verbatim
                   AddedMention(entity_id="INS-9999", text="CVGBs", confidence=0.9),               # unknown id
                   AddedMention(entity_id="ISS-0002", text="reserves", confidence=0.2)],           # below threshold
            topics=["FX", " fx ", "Downgrade"], summary=" Reserves note. ")
        r = apply_annotation(cur, doc, annotation, date(2026, 10, 27), threshold=0.5)
        got = cur.execute("select about_issuers, about_instruments, topics, summary, annotated_by from documents "
                          "where document_id = %s", (doc["document_id"],)).fetchone()
    assert "ISS-0001" in r["about"]["about_issuers"]
    assert "INS-1004" in r["about"]["about_instruments"] and "INS-1003" not in r["about"]["about_instruments"]
    assert [a["kept"] for a in r["added"]] == [True, False, False, False]
    assert "not verbatim" in r["added"][1]["reason"] and "unknown" in r["added"][2]["reason"]
    assert "below threshold" in r["added"][3]["reason"]
    assert got[0] == r["about"]["about_issuers"] and "INS-1004" in got[1]
    assert got[2:] == (["fx", "downgrade"], "Reserves note.", "LLM")
    assert r["counts"]["llm_only"] >= 1            # INS-1004; ISS-0001 is also found by the scan ("ROC"), so it is "both"


def test_choice_outside_candidates_is_dropped(conn):
    doc = load_doc(conn, MACRO_NOTE, "run kl-load")
    with conn.cursor() as cur:
        corvana = mention(mentions_of(cur, doc), "Corvana")
        r = ground(cur, doc, Annotation(mentions=[MentionChoice(mention_no=corvana["no"], entity_id="ISS-0009",
                                                                confidence=1.0)], added=[], topics=[], summary=""))
    entry = next(m for m in r["mentions"] if m["no"] == corvana["no"])
    assert not entry["kept"] and "not a candidate" in entry["reason"]


def test_clean_topics():
    assert clean_topics(["FX", " fx ", "Downgrade", "a", "b", "c", "d"]) == ["fx", "downgrade", "a", "b", "c"]


# --- experimental: relationship extraction (off by default, never run by kl-update) ----------------------------

PROPOSED = [
    ProposedStatement(subject_name="Republic of Corvana", predicate="OWNS", object_name="Corvana Telecommunications",
                      value_num=20, quote="the government's stake in Corvana Telecommunications is now 20% "
                                          "following last year's placement"),
    ProposedStatement(subject_name="CorTel", predicate="TRADES_AS_PROXY_FOR", object_name="Republic of Corvana",
                      quote="its bonds have continued to trade with the sovereign"),
    ProposedStatement(subject_name="Corvana Development Bank", predicate="GUARANTEED_BY",
                      object_name="Republic of Corvana", value_text="explicit", quote="given its explicit guarantee"),
    ProposedStatement(subject_name="Corvana National Oil Company", predicate="RATING_CAPPED_BY",
                      object_name="Republic of Corvana",
                      quote="Agency A downgraded the Republic of Corvana to B (outlook Negative)"),   # misquoted
    ProposedStatement(subject_name="Corvana Steel", predicate="GUARANTEED_BY", object_name="Republic of Corvana",
                      quote="we expect it to follow within days"),                                   # unknown entity
    ProposedStatement(subject_name="Corvana Development Bank", predicate="HAS_VIEW", object_name="",
                      quote="we expect it to follow within days"),                                   # gone predicate
]


@pytest.mark.experimental
def test_extraction_check_and_insert(conn):
    doc = load_doc(conn, DELTA_NOTE, "run kl-update data/updates/2026-10-28")
    with conn.cursor() as cur:
        accepted, rejected = check_and_insert(cur, doc, PROPOSED, date(2026, 10, 28))
        assert [(a["subject_id"], a["predicate"], a["object_id"]) for a in accepted] == [
            ("ISS-0001", "OWNS", "ISS-0005"), ("ISS-0005", "TRADES_AS_PROXY_FOR", "ISS-0001"),
            ("ISS-0004", "GUARANTEED_BY", "ISS-0001")]
        assert [r["reason"] for r in rejected] == [
            "quote is not verbatim in the document",
            "subject 'Corvana Steel' resolves to no known entity for GUARANTEED_BY",
            "predicate 'HAS_VIEW' is not allowed"]
        rows = cur.execute("select value_num, as_of, status, method, visibility, source_system from statements "
                           "where document_id = %s and method = 'LLM' order by statement_id",
                           (doc["document_id"],)).fetchall()
        assert len(rows) == 3 and Decimal(20) in {r[0] for r in rows}
        assert {r[1:] for r in rows} == {(date(2026, 10, 28), "PROPOSED", "LLM", "external", "ResearchHub")}
        check_and_insert(cur, doc, PROPOSED[:3], date(2026, 10, 28))               # rerun: unique index, nothing new
        assert cur.execute("select count(*) from statements where document_id = %s and method = 'LLM'",
                           (doc["document_id"],)).fetchone()[0] == 3


@pytest.mark.experimental
def test_candidate_types(conn):
    with conn.cursor() as cur:
        defs = predicate_defs(cur)
    assert candidate_types("ISSUED_BY", defs["ISSUED_BY"][1], "subject") == ["instrument"]
    assert candidate_types("OWNS", defs["OWNS"][1], "object") == ["issuer"]
    assert candidate_types("COUNTRY_OF_RISK", defs["COUNTRY_OF_RISK"][1], "object") == ["country"]
    assert "DENOMINATED_IN" not in defs and "HAS_VIEW" not in defs and "EXPOSED_TO" not in defs
