"""kl-load: full rebuild of corvana_kl from the data pack and the curation seed. Never calls the LLM.

Order: schema files (010 generated tables, 020 logic, 030 security); metadata (sources, entitlements,
predicate_def, rating_scale); level 1 as delivered plus curated aliases[] and ids resolved through the alias view;
documents with the alias-scan annotation (RULE); the statements no file column holds (country-of-risk rules, the
two ownership.notes rules, the curated rows); then roles and grants from entitlements.
"""
from __future__ import annotations

import csv
import re
from fnmatch import fnmatchcase
from datetime import date, datetime, time
from pathlib import Path, PurePosixPath
from typing import Any

import psycopg
import yaml
from psycopg import sql

from kl import config
from kl.resolve import alias_patterns, document_scan_text, resolve, rule_annotation

PACK = config.PACK_DIR
CURATION = config.CURATION_DIR
AS_OF = config.AS_OF

STATEMENT_COLS = ("subject_type", "subject_id", "predicate", "object_type", "object_id", "value_num", "value_text",
                  "holds", "as_of", "source_system", "source_file", "document_id", "quote", "method", "status",
                  "visibility", "updated_on")
ITEM_KEYS = {"file", "doc_time", "subject", "predicate", "object", "value_num", "value_text", "holds", "as_of", "quote"}
# File columns the model does not keep (model/table_review.md); they are read and dropped, never loaded.
DROPPED = {"issuers": {"lei", "issuer_type", "sector"}, "instruments": {"coupon", "maturity"}, "curves": {"country"}}
# Name columns of a row, in the order the alias view reads them; a curated alias equal to one of these is redundant.
OWN_NAMES = {"issuer": ("issuer_id", "legal_name", "short_name"), "instrument": ("instrument_id", "ticker", "isin"),
             "curve": ("curve_id",), "country": ("code", "name")}
ID_COLUMN = {"issuer": "issuer_id", "instrument": "instrument_id", "curve": "curve_id", "country": "code"}
# handle: word characters and dots ("dk", "j.s"); a line whose handle does not match is a continuation line
CHAT_LINE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] ([\w.]+): (.*)$")
SOURCE_SYSTEM_OF = {"research": "ResearchHub", "desk_notes": "DeskNotes"}

Docs = dict[tuple[str, str | None], dict[str, Any]]


class InputError(ValueError):
    """A delivered file that cannot be read or applied: the message starts with the file and, where known, the line
    ("updates/2026-11-04/research/x.md:5: ..."). Raised inside the load or ingest transaction, so nothing is kept."""


# --- small helpers ---------------------------------------------------------------------------------------------

def read_yaml(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_csv(path: Path) -> list[dict[str, Any]]:
    """CSV rows as dicts; empty cells become None. A UTF-8 byte-order mark (an Excel export) is tolerated."""
    return [row for _line, row in read_csv_lines(path)]


def read_csv_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    """(line number, row) per CSV row, the line being the row's last physical line in the file (header = line 1).
    A row with more cells than the header is an InputError naming the line."""
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if None in row:
                raise InputError(f"{_name(path)}:{reader.line_num}: more cells than the header has columns")
            out.append((reader.line_num, {k: (v if v != "" else None) for k, v in row.items()}))
    return out


def _name(path: Path) -> str:
    """The pack-relative path when the file is in the pack, else the path as given."""
    try:
        return rel(path)
    except ValueError:
        return path.as_posix()


def rel(path: Path) -> str:
    return path.relative_to(PACK).as_posix()


def squash(text: str) -> str:
    """Collapse every whitespace run to one space (the quote check is whitespace-insensitive)."""
    return " ".join(text.split())


def insert_sql(table: str, cols: list[str]) -> sql.Composed:
    return sql.SQL("insert into {} ({}) values ({})").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, cols)),
        sql.SQL(", ").join([sql.Placeholder()] * len(cols)))


