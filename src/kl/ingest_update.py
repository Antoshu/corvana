"""kl-update: apply one delivery folder (e.g. data/updates/2026-10-28) to a loaded corvana_kl. Idempotent.

Rules (model/ground_truth.md section 12):
  order                                        issuers, curves, instruments, ownership, ratings, positions (by
                                               dependency, whatever the file names), then documents
  level-1 row, new key                         AUTO: inserted, names resolved, rule statements derived
  level-1 row, existing key, changed value     NOT applied: discarded and logged for a person
  level-1 row, existing key, same value        SKIP (audit columns last_updated / updated_on / source_file are
                                               not compared; columns the model drops cannot be compared and are
                                               noted once per file)
  name ids still null after the files          re-resolved through the alias view on every run (AUTO), so a row
                                               whose entity arrives later resolves without a reload
  ownership note negated ("... withdrawn")     no rule statement; DISCARD logged for a person
  reference-grade statement that contradicts   NOT applied: discarded and logged
  an existing one on its link
  document                                     AUTO into documents with the alias-scan annotation; grounded LLM
                                               annotation (about_*, topics, summary) when a key is present. No
                                               relationship extraction (decision 2026-11-01). The same title and
                                               text already stored under another path: SKIP (a re-sent note)
  unreadable file                              InputError naming file and line; the whole batch rolls back
  quality                                      data_quality before and after, flags opened and closed reported
                                               (UNKNOWN_LABEL / UNKNOWN_BOOK: stored, seen by no user)
No bookkeeping tables: a rerun finds every row by its natural key and does nothing. The log is the console and
transcripts/update_<date>.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from kl import config
from kl.load import (DROPPED, PACK, InputError, aliases_for, country_of_risk, curated_aliases, document_rows, insert,
                     insert_document, interpret_note, level1_row, ownership_rules, read_csv_lines, rel,
                     resolve_instrument, resolve_ownership, resolve_rating, vehicle_parents)
from kl.resolve import alias_patterns, resolve

KEYS = {"instruments": ("instrument_id",), "issuers": ("issuer_id",), "curves": ("curve_id",),
        "ratings": ("entity", "agency", "action_date"), "ownership": ("owner", "owned_entity", "as_of_date"),
        "positions": ("book", "instrument_ref", "as_of_date")}
RESOLVERS = {"instruments": resolve_instrument, "ownership": resolve_ownership, "ratings": resolve_rating}
ALIASED = {"issuers": "issuer", "instruments": "instrument", "curves": "curve"}
# Bookkeeping columns: a change here alone is not a change of the row (a master refresh bumps last_updated).
AUDIT = {"source_file", "updated_on", "last_updated"}
# Delta files are applied in dependency order, whatever their names: names resolve against rows already applied.
TABLE_ORDER = ("issuers", "curves", "instruments", "ownership", "ratings", "positions")
# (resolved id column, raw name column) pairs: a raw name with a null id is an UNRESOLVED_NAME flag.
NAME_COLUMNS = (("issuer_id", "issuer_name"), ("guarantor_id", "guarantor_name"), ("owner_id", "owner"),
                ("owned_id", "owned_entity"), ("issuer_id", "entity"))
REFERENCE_GRADE = ("INFERRED", "CONFIRMED")
FLAG_KEY = ("kind", "subject", "edge_id", "other_edge_id")

Log = list[dict[str, Any]]


def log(entries: Log, action: str, table: str | None, key: str | None, message: str) -> None:
    entries.append({"action": action, "table": table, "key": key, "message": message})
    print(f"  {action:<8} {table or '':<12} {key or '':<45} {message}")


def same(db_value: Any, file_value: Any) -> bool:
    """Compare a stored value with the delivered text, by the stored value's type."""
    if db_value is None or file_value is None:
        return db_value is None and file_value is None
    if isinstance(db_value, bool):
        return db_value == (str(file_value).strip().lower() == "true")
    if isinstance(db_value, Decimal):
        return db_value == Decimal(str(file_value))
    if isinstance(db_value, date):
        return db_value == (file_value if isinstance(file_value, date) else date.fromisoformat(str(file_value)))
    return str(db_value).rstrip() == str(file_value).rstrip()


