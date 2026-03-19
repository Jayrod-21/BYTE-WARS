"""
mcp/ — MCP (Model Context Protocol) tool server for BYTE Wars.

This package contains:
- tool_server.py: FastMCP server with base combat actions registered as tools
- tool_registry.py: Dynamic tool registration system for NFT skills
- tool_bridge.py: Bridge between MCP tool calls and the DamageResolver
- game_state.py: Game state object that bots receive each turn
- bot_response.py: Bot response parsing and validation
"""

from mcp_tools.tool_server import create_mcp_server
from mcp_tools.tool_registry import ToolRegistry
from mcp_tools.tool_bridge import ToolBridge
from mcp_tools.game_state import GameState, build_game_state
from mcp_tools.bot_response import BotResponseParser

__all__ = [
    "create_mcp_server",
    "ToolRegistry",
    "ToolBridge",
    "GameState",
    "build_game_state",
    "BotResponseParser",
]
