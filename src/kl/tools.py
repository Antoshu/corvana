"""Typed tool functions over the knowledge layer.

Every function takes the asking user first. Entitlements are enforced by Postgres: each call runs under
SET ROLE <user>, so row-level security and the security_invoker views decide what is visible. Nothing is
filtered for visibility in Python.

Citations are statement ids (a row in statements) or edge ids (a level-1 link projected by the edges view,
e.g. instruments:INS-1004:issuer_id) plus the document text. A document's summary and topics are pointers to
the document, never citations.

Summary first: get_exposure returns a summary by default (one edge id per hop, flag kinds, ranked research
without text); get_path and get_document are the drill-downs. Unresolved holdings are returned apart from the
exposed/not-exposed positions so "cannot tell" is never read as "no". Research is ranked in SQL
(research_for_paths), never in Python.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import BaseModel

from kl import config

HIGH_STATUS = ("REFERENCE", "INFERRED", "CONFIRMED")
STATUS_RANK = {"CONFIRMED": 3, "REFERENCE": 2, "INFERRED": 2}          # as in current_statements; PROPOSED is 1
# A path ending in SOVEREIGN_IS is keyed by its whole tail through these (country, currency or curve route).
SOVEREIGN_TAIL = {"SOVEREIGN_IS", "CURRENCY_OF", "DENOMINATED_IN", "PRICED_OFF", "COUNTRY_OF_RISK"}
LABELS = {
    "REFERENCES_CREDIT": "CDS protection referencing the sovereign",
    "GUARANTEED_BY": "guaranteed by {to}",
    "OWNS": "state-owned ({value}% stake)",
    "FINANCING_VEHICLE_OF": "financing vehicle of {to}",
    "COUNTRY_OF_RISK": "country of risk is the sovereign's",
    "DENOMINATED_IN": "denominated in the sovereign's currency",
    "PRICED_OFF": "priced off the sovereign's rates curve",
    "TRADES_AS_PROXY_FOR": "trades as a sovereign proxy",
    "BETA_TO": "spread beta {value} to the sovereign",
    "CORRELATED_WITH": "correlation {value} with the sovereign",
    "RATING_CAPPED_BY": "rating capped at the sovereign",
}
# Channel order in a position: specific links first, the generic country/currency routes last.
CHANNEL_ORDER = ["ISSUED_BY", "REFERENCES_CREDIT", "GUARANTEED_BY", "OWNS", "FINANCING_VEHICLE_OF", "RATING_CAPPED_BY",
                 "BETA_TO", "TRADES_AS_PROXY_FOR", "CORRELATED_WITH", "PRICED_OFF", "DENOMINATED_IN", "COUNTRY_OF_RISK"]
NOTES = ["derivative sign convention is undocumented; quantities reported as in the OMS"]
IDENTIFIER_COLUMNS = {"isin", "ticker", "id"}
EXACT_COLUMNS = {"legal_name", "name", "curve_id", "currency"}
NAMES_SQL = """
select 'issuer' as t, issuer_id as id, legal_name as name from issuers
union all select 'instrument', instrument_id, description from instruments
union all select 'curve', curve_id, coalesce(description, curve_id) from curves
union all select 'country', code::text, name from country
union all select distinct 'currency', entity_id, entity_id from alias where entity_type = 'currency'
"""
ABOUT = {"issuer": "about_issuers", "instrument": "about_instruments", "curve": "about_curves",
         "currency": "about_currencies"}
DOC_COLUMNS = ("document_id", "source_system", "source_file", "kind", "title", "publisher", "author", "published_at",
               "visibility", "about_issuers", "about_instruments", "about_curves", "about_currencies",
               "topics", "summary", "annotated_by")


# --- models ----------------------------------------------------------------------------------------------------

class Citation(BaseModel):
    statement_id: int | None                     # null for a level-1 edge
    edge_id: str                                 # 'stmt:<id>' or e.g. 'instruments:INS-1004:issuer_id'
    predicate: str
    source_system: str
    source_file: str
    document_title: str | None
    published_at: datetime | None
    as_of: date
    quote: str | None                            # verbatim document text, the rule, or the raw name column
    status: str
    method: str | None                           # RULE | MANUAL | LLM; null for a level-1 edge
    visibility: str | None
    tier: int


class EntityMatch(BaseModel):
    entity_type: str
    entity_id: str
    name: str
    matched_alias: str
    match_kind: Literal["exact", "alias", "identifier"]


class Position(BaseModel):
    book: str
    instrument_ref: str
    ref_type: str
    quantity: Decimal
    notional_ccy: str
    as_of_date: date
    instrument_id: str | None
    description: str | None
    instrument_type: str | None
    resolution_note: str


class Hop(BaseModel):
    from_node: str
    predicate: str
    to_node: str
    grade: Literal["high", "low"]
    citations: list[Citation]


class Channel(BaseModel):
    key: str                                     # terminal predicate(s), e.g. OWNS or COUNTRY_OF_RISK>SOVEREIGN_IS
    label: str
    grade: Literal["high", "low"]
    hops: list[Hop]                              # the representative path
    paths_considered: int                        # paths with this key; one is shown


class ChannelSummary(BaseModel):
    key: str
    label: str
    grade: Literal["high", "low"]
    hop_count: int
    edge_ids: list[str]                          # one per hop of the representative path: the edge precedence picks
    paths_considered: int


class PathReport(Channel):
    """get_path: one channel of one instrument with every citation (the drill-down behind a ChannelSummary)."""
    user: str
    as_of: date
    instrument_id: str
    target_id: str


class QualityFlag(BaseModel):
    kind: str
    subject: str
    edge_id: str | None
    other_edge_id: str | None
    message: str


class PositionExposure(BaseModel):
    position: Position
    exposed: Literal["yes", "unconfirmed", "no"]
    channels: list[Channel]
    flags: list[QualityFlag]


class FlagSummary(BaseModel):
    kind: str
    message: str


class PositionSummary(BaseModel):
    position: Position
    exposed: Literal["yes", "unconfirmed", "no"]
    channels: list[ChannelSummary]
    flags: list[FlagSummary]


class Unresolved(BaseModel):
    """A holding the layer could not identify: real money, never resolved by guess, never counted as 'no'."""
    position: Position
    flag_message: str                            # the UNRESOLVED_REF message, with the nearest-match hint if any


class Statement(BaseModel):
    statement_id: int | None
    edge_id: str
    subject_type: str
    subject_id: str
    predicate: str
    object_type: str
    object_id: str
    value_num: Decimal | None
    value_text: str | None
    holds: bool
    as_of: date
    status: str
    method: str | None
    visibility: str | None
    tier: int
    source_system: str
    source_file: str
    document_title: str | None
    published_at: datetime | None
    quote: str | None
    hidden_newer_count: int = 0                  # on a current row: newer statements on this link the user cannot see


class StatementSet(BaseModel):
    entity_id: str
    predicate: str | None
    as_of: date
    current: list[Statement]
    other_sources: list[Statement]
    flags: list[QualityFlag]
    hidden_newer_count: int


class DocumentSummary(BaseModel):
    """A document without its text: what it is about, topics and the one-line summary (pointers, not citations)."""
    document_id: int
    source_system: str
    source_file: str
    kind: str
    title: str | None
    publisher: str | None
    author: str | None
    published_at: datetime
    visibility: str | None
    about_issuers: list[str]
    about_instruments: list[str]
    about_curves: list[str]
    about_currencies: list[str]
    topics: list[str]
    summary: str | None                          # a pointer to the document, never a citation
    annotated_by: str                            # RULE (alias scan) or LLM


class Document(DocumentSummary):
    text: str                                    # the only citable content of a document


class ResearchSummary(BaseModel):
    """One ranked document in an exposure summary; fetch the text with get_document before quoting it."""
    document_id: int
    title: str | None
    publisher: str | None
    published_at: datetime
    visibility: str | None
    summary: str | None
    topics: list[str]
    about_on_path: list[str]                     # entity ids on the user's paths that the document is about


class RatingEvent(BaseModel):
    agency: str
    rating: str
    outlook: str
    action_date: date
    rank: int | None


class RatingHistory(BaseModel):
    issuer_id: str
    current: RatingEvent | None
    history: list[RatingEvent]
    sovereign_issuer_id: str | None
    sovereign_current: RatingEvent | None
    notches_vs_sovereign: int | None


class ExposureSummary(BaseModel):
    """get_exposure(detail='summary'): verdicts, channel keys with one edge id per hop, flag kinds, unresolved
    holdings apart, ranked research without text."""
    user: str
    as_of: date
    target: EntityMatch
    target_rating: RatingHistory | None
    positions: list[PositionSummary]
    positions_omitted: int = 0                   # resolved positions beyond max_positions (least exposed first)
    unresolved: list[Unresolved]
    research: list[ResearchSummary]
    notes: list[str]


class ExposureReport(BaseModel):
    """get_exposure(detail='full'): every hop with every citation and the ranked documents with their text."""
    user: str
    as_of: date
    target: EntityMatch
    target_rating: RatingHistory | None
    positions: list[PositionExposure]
    unresolved: list[Unresolved]
    research: list[Document]
    notes: list[str]


# --- connection and helpers ------------------------------------------------------------------------------------

def connect() -> psycopg.Connection:
    """Admin connection; every query must still run inside as_user()."""
    return psycopg.connect(config.admin_dsn(), autocommit=True, row_factory=dict_row)


@contextmanager
def as_user(conn: psycopg.Connection, user: str) -> Iterator[psycopg.Cursor]:
    """SET ROLE to a user listed in entitlements for the duration of the block."""
    with conn.cursor() as cur:
        cur.execute("select 1 from entitlements where username = %s", (user,))
        if cur.fetchone() is None:
            raise ValueError(f"unknown user {user!r}: not in entitlements")
        cur.execute(sql.SQL("set role {}").format(sql.Identifier(user)))
        try:
            yield cur
        finally:
            cur.execute("reset role")


def _all(cur: psycopg.Cursor, query: str, params: Any = ()) -> list[dict[str, Any]]:
    cur.execute(query, params)
    return cur.fetchall()


def _names(cur: psycopg.Cursor) -> dict[tuple[str, str], str]:
    return {(r["t"], r["id"]): r["name"] for r in _all(cur, NAMES_SQL)}


def _entity_type(cur: psycopg.Cursor, entity_id: str) -> str:
    """The type of an entity id (issuer preferred when a code is shared); unknown ids are an error."""
    rows = _all(cur, "select distinct entity_type from alias where entity_id = %s", (entity_id,))
    if not rows:
        raise ValueError(f"unknown entity id {entity_id!r}; use find_entity to look up a name")
    types = [r["entity_type"] for r in rows]
    return "issuer" if "issuer" in types else sorted(types)[0]


def _match_kind(name_column: str, alias: str, name: str) -> Literal["exact", "alias", "identifier"]:
    if name_column in IDENTIFIER_COLUMNS:
        return "identifier"
    return "exact" if name_column in EXACT_COLUMNS or alias.lower() == name.lower() else "alias"


def _flag(row: dict[str, Any]) -> QualityFlag:
    return QualityFlag(kind=row["kind"], subject=row["subject"], edge_id=row["edge_id"],
                       other_edge_id=row["other_edge_id"], message=row["message"])


def _fmt(value: Decimal | None) -> str:
    return "?" if value is None else f"{value.normalize():f}"


# --- tools -----------------------------------------------------------------------------------------------------

def find_entity(user: str, query: str, as_of: date | None = None) -> list[EntityMatch]:
    """Look up a name: exact match on any alias, id, ISIN or ticker first, then a substring match on aliases.

    as_of is accepted for a uniform signature; aliases are not versioned in time.
    """
    with connect() as conn, as_user(conn, user) as cur:
        return _find_entity(cur, query)


def _find_entity(cur: psycopg.Cursor, query: str) -> list[EntityMatch]:
    names = _names(cur)
    rows = _all(cur, "select distinct on (entity_type, entity_id) entity_type, entity_id, alias, name_column "
                     "from alias where lower(alias) = lower(%s) order by entity_type, entity_id, name_column", (query,))
    if not rows:
        rows = _all(cur, "select distinct on (entity_type, entity_id) entity_type, entity_id, alias, name_column "
                         "from alias where alias ilike %s order by entity_type, entity_id, length(alias)",
                    (f"%{query}%",))
        return [EntityMatch(entity_type=r["entity_type"], entity_id=r["entity_id"],
                            name=names.get((r["entity_type"], r["entity_id"]), r["entity_id"]),
                            matched_alias=r["alias"], match_kind="alias") for r in rows]
    return [EntityMatch(entity_type=r["entity_type"], entity_id=r["entity_id"],
                        name=names.get((r["entity_type"], r["entity_id"]), r["entity_id"]),
                        matched_alias=r["alias"],
                        match_kind=_match_kind(r["name_column"], r["alias"],
                                               names.get((r["entity_type"], r["entity_id"]), "")))
            for r in rows]


def get_positions(user: str, as_of: date | None = None) -> list[Position]:
    """The user's positions on the latest position date on or before as_of, each resolved or explicitly not."""
    with connect() as conn, as_user(conn, user) as cur:
        return _positions(cur, as_of or config.AS_OF)


