

from __future__ import annotations

# Delayed import to avoid circular import
def get_mcp_manager():
    from clinecode.mcp.manager import MCPManager
    return MCPManager

__all__ = ["get_mcp_manager"]