def insert(cur: psycopg.Cursor, table: str, rows: list[dict[str, Any]], on_conflict: bool = False) -> None:
    """Insert dict rows. on_conflict skips rows that hit a unique constraint (deltas, reruns); the base load is strict."""
    if rows:
        cols = list(rows[0])
        query = insert_sql(table, cols) + sql.SQL(" on conflict do nothing" if on_conflict else "")
        cur.executemany(query, [[r[c] for c in cols] for r in rows])


def source_system_for(source_file: str) -> str:
    """ResearchHub for research/, DeskNotes for desk_notes/, also under updates/<date>/."""
    parts = source_file.split("/")
    folder = parts[-2] if len(parts) >= 2 else ""
    if folder not in SOURCE_SYSTEM_OF:
        raise ValueError(f"{source_file}: no source system for folder {folder!r}")
    return SOURCE_SYSTEM_OF[folder]


# --- schema and metadata ---------------------------------------------------------------------------------------

def apply_schema(conn: psycopg.Connection) -> None:
    with conn.transaction():
        for path in config.SCHEMA_FILES:
            conn.execute(path.read_text(encoding="utf-8"))


def load_metadata(cur: psycopg.Cursor) -> None:
    prov = {"updated_on": AS_OF}
    sources = [{"source_id": k, "description": v.get("description"), "reliability": v.get("reliability"),
                "source_file": "sources.yaml", **prov} for k, v in read_yaml(PACK / "sources.yaml")["sources"].items()]
    sources.append({"source_id": "Curated", "description": "Knowledge-layer curated seed (this repository)",
                    "reliability": "high - reviewed by hand", "source_file": "src/kl/curation", **prov})
    insert(cur, "sources", sources)
    users = read_yaml(PACK / "entitlements.yaml")["users"]
    insert(cur, "entitlements", [{"username": u, "books": v["books"], "research_visibility": v["research_visibility"],
                                  "source_file": "entitlements.yaml", **prov} for u, v in users.items()])
    insert(cur, "predicate_def", [{**r, "single_valued": r["single_valued"].lower() == "true"}
                                  for r in read_csv(CURATION / "predicate_def.csv")])
    insert(cur, "rating_scale", [{**s, **prov} for s in read_csv(CURATION / "rating_scale.csv")])


# --- level 1 ---------------------------------------------------------------------------------------------------

def curated_aliases() -> dict[tuple[str, str], list[str]]:
    """{(entity_type, entity_id): [alias, ...]} from curation/aliases.yaml, in file order."""
    out: dict[tuple[str, str], list[str]] = {}
    for entity_type, by_id in (read_yaml(CURATION / "aliases.yaml") or {}).items():
        if entity_type not in OWN_NAMES:
            raise ValueError(f"aliases.yaml: unknown entity type {entity_type!r}")
        for entity_id, entries in by_id.items():
            for e in entries:
                if set(e) - {"alias", "source"}:
                    raise ValueError(f"aliases.yaml: unknown keys in {e}")
                out.setdefault((entity_type, str(entity_id)), []).append(str(e["alias"]))
    return out


def aliases_for(entity_type: str, row: dict[str, Any], curated: dict[tuple[str, str], list[str]],
                extra: list[str] | None = None) -> list[str]:
    """The aliases[] value for one row: curated names (plus `extra`) minus names already in the row's own columns."""
    own = {str(row[c]).lower() for c in OWN_NAMES[entity_type] if row.get(c)}
    out: list[str] = []
    for a in (extra or []) + curated.get((entity_type, str(row[ID_COLUMN[entity_type]])), []):
        if a.lower() not in own and a.lower() not in {x.lower() for x in out}:
            out.append(a)
    return out


def level1_row(table: str, row: dict[str, Any], source_file: str, updated_on: date) -> dict[str, Any]:
    """A file row minus the columns the model dropped, plus provenance."""
    return {**{k: v for k, v in row.items() if k not in DROPPED.get(table, set())},
            "source_file": source_file, "updated_on": updated_on}