def _positions(cur: psycopg.Cursor, as_of: date) -> list[Position]:
    # Per book, the latest position date on or before as_of among rows known by then (positions_as_of). An
    # instrument that arrived after as_of was not known on that date: point in time.
    rows = _all(cur, "select p.*, p.instrument_updated_on > known_by(%s) as unknown_then "
                     "from positions_as_of(%s) p order by book, instrument_ref", (as_of, as_of))
    out = []
    for r in rows:
        known = r["instrument_id"] is not None and not r["unknown_then"]
        note = (f"resolved by {r['ref_type']}" if known else
                f"matches no instrument known on {as_of}; not guessed" if r["instrument_id"] else
                "matches no instrument; not guessed")
        out.append(Position(book=r["book"], instrument_ref=r["instrument_ref"], ref_type=r["ref_type"],
                            quantity=r["quantity"], notional_ccy=r["notional_ccy"], as_of_date=r["as_of_date"],
                            instrument_id=r["instrument_id"] if known else None,
                            description=r["instrument_description"] if known else None,
                            instrument_type=r["instrument_type"] if known else None, resolution_note=note))
    return out


def _citations(cur: psycopg.Cursor, edge_ids: list[str]) -> dict[str, tuple[Citation, dict[str, Any]]]:
    rows = _all(cur, "select e.*, d.title as document_title, d.published_at from edges e "
                     "left join documents d on d.document_id = e.document_id where e.edge_id = any(%s)", (edge_ids,))
    return {r["edge_id"]: (Citation.model_validate(r), r) for r in rows}


