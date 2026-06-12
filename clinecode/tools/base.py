from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".tox", ".mypy_cache"}

MAX_OUTPUT_CHARS = 10000

ToolCategory = Literal["read", "write", "command"]


@dataclass
class ToolResult:
    output: str
    is_error: bool = False


class Tool(ABC): #ABC Abstract Base Class 确保所有继承 Tool 的子类必须实现特定的方法。
    name: str
    description: str
    params_model: type[BaseModel]
    category: ToolCategory = "read" #工具类别
    is_concurrency_safe: bool = False #是否并发安全
    is_system_tool: bool = False #是否为系统工具
    should_defer: bool = False #是否应该延迟执行   提升速度，节省内存，只有当需要的时候才加载tool

    @property
    def is_read_only(self) -> bool:
        return self.category == "read"


    def get_schema(self) -> dict[str, Any]:
        schema = self.params_model.model_json_schema()
        schema.pop("title", None)
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": schema,
        }

    @abstractmethod
    async def execute(self, params: BaseModel) -> ToolResult: ...
# 调用这个方法时，它不会立即执行完，而是返回一个协程对象。
# 需要在调用前使用 await 关键字（例如 result = await tool.execute(params)）

# --- 流式事件 ---

#在流式输出中，模型不是一次性返回所有文字，而是一个字、一个词地吐出来。每当有新的文字生成时，就会产生一个 TextDelta 事件。
@dataclass
class TextDelta: 
    text: str


@dataclass
class ToolCallStart:
    tool_name: str
    tool_id: str

# 工具的参数（通常是 JSON 字符串）也是流式传输的，这个类用来承载参数的中间片段。
@dataclass
class ToolCallDelta:
    text: str


@dataclass
class ToolCallComplete:
    tool_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class ThinkingDelta:
    text: str


@dataclass
class ThinkingComplete:
    thinking: str
    signature: str


@dataclass
class StreamEnd:
    stop_reason: str
    input_tokens: int = 0
    output_tokens: int = 0
    # API 返回的 prompt cache 用量。Anthropic 把缓存前缀 token 分为
    # "read"（cache 命中，按 10% 计费）和 "creation"（cache 写入）。
    # input_tokens 已排除这两部分，因此实际 prompt 大小 =
    # input + cache_read + cache_creation。OpenAI 系列只暴露
    # cache_read（通过 *_tokens_details.cached_tokens），没有 creation
    # 计数，所以 cache_creation 在那边始终为 0。
    cache_read: int = 0 #缓存命中的 Token 数
    cache_creation: int = 0 #写入缓存的 Token 数。


StreamEvent = TextDelta | ThinkingDelta | ThinkingComplete | ToolCallStart | ToolCallDelta | ToolCallComplete | StreamEnd