def resolve_instrument(cur: psycopg.Cursor, row: dict[str, Any]) -> dict[str, Any]:
    """issuer_id and guarantor_id resolved from the raw names through the alias view; None when unresolved."""
    return {**row,
            "issuer_id": resolve(cur, "issuer", row["issuer_name"]) if row.get("issuer_name") else None,
            "guarantor_id": resolve(cur, "issuer", row["guarantor_name"]) if row.get("guarantor_name") else None}


def resolve_ownership(cur: psycopg.Cursor, row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "owner_id": resolve(cur, "issuer", row["owner"]), "owned_id": resolve(cur, "issuer", row["owned_entity"])}


def resolve_rating(cur: psycopg.Cursor, row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "issuer_id": resolve(cur, "issuer", row["entity"])}


def load_level1(cur: psycopg.Cursor) -> dict[str, list[dict[str, Any]]]:
    """Countries (sovereign null), issuers, then the sovereign link; curves, instruments, ownership, ratings,
    positions. Returns the loaded rows (with resolved ids) for the statement rules."""
    curated = curated_aliases()
    prov = {"updated_on": AS_OF}
    data: dict[str, list[dict[str, Any]]] = {}

    countries = read_yaml(CURATION / "countries.yaml")
    insert(cur, "country", [{"code": c["code"], "name": c["name"],
                             "aliases": aliases_for("country", c, curated, c.get("aliases")),
                             "currency": c.get("currency"), "sovereign_issuer_id": None, **prov} for c in countries])

    issuers = [level1_row("issuers", r, "reference/issuers.csv", AS_OF) for r in read_csv(PACK / "reference" / "issuers.csv")]
    insert(cur, "issuers", [{**r, "aliases": aliases_for("issuer", r, curated)} for r in issuers])
    data["issuers"] = issuers
    for c in countries:
        if c.get("sovereign_issuer_id"):
            cur.execute("update country set sovereign_issuer_id = %s where code = %s", (c["sovereign_issuer_id"], c["code"]))

    curves = [level1_row("curves", r, "reference/curves.csv", AS_OF) for r in read_csv(PACK / "reference" / "curves.csv")]
    insert(cur, "curves", [{**r, "aliases": aliases_for("curve", r, curated)} for r in curves])
    data["curves"] = curves

    instruments = [resolve_instrument(cur, {**level1_row("instruments", r, "reference/instruments.csv", AS_OF),
                                            "aliases": aliases_for("instrument", r, curated)})
                   for r in read_csv(PACK / "reference" / "instruments.csv")]
    insert(cur, "instruments", instruments)
    data["instruments"] = instruments

    ownership = [resolve_ownership(cur, level1_row("ownership", r, "reference/ownership.csv", AS_OF))
                 for r in read_csv(PACK / "reference" / "ownership.csv")]
    insert(cur, "ownership", ownership)
    data["ownership"] = ownership

    ratings = [resolve_rating(cur, level1_row("ratings", r, "reference/ratings.csv", AS_OF))
               for r in read_csv(PACK / "reference" / "ratings.csv")]
    insert(cur, "ratings", ratings)
    data["ratings"] = ratings

    for path in sorted((PACK / "positions").glob("positions_*.csv")):
        insert(cur, "positions", [level1_row("positions", r, rel(path), AS_OF) for r in read_csv(path)])
    return data


# --- level 3: documents ----------------------------------------------------------------------------------------

def _front_matter_line(head: str, key: str) -> int:
    """File line of `key:` in a front matter block (line 1 is the opening '---'); 2 when the key is absent."""
    for i, line in enumerate(head.split("\n")):
        if line.startswith(f"{key}:"):
            return i + 2
    return 2