def _best(edges: list[dict[str, Any]]) -> dict[str, Any]:
    """The edge the precedence rule would pick: status rank, then source tier, then latest as_of, then edge id."""
    return max(edges, key=lambda e: (STATUS_RANK.get(e["status"], 1), e["tier"], e["as_of"], e["edge_id"]))


def _key_start(predicates: list[str]) -> int:
    """Index of the first hop of the channel key: the last hop, or the whole sovereign tail."""
    i = len(predicates) - 1
    if predicates[i] == "SOVEREIGN_IS":
        while i > 0 and predicates[i - 1] in SOVEREIGN_TAIL:
            i -= 1
    return i


def _channels(paths: list[dict[str, Any]], cites: dict[str, tuple[Citation, dict[str, Any]]],
              names: dict[tuple[str, str], str]) -> list[Channel]:
    """Group one instrument's paths by channel key; keep the best path per key (all-high first, then shortest)."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for p in paths:
        groups.setdefault(">".join(p["predicates"][_key_start(p["predicates"]):]), []).append(p)
    out = []
    for key, group in groups.items():
        rep = min(group, key=lambda p: ("low" in p["hop_grades"], p["depth"], p["predicates"]))
        hops = []
        for i, pred in enumerate(rep["predicates"]):
            found = [cites[e] for e in rep["hop_edge_ids"][i].split(",") if e in cites]
            hops.append(Hop(from_node=rep["nodes"][i], predicate=pred, to_node=rep["nodes"][i + 1],
                            grade=rep["hop_grades"][i], citations=[c for c, _ in found]))
        start = _key_start(rep["predicates"])
        first = hops[start]
        if first.predicate == "ISSUED_BY":
            label = "issued by the sovereign"
        else:
            edges = [r for e in rep["hop_edge_ids"][start].split(",") if e in cites for r in [cites[e][1]]]
            value = _best(edges)["value_num"] if edges else None
            label = LABELS.get(first.predicate, first.predicate.lower()).format(
                to=names.get(tuple(first.to_node.split(":", 1)), first.to_node), value=_fmt(value))
        via = [names.get(tuple(n.split(":", 1)), n) for n in rep["nodes"][1:start + 1]]
        own_issuer_only = start == 1 and rep["predicates"][0] == "ISSUED_BY"
        if via and not own_issuer_only:
            label += " via " + " -> ".join(via)
        grade = "low" if "low" in rep["hop_grades"] else "high"
        out.append(Channel(key=key, label=label, grade=grade, hops=hops, paths_considered=len(group)))
    rank = {p: i for i, p in enumerate(CHANNEL_ORDER)}
    return sorted(out, key=lambda c: (rank.get(c.key.split(">")[0], len(rank)), c.grade != "high", c.key))


def _path_ids(nodes: set[str]) -> list[str]:
    """The entity ids among 'type:id' nodes that a document can be about (issuer, instrument, curve, currency)."""
    return sorted({n.split(":", 1)[1] for n in nodes if n.split(":", 1)[0] in ABOUT})


def _research_for_paths(cur: psycopg.Cursor, ids: list[str], as_of: date, limit: int | None) -> list[dict[str, Any]]:
    """Visible documents about any of the ids, ranked and capped by research_for_paths in SQL (no ranking here)."""
    return _all(cur, "select * from research_for_paths(%s, %s, %s)", (ids, as_of, limit))


def _summary_channel(c: Channel) -> ChannelSummary:
    """One edge id per hop: the edge the precedence rule would pick among the hop's citations."""
    picks = [_best([ci.model_dump() for ci in h.citations])["edge_id"] if h.citations else "" for h in c.hops]
    return ChannelSummary(key=c.key, label=c.label, grade=c.grade, hop_count=len(c.hops), edge_ids=picks,
                          paths_considered=c.paths_considered)


