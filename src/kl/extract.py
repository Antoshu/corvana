"""LLM annotation of one document, grounded in the alias scan. Command: kl-annotate.

The deterministic half is the source of truth: the alias scan of title + text (resolve.scan_mentions) finds every
span that matches a known name and lists the entities it could be. The model is shown each mention with its
context and candidates, and returns, per mention, the chosen entity and a confidence in [0, 1]; it may add
mentions the scan missed when it quotes the verbatim text that names them ("the 2033" -> INS-1004). It also
returns topics and a one-sentence summary (a pointer to the document, never a citation).

What enters about_*: every unambiguous scan match (one candidate) is always kept; an ambiguous mention takes the
model's choice when it is one of the candidates and its confidence is at or above the threshold; an added mention
is kept when its id exists and its text is verbatim in title + text at or above the threshold. Everything else is
dropped and reported with its confidence. Confidences are reported (console, transcripts), never stored.

Relationship extraction (statements from text) is an experiment behind `kl-annotate --extract`: its own prompt
and schema, off by default, never run by kl-update. The checks it uses (check_statements, check_and_insert) are
deterministic and tested.

Who calls what: kl-load never calls the model. kl-annotate annotates the base pack. kl-update annotates a delta's
documents. The key is read by the SDK from the environment only; it is never printed or written.
"""
from __future__ import annotations

import argparse
from datetime import date
from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel

from kl import config
from kl.load import insert, squash, statement
from kl.resolve import (ABOUT_COLUMNS, ENTITY_TYPES, Mention, alias_patterns, document_scan_text, mention_ids,
                        merge_annotation, resolve_any, scan_mentions)

MAX_TOPICS = 5
NAMES_SQL = """
select 'issuer' as t, issuer_id as id, legal_name as name from issuers
union all select 'instrument', instrument_id, description from instruments
union all select 'curve', curve_id, coalesce(description, curve_id) from curves
union all select 'country', code::text, name from country
union all select distinct 'currency', entity_id, entity_id from alias where entity_type = 'currency'
"""


# --- output model ----------------------------------------------------------------------------------------------

class MentionChoice(BaseModel):
    mention_no: int
    entity_id: str | None                        # one of the mention's candidate ids, or null: not a reference
    confidence: float                            # in [0, 1], given the context


class AddedMention(BaseModel):
    entity_id: str                               # a known entity id the scan missed
    text: str                                    # the verbatim text that names it
    confidence: float


class Annotation(BaseModel):
    mentions: list[MentionChoice]
    added: list[AddedMention]
    topics: list[str]
    summary: str


# --- the deterministic half ------------------------------------------------------------------------------------

def _rows(cur: psycopg.Cursor) -> list[tuple]:
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in cur.fetchall()]


def entity_names(cur: psycopg.Cursor) -> dict[tuple[str, str], str]:
    cur.execute(NAMES_SQL)
    return {(t, i): n for t, i, n in _rows(cur)}


def mentions_of(cur: psycopg.Cursor, doc: dict[str, Any]) -> list[Mention]:
    return scan_mentions(document_scan_text(doc), alias_patterns(cur))


def clean_topics(topics: list[str]) -> list[str]:
    out: list[str] = []
    for t in topics:
        t = " ".join(t.lower().split())
        if t and t not in out:
            out.append(t)
    return out[:MAX_TOPICS]


