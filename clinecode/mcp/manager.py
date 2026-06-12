from __future__ import annotations

import logging

from clinecode.config import MCPServerConfig
from clinecode.mcp.client import MCPClient
from clinecode.mcp.tool_wrapper import MCPToolWrapper
from clinecode.tools import ToolRegistry

logger = logging.getLogger(__name__)


class MCPManager:


    def __init__(self) -> None:
        self._configs: dict[str, MCPServerConfig] = {}
        self._clients: dict[str, MCPClient] = {}


    def load_configs(self, configs: list[MCPServerConfig]) -> None:
        for cfg in configs:
            self._configs[cfg.name] = cfg

# 批量注册 MCP（Model Context Protocol）工具到指定的工具注册表中
    async def register_all_tools(self, registry: ToolRegistry) -> list[str]:
        errors: list[str] = []
        for name, config in self._configs.items():
            try:
                client = MCPClient(config)
                await client.connect()
                self._clients[name] = client

                tools = await client.list_tools()
                for tool_def in tools:
                    wrapper = MCPToolWrapper(name, tool_def, client)
                    registry.register(wrapper)
                    logger.info("Registered MCP tool: %s", wrapper.name)

            except Exception as e:
                msg = f"MCP server '{name}': {e}"
                logger.warning(msg)
                errors.append(msg)

        return errors


    async def get_client(self, name: str) -> MCPClient | None:
        client = self._clients.get(name)
        if client is None: #客户端不在缓存里
            config = self._configs.get(name)
            if config is None: #看有没有配置
                return None
            client = MCPClient(config) #有就现场创建
            await client.connect() 
            self._clients[name] = client
            return client

        if not client.is_alive: #如果在缓存里但连接断了
            logger.info("Reconnecting MCP server '%s'", name)
            await client.close() #先关旧的
            client = MCPClient(self._configs[name]) #每次重连都创建新的MCPClient实例，避免旧的AsyncExitStack状态混乱
            await client.connect()
            self._clients[name] = client

        return client


    async def shutdown(self) -> None:
        for name, client in self._clients.items():
            try:
                await client.close()
                logger.info("MCP server '%s' closed", name)
            except Exception:
                logger.debug("Error closing MCP server '%s'", name, exc_info=True)
        self._clients.clear()
