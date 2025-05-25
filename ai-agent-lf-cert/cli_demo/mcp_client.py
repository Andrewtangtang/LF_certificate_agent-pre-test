#!/usr/bin/env python3
"""
Simple CLI for interacting with the LF-Cert-Prep FastMCP server.

Usage:
    python mcp_client.py            # list tools
    python mcp_client.py random     # random question
    python mcp_client.py search <query words…>   # semantic search question
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict
from dotenv import load_dotenv

from fastmcp import Client, FastMCP

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")
print(f"MCP_URL: {MCP_URL}")


class MCPClient:
    def __init__(self):
        self.mcp_url = os.getenv("MCP_URL", "http://localhost:8000/mcp")

    async def list_tools(self) -> None:
        client = Client(self.mcp_url)
        async with client:
            tools = await client.list_tools()
            print("Available tools on server:")
            for t in tools:
                print(f"  • {t.name}: {t.description}")
    
    async def random_question(self) -> Dict[str, Any]:
        client = Client(self.mcp_url)
        async with client:
            result = await client.call_tool("get_random_question")
            # result is List[TextContent]; we only need the text of the first element
            qa_json: str = result[0].text
            return json.loads(qa_json)

    async def search_question(self, query: str) -> Dict[str, Any]:
        client = Client(self.mcp_url)
        async with client:
            result = await client.call_tool("get_question_and_answer", {"text": query})
            # result is List[TextContent]; we only need the text of the first element
            qa_json: str = result[0].text
            return json.loads(qa_json)


if __name__ == "__main__":
    try:
        mcp_client = MCPClient()
        result = asyncio.run(mcp_client.search_question("explain the function of kube-proxy"))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except KeyboardInterrupt:
        pass