def ground(cur: psycopg.Cursor, doc: dict[str, Any], annotation: Annotation,
           threshold: float = config.ANNOTATE_MIN_CONFIDENCE) -> dict[str, Any]:
    """Decide what enters about_* and why. Returns a report dict: mentions (each with candidates, choice,
    confidence, kept, reason), added (same), the final arrays and the scan-only / LLM-only / both counts.
    Pure: nothing written."""
    mentions = mentions_of(cur, doc)
    names = entity_names(cur)
    choices = {c.mention_no: c for c in annotation.mentions}
    from_scan: set[tuple[str, str]] = set()      # unambiguous matches (always kept)
    from_llm: set[tuple[str, str]] = set()       # the model's contribution: confirmations, choices, additions
    report_mentions = []
    for m in mentions:
        cands = m["candidates"]
        c = choices.get(m["no"])
        entry = {"no": m["no"], "text": m["text"], "context": m["context"],
                 "candidates": [f"{t} {i} ({names.get((t, i), i)})" for t, i in cands],
                 "choice": c.entity_id if c else None, "confidence": c.confidence if c else None}
        if len(cands) == 1:
            from_scan.add(cands[0])
            if c and c.entity_id == cands[0][1] and c.confidence >= threshold:
                from_llm.add(cands[0])
                entry.update(kept=True, reason="unambiguous scan match, confirmed by the model")
            else:
                entry.update(kept=True, reason="unambiguous scan match, always kept; the model "
                             + ("gave no answer" if c is None else
                                f"said {'null' if c.entity_id is None else c.entity_id} (conf {c.confidence:.2f})"))
        elif c is None:
            entry.update(kept=False, reason="ambiguous and the model gave no answer")
        elif c.entity_id is None:
            entry.update(kept=False, reason="model: not a reference to any candidate")
        elif c.entity_id not in {i for _, i in cands}:
            entry.update(kept=False, reason="model chose an id that is not a candidate")
        elif c.confidence < threshold:
            entry.update(kept=False, reason=f"confidence {c.confidence:.2f} below threshold {threshold}")
        else:
            chosen = next(t for t, i in cands if i == c.entity_id)
            from_llm.add((chosen, c.entity_id))
            entry.update(kept=True, reason="model's choice among the candidates")
        report_mentions.append(entry)
    haystack = squash(document_scan_text(doc))
    report_added = []
    for a in annotation.added:
        entry = {"entity_id": a.entity_id, "text": a.text, "confidence": a.confidence}
        kind = next((t for (t, i) in names if i == a.entity_id), None)
        if kind is None:
            entry.update(kept=False, reason="unknown entity id")
        elif kind not in ABOUT_COLUMNS:
            entry.update(kept=False, reason=f"{kind} has no about_* column (reported only)")
        elif not a.text.strip() or squash(a.text) not in haystack:
            entry.update(kept=False, reason="text is not verbatim in title + text")
        elif a.confidence < threshold:
            entry.update(kept=False, reason=f"confidence {a.confidence:.2f} below threshold {threshold}")
        else:
            from_llm.add((kind, a.entity_id))
            entry.update(kept=True, reason="known id, verbatim text")
        report_added.append(entry)
    arrays = merge_annotation(_arrays(from_scan), _arrays(from_llm))
    return {"document_id": doc["document_id"], "source_file": doc["source_file"], "mentions": report_mentions,
            "added": report_added, "about": arrays,
            "counts": {"scan_only": len(from_scan - from_llm), "llm_only": len(from_llm - from_scan),
                       "both": len(from_scan & from_llm)},
            "topics": clean_topics(annotation.topics), "summary": annotation.summary.strip()}


def _arrays(pairs: set[tuple[str, str]]) -> dict[str, list[str]]:
    out: dict[str, set[str]] = {col: set() for col in ABOUT_COLUMNS.values()}
    for t, i in pairs:
        if t in ABOUT_COLUMNS:
            out[ABOUT_COLUMNS[t]].add(i)
    return {col: sorted(ids) for col, ids in out.items()}


def apply_annotation(cur: psycopg.Cursor, doc: dict[str, Any], annotation: Annotation,
                     updated_on: date, threshold: float = config.ANNOTATE_MIN_CONFIDENCE) -> dict[str, Any]:
    """ground(), then write about_*, topics, summary and annotated_by = LLM onto the document row.
    annotated_by = LLM means "the LLM ran"; the unambiguous scan matches are in the arrays regardless."""
    r = ground(cur, doc, annotation, threshold)
    a = r["about"]
    cur.execute("update documents set about_issuers = %s, about_instruments = %s, about_curves = %s, "
                "about_currencies = %s, topics = %s, summary = %s, annotated_by = 'LLM', updated_on = %s "
                "where document_id = %s",
                (a["about_issuers"], a["about_instruments"], a["about_curves"], a["about_currencies"],
                 r["topics"], r["summary"] or None, updated_on, doc["document_id"]))
    return r