VERDICT_ORDER = {"yes": 0, "unconfirmed": 1, "no": 2}


def _summarise(report: ExposureReport, on_path: dict[int, list[str]], max_positions: int | None) -> ExposureSummary:
    """The summary keeps at most max_positions resolved positions: exposed first (yes, then unconfirmed, then no),
    then the largest absolute quantity, listed in the report's order (book, ref). Quantities are compared as
    delivered, across currencies: a size cap, not a ranking. The unresolved holdings are never omitted."""
    kept = report.positions
    if max_positions is not None and len(kept) > max_positions:
        rank = sorted(range(len(kept)), key=lambda i: (VERDICT_ORDER[kept[i].exposed], -abs(kept[i].position.quantity), i))
        top = set(rank[:max_positions])
        kept = [pe for i, pe in enumerate(kept) if i in top]
    return ExposureSummary(
        user=report.user, as_of=report.as_of, target=report.target, target_rating=report.target_rating,
        positions=[PositionSummary(position=pe.position, exposed=pe.exposed,
                                   channels=[_summary_channel(c) for c in pe.channels],
                                   flags=[FlagSummary(kind=f.kind, message=f.message) for f in pe.flags])
                   for pe in kept],
        positions_omitted=len(report.positions) - len(kept),
        unresolved=report.unresolved,
        research=[ResearchSummary(document_id=d.document_id, title=d.title, publisher=d.publisher,
                                  published_at=d.published_at, visibility=d.visibility, summary=d.summary,
                                  topics=d.topics, about_on_path=on_path[d.document_id]) for d in report.research],
        notes=report.notes)


