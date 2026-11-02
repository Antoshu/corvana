"""The MCP server as a client sees it: started over stdio, eight tools, entitlements applied per user argument."""
from __future__ import annotations

import json
import sys
from typing import Any

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER = StdioServerParameters(command=sys.executable, args=["-m", "kl.mcp_server"])


def payload(result: Any) -> Any:
    """The tool's return value: structured content when present, else the JSON text block."""
    assert not result.is_error, result.content
    structured = result.structured_content
    data = structured if structured is not None else json.loads(result.content[0].text)
    return data["result"] if isinstance(data, dict) and set(data) == {"result"} else data


async def session_run() -> tuple[list[str], Any, Any]:
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        names = sorted(t.name for t in (await session.list_tools()).tools)
        bob = payload(await session.call_tool("get_positions", {"user": "bob"}))
        alice = payload(await session.call_tool("get_positions", {"user": "alice"}))
        return names, bob, alice


def test_mcp_server():
    names, bob, alice = anyio.run(session_run)
    assert names == ["find_entity", "get_document", "get_documents", "get_exposure", "get_path", "get_positions",
                     "get_ratings", "get_statements"]
    assert len(bob) == 8 and {p["book"] for p in bob} == {"EM_CREDIT"}
    assert len(alice) == 6 and {p["book"] for p in alice} == {"EM_MACRO"}