# --- the prompt and the call -----------------------------------------------------------------------------------

def build_prompt(cur: psycopg.Cursor, doc: dict[str, Any]) -> str:
    """The grounded annotation prompt: role, input, output format, the numbered mentions with context and
    candidates, the task, and the full known-entity list."""
    mentions = mentions_of(cur, doc)
    names = entity_names(cur)
    cur.execute("select entity_type, entity_id, string_agg(distinct alias, '; ') from alias "
                "where entity_type = any(%s) group by 1, 2 order by 1, 2", (list(ENTITY_TYPES),))
    known = "\n".join(f"- {t} {i} ({names.get((t, i), i)}): {a}" for t, i, a in _rows(cur))
    blocks = []
    for m in mentions:
        cands = "; ".join(f"{t} {i} \"{names.get((t, i), i)}\"" for t, i in m["candidates"])
        tag = "one candidate" if len(m["candidates"]) == 1 else f"{len(m['candidates'])} candidates, choose"
        blocks.append(f"[{m['no']}] span \"{m['text']}\" (chars {m['start']}-{m['end']}; {tag})\n"
                      f"    context: ...{m['context']}...\n"
                      f"    candidates: {cands}")
    grounding = "\n".join(blocks) if blocks else "(the scan found no mention)"
    return f"""You are an expert annotator for a credit knowledge base. Every entity in it is fictional: use only the
candidate entities and the document given here, never outside knowledge or real-world names.

INPUT you receive
1. One document: title, publisher, date and its full text (research note or a desk-chat line).
2. A numbered list of MENTIONS: every span of the title or text that a deterministic scan matched to a known
   name, with about {120} characters of context on each side and the candidate entities (type, id, name) the span
   could refer to. Some spans have one candidate; some have several, e.g. "Corvana" may be the country QC or the
   issuer ISS-0001 Republic of Corvana; a ticker root like CORVAN may be the issuer or part of an instrument's
   ticker; "CNOC" may be ISS-0002 Corvana National Oil Company or its vehicle ISS-0007 CNOC Finance B.V.
3. The full list of KNOWN ENTITIES by id, with every name each is known by.

OUTPUT you return (JSON matching the schema)
- mentions: one item per numbered mention, in order: mention_no; entity_id = the id of the one candidate this
  span refers to in its context, or null when the span is not a reference to any of the candidates (e.g. a word
  that is part of a longer name already covered by another mention, or a different sense); confidence = your
  probability in [0, 1] that entity_id is right given the context (1.0 only when the context leaves no doubt;
  below 0.5 means you would not stake the annotation on it).
- added: mentions the scan MISSED: a known entity the document clearly refers to without using one of its listed
  names. Give entity_id, text = the exact verbatim passage of the title or text that names it, copied character
  for character (e.g. text "the 2033" for the instrument INS-1004 Corvana Government Bond 10.5% 2033), and
  confidence as above. Do not add an entity that is merely related; only one the text itself refers to.
- topics: at most {MAX_TOPICS} lower-case words or short phrases (e.g. downgrade, guarantee, ownership, fx, proxy).
- summary: one sentence saying what the document is about. It is a pointer to the document, never a citation.

MENTIONS found by the scan
{grounding}

TASK: for each mention choose the entity (or null) with a confidence; list the mentions the scan missed with the
verbatim text; give topics and the summary.

KNOWN ENTITIES
{known}

DOCUMENT: {doc.get('title') or doc['source_file']} ({doc.get('publisher')}, {doc['published_at']:%Y-%m-%d})
<document>
{document_scan_text(doc)}
</document>"""