def parse_research(path: Path) -> dict[str, Any]:
    """A research note: YAML front matter, or the two-line 'Title: ...' / 'a | author | date | visibility: x' header.
    Anything else is an InputError naming the file and line."""
    where = _name(path)
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    if raw.startswith("---\n"):
        if "\n---\n" not in raw[4:]:
            raise InputError(f"{where}:1: front matter opened with '---' is never closed")
        head, body = raw[4:].split("\n---\n", 1)
        try:
            meta = yaml.safe_load(head)
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            line = f":{mark.line + 2}" if mark is not None else ""
            raise InputError(f"{where}{line}: front matter is not valid YAML "
                             f"({getattr(e, 'problem', None) or e}); quote a value that contains ': '") from None
        if not isinstance(meta, dict):
            raise InputError(f"{where}:2: front matter is not a list of 'key: value' lines")
        for key in ("title", "date"):
            if not meta.get(key):
                raise InputError(f"{where}:{_front_matter_line(head, key)}: front matter has no {key}")
        day = meta["date"]
        if not isinstance(day, date):
            try:
                day = date.fromisoformat(str(day))
            except ValueError:
                raise InputError(f"{where}:{_front_matter_line(head, 'date')}: date {meta['date']!r} is not "
                                 f"YYYY-MM-DD") from None
        return {"title": str(meta["title"]), "publisher": meta.get("source"), "author": meta.get("author"),
                "published_at": datetime.combine(day, time()), "visibility": meta.get("visibility"), "text": body}
    lines = raw.split("\n", 2)
    if len(lines) < 3 or not lines[0].startswith("Title:"):
        raise InputError(f"{where}:1: no front matter ('---') and no 'Title:' header")
    first, second, body = lines
    parts = [p.strip() for p in second.split("|")]
    if len(parts) != 4 or not parts[3].startswith("visibility:"):
        raise InputError(f"{where}:2: header line 2 is not 'kind | author | DD Mon YYYY | visibility: label': "
                         f"{second!r}")
    _kind, author, when, vis = parts
    try:
        published = datetime.strptime(when, "%d %b %Y")
    except ValueError:
        raise InputError(f"{where}:2: date {when!r} is not 'DD Mon YYYY'") from None
    return {"title": first.removeprefix("Title:").strip(), "publisher": "Internal - " + author.removesuffix(" team"),
            "author": author, "published_at": published, "visibility": vis.split(":", 1)[1].strip(), "text": body}


def parse_desk_notes(path: Path) -> list[dict[str, Any]]:
    """One entry per '[YYYY-MM-DD HH:MM] handle: text' line, wrapped lines appended."""
    entries: list[tuple[str, str, list[str]]] = []
    for line in path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").split("\n"):
        m = CHAT_LINE.match(line)
        if m:
            entries.append((m[1], m[2], [m[3]]))
        elif entries:
            entries[-1][2].append(line)
    return [{"published_at": datetime.strptime(t, "%Y-%m-%d %H:%M"), "author": a, "text": "\n".join(ls).strip()}
            for t, a, ls in entries]


def document_rows(folder: Path) -> list[dict[str, Any]]:
    """Document rows (without annotation or updated_on) for every note and desk line under a folder."""
    rows: list[dict[str, Any]] = []
    for path in sorted((folder / "research").glob("*.md")):
        rows.append({"source_file": rel(path), "source_system": "ResearchHub", "kind": "RESEARCH", **parse_research(path)})
    for path in sorted((folder / "desk_notes").glob("*.md")):
        label = desk_label(rel(path))
        rows += [{"source_file": rel(path), "source_system": "DeskNotes", "kind": "DESK_NOTE", "title": None,
                  "publisher": label.get("publisher"), "visibility": label.get("visibility"), **e}
                 for e in parse_desk_notes(path)]
    return rows


def desk_label(source_file: str) -> dict[str, Any]:
    """The desk_notes.yaml entry for a desk-notes file: its `file` matched as a glob against the pack path, or by
    file name, so a delivery's copy of a desk's notes (updates/<date>/desk_notes/<same name>) keeps the desk's
    label. No match: {} (no label; the document is stored and flagged UNLABELLED_DOCUMENT)."""
    for d in read_yaml(CURATION / "desk_notes.yaml"):
        pattern = str(d["file"])
        if fnmatchcase(source_file, pattern) or PurePosixPath(source_file).name == PurePosixPath(pattern).name:
            return d
    return {}