# --- statements: the contradiction guard -------------------------------------------------------------------------

def contradicting_reference(cur: psycopg.Cursor, row: dict[str, Any], as_of: date) -> tuple[str, str] | None:
    """(edge_id, value) of a reference-grade edge current on the same link that disagrees with `row`, or None."""
    cur.execute("select single_valued, compare from predicate_def where predicate = %s", (row["predicate"],))
    got = cur.fetchone()
    if got is None:
        raise ValueError(f"unknown predicate {row['predicate']!r}")
    single_valued, compare = (got.values() if isinstance(got, dict) else got)
    link_key = f"{row['subject_type']}|{row['subject_id']}|{row['predicate']}|{'' if single_valued else row['object_id']}"
    if compare == "object":
        mine = row["object_id"]
    elif compare == "value_num":
        cur.execute("select num_key(%s::numeric)", (row.get("value_num"),))
        mine = _row(cur.fetchone())[0]
    else:
        mine = str(row.get("holds", True)).lower()
    return _contradiction(cur, link_key, mine, as_of)


def _contradiction(cur: psycopg.Cursor, link_key: str, mine: str, as_of: date) -> tuple[str, str] | None:
    """The current winner of the link (rn = 1) when it is reference-grade and disagrees with `mine`. Losers are not
    compared: a row agreeing with a CONFIRMED winner does not contradict the INFERRED row the person overruled."""
    cur.execute("select edge_id, compare_key from current_statements(%s, %s) where rn = 1 and high_tier",
                (as_of, link_key))
    got = cur.fetchone()
    if got is None:
        return None
    edge_id, compare_key = (tuple(got.values()) if isinstance(got, dict) else tuple(got))
    return (edge_id, compare_key) if compare_key != mine else None


def add_statements(cur: psycopg.Cursor, entries: Log, rows: list[dict[str, Any]], as_of: date,
                   rederive: bool = False) -> int:
    """Insert rule statements. A reference-grade row that contradicts the reference-grade winner on its link is
    discarded and logged, never applied. rederive=True (derive_country_of_risk only) allows one exception: the same
    rule re-derived with newer evidence (a financing-vehicle note) replaces the rule's own older row on the link; it
    wins by date and the older row reads SUPERSEDED. Returns the number of rows written (or already present)."""
    written = 0
    for row in rows:
        key = f"{row['subject_id']} {row['predicate']} {row['object_id']}"
        if row["status"] in REFERENCE_GRADE:
            hit = contradicting_reference(cur, row, as_of)
            if hit and rederive and _rederived(cur, row, hit[0]):
                log(entries, "AUTO", "statements", key, f"rule re-derived with newer evidence; supersedes {hit[0]}")
                hit = None
            if hit:
                log(entries, "DISCARD", "statements", key,
                    f"reference-grade {row['status']} row contradicts {hit[0]} (current value {hit[1]!r}); "
                    f"not applied, for a person to decide")
                continue
        insert(cur, "statements", [row], on_conflict=True)
        written += 1
    return written


def _rederived(cur: psycopg.Cursor, row: dict[str, Any], edge_id: str) -> bool:
    """True when edge_id is a RULE statement from the same source as `row`, with an older as_of."""
    if row.get("method", "RULE") != "RULE" or not edge_id.startswith("stmt:"):
        return False
    cur.execute("select method::text, source_system, as_of from statements where statement_id = %s",
                (int(edge_id.removeprefix("stmt:")),))
    got = cur.fetchone()
    if got is None:
        return False
    method, source_system, old_as_of = (tuple(got.values()) if isinstance(got, dict) else tuple(got))
    return method == "RULE" and source_system == row["source_system"] and old_as_of < row["as_of"]


# --- level 1 -------------------------------------------------------------------------------------------------------