def get_exposure(user: str, target_id: str, as_of: date | None = None, detail: Literal["summary", "full"] = "summary",
                 max_documents: int | None = 10, max_positions: int | None = 200) -> ExposureSummary | ExposureReport:
    """How each of the user's positions is linked to the target entity as of a date.

    summary (default): per resolved position the verdict (yes / unconfirmed / no), the channels with grade, hop
    count and one edge id per hop, and the flag kinds with their message; the holdings the layer could not
    identify in their own `unresolved` block with the UNRESOLVED_REF message; the visible research about the
    entities on the paths, ranked in SQL (entities matched, then newest) and capped at max_documents, without
    text. Drill down with get_path (every citation on a channel) and get_document (the text).
    full: every hop with every citation and the same ranked documents with their text; same `unresolved` block.
    max_positions caps the summary's resolved positions (exposed first, then largest absolute quantity; the rest
    counted in positions_omitted; unresolved holdings are never omitted); null = no cap. The full report is not
    capped.
    """
    as_of = as_of or config.AS_OF
    if detail not in ("summary", "full"):
        raise ValueError("detail must be 'summary' or 'full'")
    for name, value in (("max_documents", max_documents), ("max_positions", max_positions)):
        if value is not None and value < 0:
            raise ValueError(f"{name} must be >= 0 or null (no cap)")
    with connect() as conn, as_user(conn, user) as cur:
        report, on_path = _exposure(cur, user, target_id, as_of, max_documents)
        return report if detail == "full" else _summarise(report, on_path, max_positions)


