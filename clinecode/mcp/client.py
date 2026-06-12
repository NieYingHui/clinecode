from __future__ import annotations

import logging
import os
from contextlib import AsyncExitStack #Python 特有的异步资源管理器
from typing import Any

import httpx #HTTP 客户端库
from mcp import ClientSession, types
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

from clinecode.config import MCPServerConfig, build_child_env, resolve_env_vars

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, config: MCPServerConfig) -> None:
        self.config = config
        self.name = config.name
        self._session: ClientSession | None = None #_session是MCP SDK 提供的会话对象，所有协议操作都走它
        self._stack: AsyncExitStack | None = None
        self._alive = False #用来快速判断连接是否存活


    @property
    def is_alive(self) -> bool:
        return self._alive


    async def connect(self) -> None:
        if self._alive: #是幂等保护，重复调用不会创建多余连接
            return

        self._stack = AsyncExitStack() #异步退出栈，用于管理多个异步上下文管理器
        await self._stack.__aenter__() #进入退出栈的上下文

        try:
            if self.config.is_stdio:
                read, write = await self._connect_stdio()
            else:
                read, write = await self._connect_http()

            session = await self._stack.enter_async_context(
                ClientSession(read, write) #创建会话对象，并将其注册到退出栈中
            )
            await session.initialize() # 初始化会话
            self._session = session
            self._alive = True
            logger.info("MCP server '%s' connected", self.name)
        except Exception:
            await self._cleanup_stack() #清理资源，并重新抛出异常
            raise


    async def _connect_stdio(self) -> tuple[Any, Any]:
        assert self._stack is not None #确保不为空
        assert self.config.command is not None

        params = StdioServerParameters( #使用配置中的命令、参数和环境变量创建 StdioServerParameters 对象
            command=self.config.command,
            args=self.config.args,
            env=build_child_env(self.config.env),
        )
        devnull = open(os.devnull, "w")
        self._stack.callback(devnull.close)
        read, write = await self._stack.enter_async_context(
            stdio_client(params, errlog=devnull) #stdio_client 创建异步上下文管理器，建立与子进程的通信
        )
        return read, write

    async def _connect_http(self) -> tuple[Any, Any]:
        assert self._stack is not None
        assert self.config.url is not None

        resolved_headers = {
            k: resolve_env_vars(v) for k, v in self.config.headers.items()
        }
        http_client = httpx.AsyncClient( #创建一个异步 HTTP 客户端
            headers=resolved_headers,
            follow_redirects=True, #表示自动跟随 HTTP 重定向
        )
        await self._stack.enter_async_context(http_client) #进入异步上下文,以便在退出时自动清理资源

        result = await self._stack.enter_async_context(
            streamable_http_client(self.config.url, http_client=http_client) #streamable_http_client传入URL和HTTP客户端,返回一个流式客户端
        )
        read, write = result[0], result[1]
        return read, write


    async def list_tools(self) -> list[types.Tool]:
        assert self._session is not None
        result = await self._session.list_tools()
        return list(result.tools) #SDK 发送tools/list请求。1ist（）是防御性复制，调用方拿到的是独立拷贝


    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> types.CallToolResult:
        assert self._session is not None
        return await self._session.call_tool(name, arguments)

    async def close(self) -> None:
        self._alive = False #先标记死亡
        self._session = None 
        await self._cleanup_stack() #再释放资源

    async def _cleanup_stack(self) -> None:
        if self._stack is not None:
            try:
                await self._stack.__aexit__(None, None, None)
            except RuntimeError as e:
                if "cancel scope" in str(e):
                    logger.debug("Cancel scope cleanup (expected during shutdown): %s", e)
                else:
                    raise
            except Exception:
                logger.debug("Error closing stack for '%s'", self.name, exc_info=True)
            self._stack = None
