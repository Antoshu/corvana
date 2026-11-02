"""Scripted tool calls (no LLM) that print a Markdown report and save it under transcripts/."""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal

from kl import config, tools

PIT_DATE = date(2025, 6, 30)


def call(name: str, **kwargs: object) -> str:
    args = ", ".join(f'{k}="{v}"' if isinstance(v, (str, date)) else f"{k}={v}" for k, v in kwargs.items())
    return f"```\n{name}({args})\n```\n"


def num(v: Decimal | None) -> str:
    return "" if v is None else f"{v.normalize():f}"


def cite_line(c: tools.Citation) -> str:
    sid = f"stmt {c.statement_id}" if c.statement_id else c.edge_id
    doc = f", {c.document_title}" if c.document_title else ""
    vis = f", {c.visibility}" if c.visibility else ""
    return f"[{sid}] {c.predicate} as_of {c.as_of}, {c.source_system} {c.status}{doc}{vis}, '{c.quote or ''}'"


def statement_rows(rows: list[tools.Statement]) -> list[str]:
    out = ["| id | subject | predicate | object | value | as_of | source | status | visibility | quote |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for s in rows:
        value = num(s.value_num) or (s.value_text or "")
        sid = f"stmt {s.statement_id}" if s.statement_id else s.edge_id
        out.append(f"| {sid} | {s.subject_id} | {s.predicate} | {s.object_id} | {value} | {s.as_of} "
                   f"| {s.document_title or s.source_file} ({s.source_system}, tier {s.tier}) | {s.status} "
                   f"| {s.visibility or 'everyone'} | {s.quote or ''} |")
    return out if rows else ["(none)"]


def doc_line(d: tools.ResearchSummary) -> list[str]:
    head = (f"- [doc {d.document_id}] {d.title or 'desk note'} ({d.publisher}, {d.published_at:%Y-%m-%d}, "
            f"{d.visibility})")
    out = [head, f"  - about, on the paths: {', '.join(d.about_on_path) or 'nothing on the paths'}"]
    if d.topics:
        out.append(f"  - topics: {', '.join(d.topics)}")
    if d.summary:
        out.append(f"  - summary (pointer, not a citation; get_document for the text): {d.summary}")
    return out


def exposure_report(user: str, as_of: date) -> str:
    lines = [f"# Exposure to a Corvana downgrade: {user}, as of {as_of}", ""]
    lines.append(call("find_entity", user=user, query="Republic of Corvana"))
    target = tools.find_entity(user, "Republic of Corvana")[0]
    lines += [f"Target: {target.entity_id} {target.name} ({target.match_kind} match)", ""]

    lines.append(call("get_ratings", user=user, issuer_id=target.entity_id, as_of=as_of.isoformat()))
    ratings = tools.get_ratings(user, target.entity_id, as_of)
    cur = ratings.current
    lines += [f"Current rating: {cur.rating} / {cur.outlook} ({cur.agency}, {cur.action_date})" if cur
              else "Current rating: none", ""]

    lines.append(call("get_positions", user=user, as_of=as_of.isoformat()))
    positions = tools.get_positions(user, as_of)
    lines += [f"{len(positions)} positions.", ""]

    lines.append(call("get_exposure", user=user, target_id=target.entity_id, as_of=as_of.isoformat()))
    report = tools.get_exposure(user, target.entity_id, as_of)                       # the summary
    lines += ["## Positions (summary)", "", "| ref | instrument | qty | exposed | channels [grade, hops] | flags |",
              "|---|---|---|---|---|---|"]
    for pe in report.positions:
        p = pe.position
        chans = "; ".join(f"{c.label} [{c.grade}, {c.hop_count}]" for c in pe.channels) or "none"
        flags = ", ".join(sorted({f.kind for f in pe.flags})) or "none"
        lines.append(f"| {p.instrument_ref} | {p.instrument_id} {p.description} | {p.quantity:,.0f} {p.notional_ccy} "
                     f"| {pe.exposed} | {chans} | {flags} |")
    lines.append("")

    lines += ["## Holdings the layer could not identify", ""]
    if report.unresolved:
        lines += ["| ref | qty | flag |", "|---|---|---|"]
        lines += [f"| {u.position.instrument_ref} ({u.position.ref_type}) | {u.position.quantity:,.0f} "
                  f"{u.position.notional_ccy} | {u.flag_message} |" for u in report.unresolved]
        lines += ["", "Not resolved by guess, not counted as exposed and not counted as safe."]
    else:
        lines.append("None.")
    lines.append("")

    lines += ["## Channels (drill-down: get_path per channel, every citation)", ""]
    for pe in report.positions:
        if not pe.channels and not pe.flags:
            continue
        p = pe.position
        lines += [f"### {p.instrument_ref} ({p.instrument_id}): {pe.exposed}", ""]
        for c in pe.channels:
            lines.append("")
            lines.append(call("get_path", user=user, instrument_id=p.instrument_id, target_id=target.entity_id,
                              channel_key=c.key, as_of=as_of.isoformat()))
            path = tools.get_path(user, p.instrument_id, target.entity_id, c.key, as_of)
            lines.append(f"- **{path.label}** [{path.grade}] (1 of {path.paths_considered} paths shown)")
            for h in path.hops:
                lines.append(f"  - {h.from_node} {h.predicate} {h.to_node} [{h.grade}]")
                lines += [f"    - {cite_line(ci)}" for ci in h.citations]
        if pe.flags:
            lines.append("- flags:")
            lines += [f"  - {f.kind}: {f.message}" for f in pe.flags]
        lines.append("")

    lines += [f"## Research about entities on the paths ({len(report.research)} documents the user may read, "
              "ranked by path entities matched, then newest)", ""]
    for d in report.research:
        lines += doc_line(d)
    lines += ["", "## Notes", ""] + [f"- {n}" for n in report.notes]
    return "\n".join(lines) + "\n"


def pit_report(user: str, as_of: date) -> str:
    lines = [f"# State stake in Corvana Power & Light: {user}", ""]
    for when in (PIT_DATE, as_of):
        lines.append(call("get_statements", user=user, entity_id="ISS-0003", predicate="OWNS", as_of=when.isoformat()))
        s = tools.get_statements(user, "ISS-0003", "OWNS", when)
        lines += [f"## as_of {when}", "", "Current (precedence winner per link):", ""] + statement_rows(s.current)
        lines += ["", "Other sources:", ""] + statement_rows(s.other_sources)
        lines += ["", "Flags:", ""] + ([f"- {f.kind}: {f.message}" for f in s.flags] or ["(none)"])
        lines += ["", f"hidden_newer_count: {s.hidden_newer_count}", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scripted knowledge-layer demo (no LLM).")
    parser.add_argument("--user", required=True, choices=["alice", "bob", "carol"])
    parser.add_argument("--question", default="exposure", choices=["exposure", "pit-cpl"])
    parser.add_argument("--as-of", type=date.fromisoformat, default=config.AS_OF)
    args = parser.parse_args()
    text = (exposure_report if args.question == "exposure" else pit_report)(args.user, args.as_of)
    config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.TRANSCRIPTS_DIR / f"{args.user}_{args.question}.md"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"written to {out}")


if __name__ == "__main__":
    main()