def get_path(user: str, instrument_id: str, target_id: str, channel_key: str, as_of: date | None = None) -> PathReport:
    """The representative path of one channel from an instrument to the target, with every citation on every hop,
    and how many paths with that key were considered. channel_key is the key shown by get_exposure
    (e.g. OWNS, GUARANTEED_BY, COUNTRY_OF_RISK>SOVEREIGN_IS)."""
    as_of = as_of or config.AS_OF
    with connect() as conn, as_user(conn, user) as cur:
        if _entity_type(cur, instrument_id) != "instrument":
            raise ValueError(f"{instrument_id!r} is not an instrument id")
        target_type = _entity_type(cur, target_id)
        paths = _all(cur, "select * from exposure_paths(%s, %s, %s, p_start_ids => %s)",
                     (target_type, target_id, as_of, [instrument_id]))
        cites = _citations(cur, sorted({e for p in paths for hop in p["hop_edge_ids"] for e in hop.split(",")}))
        channels = {c.key: c for c in _channels(paths, cites, _names(cur))}
        if channel_key not in channels:
            raise ValueError(f"no channel {channel_key!r} from {instrument_id} to {target_id} as of {as_of}; "
                             f"available: {sorted(channels) or 'none'}")
        return PathReport(user=user, as_of=as_of, instrument_id=instrument_id, target_id=target_id,
                          **channels[channel_key].model_dump())