def annotate_document(client: Any, doc: dict[str, Any], cur: psycopg.Cursor) -> Annotation:
    """One structured-output call for the document (annotation only)."""
    response = client.messages.parse(
        model=config.ANNOTATE_MODEL, max_tokens=8000,
        messages=[{"role": "user", "content": build_prompt(cur, doc)}], output_format=Annotation)
    if response.stop_reason == "refusal":
        raise RuntimeError(f"annotation refused for {doc['source_file']}: {response.stop_details}")
    if response.parsed_output is None:
        raise RuntimeError(f"annotation returned no parsable output for {doc['source_file']} "
                           f"(stop_reason {response.stop_reason})")
    return response.parsed_output


def annotate(client: Any, cur: psycopg.Cursor, doc: dict[str, Any], updated_on: date) -> dict[str, Any]:
    """Call the model and apply the grounded annotation. Returns the report dict."""
    return apply_annotation(cur, doc, annotate_document(client, doc, cur), updated_on)


def describe(r: dict[str, Any]) -> list[str]:
    """Markdown lines for one document's annotation report: every mention with candidates, choice and
    confidence; added mentions; what was dropped and why; the final arrays with their provenance counts."""
    c = r["counts"]
    about = {col: ids for col, ids in r["about"].items() if ids}
    lines = [f"### document {r['document_id']} `{r['source_file']}`", "",
             f"- about_* ids: {sum(len(v) for v in about.values())} (scan only {c['scan_only']}, LLM only "
             f"{c['llm_only']}, both {c['both']}; both = unambiguous match the model confirmed, LLM only = its "
             f"choice on an ambiguous span or an added mention)"
             + (": " + "; ".join(f"{col} {', '.join(ids)}" for col, ids in about.items()) if about else ""),
             f"- topics: {', '.join(r['topics']) or 'none'}",
             f"- summary (pointer, not a citation): {r['summary']}",
             "- mentions:"]
    for m in r["mentions"]:
        conf = "" if m["confidence"] is None else f" conf {m['confidence']:.2f}"
        lines.append(f"  - [{m['no']}] \"{m['text']}\" -> {m['choice'] or 'null'}{conf}: "
                     f"{'kept' if m['kept'] else 'DROPPED'} ({m['reason']}); candidates: {'; '.join(m['candidates'])}")
    if r["added"]:
        lines.append("- added by the model:")
        for a in r["added"]:
            lines.append(f"  - {a['entity_id']} \"{a['text']}\" conf {a['confidence']:.2f}: "
                         f"{'kept' if a['kept'] else 'DROPPED'} ({a['reason']})")
    return lines + [""]


# --- experimental: relationship extraction --------------------------------------------------------------------

NOT_EXTRACTED = {"DENOMINATED_IN", "PRICED_OFF", "CURRENCY_OF", "SOVEREIGN_IS"}
SUBJECT_TYPES = {"ISSUED_BY": ["instrument"], "REFERENCES_CREDIT": ["instrument"]}
PERCENT = {"OWNS"}
HOLDS_FALSE_OK = {"TRADES_AS_PROXY_FOR", "CORRELATED_WITH"}


class ProposedStatement(BaseModel):
    subject_name: str
    predicate: str
    object_name: str
    value_num: float | None = None
    value_text: str | None = None
    holds: bool = True
    as_of: str | None = None                     # YYYY-MM-DD, only when the text dates the fact
    quote: str


class Extraction(BaseModel):
    statements: list[ProposedStatement]


def predicate_defs(cur: psycopg.Cursor) -> dict[str, tuple[str, str]]:
    """{predicate: (direction, description)} for the predicates extraction may use."""
    cur.execute("select predicate, direction, description from predicate_def order by predicate")
    return {p: (d, desc) for p, d, desc in _rows(cur) if p not in NOT_EXTRACTED}


def candidate_types(predicate: str, description: str, side: Literal["subject", "object"]) -> list[str]:
    """Entity types to try for one side of a predicate, read from its description; issuer first."""
    if side == "subject" and predicate in SUBJECT_TYPES:
        return SUBJECT_TYPES[predicate]
    left, _, right = description.partition("->")
    text = left if side == "subject" else right.split(";")[0]
    named = [t for t in ENTITY_TYPES if t in text]
    return named or ["issuer"]                   # "owner -> owned" is issuers


