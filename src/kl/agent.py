"""Claude agent over kl.tools, using the SDK tool runner.

The asking user is bound by this harness when the tools are built, never chosen by the model: every tool closure
calls kl.tools with that user, so Postgres row-level security decides what the agent can see.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from datetime import date
from typing import Any

from anthropic import beta_tool

from kl import config, tools

DEFAULT_QUESTION = ("If the Republic of Corvana is downgraded, what in my book is exposed, how, "
                    "and what does our research say about it?")
SYSTEM = """You are a research assistant for a portfolio manager. Today is {as_of}.
Answer only from tool results. Start with get_exposure: it returns a summary (per position the verdict, the
channels with one edge id per hop, the flag kinds; the holdings the layer could not identify in `unresolved`;
the research ranked by relevance with a one-line summary each). Call get_path only for the channels you will
describe in detail, and get_document only for the documents you will quote.
Cite every fact with its statement id or edge id in square brackets, e.g. [stmt 18] or
[instruments:INS-1004:issuer_id] (the summary's edge_ids are enough for a channel you do not drill into), or
with the document id and a short verbatim quote of its text, e.g. [doc 8: "explicitly guaranteed"]. Use exactly
these forms: "[stmt 15]" with a space and no colon, "[edge id]" as returned, and "[doc 8: "quote"]"; no other. A
document's summary and topics are pointers that help you choose which documents to read; never cite or quote a
summary, only the text fetched with get_document. Use get_statements for a specific link (entity_id plus
predicate), not entity-wide, and only for links you will discuss.
When a link's status is INFERRED say "inferred"; when it is PROPOSED say "research only, unconfirmed". When a
current row in a get_statements result has hidden_newer_count > 0, say that newer information on that link
exists that the user is not entitled to see, naming the link (e.g. "newer information on the state's stake in
CPL exists that you are not entitled to see"), never the sovereign or the book in general, and nothing more
about it. List the unresolved holdings explicitly, with their amount and the flag message; they are neither
exposed nor safe. Do not mention entities or documents the tools did not return."""

Call = dict[str, Any]


def _day(value: str | None, default: date) -> date:
    return date.fromisoformat(value) if value else default


def make_tools(user: str, today: date, calls: list[Call]) -> list[Any]:
    """The eight tools, bound to one user and default date. Every call and its JSON result is appended to calls."""

    def run(name: str, args: dict[str, Any], fn: Callable[[], Any]) -> str:
        try:
            result = fn()
            text = (json.dumps([r.model_dump(mode="json") for r in result]) if isinstance(result, list)
                    else result.model_dump_json())
        except ValueError as e:                              # unknown id or name: tell the model, keep going
            text = json.dumps({"error": str(e)})
        calls.append({"name": name, "args": args, "result": text})
        return text

    @beta_tool
    def find_entity(query: str) -> str:
        """Find issuers, instruments, curves, countries or currencies by any name, ISIN, ticker or id.

        Args:
            query: A name, alias, ISIN, ticker or id, e.g. "Republic of Corvana" or "XS2600112234".
        """
        return run("find_entity", {"query": query}, lambda: tools.find_entity(user, query, today))

    @beta_tool
    def get_positions() -> str:
        """The user's positions on the latest position date, each resolved to an instrument or marked unresolved."""
        return run("get_positions", {}, lambda: tools.get_positions(user, today))

    @beta_tool
    def get_exposure(target_id: str, max_documents: int = 10) -> str:
        """Summary of how each of the user's positions is exposed to a target entity. Call this first.

        Per resolved position: the verdict (yes / unconfirmed / no), every channel linking its instrument to the
        target (issuance, guarantee, ownership, country of risk, currency, curve, proxy, beta, correlation) with
        its key, grade, hop count and one citable edge id per hop, and the data-quality flag kinds with their
        message. `unresolved`: holdings the layer could not identify, with amount and flag message; report them
        as neither exposed nor safe. `research`: the documents the user may read about the entities on the
        paths, ranked by path entities matched then newest, each with id, title, date, label, one-line summary,
        topics and the path entities it is about; no text. Drill down with get_path (every citation on one
        channel) and get_document (the text to quote).

        Args:
            target_id: Entity id of the target, e.g. "ISS-0001". Use find_entity to get it from a name.
            max_documents: Cap on the ranked research list (default 10).
        """
        return run("get_exposure", {"target_id": target_id, "max_documents": max_documents},
                   lambda: tools.get_exposure(user, target_id, today, "summary", max_documents))

    @beta_tool
    def get_path(instrument_id: str, target_id: str, channel_key: str) -> str:
        """The representative path of one channel from an instrument to the target, with every citation on every
        hop (statement ids, level-1 edge ids, source, as-of, quote, status) and the number of paths considered.
        Use it for the channels you describe in detail.

        Args:
            instrument_id: The position's instrument id, e.g. "INS-1005".
            target_id: The target entity id, e.g. "ISS-0001".
            channel_key: The channel key from get_exposure, e.g. "OWNS" or "COUNTRY_OF_RISK>SOVEREIGN_IS".
        """
        return run("get_path", {"instrument_id": instrument_id, "target_id": target_id, "channel_key": channel_key},
                   lambda: tools.get_path(user, instrument_id, target_id, channel_key, today))

    @beta_tool
    def get_statements(entity_id: str, predicate: str | None = None, as_of: str | None = None) -> str:
        """All links about an entity as of a date, with the current value per link.

        Covers statements (rules and documents) and level-1 edges (security master, ownership tracker, curated
        country data) together. Returns the precedence winner per link, the other sources, data-quality flags
        (STALE, CONFLICT, CORROBORATED, SUPERSEDED), and hidden_newer_count: on each current row, the number of
        newer statements on that link the user is not entitled to see (a count only); the top-level figure is
        the sum.

        Args:
            entity_id: Entity id, e.g. "ISS-0003".
            predicate: Optional predicate filter, e.g. "OWNS", "COUNTRY_OF_RISK", "GUARANTEED_BY".
            as_of: Optional date YYYY-MM-DD for a point-in-time answer; defaults to today.
        """
        day = _day(as_of, default=today)
        return run("get_statements", {"entity_id": entity_id, "predicate": predicate, "as_of": as_of},
                   lambda: tools.get_statements(user, entity_id, predicate, day))

    @beta_tool
    def get_documents(entity_id: str | None = None) -> str:
        """Research notes and desk-note lines the user may read, without their text: what each is about
        (about_issuers, about_instruments, about_curves, about_currencies), topics and a one-line summary.
        The summary is a pointer, never a citation; fetch the text with get_document before quoting.

        Args:
            entity_id: Optional entity id; only documents about it are returned.
        """
        return run("get_documents", {"entity_id": entity_id}, lambda: tools.get_documents(user, entity_id, None, today))

    @beta_tool
    def get_document(document_id: int) -> str:
        """One document with its text, the only citable content of a document. Use it for every document you
        quote. A document the user is not entitled to read comes back as an error.

        Args:
            document_id: The document id from get_exposure or get_documents, e.g. 8.
        """
        return run("get_document", {"document_id": document_id}, lambda: tools.get_document(user, document_id))

    @beta_tool
    def get_ratings(issuer_id: str) -> str:
        """Rating history and current rating of an issuer, and notches versus its sovereign.

        Args:
            issuer_id: Issuer id, e.g. "ISS-0001".
        """
        return run("get_ratings", {"issuer_id": issuer_id}, lambda: tools.get_ratings(user, issuer_id, today))

    return [find_entity, get_positions, get_exposure, get_path, get_statements, get_documents, get_document, get_ratings]


def slug(question: str) -> str:
    if question == DEFAULT_QUESTION:
        return "exposure"
    words = re.findall(r"[a-z0-9]+", question.lower())
    return "-".join(words[:6]) or "question"


def transcript(user: str, as_of: date, question: str, calls: list[Call], answer: str) -> str:
    lines = [f"# Agent transcript: {user}, as of {as_of}", "", f"Model: {config.ANTHROPIC_MODEL}", "",
             "## Question", "", question, "", "## Tool calls", ""]
    for i, c in enumerate(calls, 1):
        args = ", ".join(f"{k}={v!r}" for k, v in c["args"].items())
        pretty = json.dumps(json.loads(c["result"]), indent=2)
        lines += [f"### {i}. {c['name']}({args})", "", "<details><summary>result</summary>", "", "```json",
                  pretty, "```", "", "</details>", ""]
    lines += ["## Answer", "", answer]
    return "\n".join(lines) + "\n"


def ask(user: str, question: str, as_of: date) -> tuple[str, list[Call]]:
    """Run the tool loop to completion. Exits with status 2 if the model refuses."""
    import anthropic

    client = anthropic.Anthropic()
    calls: list[Call] = []
    runner = client.beta.messages.tool_runner(
        model=config.ANTHROPIC_MODEL, max_tokens=16000, system=SYSTEM.format(as_of=as_of),
        tools=make_tools(user, as_of, calls), messages=[{"role": "user", "content": question}])
    last = None
    for message in runner:
        if message.stop_reason == "refusal":
            print(f"refused: {message.stop_details}", file=sys.stderr)
            sys.exit(2)
        last = message
    answer = "".join(b.text for b in last.content if b.type == "text") if last else ""
    return answer, calls


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the knowledge-layer agent a question as one user.")
    parser.add_argument("--user", required=True, choices=["alice", "bob", "carol"])
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--as-of", type=date.fromisoformat, default=config.AS_OF)
    parser.add_argument("--dry-run", action="store_true", help="print the system prompt and tool schemas; no API call")
    args = parser.parse_args()
    if args.dry_run:
        print(SYSTEM.format(as_of=args.as_of), "\n")
        print(json.dumps([t.to_dict() for t in make_tools(args.user, args.as_of, [])], indent=2))
        return
    if not config.llm_available():
        raise SystemExit("kl-agent needs ANTHROPIC_API_KEY (put it in .env); use kl-demo for the scripted run")
    answer, calls = ask(args.user, args.question, args.as_of)
    text = transcript(args.user, args.as_of, args.question, calls, answer)
    config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.TRANSCRIPTS_DIR / f"agent_{args.user}_{slug(args.question)}.md"
    out.write_text(text, encoding="utf-8")
    print(answer)
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
