"""Compare the grounded LLM annotation stored on documents.about_* with the deterministic alias scan.

Reads only. For every document it prints three set sizes and the ids that differ:
  scan_all   every alias match in title + text, ambiguous candidates included (countries have no column)
  unamb      only matches with exactly one candidate (what the rule keeps on its own)
  llm        the about_* arrays as stored after kl-annotate (scan floor ∪ model choices and additions)

    uv run python scripts/annotation_vs_scan.py
"""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from kl import config, resolve

COLS = ["about_issuers", "about_instruments", "about_curves", "about_currencies"]


def main() -> None:
    with psycopg.connect(config.admin_dsn(), row_factory=dict_row) as conn, conn.cursor() as cur:
        pats = resolve.alias_patterns(cur)
        cur.execute("select * from documents order by document_id")
        tot = {"scan_all": 0, "unamb": 0, "llm": 0}
        for d in cur.fetchall():
            text = resolve.document_scan_text(d)
            scan = resolve.rule_annotation(text, pats)
            unamb = resolve.mention_ids(resolve.scan_mentions(text, pats), True)
            S = {(c, i) for c in COLS for i in scan.get(c, [])}
            U = {(c, i) for c in COLS for i in unamb.get(c, [])}
            L = {(c, i) for c in COLS for i in d[c]}
            tot["scan_all"] += len(S); tot["unamb"] += len(U); tot["llm"] += len(L)
            title = (d["title"] or d["text"][:50]).replace("\n", " ")
            print(f"doc {d['document_id']:>2} {title[:48]:<48} scan_all={len(S):>2} unamb={len(U):>2} llm={len(L):>2}"
                  f"  llm-only={sorted(i for _, i in L - S)}  scan-only={sorted(i for _, i in S - L)}")
        print(f"\ntotals: scan_all={tot['scan_all']} unamb={tot['unamb']} llm={tot['llm']}")


if __name__ == "__main__":
    main()
