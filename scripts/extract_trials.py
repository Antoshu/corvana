"""Run the LLM extraction on one document N times and show which expected statements each run produces.

Nothing is written to the database. Use it to see how stable the extractor is for a document, and to try a
prompt change: edit build_extraction_prompt in src/kl/extract.py, run this again, compare.

    uv run python scripts/extract_trials.py                     # document 13 (the 2026-10-28 Bank B note), 5 runs
    uv run python scripts/extract_trials.py --runs 10
    uv run python scripts/extract_trials.py --document 4        # any document id; expected rows only known for 13
    uv run python scripts/extract_trials.py --show-prompt       # print the prompt sent, then exit

Relationship extraction is an experiment (decision 2026-11-01): kl-update does not run it and no test asserts
its rows. `uv run kl-annotate --document 13 --extract` stores what passes the auto-check, if you want it in the database.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date

import anthropic
import psycopg
from psycopg.rows import dict_row

from kl import config
from kl.extract import build_extraction_prompt, check_statements, extract_document

# The three rows tests/expected/update_2026-10-28.md asks for from document 13: (subject, predicate, object).
EXPECTED_13 = {
    ("ISS-0001", "OWNS", "ISS-0005"): "state owns 20% of CorTel",
    ("ISS-0005", "TRADES_AS_PROXY_FOR", "ISS-0001"): "CorTel trades with the sovereign",
    ("ISS-0004", "GUARANTEED_BY", "ISS-0001"): "CDB explicitly guaranteed",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--document", type=int, default=13, help="document id (default 13, the delta note)")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--show-prompt", action="store_true")
    args = ap.parse_args()

    with psycopg.connect(config.admin_dsn(), row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("select * from documents where document_id = %s", (args.document,))
        doc = cur.fetchone()
        if doc is None:
            raise SystemExit(f"document {args.document} not found; run kl-load (and kl-update for 13) first")
        if args.show_prompt:
            print(build_extraction_prompt(cur, doc))
            return

        expected = EXPECTED_13 if args.document == 13 else {}
        client = anthropic.Anthropic()
        print(f"model {config.ANNOTATE_MODEL}; document {doc['document_id']} {doc['source_file']}; {args.runs} runs\n")
        seen: Counter[tuple[str, str, str]] = Counter()
        for i in range(1, args.runs + 1):
            extraction = extract_document(client, doc, cur)
            accepted, rejected = check_statements(cur, doc, extraction.statements, date.today())
            keys = [(a["subject_id"], a["predicate"], a["object_id"]) for a in accepted]
            seen.update(set(keys))
            got = [k for k in expected if k in keys]
            missing = [k for k in expected if k not in keys]
            extra = [k for k in keys if k not in expected]
            print(f"run {i}: {len(accepted)} accepted, {len(rejected)} rejected"
                  + (f"; expected found {len(got)}/{len(expected)}" if expected else ""))
            for k in missing:
                print(f"   MISSING  {k[0]} {k[1]} {k[2]}   ({expected[k]})")
            for k in extra:
                print(f"   extra    {k[0]} {k[1]} {k[2]}")
            for r in rejected:
                print(f"   rejected {r['raw'].get('subject_name')} {r['raw'].get('predicate')} "
                      f"{r['raw'].get('object_name')}: {r['reason']}")
        print("\nhow often each accepted row appeared:")
        for k, n in sorted(seen.items(), key=lambda kv: -kv[1]):
            tag = "expected" if k in expected else "extra"
            print(f"  {n}/{args.runs}  {k[0]} {k[1]} {k[2]}  [{tag}]")
        if expected:
            never = [k for k in expected if seen[k] == 0]
            if never:
                print("\nnever produced:", ", ".join(" ".join(k) for k in never))
        conn.rollback()  # belt and braces: nothing was written


if __name__ == "__main__":
    main()
