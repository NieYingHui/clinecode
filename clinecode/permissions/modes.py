
from __future__ import annotations

from enum import Enum
from typing import Literal

from clinecode.tools.base import ToolCategory

# Literal(字面意思)类型在类型检查时能限制取值范围，但运行时没有强制约束。
# 用字符串而不是枚举来表示判定效果，和 YAML 文件里的effect字段值保持一致，省去了转換步骤。
DecisionEffect = Literal["allow", "deny", "ask"]


class PermissionMode(str, Enum):
    DEFAULT = "default"
    ACCEPT_EDITS = "acceptEdits"
    PLAN = "plan"
    BYPASS = "bypassPermissions"
    CUSTOM = "custom" #CUSToM 模式下所有工具分类都返回ask
    DONT_ASK = "dontAsk" #所有操作都放行


_MODE_MATRIX: dict[PermissionMode, dict[ToolCategory, DecisionEffect]] = {
    PermissionMode.DEFAULT: {"read": "allow", "write": "ask", "command": "ask"},
    PermissionMode.ACCEPT_EDITS: {"read": "allow", "write": "allow", "command": "ask"},
    PermissionMode.PLAN: {"read": "allow", "write": "ask", "command": "ask"},
    PermissionMode.BYPASS: {"read": "allow", "write": "allow", "command": "allow"},
    PermissionMode.CUSTOM: {"read": "ask", "write": "ask", "command": "ask"},
    PermissionMode.DONT_ASK: {"read": "allow", "write": "allow", "command": "allow"},
}


def mode_decide(mode: PermissionMode, category: ToolCategory) -> DecisionEffect:
    return _MODE_MATRIX[mode][category]
