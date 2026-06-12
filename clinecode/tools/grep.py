
from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from clinecode.tools.base import SKIP_DIRS, Tool, ToolResult


class Params(BaseModel):
    pattern: str = Field(description="Regex pattern to search for")
    path: str = Field(default=".", description="Base directory to search from") 
    include: str = Field(default="", description="Glob filter for filenames (e.g. '*.py')") #用于文件名过滤


class Grep(Tool): #用于在文件系统中搜索符合特定正则表达式模式的文本内容
    name = "Grep"
    description = "Search file contents using a regex pattern, returning file:line:content matches."
    params_model = Params
    category = "read"
    is_concurrency_safe = True


    async def execute(self, params: Params) -> ToolResult:
        base = Path(params.path)
        if not base.exists():
            return ToolResult(output=f"Error: path not found: {params.path}", is_error=True)

        try:
            regex = re.compile(params.pattern) #将输入的正则表达式模式编译为可用的正则对象
        except re.error as e:
            return ToolResult(output=f"Error: invalid regex: {e}", is_error=True)

        glob_pattern = params.include if params.include else "**/*" #如果没有指定include参数，默认使用**/*匹配所有文件
        if not glob_pattern.startswith("**/"): #确保glob模式以**/开头，实现递归搜索子目录的功能
            glob_pattern = "**/" + glob_pattern

        results: list[str] = []
        for file_path in sorted(base.glob(glob_pattern)): #使用sorted()确保按文件名顺序处理 使用glob()查找匹配的文件
            if not file_path.is_file():
                continue
            if any(part in SKIP_DIRS for part in file_path.parts):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore") #文件读取
            except (OSError, UnicodeDecodeError):
                continue
            for line_num, line in enumerate(text.splitlines(), 1): #使用enumerate()获取行号（从1开始计数）
                if regex.search(line): #对每行应用正则表达式搜索
                    rel = file_path.relative_to(base)
                    results.append(f"{rel}:{line_num}:{line}") #记录相对路径、行号和匹配行

        if not results:
            return ToolResult(output="No matches found.")
        return ToolResult(output="\n".join(results))

