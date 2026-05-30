"""Bright Data MCP client via langchain-mcp-adapters (SSE transport)."""
import logging
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from dealscout.config import BRIGHT_DATA_TOKEN, MCP_SSE_URL

logger = logging.getLogger(__name__)

# User-facing alias -> Bright Data tool name patterns (first match wins)
TOOL_ALIASES: dict[str, list[str]] = {
    "web_search": ["search_engine", "web_search", "serp"],
    "scraping_browser": ["scraping_browser", "browser_scrape", "browser"],
    "web_unlocker": ["web_unlocker", "scrape_as_markdown", "unlocker"],
    "web_scraper_api": ["web_scraper", "scraper_api", "structured"],
}

_client: MultiServerMCPClient | None = None
_tools: list[BaseTool] | None = None


def _build_client() -> MultiServerMCPClient:
    if not BRIGHT_DATA_TOKEN:
        raise ValueError("BRIGHT_DATA_TOKEN not set in .env")
    return MultiServerMCPClient(
        {
            "bright_data": {
                "url": MCP_SSE_URL,
                "transport": "sse",
            }
        }
    )


async def get_tools() -> list[BaseTool]:
    global _client, _tools
    if _tools is not None:
        return _tools
    _client = _build_client()
    _tools = await _client.get_tools()
    logger.info("Loaded %d Bright Data MCP tools: %s", len(_tools), [t.name for t in _tools])
    return _tools


def _find_tool(tools: list[BaseTool], alias: str) -> BaseTool | None:
    patterns = TOOL_ALIASES.get(alias, [alias])
    for pattern in patterns:
        for tool in tools:
            if pattern.lower() in tool.name.lower():
                return tool
    return None


async def invoke_tool(alias: str, **kwargs: Any) -> str:
    """Invoke a Bright Data MCP tool by alias. Returns text content or error string."""
    try:
        tools = await get_tools()
        tool = _find_tool(tools, alias)
        if tool is None:
            # Fallback: try scrape_as_markdown for any scrape alias
            tool = _find_tool(tools, "web_unlocker")
        if tool is None:
            return f"[error] No MCP tool found for alias '{alias}'"
        result = await tool.ainvoke(kwargs)
        if isinstance(result, str):
            return result
        return str(result)
    except Exception as exc:
        logger.exception("MCP tool %s failed", alias)
        return f"[error] {alias}: {exc}"


async def web_search(query: str) -> str:
    return await invoke_tool("web_search", query=query)


async def scrape_url(url: str, tool_alias: str = "web_unlocker") -> str:
    """Scrape a URL using the specified tool tier."""
    return await invoke_tool(tool_alias, url=url)


async def browser_scrape(url: str) -> str:
    return await invoke_tool("scraping_browser", url=url)