def doc_key(d: dict[str, Any]) -> tuple[str, str | None]:
    """(source_file, 'YYYY-MM-DD HH:MM' for a desk line else None): how statements.yaml addresses a document."""
    return d["source_file"], d["published_at"].strftime("%Y-%m-%d %H:%M") if d["kind"] == "DESK_NOTE" else None


def insert_document(cur: psycopg.Cursor, d: dict[str, Any], patterns: list, updated_on: date,
                    on_conflict: bool = False) -> int | None:
    """Insert one document with its alias-scan annotation (RULE); returns its id, or None when on_conflict and it
    already exists."""
    row = {**d, **rule_annotation(document_scan_text(d), patterns), "topics": [], "summary": None, "annotated_by": "RULE",
           "updated_on": updated_on}
    conflict = " on conflict do nothing" if on_conflict else ""
    cur.execute(insert_sql("documents", list(row)) + sql.SQL(conflict + " returning document_id"), list(row.values()))
    got = cur.fetchone()
    return got[0] if got else None


def load_documents(cur: psycopg.Cursor) -> Docs:
    """Insert the base pack's documents. Returns {doc_key: row with document_id}."""
    patterns = alias_patterns(cur)
    docs: Docs = {}
    for d in document_rows(PACK):
        docs[doc_key(d)] = {**d, "document_id": insert_document(cur, d, patterns, AS_OF)}
    return docs


# --- level 2: statements ---------------------------------------------------------------------------------------

def statement(**kw: Any) -> dict[str, Any]:
    unknown = set(kw) - set(STATEMENT_COLS)
    if unknown:
        raise ValueError(f"unknown statement columns {unknown}")
    row = dict.fromkeys(STATEMENT_COLS)
    row.update(holds=True, method="RULE", updated_on=AS_OF)
    row.update(kw)
    if row["status"] == "REFERENCE":
        raise ValueError("REFERENCE is never stored in statements; it belongs to level-1 edges only")
    return row


def _words(phrase: str) -> re.Pattern[str]:
    return re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, phrase.split())) + r"(?!\w)", re.IGNORECASE)


def interpret_note(note: str | None) -> tuple[list[dict[str, Any]], list[str]]:
    """What curation/ownership_notes_rules.yaml reads in one ownership note: ([{predicate, holds, phrase}], refused),
    one entry per predicate. refused names each matching phrase that a negation in the same note voids
    ("'sovereign guarantee' with 'withdrawn'"); a refused note yields no entries at all."""
    if not note:
        return [], []
    cfg = read_yaml(CURATION / "ownership_notes_rules.yaml")
    hits: dict[str, dict[str, Any]] = {}
    for rule in cfg["rules"]:
        if _words(rule["phrase"]).search(note) and rule["predicate"] not in hits:
            hits[rule["predicate"]] = {"predicate": rule["predicate"], "holds": bool(rule.get("holds", True)),
                                       "phrase": rule["phrase"]}
    negations = [n for n in cfg.get("negations", []) if _words(str(n)).search(note)]
    if hits and negations:
        return [], [f"{h['phrase']!r} with {negations[0]!r}" for h in hits.values()]
    return list(hits.values()), []