def derived_statements(cur: psycopg.Cursor, table: str, row: dict[str, Any], source_file: str,
                       batch_date: date) -> list[dict[str, Any]]:
    """Rule statements one new level-1 row implies at once: the notes rules for ownership. COUNTRY_OF_RISK is not
    derived per row: it depends on the ownership notes (a financing vehicle takes its parent's country), which may
    arrive in the same batch after the issuer, so derive_country_of_risk runs once after all the batch's files."""
    if table == "ownership":
        return ownership_rules(row, source_file, batch_date)
    return []


def derive_country_of_risk(cur: psycopg.Cursor, entries: Log, batch_date: date) -> None:
    """COUNTRY_OF_RISK for every issuer from the rule (incorporation, or the parent's country for a financing
    vehicle), against the full issuers and ownership tables after this batch. An issuer without a RULE row gets one;
    an issuer whose latest RULE row names another country (a vehicle note arrived later) gets a new row dated by the
    newer evidence, which supersedes it through add_statements. Nothing is written when the rule agrees."""
    with cur.connection.cursor(row_factory=dict_row) as dcur:
        dcur.execute("select issuer_id, country_of_incorporation, last_updated, source_file from issuers")
        issuers = dcur.fetchall()
        dcur.execute("select owner_id, owned_id, notes, as_of_date from ownership")
        ownership = dcur.fetchall()
        dcur.execute("select distinct on (subject_id) subject_id, object_id, as_of from statements "
                     "where predicate = 'COUNTRY_OF_RISK' and subject_type = 'issuer' and method = 'RULE' "
                     "order by subject_id, as_of desc, statement_id desc")
        current = {r["subject_id"]: r for r in dcur.fetchall()}
    incorporated = {r["issuer_id"]: r["country_of_incorporation"] for r in issuers}
    vehicle_of = vehicle_parents(ownership)
    evidence = {r["owned_id"]: r["as_of_date"] for r in ownership if r["owned_id"] in vehicle_of}
    for r in issuers:
        row = country_of_risk(r, incorporated, vehicle_of, r["source_file"], batch_date)
        have = current.get(r["issuer_id"])
        if have and have["object_id"] == row["object_id"]:
            continue
        if have:                                   # the rule changed its answer: date it by the newer evidence
            row["as_of"] = max(d for d in (row["as_of"], evidence.get(r["issuer_id"])) if d)
        n = add_statements(cur, entries, [row], batch_date, rederive=bool(have))
        if n and not have:                         # a re-derivation is logged by add_statements
            log(entries, "AUTO", "statements", f"{r['issuer_id']} COUNTRY_OF_RISK {row['object_id']}",
                f"rule statement: {row['quote']}")


def check_header(cur: psycopg.Cursor, table: str, columns: list[str], source_file: str) -> None:
    """A delta file's header: every key column present, no column the table neither stores nor drops."""
    if table not in KEYS:
        raise InputError(f"{source_file}: no table {table!r} for a delta file; expected one of {', '.join(TABLE_ORDER)}")
    cur.execute("select column_name from information_schema.columns where table_schema = 'public' and table_name = %s",
                (table,))
    known = {_row(r)[0] for r in cur.fetchall()} | DROPPED.get(table, set())
    missing = [k for k in KEYS[table] if k not in columns]
    unknown = [c for c in columns if c not in known]
    if missing or unknown:
        raise InputError(f"{source_file}:1: header {columns!r}: "
                         + "; ".join(([f"missing key column(s) {', '.join(missing)}"] if missing else [])
                                     + ([f"unknown column(s) {', '.join(unknown)}"] if unknown else [])))


