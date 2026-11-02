"""MCP server over kl.tools (stdio), eight tools. `user` is a required argument on every tool: the proof-of-concept
stand-in for an authenticated identity. Entitlements are still enforced by Postgres under SET ROLE.

Uses mcp 2.x, where FastMCP is called MCPServer.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from kl import tools

mcp = MCPServer("corvana-knowledge-layer",
                instructions="Corvana knowledge layer: positions, exposure paths, links with provenance, "
                             "research documents and ratings. Every tool takes the asking user; results are "
                             "filtered by that user's entitlements. Cite statement ids, edge ids and document "
                             "text; a document's summary is a pointer, never a citation.")


@mcp.tool()
def find_entity(user: str, query: str, as_of: date | None = None) -> list[dict[str, Any]]:
    """Look up an issuer, instrument, curve, country or currency by any name, id, ISIN or ticker."""
    return [m.model_dump(mode="json") for m in tools.find_entity(user, query, as_of)]


@mcp.tool()
def get_positions(user: str, as_of: date | None = None) -> list[dict[str, Any]]:
    """The user's positions on the latest date on or before as_of, each resolved to an instrument or flagged."""
    return [p.model_dump(mode="json") for p in tools.get_positions(user, as_of)]


@mcp.tool()
def get_exposure(user: str, target_id: str, as_of: date | None = None, detail: Literal["summary", "full"] = "summary",
                 max_documents: int | None = 10, max_positions: int | None = 200) -> dict[str, Any]:
    """Per resolved position, the verdict and every channel linking its instrument to the target entity; the
    holdings the layer could not identify in `unresolved`; the visible research about the entities on the paths,
    ranked in SQL and capped. summary (default): one edge id per hop, flag kinds, research without text. full:
    every citation per hop and the documents' text. max_positions caps the summary's positions (largest absolute
    quantity kept, the rest counted in positions_omitted)."""
    return tools.get_exposure(user, target_id, as_of, detail, max_documents, max_positions).model_dump(mode="json")


@mcp.tool()
def get_path(user: str, instrument_id: str, target_id: str, channel_key: str,
             as_of: date | None = None) -> dict[str, Any]:
    """The representative path of one channel (key from get_exposure) from an instrument to the target, with
    every citation on every hop and the number of paths considered."""
    return tools.get_path(user, instrument_id, target_id, channel_key, as_of).model_dump(mode="json")


@mcp.tool()
def get_statements(user: str, entity_id: str, predicate: str | None = None,
                   as_of: date | None = None) -> dict[str, Any]:
    """Links about an entity as of a date, over statements and level-1 edges: current value per link, other
    sources, flags, and a count of newer statements the user is not entitled to see."""
    return tools.get_statements(user, entity_id, predicate, as_of).model_dump(mode="json")


@mcp.tool()
def get_documents(user: str, entity_id: str | None = None, since: date | None = None,
                  as_of: date | None = None, text: bool = False) -> list[dict[str, Any]]:
    """Research notes and desk-note lines visible to the user, optionally only those about an entity. Each row
    has the about_* ids, topics and a summary (a pointer to the document, not a citation); text=True adds the
    text."""
    return [d.model_dump(mode="json") for d in tools.get_documents(user, entity_id, since, as_of, text)]


@mcp.tool()
def get_document(user: str, document_id: int) -> dict[str, Any]:
    """One document with its text (the citable content). Not visible to the user or missing: an error."""
    return tools.get_document(user, document_id).model_dump(mode="json")


@mcp.tool()
def get_ratings(user: str, issuer_id: str, as_of: date | None = None) -> dict[str, Any]:
    """Rating history and current rating of an issuer, and notches versus its sovereign."""
    return tools.get_ratings(user, issuer_id, as_of).model_dump(mode="json")


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