def check(cur: psycopg.Cursor, doc: dict[str, Any], p: ProposedStatement,
          defs: dict[str, tuple[str, str]]) -> tuple[list[str], dict[str, Any]]:
    """Reasons the statement fails the auto-check (empty if it passes) and the resolved fields."""
    reasons: list[str] = []
    fields: dict[str, Any] = {}
    if p.predicate not in defs:
        return [f"predicate {p.predicate!r} is not allowed"], fields
    _direction, description = defs[p.predicate]
    subject = resolve_any(cur, candidate_types(p.predicate, description, "subject"), p.subject_name)
    if subject is None:
        reasons.append(f"subject {p.subject_name!r} resolves to no known entity for {p.predicate}")
    else:
        fields.update(subject_type=subject[0], subject_id=subject[1])
    obj = resolve_any(cur, candidate_types(p.predicate, description, "object"), p.object_name) if p.object_name else None
    if obj is None:
        reasons.append(f"object {p.object_name!r} resolves to no known entity for {p.predicate}")
    else:
        fields.update(object_type=obj[0], object_id=obj[1])
    if not p.quote.strip() or squash(p.quote) not in squash(doc["text"]):
        reasons.append("quote is not verbatim in the document")
    if p.predicate in PERCENT and p.value_num is not None and not 0 <= p.value_num <= 100:
        reasons.append(f"{p.predicate} value {p.value_num} outside 0-100")
    if not p.holds and p.predicate not in HOLDS_FALSE_OK:
        reasons.append(f"holds=false is only allowed on {', '.join(sorted(HOLDS_FALSE_OK))}")
    if p.as_of:
        try:
            fields["as_of"] = date.fromisoformat(p.as_of)
        except ValueError:
            reasons.append(f"as_of {p.as_of!r} is not YYYY-MM-DD")
    return reasons, fields


