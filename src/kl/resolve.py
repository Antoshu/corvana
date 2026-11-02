"""Name resolution through the alias view, and the deterministic alias scan that annotates a document.

Exact match on lower(alias) within an entity type; no fuzzy matching. A name that maps to no entity, or to more
than one, resolves to None: the caller reports it (UNRESOLVED_NAME, a dropped annotation) and never guesses.
"""
from __future__ import annotations

import html
import re
from typing import Any

import psycopg

ENTITY_TYPES = ("issuer", "instrument", "curve", "country", "currency")
ABOUT_COLUMNS = {"issuer": "about_issuers", "instrument": "about_instruments", "curve": "about_curves",
                 "currency": "about_currencies"}
REF_COLUMN = {"ISIN": "isin", "INTERNAL": "instrument_id", "TICKER": "ticker"}
MIN_SCAN_LENGTH = 3                       # "US", "UK", "QC" are too short to scan for in prose


def _values(row: Any) -> list[Any]:
    return list(row.values()) if isinstance(row, dict) else list(row)


def resolve(cur: psycopg.Cursor, entity_type: str, name: str) -> str | None:
    """The one entity id of this type whose alias equals `name` case-insensitively, or None."""
    cur.execute("select distinct entity_id from alias where entity_type = %s and lower(alias) = lower(%s)",
                (entity_type, name.strip()))
    rows = cur.fetchall()
    return _values(rows[0])[0] if len(rows) == 1 else None


def resolve_any(cur: psycopg.Cursor, types: list[str] | tuple[str, ...], name: str) -> tuple[str, str] | None:
    """(entity_type, entity_id) for the first type in `types` that resolves the name."""
    for t in types:
        entity_id = resolve(cur, t, name)
        if entity_id is not None:
            return t, entity_id
    return None


def find_instrument(cur: psycopg.Cursor, ref: str, ref_type: str) -> str | None:
    """Resolve an OMS instrument reference by the identifier kind it declares (ISIN, INTERNAL, TICKER)."""
    column = REF_COLUMN.get(ref_type.upper())
    if column is None:
        raise ValueError(f"unknown ref_type {ref_type!r}")
    cur.execute(f"select instrument_id from instruments where {column} = %s", (ref,))
    row = cur.fetchone()
    return _values(row)[0] if row else None


def alias_patterns(cur: psycopg.Cursor) -> list[tuple[str, str, str, re.Pattern[str]]]:
    """Every alias of 3+ characters as a case-insensitive whole-word pattern: (entity_type, entity_id, alias, re)."""
    cur.execute("select entity_type, entity_id, alias from alias where length(alias) >= %s "
                "order by entity_type, entity_id, alias", (MIN_SCAN_LENGTH,))
    return [(t, i, a, re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)", re.IGNORECASE))
            for t, i, a in (_values(r) for r in cur.fetchall())]


CONTEXT_CHARS = 120


class Mention(dict):
    """One span the alias scan found: {no, start, end, text, context, candidates: [(entity_type, entity_id)]}.
    A plain dict subclass so it serialises and prints without ceremony."""


def scan_mentions(text: str, patterns: list[tuple[str, str, str, re.Pattern[str]]]) -> list[Mention]:
    """The alias scan, as mentions. Within an entity type, longest alias first, and a shorter alias does not match
    inside a span a longer one already claimed ("Corvana" inside "Corvana Telecommunications" is CorTel, not the
    Republic). Types are scanned independently, so the instrument "CDB 27s" does not hide the issuer "CDB".
    Spans that coincide across types become one mention with several candidates ("Corvana" -> country QC or
    issuer ISS-0001). Deterministic; no key needed."""
    by_type: dict[str, dict[str, tuple[re.Pattern[str], list[str]]]] = {}
    for entity_type, entity_id, alias, pattern in patterns:
        entry = by_type.setdefault(entity_type, {}).setdefault(alias.lower(), (pattern, []))
        if entity_id not in entry[1]:
            entry[1].append(entity_id)
    by_span: dict[tuple[int, int], list[tuple[str, str]]] = {}
    for entity_type in sorted(by_type):
        aliases = by_type[entity_type]
        claimed: list[tuple[int, int]] = []
        for alias in sorted(aliases, key=lambda a: (-len(a), a)):
            pattern, ids = aliases[alias]
            spans = [m.span() for m in pattern.finditer(text)
                     if not any(s < m.end() and m.start() < e for s, e in claimed)]
            claimed += spans
            for span in spans:
                by_span.setdefault(span, []).extend((entity_type, i) for i in ids)
    out: list[Mention] = []
    for no, (start, end) in enumerate(sorted(by_span), start=1):
        out.append(Mention(no=no, start=start, end=end, text=text[start:end],
                           context=" ".join(text[max(0, start - CONTEXT_CHARS):end + CONTEXT_CHARS].split()),
                           candidates=sorted(set(by_span[(start, end)]))))
    return out


def mention_ids(mentions: list[Mention], unambiguous_only: bool = False) -> dict[str, list[str]]:
    """about_* arrays from mentions: every candidate, or only those of mentions with exactly one candidate."""
    found: dict[str, set[str]] = {col: set() for col in ABOUT_COLUMNS.values()}
    for m in mentions:
        if unambiguous_only and len(m["candidates"]) != 1:
            continue
        for entity_type, entity_id in m["candidates"]:
            col = ABOUT_COLUMNS.get(entity_type)
            if col:
                found[col].add(entity_id)
    return {col: sorted(ids) for col, ids in found.items()}


def rule_annotation(text: str, patterns: list[tuple[str, str, str, re.Pattern[str]]]) -> dict[str, list[str]]:
    """The deterministic annotation: {about_issuers: [...], about_instruments: [...], about_curves: [...],
    about_currencies: [...]} with every candidate of every mention the scan finds (an ambiguous span tags all its
    candidates; the LLM annotator later picks one)."""
    return mention_ids(scan_mentions(text, patterns))


DOTTED_ABBREVIATION = re.compile(r"(?<![\w.])(?:[A-Za-z]\.){2,}")


def normalise_for_scan(text: str) -> str:
    """HTML entities decoded ("Power &amp; Light" -> "Power & Light") and dotted abbreviations closed up
    ("C.N.O.C." -> "CNOC"), so a name written that way meets its alias. Only what the scan reads; the stored text
    is untouched."""
    return DOTTED_ABBREVIATION.sub(lambda m: m.group(0).replace(".", ""), html.unescape(text))


def document_scan_text(doc: dict[str, Any]) -> str:
    """What the alias scan reads: the title (research notes name their subject there) and the text, normalised."""
    return normalise_for_scan(f"{doc.get('title') or ''}\n{doc['text']}")


def merge_annotation(*parts: dict[str, list[str]]) -> dict[str, list[str]]:
    """about_* = union of several {about_*: ids} dicts."""
    return {col: sorted({i for p in parts for i in p.get(col, [])}) for col in ABOUT_COLUMNS.values()}
