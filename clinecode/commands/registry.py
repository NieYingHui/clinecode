from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Protocol


class CommandType(str, Enum):
    LOCAL = "local"
    LOCAL_UI = "local_ui"
    PROMPT = "prompt"


class UIController(Protocol):
    def add_system_message(self, text: str) -> None: ... #显示一条系统消息


    def send_user_message(self, text: str) -> None: ... #将文本作为用户消息发送给Agent
    def set_plan_mode(self, enabled: bool) -> None: ... #切换PlanMode
    def get_token_count(self) -> tuple[int, int]: ... #获取当前token数
    def refresh_status(self) -> None: ... #刷新状态栏

# LoCAL：直接await handler，handler内部通过ctx.ui.add_system_message（）展示结果
# LOCAL_UI：也走handler，但handler里会调用ctx.ui.set_plan_mode（）或ctx.config["clear_chat"]（）等UI 操作
# PRoMPT：handler通过ctx.ui.send_user_message（）把构造好的提示词发给 LLM

@dataclass
class CommandContext:
    args: str
    agent: Any
    conversation: Any
    session: Any
    session_manager: Any
    memory_manager: Any
    ui: UIController
    config: Any

# CommandHandler 代表了一个处理命令的异步函数
# 输入参数：接受一个类型为 CommandContext 的参数
# 返回值：返回一个协程对象，即返回类型注解为 Awaitable[None]，表示它是一个异步函数，最终返回 None
CommandHandler = Callable[[CommandContext], Awaitable[None]]


@dataclass
class Command:
    name: str
    description: str
    type: CommandType
    handler: CommandHandler # 执行函数
    aliases: list[str] = field(default_factory=list) #别名
    usage: str = "" # 用法示例
    arg_prompt: str = "" # 参数提示语（可选)
    hidden: bool = False #是否在帮助列表隐藏


class CommandRegistry:


    def __init__(self) -> None:
        self._commands: dict[str, Command] = {} #commands 按主名称索引
        self._alias_map: dict[str, str] = {} #_alias_map 把别名映射到主名称
        self._lock = asyncio.Lock() #锁是为Skll 动态注册准备的，Skill 加载在后台异步进行，和用户操作可能同时发生

    async def register(self, command: Command) -> None: #用于启动阶段批量注册内置命令，不用 await,加锁保护并发安全
        async with self._lock:
            if command.name in self._commands or command.name in self._alias_map:
                raise ValueError(
                    f"Command name '{command.name}' conflicts with an existing command or alias"
                )
            for alias in command.aliases:
                if alias in self._alias_map or alias in self._commands:
                    raise ValueError(
                        f"Alias '{alias}' conflicts with an existing command or alias"
                    )
            self._commands[command.name] = command
            for alias in command.aliases:
                self._alias_map[alias] = command.name

    def register_sync(self, command: Command) -> None: #register_sync用于启动阶段批量注册内置命令，不用await
        if command.name in self._commands or command.name in self._alias_map:
            raise ValueError(
                f"Command name '{command.name}' conflicts with an existing command or alias"
            )
        for alias in command.aliases:
            if alias in self._alias_map or alias in self._commands:
                raise ValueError(
                    f"Alias '{alias}' conflicts with an existing command or alias"
                )
        self._commands[command.name] = command
        for alias in command.aliases:
            self._alias_map[alias] = command.name


    def find(self, name: str) -> Command | None:
        if name in self._commands:
            return self._commands[name]
        canon = self._alias_map.get(name)
        if canon:
            return self._commands.get(canon)
        return None


    def list_commands(self) -> list[Command]:
        return [cmd for cmd in self._commands.values() if not cmd.hidden]
