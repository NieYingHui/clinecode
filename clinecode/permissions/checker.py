from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from clinecode.permissions.dangerous import DangerousCommandDetector, is_safe_command
from clinecode.permissions.modes import DecisionEffect, PermissionMode, mode_decide
from clinecode.permissions.rules import RuleEngine, extract_content
from clinecode.permissions.sandbox import PathSandbox
from clinecode.tools.base import Tool

_PLAN_MODE_ALLOWED_TOOLS = frozenset({"Agent", "ToolSearch", "AskUserQuestion", "ExitPlanMode"})
# 维护了一个 Plan模式工具白名单（frozenset是不可变集合，比普通 set 更安全）。

@dataclass
class Decision: #决定
    effect: DecisionEffect
    reason: str


class PermissionChecker:
# 依赖注入做得很彻底。DangerousCommandDetector、PathSandbox、RuleEngine三个组件都从外部注入，而不是在构造函数里自己创建。
# 这样做的好处是测试时可以轻松替换成 mock 对象，不需要真实的文件系统和项目目录。
# 三个组件全部从构造函数注入，最接近教科书式的依赖注入。测试时可以轻松替换成 mock 对象，不需要真实的文件系统和项目目录。
    def __init__(
        self,
        detector: DangerousCommandDetector,
        sandbox: PathSandbox,
        rule_engine: RuleEngine,
        mode: PermissionMode = PermissionMode.DEFAULT,
    ) -> None:
        self.detector = detector
        self.sandbox = sandbox
        self.rule_engine = rule_engine
        self.mode = mode
        self.plan_file_path: str = ""


    def check(self, tool: Tool, arguments: dict[str, Any]) -> Decision:
        content = extract_content(tool.name, arguments)

        # Layer 0: Plan 模式例外放行
        if self.mode == PermissionMode.PLAN:
            if tool.name in _PLAN_MODE_ALLOWED_TOOLS:
                return Decision(effect="allow", reason="Plan mode: allowed tool")
            if tool.name in ("WriteFile", "EditFile") and content:
                if self._is_plan_file(content):
                    return Decision(effect="allow", reason="Plan mode: plan file write")

        # Layer 1: 安全的只读命令（自动放行）
        if tool.category == "command" and is_safe_command(content or ""):
            return Decision(effect="allow", reason="Safe read-only command")

        # Layer 1b: 危险命令黑名单（仅 Bash）
        if tool.category == "command":
            hit, reason = self.detector.detect(content)
            if hit:
                return Decision(effect="deny", reason=f"危险命令拦截: {reason}")

        # Layer 2: 路径沙箱（仅文件类工具）
        if tool.category in ("read", "write") and content:
            ok, reason = self.sandbox.check(content)
            if not ok:
                return Decision(effect="deny", reason=f"路径沙箱拦截: {reason}")

        # Layer 3: 规则引擎匹配
        rule_result = self.rule_engine.evaluate(tool.name, content)
        if rule_result == "allow":
            return Decision(effect="allow", reason="权限规则放行")
        if rule_result == "deny":
            return Decision(effect="deny", reason="权限规则拒绝")

        # Layer 4: 权限模式兜底判定
        effect = mode_decide(self.mode, tool.category)
        if effect == "allow":
            return Decision(effect="allow", reason=f"权限模式 {self.mode.value} 放行")
        if effect == "deny":
            return Decision(effect="deny", reason=f"权限模式 {self.mode.value} 拒绝")

        # Layer 5: 触发人工确认（HITL）
        return Decision(effect="ask", reason="需要用户确认")


    def _is_plan_file(self, target_path: str) -> bool: #判断给定的路径是否指向一个"计划文件"(plan file)
        if not self.plan_file_path or not target_path:
            return ".clinecode/plans/" in target_path #如果plan_file_path为空，则检查target_path中是否包含".clinecode/plans/"子串
        try:
            abs_target = os.path.abspath(target_path) #转换为绝对路径
            abs_plan = os.path.abspath(self.plan_file_path)
            if abs_target == abs_plan:
                return True
        except Exception:
            pass
        if os.path.basename(target_path) == os.path.basename(self.plan_file_path): #比较两个路径的文件名
            return True
        return ".clinecode/plans/" in target_path
