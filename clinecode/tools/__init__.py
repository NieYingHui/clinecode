from __future__ import annotations

from typing import TYPE_CHECKING, Any

from clinecode.tools.base import Tool

if TYPE_CHECKING:
    from clinecode.cache import FileCache


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._disabled: set[str] = set() #存储被禁用的工具名称
        self._discovered: set[str] = set() #存储已被"发现"的工具名称

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)


    def is_enabled(self, name: str) -> bool: #检查工具是否已注册且未被禁用
        return name in self._tools and name not in self._disabled

    def enable(self, name: str) -> None: #启用工具
        self._disabled.discard(name) #从禁用集合中移除工具名称


    def disable(self, name: str) -> None: #禁用工具 
        if name in self._tools:
            self._disabled.add(name)

    def enable_all(self) -> None: #启用所有工具
        self._disabled.clear()


    def mark_discovered(self, name: str) -> None: #标记工具为已发现
        self._discovered.add(name)

    def is_discovered(self, name: str) -> bool: #检查工具是否已发现
        return name in self._discovered


    def get_deferred_tool_names(self) -> list[str]: #获取延迟工具名称
        return [
            name
            for name, tool in self._tools.items()
            if getattr(tool, "should_defer", False)
            and name not in self._discovered
            and name not in self._disabled
        ]

    def search_deferred( #搜索延迟工具
        self, query: str, max_results: int, protocol: str = "anthropic"
    ) -> list[dict[str, Any]]:
        query_lower = query.lower()
        scored: list[tuple[int, str, Tool]] = []
        for name, tool in self._tools.items():
            if not getattr(tool, "should_defer", False):
                continue
            if name in self._disabled:
                continue
            score = 0
            name_lower = name.lower()
            desc_lower = (tool.description or "").lower()
            if query_lower in name_lower: #查询字符串完全包含在工具名称
                score += 10
            if query_lower in desc_lower: #查询字符串完全包含在工具描述
                score += 5
            for word in query_lower.split(): 
                if word in name_lower: #查询字符串的每个单词包含在工具名称
                    score += 3
                if word in desc_lower: #查询字符串的每个单词包含在工具描述
                    score += 1
            if score > 0:
                scored.append((score, name, tool))
        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[dict[str, Any]] = []
        for _, _name, tool in scored[:max_results]:
            base = tool.get_schema()
            if protocol in ("openai", "openai-compat"):
                results.append({
                    "type": "function",
                    "name": base["name"],
                    "description": base["description"],
                    "parameters": base["input_schema"],
                })
            else:
                results.append(base)
        return results

    def find_deferred_by_names( #按名称查找延迟工具
        self, names: list[str], protocol: str = "anthropic"
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for name in names:
            tool = self._tools.get(name)
            if tool is None:
                continue
            if not getattr(tool, "should_defer", False):
                continue
            base = tool.get_schema()
            if protocol in ("openai", "openai-compat"):
                results.append({
                    "type": "function",
                    "name": base["name"],
                    "description": base["description"],
                    "parameters": base["input_schema"],
                })
            else:
                results.append(base)
        return results

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())


    def get_all_schemas(self, protocol: str = "anthropic") -> list[dict[str, Any]]: #获取所有工具模式
        schemas: list[dict[str, Any]] = []
        for name, tool in self._tools.items():
            if name in self._disabled:
                continue
            if getattr(tool, "should_defer", False) and name not in self._discovered:
                continue
            base = tool.get_schema()
            if protocol in ("openai", "openai-compat"):
                schemas.append({
                    "type": "function",
                    "name": base["name"],
                    "description": base["description"],
                    "parameters": base["input_schema"],
                })
            else:
                schemas.append(base)
        return schemas


def create_default_registry(file_cache: FileCache | None = None, file_history: Any = None) -> ToolRegistry:
    from clinecode.tools.bash import Bash
    from clinecode.tools.edit_file import EditFile
    from clinecode.tools.file_state_cache import FileStateCache
    from clinecode.tools.glob import Glob
    from clinecode.tools.grep import Grep
    from clinecode.tools.read_file import ReadFile
    from clinecode.tools.write_file import WriteFile

    file_state_cache = FileStateCache()

    registry = ToolRegistry()
    registry.register(ReadFile(file_cache=file_cache, file_state_cache=file_state_cache))
    registry.register(WriteFile(file_cache=file_cache, file_history=file_history, file_state_cache=file_state_cache))
    registry.register(EditFile(file_cache=file_cache, file_history=file_history, file_state_cache=file_state_cache))
    registry.register(Bash())
    registry.register(Glob())
    registry.register(Grep())
    return registry