def _exposure(cur: psycopg.Cursor, user: str, target_id: str, as_of: date, max_documents: int | None
              ) -> tuple[ExposureReport, dict[int, list[str]]]:
    """The full report plus {document_id: path ids it is about}; the summary is derived from it."""
    if max_documents is not None and max_documents < 0:
        raise ValueError("max_documents must be >= 0 or null (no cap)")
    target_type = _entity_type(cur, target_id)
    name = _names(cur).get((target_type, target_id), target_id)
    target = EntityMatch(entity_type=target_type, entity_id=target_id, name=name, matched_alias=target_id,
                         match_kind="exact")
    rating = _ratings(cur, target_id, as_of) if target_type == "issuer" else None
    positions = _positions(cur, as_of)
    held = sorted({p.instrument_id for p in positions if p.instrument_id})
    paths = _all(cur, "select * from exposure_paths(%s, %s, %s, p_start_ids => %s)",
                 (target_type, target_id, as_of, held))
    cites = _citations(cur, sorted({e for p in paths for hop in p["hop_edge_ids"] for e in hop.split(",")}))
    quality = _all(cur, "select * from data_quality(%s)", (as_of,))
    # Per held instrument, the data_quality subject of the name that says who stands behind it: the issuer, or the
    # guarantor when the instrument names no issuer. An UNRESOLVED_NAME on it (no id, or an entity that arrived
    # after as_of) makes the position "cannot tell" unless another channel links it.
    unresolved_names: dict[str, list[str]] = {}
    for r in _all(cur, "select instrument_id, issuer_name, guarantor_name from instruments "
                       "where instrument_id = any(%s)", (held,)):
        column = "issuer_name" if r["issuer_name"] else "guarantor_name" if r["guarantor_name"] else None
        if column:
            unresolved_names[r["instrument_id"]] = [f"instruments|{r['instrument_id']}|{column}"]

    names = _names(cur)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for p in paths:
        grouped.setdefault(p["start_id"], []).append(p)
    by_instrument = {i: _channels(ps, cites, names) for i, ps in grouped.items()}

    exposures, unresolved = [], []
    for pos in positions:
        if pos.instrument_id is None:
            # a real holding the layer could not identify: its own block, with the UNRESOLVED_REF message
            message = next((q["message"] for q in quality if q["kind"] == "UNRESOLVED_REF"
                            and q["subject"] == f"{pos.book}|{pos.instrument_ref}"), pos.resolution_note)
            unresolved.append(Unresolved(position=pos, flag_message=message))
            continue
        channels = by_instrument.get(pos.instrument_id, [])
        names_missing = [q["message"] for q in quality if q["kind"] == "UNRESOLVED_NAME"
                         and q["subject"] in unresolved_names.get(pos.instrument_id, ())]
        if names_missing and not channels:
            # the instrument is known but who stands behind it is not: "cannot tell", never "no"
            unresolved.append(Unresolved(position=pos, flag_message="; ".join(names_missing)))
            continue
        exposed = ("no" if not channels else
                   "yes" if any(c.grade == "high" for c in channels) else "unconfirmed")
        # flags look at every path considered, not only the representative ones
        ids = {e for p in grouped.get(pos.instrument_id, []) for hop in p["hop_edge_ids"] for e in hop.split(",")}
        flags = [_flag(q) for q in quality if q["edge_id"] in ids or q["other_edge_id"] in ids]
        flags += [_flag(q) for q in quality if q["kind"] == "UNRESOLVED_NAME"
                  and q["subject"] in unresolved_names.get(pos.instrument_id, ())]
        exposures.append(PositionExposure(position=pos, exposed=exposed, channels=channels, flags=flags))

    nodes = {n for chans in by_instrument.values() for ch in chans for h in ch.hops
             for n in (h.from_node, h.to_node)} | {f"instrument:{i}" for i in held}
    docs = _research_for_paths(cur, _path_ids(nodes), as_of, max_documents)
    report = ExposureReport(user=user, as_of=as_of, target=target, target_rating=rating, positions=exposures,
                            unresolved=unresolved, research=_documents(docs), notes=NOTES)
    return report, {d["document_id"]: d["about_on_path"] for d in docs}


def get_statements(user: str, entity_id: str, predicate: str | None = None,
                   as_of: date | None = None) -> StatementSet:
    """Every visible link about an entity as of a date, over statements and level-1 edges together: the precedence
    winner per link, the other sources, quality flags, and how many newer statements exist that the user cannot see."""
    as_of = as_of or config.AS_OF
    with connect() as conn, as_user(conn, user) as cur:
        _entity_type(cur, entity_id)
        rows = _all(cur, "select c.*, d.title as document_title, d.published_at "
                         "from current_statements(%s) c left join documents d on d.document_id = c.document_id "
                         "where (c.subject_id = %s or c.object_id = %s) and (%s::text is null or c.predicate = %s) "
                         "order by c.link_key, c.rn", (as_of, entity_id, entity_id, predicate, predicate))
        links = {r["link_key"] for r in rows}
        flags = [_flag({**q, "subject": q["link_key"], "edge_id": q["winner_edge"], "other_edge_id": q["other_edge"]})
                 for q in _all(cur, "select * from link_quality(%s) order by link_key, other_edge", (as_of,))
                 if q["link_key"] in links]
        single = {r["predicate"]: r["single_valued"] for r in _all(cur, "select * from predicate_def")}
        hidden = 0
        for w in (r for r in rows if r["rn"] == 1):
            cur.execute("select hidden_newer_count(%s, %s, %s, %s, %s, %s) as n",
                        (w["subject_type"], w["subject_id"], w["predicate"],
                         None if single[w["predicate"]] else w["object_id"], w["as_of"], as_of))
            w["hidden_newer_count"] = cur.fetchone()["n"]            # per link, so an answer can name the link
            hidden += w["hidden_newer_count"]
        return StatementSet(entity_id=entity_id, predicate=predicate, as_of=as_of,
                            current=[Statement.model_validate(r) for r in rows if r["rn"] == 1],
                            other_sources=[Statement.model_validate(r) for r in rows if r["rn"] > 1],
                            flags=flags, hidden_newer_count=hidden)