def check_statements(cur: psycopg.Cursor, doc: dict[str, Any], proposed: list[ProposedStatement],
                     batch_date: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Auto-check each proposed statement: (rows that pass, built as PROPOSED LLM statements; rejects with reason).
    Nothing is written."""
    defs = predicate_defs(cur)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for p in proposed:
        reasons, fields = check(cur, doc, p, defs)
        if reasons:
            rejected.append({"raw": p.model_dump(), "reason": "; ".join(reasons)})
            continue
        accepted.append(statement(
            predicate=p.predicate, value_num=p.value_num, value_text=p.value_text, holds=p.holds,
            as_of=fields.pop("as_of", doc["published_at"].date()), source_system=doc["source_system"],
            source_file=doc["source_file"], document_id=doc["document_id"], quote=p.quote, method="LLM",
            status="PROPOSED", visibility=doc["visibility"], updated_on=batch_date, **fields))
    return accepted, rejected


def check_and_insert(cur: psycopg.Cursor, doc: dict[str, Any], proposed: list[ProposedStatement],
                     batch_date: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """check_statements, then insert the passes as PROPOSED statements (reruns hit the unique index and do nothing)."""
    accepted, rejected = check_statements(cur, doc, proposed, batch_date)
    insert(cur, "statements", accepted, on_conflict=True)
    return accepted, rejected


def build_extraction_prompt(cur: psycopg.Cursor, doc: dict[str, Any]) -> str:
    """The experimental relationship-extraction prompt (unchanged design; measured, not used by default)."""
    defs = predicate_defs(cur)
    cur.execute("select entity_type, entity_id, string_agg(distinct alias, '; ') from alias "
                "where entity_type = any(%s) group by 1, 2 order by 1, 2", (list(ENTITY_TYPES),))
    names = "\n".join(f"- {t} {i}: {a}" for t, i, a in _rows(cur))
    predicates = "\n".join(f"- {p}: {desc}" for p, (_, desc) in defs.items())
    return f"""Extract relationship statements from the research document below for a credit knowledge base.

Allowed predicates (use only these):
{predicates}

Known entities, by id, with every name they are known by:
{names}

Rules:
- One statement per relationship between two known entities that the text states. Opinions, forecasts and
  recommendations are not statements. Do not infer facts the text does not state.
- subject_name and object_name must be one of the listed names, copied exactly.
- quote must be copied verbatim from the text: a contiguous passage that supports the statement.
- OWNS: subject is the owner, object the owned entity, value_num the stake in percent.
- holds=false records an explicit denial (e.g. "does not trade as a proxy"); use it only when the text denies the link.
- Set as_of (YYYY-MM-DD) only when the text dates the fact itself; otherwise leave it null.

Document: {doc.get('title') or doc['source_file']} ({doc.get('publisher')}, {doc['published_at']:%Y-%m-%d})

<document>
{doc['text']}
</document>"""


def extract_document(client: Any, doc: dict[str, Any], cur: psycopg.Cursor) -> Extraction:
    """One structured-output call proposing relationship statements (experimental)."""
    response = client.messages.parse(
        model=config.ANNOTATE_MODEL, max_tokens=8000,
        messages=[{"role": "user", "content": build_extraction_prompt(cur, doc)}], output_format=Extraction)
    if response.stop_reason == "refusal":
        raise RuntimeError(f"extraction refused for {doc['source_file']}: {response.stop_details}")
    if response.parsed_output is None:
        raise RuntimeError(f"extraction returned no parsable output for {doc['source_file']} "
                           f"(stop_reason {response.stop_reason})")
    return response.parsed_output


# --- kl-annotate -----------------------------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Grounded LLM annotation of documents (about_*, topics, summary).")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--all", action="store_true", help="every document")
    which.add_argument("--missing", action="store_true", help="documents not yet annotated by the LLM")
    which.add_argument("--document", type=int, help="one document id")
    parser.add_argument("--extract", action="store_true",
                        help="EXPERIMENTAL: also run relationship extraction and store the statements that pass the auto-check")
    parser.add_argument("--as-of", type=date.fromisoformat, default=config.AS_OF, help="updated_on for the rows")
    args = parser.parse_args()
    if not config.llm_available():
        raise SystemExit("kl-annotate needs ANTHROPIC_API_KEY (put it in .env); the alias-scan annotation from "
                         "kl-load stays in place without it")
    import anthropic

    client = anthropic.Anthropic()
    where = "where annotated_by <> 'LLM'" if args.missing else "where document_id = %s" if args.document else ""
    params = (args.document,) if args.document else ()
    lines = [f"# Grounded LLM annotation ({config.ANNOTATE_MODEL}), threshold {config.ANNOTATE_MIN_CONFIDENCE}, "
             f"updated_on {args.as_of}", ""]
    with psycopg.connect(config.admin_dsn(), autocommit=True) as conn:
        with conn.cursor(row_factory=dict_row) as dcur:
            docs = dcur.execute(f"select * from documents {where} order by document_id", params).fetchall()
        print(f"annotating {len(docs)} document(s) with {config.ANNOTATE_MODEL}")
        for doc in docs:
            with conn.transaction(), conn.cursor() as cur:
                block = describe(annotate(client, cur, doc, args.as_of))
                if args.extract:
                    accepted, rejected = check_and_insert(cur, doc, extract_document(client, doc, cur).statements,
                                                          args.as_of)
                    block.insert(-1, f"- EXPERIMENTAL extraction: {len(accepted)} statement(s) stored as PROPOSED, "
                                     f"{len(rejected)} rejected")
                    block[-1:-1] = [f"  - ok: {a['subject_id']} {a['predicate']} {a['object_id']}: \"{a['quote']}\""
                                    for a in accepted]
                    block[-1:-1] = [f"  - rejected: {x['raw']['subject_name']} {x['raw']['predicate']} "
                                    f"{x['raw']['object_name']}: {x['reason']}" for x in rejected]
            print("\n".join(block))
            lines += block
    config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.TRANSCRIPTS_DIR / "annotate.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"written to {out}")


if __name__ == "__main__":
    main()