def apply_level1_rows(cur: psycopg.Cursor, entries: Log, table: str, rows: list[dict[str, Any]], source_file: str,
                      batch_date: date, lines: list[int] | None = None) -> None:
    """New key -> AUTO. Existing key with a changed value -> DISCARD (logged, row untouched). Identical -> SKIP.
    A row that cannot be applied raises InputError naming the file and line (`lines`, when given)."""
    if table not in KEYS:
        raise InputError(f"{source_file}: no table {table!r} for a delta file; expected one of {', '.join(TABLE_ORDER)}")
    curated = curated_aliases()
    carried_dropped: set[str] = set()
    existing_rows = 0
    for i, raw in enumerate(rows):
        where = f"{source_file}:{lines[i]}" if lines else source_file
        try:
            outcome = _apply_row(cur, entries, table, raw, source_file, batch_date, curated)
        except InputError:
            raise
        except psycopg.Error as e:
            diag = e.diag.message_primary or str(e).splitlines()[0]
            detail = f" ({e.diag.message_detail})" if e.diag.message_detail else ""
            raise InputError(f"{where}: {table} row not applied: {diag}{detail}") from None
        except (ValueError, KeyError, TypeError) as e:
            raise InputError(f"{where}: {table} row not applied: {type(e).__name__}: {e}") from None
        if outcome != "AUTO":
            existing_rows += 1
            carried_dropped |= {c for c in DROPPED.get(table, set()) if raw.get(c) not in (None, "")}
    if carried_dropped:
        log(entries, "SKIP", table, source_file,
            f"ignored column change: {existing_rows} existing row(s) also carry {', '.join(sorted(carried_dropped))}, "
            f"which the model does not store; a change there is neither compared nor applied")


def _apply_row(cur: psycopg.Cursor, entries: Log, table: str, raw: dict[str, Any], source_file: str,
               batch_date: date, curated: dict) -> str:
    """One delta row; returns the action logged (AUTO, SKIP or DISCARD)."""
    row = level1_row(table, raw, source_file, batch_date)
    key = "|".join(str(row[k]) for k in KEYS[table])
    where = sql.SQL(" and ").join(sql.SQL("{} = %s").format(sql.Identifier(k)) for k in KEYS[table])
    with cur.connection.cursor(row_factory=dict_row) as dcur:
        dcur.execute(sql.SQL("select * from {} where ").format(sql.Identifier(table)) + where,
                     [row[k] for k in KEYS[table]])
        existing = dcur.fetchone()
    if existing is None:
        prepared = RESOLVERS.get(table, lambda _c, r: r)(cur, row)
        if table in ALIASED:
            prepared["aliases"] = aliases_for(ALIASED[table], prepared, curated)
        insert(cur, table, [prepared])
        unresolved = [id_col for id_col, name_col in NAME_COLUMNS
                      if prepared.get(name_col) and id_col in prepared and prepared[id_col] is None]
        n = add_statements(cur, entries, derived_statements(cur, table, prepared, source_file, batch_date), batch_date)
        note = f"; UNRESOLVED_NAME on {', '.join(unresolved)}" if unresolved else ""
        log(entries, "AUTO", table, key, f"new row from {source_file}; {n} rule statement(s){note}")
        if table == "ownership":
            refused_notes(entries, key, prepared.get("notes"))
        return "AUTO"
    changed = {c: v for c, v in row.items() if c not in AUDIT and c in existing and not same(existing[c], v)}
    if not changed:
        log(entries, "SKIP", table, key, "identical to the stored row")
        return "SKIP"
    detail = "; ".join(f"{c}: {existing[c]!r} -> {v!r}" for c, v in sorted(changed.items()))
    log(entries, "DISCARD", table, key, f"existing key with a changed value ({detail}); not applied, "
                                         f"for a person to decide")
    return "DISCARD"


def refused_notes(entries: Log, key: str, note: str | None) -> None:
    """Log an ownership note the rules would have read as a link but for a negation in it."""
    _found, refused = interpret_note(note)
    if refused:
        log(entries, "DISCARD", "statements", key,
            f"ownership note {note!r} not read as a link ({'; '.join(refused)}): no rule statement; "
            f"for a person to decide")