def ownership_rules(r: dict[str, Any], source_file: str, updated_on: date = AS_OF) -> list[dict[str, Any]]:
    """The rules over ownership.notes (curation/ownership_notes_rules.yaml): a curated phrase -> owned <predicate>
    owner, INFERRED, dated as_of_date, quoting the note; a negated note gives nothing (interpret_note reports it).
    The OWNS link itself is not a statement: the edges view projects owner_id -> owned_id."""
    if not r.get("notes") or not (r.get("owner_id") and r.get("owned_id")):
        return []
    common = {"subject_type": "issuer", "subject_id": r["owned_id"], "object_type": "issuer", "object_id": r["owner_id"],
              "as_of": r["as_of_date"], "source_system": "OwnershipTracker", "source_file": source_file,
              "quote": r["notes"], "status": "INFERRED", "updated_on": updated_on}
    found, _refused = interpret_note(r["notes"])
    return [statement(**common, predicate=h["predicate"], holds=h["holds"],
                      value_text=r["notes"] if h["predicate"] == "GUARANTEED_BY" else None) for h in found]


def vehicle_parents(ownership: list[dict[str, Any]]) -> dict[str, str]:
    """{vehicle issuer_id: parent issuer_id} from the tracker notes the rules read as FINANCING_VEHICLE_OF."""
    return {r["owned_id"]: r["owner_id"] for r in ownership
            if r.get("owner_id") and r.get("owned_id")
            and any(h["predicate"] == "FINANCING_VEHICLE_OF" and h["holds"] for h in interpret_note(r.get("notes"))[0])}


def country_of_risk(r: dict[str, Any], incorporated: dict[str, str], vehicle_of: dict[str, str],
                    source_file: str, updated_on: date = AS_OF) -> dict[str, Any]:
    """COUNTRY_OF_RISK for one issuer: its incorporation, or its parent's when it is a financing vehicle."""
    iid = r["issuer_id"]
    if iid in vehicle_of:
        parent = vehicle_of[iid]
        code = incorporated[parent]
        quote = f"rule: a financing vehicle takes its parent's country of risk (parent {parent}, {code})"
    else:
        code = incorporated[iid]
        quote = f"rule: country of risk defaults to country of incorporation (issuers.country_of_incorporation = {code})"
    as_of = r.get("last_updated")
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    return statement(subject_type="issuer", subject_id=iid, predicate="COUNTRY_OF_RISK", object_type="country",
                     object_id=code, as_of=as_of or updated_on, source_system="SecMaster",
                     source_file=source_file, status="INFERRED", quote=quote, updated_on=updated_on)


