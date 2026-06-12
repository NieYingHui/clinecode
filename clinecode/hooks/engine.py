from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from clinecode.hooks.executors import execute_action
from clinecode.hooks.models import ActionResult, Hook, HookContext, ToolRejectedError

log = logging.getLogger(__name__)


@dataclass
class HookNotification:
    hook_id: str
    event: str
    output: str
    success: bool


class HookEngine:
    def __init__(self, hooks: list[Hook] | None = None) -> None:
        self.hooks: list[Hook] = hooks or [] # 存所有注册的规则
        self._prompt_messages: list[str] = [] # 收集 prompt 类型 Hook 的输出，等外部来取走注入到对话上下文
        self._notifications: list[HookNotification] = [] # _notifications 是通知队列，记录每条 Hook 的执行结果


    def find_matching_hooks(self, event: str, ctx: HookContext) -> list[Hook]: # 找到所有匹配的 Hook
        matched: list[Hook] = []
        for hook in self.hooks:
            if hook.event != event:
                continue
            if not hook.should_run():
                continue
            if hook.condition is not None and not hook.condition.evaluate(ctx): # 做条件表达式求值
                continue
            matched.append(hook)
        return matched


    async def run_hooks(self, event: str, ctx: HookContext) -> None:
        matched = self.find_matching_hooks(event, ctx)
        for hook in matched:
            hook.mark_executed()
            if hook.async_exec:
                asyncio.ensure_future(self._run_single(hook, ctx)) # 扔到后台，不等它跑完就继续下一个
            else:
                await self._run_single(hook, ctx)


    async def _run_single(self, hook: Hook, ctx: HookContext) -> None: # 负责执行单个Hook并收集结果：
        try:
            result = await execute_action(hook.action, ctx)
            if hook.action.type == "prompt" and result.success:
                self._prompt_messages.append(result.output)
            self._notifications.append(
                HookNotification(
                    hook_id=hook.id,
                    event=hook.event,
                    output=result.output,
                    success=result.success,
                )
            )
            if not result.success:
                log.warning(
                    "Hook '%s' action failed: %s", hook.id, result.output
                )
        except Exception as e:
            log.warning("Hook '%s' execution error: %s", hook.id, e)
            self._notifications.append(
                HookNotification(
                    hook_id=hook.id,
                    event=hook.event,
                    output=str(e),
                    success=False,
                )
            )


    async def run_pre_tool_hooks( # 唯一能阻断执行的入口
        self, ctx: HookContext
    ) -> ToolRejectedError | None:
        matched = self.find_matching_hooks("pre_tool_use", ctx)
        for hook in matched:
            hook.mark_executed()
            try:
                result = await execute_action(hook.action, ctx)
                self._notifications.append(
                    HookNotification(
                        hook_id=hook.id,
                        event="pre_tool_use",
                        output=result.output,
                        success=result.success,
                    )
                )
                if hook.reject:
                    return ToolRejectedError(
                        tool=ctx.tool_name,
                        reason=result.output,
                        hook_id=hook.id,
                    )
            except Exception as e:
                log.warning("Hook '%s' execution error: %s", hook.id, e)
        return None
    
# _prompt_messages专门收集 prompt 类型 Hook 的输出，Agent Loop 每轮迭代前取走这些消息，注入到system prompt 区域。
    def get_prompt_messages(self) -> list[str]:
        messages = list(self._prompt_messages)
        self._prompt_messages.clear() # 「取走就清空」的一次性消费模式
        return messages

# _notifications 收集所有 Hook 的执行结果，用于日志、调试、状态展示。
    def drain_notifications(self) -> list[HookNotification]:
        notifications = list(self._notifications)
        self._notifications.clear() #「取走就清空」的一次性消费模式
        return notifications