def get_documents(user: str, entity_id: str | None = None, since: date | None = None,
                  as_of: date | None = None, text: bool = False) -> list[DocumentSummary] | list[Document]:
    """Visible documents published on or before as_of, optionally only those about an entity (its id in one of the
    about_* columns) or since a date, oldest first. By default the row without its text (about_*, topics, summary);
    text=True adds the text. get_document fetches one document's text for a citation."""
    as_of = as_of or config.AS_OF
    with connect() as conn, as_user(conn, user) as cur:
        if entity_id is not None:
            _entity_type(cur, entity_id)
        docs = _all(cur, "select d.* from documents d where d.published_at < %s and d.updated_on <= known_by(%s) "
                         "and (%s::date is null or d.published_at >= %s) "
                         "and (%s::text is null or %s = any(d.about_issuers) or %s = any(d.about_instruments) "
                         "or %s = any(d.about_curves) or %s = any(d.about_currencies)) "
                         "order by d.published_at, d.document_id",
                    (as_of + timedelta(days=1), as_of, since, since, entity_id, entity_id, entity_id, entity_id,
                     entity_id))
        return _documents(docs) if text else _summaries(docs)


def get_document(user: str, document_id: int) -> Document:
    """One document with its text: the citation fetch. Row-level security applies, so a document the user is not
    entitled to read is indistinguishable from one that does not exist; both raise ValueError."""
    with connect() as conn, as_user(conn, user) as cur:
        docs = _all(cur, "select d.* from documents d where d.document_id = %s", (document_id,))
        if not docs:
            raise ValueError(f"document {document_id} does not exist or is not visible to {user}")
        return _documents(docs)[0]


def _summaries(docs: list[dict[str, Any]]) -> list[DocumentSummary]:
    return [DocumentSummary(**{k: d[k] for k in DOC_COLUMNS}) for d in docs]


def _documents(docs: list[dict[str, Any]]) -> list[Document]:
    return [Document(**{k: d[k] for k in DOC_COLUMNS + ("text",)}) for d in docs]


def get_ratings(user: str, issuer_id: str, as_of: date | None = None) -> RatingHistory:
    """Rating events for an issuer up to as_of, the current rating, and notches versus its sovereign."""
    with connect() as conn, as_user(conn, user) as cur:
        if _entity_type(cur, issuer_id) != "issuer":
            raise ValueError(f"{issuer_id!r} is not an issuer id")
        return _ratings(cur, issuer_id, as_of or config.AS_OF)


def _ratings(cur: psycopg.Cursor, issuer_id: str, as_of: date) -> RatingHistory:
    def events(iid: str) -> list[RatingEvent]:
        return [RatingEvent.model_validate(r) for r in _all(
            cur, "select r.agency, r.rating, r.outlook, r.action_date, s.rank from ratings r "
                 "left join rating_scale s on s.agency = r.agency and s.rating = r.rating "
                 "where r.issuer_id = %s and r.action_date <= %s and r.updated_on <= known_by(%s) "
                 "order by r.action_date desc, r.agency", (iid, as_of, as_of))]

    history = events(issuer_id)
    rows = _all(cur, "select object_id from current_statements(%s) where subject_type = 'issuer' "
                     "and subject_id = %s and predicate = 'COUNTRY_OF_RISK' and rn = 1", (as_of, issuer_id))
    if not rows:
        rows = _all(cur, "select country_of_incorporation as object_id from issuers where issuer_id = %s",
                    (issuer_id,))
    sov = _all(cur, "select sovereign_issuer_id from country where code = %s", (rows[0]["object_id"],)) if rows else []
    sovereign_id = sov[0]["sovereign_issuer_id"] if sov else None
    current = history[0] if history else None
    sovereign_current = None
    if sovereign_id:
        sov_events = events(sovereign_id)
        same_agency = [e for e in sov_events if current and e.agency == current.agency]
        sovereign_current = (same_agency or sov_events or [None])[0]
    notches = (current.rank - sovereign_current.rank
               if current and sovereign_current and current.rank is not None and sovereign_current.rank is not None
               else None)
    return RatingHistory(issuer_id=issuer_id, current=current, history=history, sovereign_issuer_id=sovereign_id,
                         sovereign_current=sovereign_current, notches_vs_sovereign=notches)