def reresolve(cur: psycopg.Cursor, entries: Log, batch_date: date) -> None:
    """Every name id still null is resolved again through the alias view, so a row whose entity arrived in this or
    a later delivery resolves without a reload. Only null ids are filled; a resolved id is never changed. An
    ownership row that becomes fully resolved gets its note rules now."""
    with cur.connection.cursor(row_factory=dict_row) as dcur:
        dcur.execute("select instrument_id, issuer_name, issuer_id, guarantor_name, guarantor_id from instruments "
                     "where (issuer_name is not null and issuer_id is null) "
                     "or (guarantor_name is not null and guarantor_id is null) order by instrument_id")
        for r in dcur.fetchall():
            for id_col, name_col in (("issuer_id", "issuer_name"), ("guarantor_id", "guarantor_name")):
                if r[name_col] and r[id_col] is None and (found := resolve(cur, "issuer", r[name_col])):
                    cur.execute(sql.SQL("update instruments set {} = %s where instrument_id = %s")
                                .format(sql.Identifier(id_col)), (found, r["instrument_id"]))
                    log(entries, "AUTO", "instruments", r["instrument_id"],
                        f"{id_col} resolved now: {r[name_col]!r} -> {found}")
        dcur.execute("select * from ownership where owner_id is null or owned_id is null order by ownership_id")
        for r in dcur.fetchall():
            key = f"{r['owner']}|{r['owned_entity']}|{r['as_of_date']}"
            got = {"owner_id": r["owner_id"] or resolve(cur, "issuer", r["owner"]),
                   "owned_id": r["owned_id"] or resolve(cur, "issuer", r["owned_entity"])}
            new = {c: v for c, v in got.items() if v and r[c] is None}
            if not new:
                continue
            cur.execute("update ownership set owner_id = %s, owned_id = %s where ownership_id = %s",
                        (got["owner_id"], got["owned_id"], r["ownership_id"]))
            n = 0
            if got["owner_id"] and got["owned_id"]:
                n = add_statements(cur, entries, ownership_rules({**r, **got}, r["source_file"], batch_date), batch_date)
                refused_notes(entries, key, r["notes"])
            log(entries, "AUTO", "ownership", key,
                f"resolved now: {', '.join(f'{c} -> {v}' for c, v in new.items())}; {n} rule statement(s)")
        dcur.execute("select entity, agency, action_date from ratings where issuer_id is null order by 1, 2, 3")
        for r in dcur.fetchall():
            if found := resolve(cur, "issuer", r["entity"]):
                cur.execute("update ratings set issuer_id = %s where entity = %s and agency = %s and action_date = %s",
                            (found, r["entity"], r["agency"], r["action_date"]))
                log(entries, "AUTO", "ratings", f"{r['entity']}|{r['agency']}|{r['action_date']}",
                    f"issuer_id resolved now: {r['entity']!r} -> {found}")


# --- documents ------------------------------------------------------------------------------------------------------

