from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from clinecode.hooks.conditions import ConditionGroup


@dataclass
class Action:
    type: str
    command: str = ""
    message: str = ""
    url: str = ""
    method: str = "POST"
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    prompt: str = ""
    timeout: int = 30


@dataclass
class ActionResult: # ActionResult是动作执行器的返回值，output是输出文本，success标记是否成功。
    output: str = ""
    success: bool = True


@dataclass
class Hook: # 1个Hook 就是一条规则：在什么事件、满足什么条件时、执行什么动作。
    id: str
    event: str
    action: Action 
    condition: ConditionGroup | None = None
    reject: bool = False # 表示这个 Hook 触发后要拦截工具执行，只能用在pre_tool_use
    once: bool = False
    async_exec: bool = False
    executed: bool = False


    def should_run(self) -> bool:
        if self.once and self.executed:
            return False
        return True


    def mark_executed(self) -> None:
        self.executed = True


@dataclass
class HookContext: #每次触发事件时，调用方把当前上下文打包成 HookContext。
    event_name: str = ""
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    file_path: str = ""
    message: str = ""
    error: str = ""

    def get_field(self, name: str) -> str: #get_field是条件匹配的入口，把字段名映射到具体的值：
        if name == "tool":
            return self.tool_name
        if name == "event":
            return self.event_name
        if name.startswith("args."):
            key = name[5:]
            value = self.tool_args.get(key, "")
            return str(value) if value else ""
        return ""

    def expand(self, template: str) -> str: # expand做模板变量替換，把命令或消息模板里的$ToOL_NAME、$FILE_PATH 替換成真实值：
        result = template
        result = result.replace("$EVENT", self.event_name)
        result = result.replace("$TOOL_NAME", self.tool_name)
        result = result.replace("$FILE_PATH", self.file_path)
        result = result.replace("$MESSAGE", self.message)
        result = result.replace("$ERROR", self.error)
        for key, value in self.tool_args.items():
            result = result.replace(f"$TOOL_ARGS.{key}", str(value))
        return result

# Too1RejectedError是 Hook 系统唯一向外「冒泡」的异常。当 pre-tool Hook 拒绝了—个工具调用时，
# 引擎构造这个错误返回给 Agent Loop，Agent Loop 把拒绝原因作为工具结果返回给 LLM。
class ToolRejectedError(Exception):
    def __init__(self, tool: str, reason: str, hook_id: str) -> None:
        self.tool = tool
        self.reason = reason
        self.hook_id = hook_id
        super().__init__(f"Tool '{tool}' rejected by hook '{hook_id}': {reason}")
