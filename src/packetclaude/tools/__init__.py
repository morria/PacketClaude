"""
Tools for Claude AI
Provides additional capabilities like web search and POTA spots
"""
from .web_search import WebSearchTool
from .pota_spots import POTASpotsTool

__all__ = ['WebSearchTool', 'POTASpotsTool']