def store_documents(cur: psycopg.Cursor, entries: Log, folder: Path, batch_date: date,
                    llm: bool) -> tuple[list[int], list[dict[str, Any]]]:
    """Documents under research/ and desk_notes/: AUTO with the alias-scan annotation; grounded LLM annotation
    for any document not yet annotated by the LLM, when a key is present. No relationship extraction (decision
    2026-11-01: the LLM finds entities only). Returns the document ids and the annotation reports."""
    patterns = alias_patterns(cur)
    ids: list[int] = []
    reports: list[dict[str, Any]] = []
    client = None
    for d in document_rows(folder):
        key = f"{d['source_file']}|{d['published_at']:%Y-%m-%d %H:%M}"
        twin = resent_twin(cur, d)
        if twin:
            log(entries, "SKIP", "documents", key, f"same title and text as document {twin[0]} ({twin[1]}); "
                                                   f"a re-sent document, not stored again")
            continue
        try:
            doc_id = insert_document(cur, d, patterns, batch_date, on_conflict=True)
        except psycopg.Error as e:
            raise InputError(f"{d['source_file']}: document not stored: {e.diag.message_primary or e}") from None
        if doc_id is None:
            cur.execute("select document_id from documents where source_file = %s and published_at = %s "
                        "and author is not distinct from %s", (d["source_file"], d["published_at"], d["author"]))
            doc_id = next(iter(_row(cur.fetchone())))
            log(entries, "SKIP", "documents", key, f"document {doc_id} already stored")
        else:
            log(entries, "AUTO", "documents", key, f"stored as document {doc_id} ({d['visibility']}), alias-scan annotation")
        ids.append(doc_id)
        cur.execute("select annotated_by from documents where document_id = %s", (doc_id,))
        if next(iter(_row(cur.fetchone()))) == "LLM":
            continue
        if not llm:
            log(entries, "SKIP", "documents", key, "LLM annotation not run: no ANTHROPIC_API_KEY; rerun the ingest "
                                                   "once one is set")
            continue
        import anthropic

        from kl.extract import annotate
        client = client or anthropic.Anthropic()
        r = annotate(client, cur, {**d, "document_id": doc_id}, batch_date)
        reports.append(r)
        n_about = sum(len(v) for v in r["about"].values())
        c = r["counts"]
        dropped = [m for m in r["mentions"] if not m["kept"]] + [a for a in r["added"] if not a["kept"]]
        log(entries, "AUTO", "documents", key, f"grounded LLM annotation: {n_about} about_* id(s) (scan only "
                                               f"{c['scan_only']}, LLM only {c['llm_only']}, both {c['both']}), "
                                               f"{len(r['mentions'])} mention(s), {len(r['added'])} added, "
                                               f"{len(dropped)} dropped; topics {', '.join(r['topics']) or 'none'}")
    return ids, reports


def content_hash(d: dict[str, Any]) -> str:
    """md5 of title and text, as Postgres computes md5(coalesce(title, '') || chr(10) || text)."""
    return hashlib.md5(f"{d.get('title') or ''}\n{d['text']}".encode("utf-8")).hexdigest()


def resent_twin(cur: psycopg.Cursor, d: dict[str, Any]) -> tuple[int, str] | None:
    """(document_id, source_file) of a document stored under another path with the same title and text: the same
    note sent again in a later delivery. A desk line must also match its time and author (short lines repeat)."""
    cur.execute("select document_id, source_file from documents "
                "where md5(coalesce(title, '') || chr(10) || text) = %s and kind = %s and source_file <> %s "
                "and (kind = 'RESEARCH' or (published_at = %s and author is not distinct from %s)) "
                "order by document_id limit 1",
                (content_hash(d), d["kind"], d["source_file"], d["published_at"], d["author"]))
    got = cur.fetchone()
    return _row(got) if got else None


def _row(r: Any) -> tuple:
    return tuple(r.values()) if isinstance(r, dict) else tuple(r)


# --- quality and report ---------------------------------------------------------------------------------------------

