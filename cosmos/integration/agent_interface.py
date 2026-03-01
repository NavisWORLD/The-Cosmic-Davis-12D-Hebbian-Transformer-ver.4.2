"""
<<<<<<< HEAD:cosmos/integration/agent_interface.py
cosmos Agent Interface.

"Hello, fellow machine!"

This module allows other AI agents (like Antigravity) to communicate with cosmos
=======
Farnsworth Agent Interface.

"Hello, fellow machine!"

This module allows other AI agents (like Antigravity) to communicate with Farnsworth
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/agent_interface.py
via a standardized high-level API.
"""

from typing import Dict, Any, List
<<<<<<< HEAD:cosmos/integration/agent_interface.py
from cosmos.mcp_server.server import cosmosMCPServer

class AgentInterface:
    def __init__(self, server: cosmosMCPServer):
=======
from farnsworth.mcp_server.server import FarnsworthMCPServer

class AgentInterface:
    def __init__(self, server: FarnsworthMCPServer):
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/agent_interface.py
        self.server = server

    async def query_knowledge(self, query: str):
        """High-level query for external agents."""
        return await self.server.recall(query)

    async def inject_thought(self, content: str):
        """Allow external agent to plant a thought."""
        return await self.server.remember(content, tags=["external_agent", "antigravity"])

    async def request_task(self, task_description: str):
<<<<<<< HEAD:cosmos/integration/agent_interface.py
        """Ask cosmos to do something."""
=======
        """Ask Farnsworth to do something."""
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/agent_interface.py
        return await self.server.delegate(task_description, agent_type="auto")

# This interface can be exposed via HTTP/RPC/MCP
