
from __future__ import annotations

from clinecode.commands.registry import CommandRegistry


def parse_command(text: str) -> tuple[str, str, bool]:
    text = text.strip()
    if not text.startswith("/"):
        return "", "", False
    text = text[1:]
    if not text:
        return "", "", True
    parts = text.split(None, 1)
    name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    return name, args, True

# 命令自动补全功能的实现，主要用于在用户输入命令前缀时，返回匹配的命令列表
def complete(registry: CommandRegistry, prefix: str) -> list[tuple[str, str]]:
    """返回匹配命令的 (display_text, command_value) 列表。"""
    prefix = prefix.lstrip("/")
    seen: set[str] = set()
    matches: list[tuple[str, str]] = []
    for cmd in registry.list_commands(): #遍历注册表中的所有命令
        if cmd.name in seen:
            continue
        if cmd.name.startswith(prefix) or any(a.startswith(prefix) for a in cmd.aliases):
            seen.add(cmd.name)
            desc = cmd.description
            if len(desc) > 30:
                desc = desc[:28] + "…"
            desc = desc.replace("[", "\\[")
            display = f"/{cmd.name:<16} — {desc}"
            matches.append((display, "/" + cmd.name))
    matches.sort(key=lambda x: x[1])
    return matches[:8]

