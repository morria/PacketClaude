"""
Web search tool for Claude
Provides internet search capability using DuckDuckGo
"""
import logging
import json
from typing import Optional, List, Dict

try:
    from ddgs import DDGS
except ImportError:
    # Fallback for older package name
    from duckduckgo_search import DDGS


logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search tool using DuckDuckGo
    """

    def __init__(self, max_results: int = 5, enabled: bool = True):
        """
        Initialize web search tool

        Args:
            max_results: Maximum number of search results to return
            enabled: Enable/disable search functionality
        """
        self.max_results = max_results
        self.enabled = enabled

    def search(self, query: str) -> str:
        """
        Perform web search

        Args:
            query: Search query

        Returns:
            JSON string with search results
        """
        if not self.enabled:
            return json.dumps({
                "error": "Web search is disabled"
            })

        try:
            logger.info(f"Performing web search: {query}")

            # Perform search using DuckDuckGo
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.max_results))

            # Format results
            formatted_results = []
            for idx, result in enumerate(results, 1):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })

            logger.info(f"Found {len(formatted_results)} search results")

            return json.dumps({
                "query": query,
                "results": formatted_results
            })

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return json.dumps({
                "error": f"Search failed: {str(e)}"
            })

    def get_tool_definition(self) -> Dict:
        """
        Get Claude API tool definition for web search

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "web_search",
            "description": "Search the internet for current information. Use this when you need up-to-date information, facts, news, or information beyond your knowledge cutoff. Returns a list of search results with titles, URLs, and snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the internet"
                    }
                },
                "required": ["query"]
            }
        }

    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute tool call from Claude

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool result as string
        """
        if tool_name == "web_search":
            query = tool_input.get("query", "")
            if not query:
                return json.dumps({"error": "No query provided"})
            return self.search(query)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
