"""kl-validate: schema and content checks on a loaded corvana_kl. Prints every failure; exit 1 if any, else 0."""
from __future__ import annotations

import sys

import psycopg
import yaml
from psycopg import sql

from kl import config
from kl.resolve import ABOUT_COLUMNS, alias_patterns, document_scan_text, mention_ids, scan_mentions
from kl.schema_gen import generate

# entity_type -> query returning every valid id of that type
ENTITY_IDS = {
    "issuer": "select issuer_id from issuers",
    "instrument": "select instrument_id from instruments",
    "curve": "select curve_id from curves",
    "country": "select code::text from country",
    "currency": "select currency::text from instruments union select currency::text from curves "
                "union select currency::text from country where currency is not null",
}
HOLDS_FALSE_OK = {"TRADES_AS_PROXY_FOR", "CORRELATED_WITH"}


def squash(text: str) -> str:
    return " ".join(text.split())


def rows(cur: psycopg.Cursor, query: str, params: tuple = ()) -> list[tuple]:
    cur.execute(query, params)
    return cur.fetchall()


def entity_ids(cur: psycopg.Cursor) -> dict[str, set[str]]:
    return {t: {r[0] for r in rows(cur, q)} for t, q in ENTITY_IDS.items()}


def check_schema(cur: psycopg.Cursor) -> list[str]:
    """1. 010_tables.sql is what kl-schema generates from model/schema.dbml."""
    path = config.SCHEMA_FILES[0]
    if not path.is_file():
        return [f"{path} is missing; run `uv run kl-schema`"]
    if path.read_text(encoding="utf-8") != generate():
        return [f"{path.name} differs from a fresh generation of {config.DBML.name}; run `uv run kl-schema` and reload"]
    return []


def check_aliases(cur: psycopg.Cursor, ids: dict[str, set[str]]) -> list[str]:
    """2. Every alias resolves to exactly one entity of its type (replaces the dropped unique index)."""
    errors = [f"alias {t} {a!r} maps to several ids: {', '.join(sorted(i))}"
              for t, a, i in rows(cur, "select entity_type, lower(alias), array_agg(distinct entity_id) from alias "
                                       "group by 1, 2 having count(distinct entity_id) > 1")]
    errors += [f"alias {t} {a!r} -> {i}: no such {t}"
               for t, i, a in rows(cur, "select entity_type, entity_id, alias from alias") if i not in ids.get(t, set())]
    return errors


def check_unresolved_names(cur: psycopg.Cursor) -> list[str]:
    """3. Every level-1 name column resolved to an id (UNRESOLVED_NAME listing; add the alias to aliases.yaml)."""
    return [f"{m}" for (m,) in rows(cur, "select message from data_quality where kind = 'UNRESOLVED_NAME' order by 1")]


def check_statement_refs(cur: psycopg.Cursor, ids: dict[str, set[str]]) -> list[str]:
    """4. Statement subjects and objects exist (subject type 'unresolved' exempt); predicates are defined."""
    errors = []
    for sid, st, si, ot, oi in rows(cur, "select statement_id, subject_type, subject_id, object_type, object_id "
                                         "from statements"):
        for role, t, i in (("subject", st, si), ("object", ot, oi)):
            if t == "unresolved":
                continue
            if i not in ids.get(t, set()):
                errors.append(f"statement {sid}: {role} {t} {i} does not exist")
    errors += [f"statement {sid}: predicate {p} not in predicate_def"
               for sid, p in rows(cur, "select statement_id, predicate from statements "
                                       "where predicate not in (select predicate from predicate_def)")]
    return errors


def check_no_reference_statements(cur: psycopg.Cursor) -> list[str]:
    """5. REFERENCE never appears in statements (it belongs to level-1 edges in the edges view only)."""
    return [f"statement {sid} has status REFERENCE"
            for (sid,) in rows(cur, "select statement_id from statements where status = 'REFERENCE'")]


def check_positions(cur: psycopg.Cursor) -> list[str]:
    """6. Every position resolves to an instrument or is reported as UNRESOLVED_REF."""
    # Both sides on the positions data_quality reads (each book at its latest date), matched on book, ref and date.
    flagged = set(rows(cur, "select p.book, p.instrument_ref, p.as_of_date from positions_as_of(current_date) p "
                            "join data_quality(current_date) q on q.kind = 'UNRESOLVED_REF' "
                            "and q.subject = p.book || '|' || p.instrument_ref"))
    return [f"position {b}/{ref} ({rt}, {d}) is unresolved and not flagged"
            for b, ref, rt, d in rows(cur, "select book, instrument_ref, ref_type, as_of_date "
                                           "from positions_as_of(current_date) "
                                           "where instrument_id is null or instrument_updated_on > known_by(current_date)")
            if (b, ref, d) not in flagged]


def check_quotes(cur: psycopg.Cursor) -> list[str]:
    """7. Document-backed statements quote their document verbatim (whitespace-insensitive)."""
    return [f"statement {sid}: quote not in document {did}: {q!r}"
            for sid, did, q, text in rows(cur, "select s.statement_id, s.document_id, s.quote, d.text from statements s "
                                               "join documents d using (document_id)")
            if not q or squash(q) not in squash(text)]