def rule_statements(data: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """The INFERRED rows: ownership.notes rules, then COUNTRY_OF_RISK for every issuer."""
    out: list[dict[str, Any]] = []
    for r in data["ownership"]:
        out += ownership_rules(r, "reference/ownership.csv")
        for reason in interpret_note(r.get("notes"))[1]:
            print(f"  ownership note {r['notes']!r} ({r['owner']} -> {r['owned_entity']}) not read as a link: {reason}")
    vehicle_of = vehicle_parents(data["ownership"])
    incorporated = {r["issuer_id"]: r["country_of_incorporation"] for r in data["issuers"]}
    out += [country_of_risk(r, incorporated, vehicle_of, "reference/issuers.csv") for r in data["issuers"]]
    return out


def curated_statements(docs: Docs) -> list[dict[str, Any]]:
    """Hand-extracted statements from curation/statements.yaml, each checked against its document's text."""
    out: list[dict[str, Any]] = []
    for item in read_yaml(CURATION / "statements.yaml"):
        if set(item) - ITEM_KEYS:
            raise ValueError(f"statements.yaml: unknown keys {set(item) - ITEM_KEYS} in {item}")
        when = item.get("doc_time")
        if when is not None and not isinstance(when, str):
            when = when.strftime("%Y-%m-%d %H:%M")
        doc = docs.get((item["file"], when))
        if doc is None:
            raise ValueError(f"statements.yaml: no document for file={item['file']} doc_time={when}: {item}")
        if squash(item["quote"]) not in squash(doc["text"]):
            raise ValueError(f"statements.yaml: quote not found verbatim in {item['file']}: {item}")
        if not item.get("object"):
            raise ValueError(f"statements.yaml: a statement needs an object: {item}")
        out.append(statement(
            subject_type=item["subject"][0], subject_id=str(item["subject"][1]), predicate=item["predicate"],
            object_type=item["object"][0], object_id=str(item["object"][1]), value_num=item.get("value_num"),
            value_text=item.get("value_text"), holds=item.get("holds", True),
            as_of=item.get("as_of") or doc["published_at"].date(), source_system=source_system_for(item["file"]),
            source_file=item["file"], document_id=doc["document_id"], quote=item["quote"], method="MANUAL",
            status="PROPOSED", visibility=doc["visibility"]))
    return out


# --- roles -----------------------------------------------------------------------------------------------------

def setup_roles(conn: psycopg.Connection) -> None:
    """Cluster roles from entitlements.yaml; memberships made to match it exactly; read grants on public."""
    users = read_yaml(PACK / "entitlements.yaml")["users"]
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("select distinct visibility from documents where visibility is not null")
        labels = {r[0] for r in cur.fetchall()} | {v for u in users.values() for v in u["research_visibility"]}
        labels |= {d["visibility"] for d in read_yaml(CURATION / "desk_notes.yaml") if d.get("visibility")}
        groups = sorted({f"book_{b.lower()}" for u in users.values() for b in u["books"]}
                        | {f"vis_{label}" for label in labels})
        cur.execute("select rolname from pg_roles")
        existing = {r[0] for r in cur.fetchall()}
        for role in [*users, *groups]:
            if role not in existing:
                cur.execute(sql.SQL("create role {} nologin").format(sql.Identifier(role)))
        for user, ent in users.items():
            want = {f"book_{b.lower()}" for b in ent["books"]} | {f"vis_{v}" for v in ent["research_visibility"]}
            cur.execute("select g.rolname from pg_auth_members m join pg_roles g on g.oid = m.roleid "
                        "join pg_roles u on u.oid = m.member where u.rolname = %s "
                        "and (g.rolname like 'book\\_%%' or g.rolname like 'vis\\_%%')", (user,))
            have = {r[0] for r in cur.fetchall()}
            for g in sorted(want - have):
                cur.execute(sql.SQL("grant {} to {}").format(sql.Identifier(g), sql.Identifier(user)))
            for g in sorted(have - want):
                cur.execute(sql.SQL("revoke {} from {}").format(sql.Identifier(g), sql.Identifier(user)))
        for role in [*users, *groups]:
            cur.execute(sql.SQL("grant usage on schema public to {}").format(sql.Identifier(role)))
            cur.execute(sql.SQL("grant select on all tables in schema public to {}").format(sql.Identifier(role)))


def counts(conn: psycopg.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("select table_name from information_schema.tables "
                    "where table_schema = 'public' and table_type = 'BASE TABLE' order by 1")
        tables = [r[0] for r in cur.fetchall()]
        out = {}
        for table in tables:
            cur.execute(sql.SQL("select count(*) from {}").format(sql.Identifier(table)))
            out[table] = cur.fetchone()[0]
        return out


def main() -> None:
    db = sql.Identifier(config.PG_DBNAME)
    with psycopg.connect(config.admin_dsn("postgres"), autocommit=True) as admin:
        admin.execute(sql.SQL("drop database if exists {} with (force)").format(db))
        admin.execute(sql.SQL("create database {}").format(db))
    with psycopg.connect(config.admin_dsn(), autocommit=True) as conn:
        apply_schema(conn)
        with conn.transaction(), conn.cursor() as cur:
            load_metadata(cur)
            data = load_level1(cur)
            docs = load_documents(cur)
            rules = rule_statements(data)
            curated = curated_statements(docs)
            insert(cur, "statements", rules + curated)
        setup_roles(conn)
        print(f"loaded {config.PG_DBNAME} as of {AS_OF}: {len(rules)} rule + {len(curated)} curated statements")
        for table, n in counts(conn).items():
            print(f"  {table:<20} {n:>5}")


if __name__ == "__main__":
    main()