def snapshot(conn: psycopg.Connection, as_of: date) -> dict[tuple, dict[str, Any]]:
    """data_quality(as_of) as the admin role (no RLS), keyed by kind, subject and edge ids."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("select * from data_quality(%s)", (as_of,))
        return {tuple(r[k] for k in FLAG_KEY): r for r in cur.fetchall()}


def cell(value: Any) -> str:
    """Text safe inside a Markdown table cell."""
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def report(conn: psycopg.Connection, batch: str, entries: Log, doc_ids: list[int],
           opened: list[dict], closed: list[dict], annotations: list[dict[str, Any]]) -> str:
    from kl.extract import describe

    with conn.cursor(row_factory=dict_row) as cur:
        docs = cur.execute("select * from documents where document_id = any(%s) order by document_id", (doc_ids,)).fetchall()

    def section(action: str) -> list[str]:
        rows = [e for e in entries if e["action"] == action]
        return (["| table | key | message |", "|---|---|---|"]
                + [f"| {e['table']} | {cell(e['key'])} | {cell(e['message'])} |" for e in rows]) if rows else ["(none)"]

    lines = [f"# Ingest of {batch}", "",
             f"{sum(e['action'] == 'AUTO' for e in entries)} AUTO, "
             f"{sum(e['action'] == 'DISCARD' for e in entries)} DISCARD, "
             f"{sum(e['action'] == 'SKIP' for e in entries)} SKIP entries this run.", "",
             "## AUTO applied", ""] + section("AUTO")
    lines += ["", "## Discarded, for a person to decide (not applied)", ""] + section("DISCARD")
    lines += ["", "## Annotation of the stored documents", "",
              "Relationships stated in the documents are not extracted (decision 2026-11-01): the LLM identifies "
              "entities only. Confidences below are reported, not stored.", ""]
    for d in docs:
        about = ", ".join(d["about_issuers"] + d["about_instruments"] + d["about_curves"] + d["about_currencies"])
        lines += [f"- document {d['document_id']} `{d['source_file']}` ({d['visibility']}): annotated_by "
                  f"{d['annotated_by']}; about {about or 'nothing'}; topics {', '.join(d['topics']) or 'none'}; "
                  f"summary: {d['summary'] or 'null'}"]
    for r in annotations:
        lines += [""] + describe(r)
    lines += ["", "## Flags opened", ""] + ([f"- {f['kind']}: {f['message']}" for f in opened] or ["(none)"])
    lines += ["", "## Flags closed", ""] + ([f"- {f['kind']}: {f['message']}" for f in closed] or ["(none)"])
    return "\n".join(lines) + "\n"


def ingest(folder: Path, llm: bool | None = None) -> tuple[str, Log]:
    folder = folder.resolve()
    batch, batch_date = rel(folder), date.fromisoformat(folder.name)
    llm = config.llm_available() if llm is None else llm
    entries: Log = []
    with psycopg.connect(config.admin_dsn(), autocommit=True) as conn:
        with conn.transaction(), conn.cursor() as cur:
            before = snapshot(conn, batch_date)
            files = {}
            for path in sorted(folder.glob("*_delta.csv")):
                table = path.stem.removesuffix("_delta")
                if table not in KEYS:
                    raise InputError(f"{rel(path)}: no table {table!r} for a delta file; expected one of "
                                     f"{', '.join(TABLE_ORDER)}")
                files[table] = path
            for table in TABLE_ORDER:
                if table in files:
                    path = files[table]
                    numbered = read_csv_lines(path)
                    with open(path, encoding="utf-8-sig", newline="") as f:
                        header = next(csv.reader(f), [])
                    check_header(cur, table, header, rel(path))
                    apply_level1_rows(cur, entries, table, [r for _l, r in numbered], rel(path), batch_date,
                                      lines=[line for line, _r in numbered])
            reresolve(cur, entries, batch_date)
            derive_country_of_risk(cur, entries, batch_date)
            doc_ids, annotations = store_documents(cur, entries, folder, batch_date, llm)
            after = snapshot(conn, batch_date)
            opened = [after[k] for k in after.keys() - before.keys()]
            closed = [before[k] for k in before.keys() - after.keys()]
            for f in sorted(opened, key=lambda f: (f["kind"], f["subject"])):
                log(entries, "FLAG", "data_quality", f["subject"], f"opened {f['kind']}: {f['message']}")
            for f in sorted(closed, key=lambda f: (f["kind"], f["subject"])):
                log(entries, "FLAG", "data_quality", f["subject"], f"closed {f['kind']}: {f['message']}")
        return report(conn, batch, entries, doc_ids, opened, closed, annotations), entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a delivery folder such as data/updates/2026-10-28.")
    parser.add_argument("folder", type=Path)
    folder = parser.parse_args().folder
    if not folder.resolve().is_relative_to(PACK.resolve()):
        raise SystemExit(f"{folder} is not inside the data pack {PACK}")
    print(f"ingesting {folder}")
    try:
        text, entries = ingest(folder)
    except InputError as e:
        print(f"ingest failed, nothing applied (the batch rolled back): {e}", file=sys.stderr)
        raise SystemExit(1) from None
    if all(e["action"] == "SKIP" for e in entries):
        print("no-op: every input already applied; report not rewritten")
        return
    config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.TRANSCRIPTS_DIR / f"update_{folder.resolve().name}.md"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"written to {out}")


if __name__ == "__main__":
    main()