def check_visibility(cur: psycopg.Cursor) -> list[str]:
    """8. Every label is entitled to someone; every document carries a label."""
    known = {r[0] for r in rows(cur, "select distinct unnest(research_visibility) from entitlements")}
    errors = [f"{what} {i}: visibility {v!r} is granted to no user"
              for what, i, v in rows(cur, "select 'document', document_id, visibility from documents "
                                          "where visibility is not null union all "
                                          "select 'statement', statement_id, visibility from statements "
                                          "where visibility is not null") if v not in known]
    errors += [f"document {i} ({f}) has no visibility label"
               for i, f in rows(cur, "select document_id, source_file from documents where visibility is null")]
    return errors


def check_books(cur: psycopg.Cursor) -> list[str]:
    """12. Every book that holds positions is entitled to someone."""
    known = {r[0] for r in rows(cur, "select distinct unnest(books) from entitlements")}
    return [f"book {b} ({n} position rows) is granted to no user; nobody can see it"
            for b, n in rows(cur, "select book, count(*) from positions group by book order by book") if b not in known]


def check_values(cur: psycopg.Cursor) -> list[str]:
    """9. Stakes within 0-100; holds=false only on predicates that record a denial."""
    errors = [f"statement {sid}: {p} value_num {v} outside 0-100"
              for sid, p, v in rows(cur, "select statement_id, predicate, value_num from statements "
                                         "where predicate = 'OWNS' and value_num is not null "
                                         "and value_num not between 0 and 100")]
    errors += [f"ownership row {i}: stake_pct {v} outside 0-100"
               for i, v in rows(cur, "select ownership_id, stake_pct from ownership where stake_pct not between 0 and 100")]
    errors += [f"statement {sid}: holds=false on {p}"
               for sid, p in rows(cur, "select statement_id, predicate from statements where not holds")
               if p not in HOLDS_FALSE_OK]
    return errors


def check_annotation(cur: psycopg.Cursor) -> list[str]:
    """10. Every document is annotated: RULE rows equal the alias scan; LLM rows contain every unambiguous scan match."""
    patterns = alias_patterns(cur)
    errors = []
    cols = list(ABOUT_COLUMNS.values())
    for doc_id, source_file, title, text, annotated_by, *arrays in rows(
            cur, f"select document_id, source_file, title, text, annotated_by, {', '.join(cols)} from documents order by 1"):
        stored = dict(zip(cols, [sorted(a) for a in arrays]))
        mentions = scan_mentions(document_scan_text({"title": title, "text": text}), patterns)
        if annotated_by == "RULE" and stored != mention_ids(mentions):
            errors.append(f"document {doc_id} ({source_file}): RULE annotation differs from the alias scan; reload")
        elif annotated_by == "LLM":
            sure = mention_ids(mentions, unambiguous_only=True)
            missing = {c: sorted(set(sure[c]) - set(stored[c])) for c in cols if set(sure[c]) - set(stored[c])}
            if missing:
                errors.append(f"document {doc_id} ({source_file}): LLM annotation lacks unambiguous scan matches {missing}")
    return errors


def check_roles(cur: psycopg.Cursor) -> list[str]:
    """11. Role memberships in Postgres equal entitlements.yaml."""
    with open(config.PACK_DIR / "entitlements.yaml", encoding="utf-8") as f:
        users = yaml.safe_load(f)["users"]
    errors = []
    for user, ent in users.items():
        want = {f"book_{b.lower()}" for b in ent["books"]} | {f"vis_{v}" for v in ent["research_visibility"]}
        have = {r[0] for r in rows(cur, "select g.rolname from pg_auth_members m join pg_roles g on g.oid = m.roleid "
                                        "join pg_roles u on u.oid = m.member where u.rolname = %s "
                                        "and (g.rolname like 'book\\_%%' or g.rolname like 'vis\\_%%')", (user,))}
        if not rows(cur, "select 1 from pg_roles where rolname = %s", (user,)):
            errors.append(f"role {user} does not exist")
        for g in sorted(want - have):
            errors.append(f"role {user} lacks {g} (entitlements.yaml grants it)")
        for g in sorted(have - want):
            errors.append(f"role {user} has {g} (not in entitlements.yaml)")
    return errors


NEEDS_IDS = (check_aliases, check_statement_refs)
CHECKS = (check_schema, check_aliases, check_unresolved_names, check_statement_refs, check_no_reference_statements,
          check_positions, check_quotes, check_visibility, check_values, check_annotation, check_roles,
          check_books)


def run_checks(cur: psycopg.Cursor) -> dict[str, list[str]]:
    """{check name: failures} for every check; the test suite runs this too."""
    ids = entity_ids(cur)
    return {(c.__doc__ or c.__name__).split("\n")[0]: (c(cur, ids) if c in NEEDS_IDS else c(cur)) for c in CHECKS}


def report(cur: psycopg.Cursor) -> None:
    """Informational: data_quality by kind and row counts per table."""
    print("data_quality (as of today):")
    for kind, n in rows(cur, "select kind, count(*) from data_quality group by 1 order by 1"):
        print(f"  {kind:<20} {n:>5}")
    print("rows:")
    for (table,) in rows(cur, "select table_name from information_schema.tables "
                              "where table_schema = 'public' and table_type = 'BASE TABLE' order by 1"):
        cur.execute(sql.SQL("select count(*) from {}").format(sql.Identifier(table)))
        print(f"  {table:<20} {cur.fetchone()[0]:>5}")


def main() -> None:
    with psycopg.connect(config.admin_dsn(), autocommit=True) as conn, conn.cursor() as cur:
        failures = 0
        for name, errors in run_checks(cur).items():
            print(f"{'FAIL' if errors else 'ok  '} {name}")
            for e in errors:
                print(f"     - {e}")
            failures += len(errors)
        report(cur)
    print(f"{failures} failure(s)" if failures else "all checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
