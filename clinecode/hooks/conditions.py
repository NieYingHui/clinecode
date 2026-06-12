from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clinecode.hooks.models import HookContext


@dataclass
class Condition:
    field: str
    operator: str
    value: str


    def evaluate(self, ctx: HookContext) -> bool:
        field_value = ctx.get_field(self.field)
        if self.operator == "==":
            return field_value == self.value
        if self.operator == "!=":
            return field_value != self.value
        if self.operator == "=~": # 正则匹配
            pattern = self.value
            if pattern.startswith("/") and pattern.endswith("/"):
                pattern = pattern[1:-1]
            try:
                return bool(re.search(pattern, field_value))
            except re.error:
                return False
        if self.operator == "~=": # 用标准库的fnmatch 做glob 匹配
            return fnmatch.fnmatch(field_value, self.value)
        return False


@dataclass
class ConditionGroup:
    conditions: list[Condition] = field(default_factory=list)
    logic: str = "and"


    def evaluate(self, ctx: HookContext) -> bool: # 组合条件的求值
        if not self.conditions:
            return True
        if self.logic == "and":
            return all(c.evaluate(ctx) for c in self.conditions)
        return any(c.evaluate(ctx) for c in self.conditions)


class ConditionParseError(Exception):
    pass


_OPERATORS = ("==", "!=", "=~", "~=")

# 遍历四种运算符找到第一个匹配的，然后按运算符位置拆分成左值（字段名）和右值（比较值）。
def _parse_single(expr: str) -> Condition:
    expr = expr.strip()
    for op in _OPERATORS:
        idx = expr.find(op)
        if idx == -1:
            continue
        field_part = expr[:idx].strip()
        value_part = expr[idx + len(op):].strip()
        if value_part.startswith('"') and value_part.endswith('"'):
            value_part = value_part[1:-1]
        return Condition(field=field_part, operator=op, value=value_part)
    raise ConditionParseError(f"No valid operator found in condition: '{expr}'")

# && 和||不能混用。也就是说，可以写A && Β && C，也可以写A || B || C，但不能写A && B || C。
# 一旦允许混用就涉及运算符优先级，需要一个完整的表达式解析器。
# 这个复杂度对 Hook 条件来说完全没必要。如果你真的需要复杂逻辑，分成多个 Hook 就行了
def parse_condition(expr: str) -> ConditionGroup | None:
    if not expr or not expr.strip():
        return None

    expr = expr.strip()
    has_and = "&&" in expr
    has_or = "||" in expr

    if has_and and has_or:
        raise ConditionParseError(
            "Cannot mix '&&' and '||' in a single condition expression. "
            "Split into separate hooks instead."
        )

    if has_and:
        parts = expr.split("&&")
        logic = "and"
    elif has_or:
        parts = expr.split("||")
        logic = "or"
    else:
        parts = [expr]
        logic = "and"

    conditions = [_parse_single(p) for p in parts] # 然后按&&或||拆分成多个子条件
    return ConditionGroup(conditions=conditions, logic=logic)
