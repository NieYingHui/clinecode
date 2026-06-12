from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical #垂直
from textual.message import Message
from textual.widgets import Static

from clinecode.agent import PermissionResponse


_PERM_OPTIONS = [
    ("Yes", PermissionResponse.ALLOW),
    ("Yes, and don't ask again for this pattern", PermissionResponse.ALLOW_ALWAYS),
    ("No", PermissionResponse.DENY),
]


class InlinePermissionWidget(Vertical, can_focus=True): #基于 Textual 框架的自定义 UI 组件
    """渲染在聊天区域内部的内联权限确认提示。允许用户对某个操作（通常是 AI 助手执行的工具命令）进行批准或拒绝

    与 Go 版 TUI 的权限对话框一致：工具名 + 描述 + 带编号的
    选项，支持方向键导航 + 回车确认。
    """

    BINDINGS = [ #键盘绑定
        Binding("up", "cursor_up", "Up", priority=True),
        Binding("down", "cursor_down", "Down", priority=True),
        Binding("enter", "select", "Select", priority=True),
        Binding("escape", "deny", "Deny", priority=True),
    ]

    class Responded(Message): #消息传递

# 当用户做出选择后，组件会通过 post_message 发送一个包含用户响应（PermissionResponse.ALLOW 或 DENY 等）的消息。
# 父组件或应用可以监听这个消息来执行后续逻辑。
        def __init__(self, response: PermissionResponse) -> None:
            super().__init__()
            self.response = response

    def __init__(self, tool_name: str, description: str, **kwargs) -> None:
        super().__init__(id="perm-inline", **kwargs)
        self._tool_name = tool_name
        self._description = description
        self._cursor = 0

    def compose(self) -> ComposeResult: #UI 渲染
        yield Static(self._build_content(), id="perm-content") #构建显示的文本字符串，在当前选中的选项前显示一个青色的箭头 ❯


# 组件挂载到屏幕上时自动调用，这里调用 self.focus() 自动获取焦点，以便用户可以直接操作。
    def on_mount(self) -> None: #生命周期与交互
        self.focus()

    def _build_content(self) -> str:
        lines = []
        lines.append(f"\n  [bold yellow]{self._tool_name} command[/bold yellow]\n")
        lines.append(f"    {self._description}\n")
        lines.append("  [dim]This command requires approval[/dim]\n")
        lines.append("  Do you want to proceed?\n")

        for i, (label, _resp) in enumerate(_PERM_OPTIONS):
            if i == self._cursor:
                lines.append(f" [bold cyan]❯[/bold cyan] {i + 1}. [bold]{label}[/bold]")
            else:
                lines.append(f"   {i + 1}. [dim]{label}[/dim]")

        return "\n".join(lines)


    def _refresh(self) -> None:
        content = self.query_one("#perm-content", Static) #查找ID为perm-content的Static组件
        content.update(self._build_content()) #调用其update 方法重新渲染文本，从而反映光标的移动

    def action_cursor_up(self) -> None:
        if self._cursor > 0:
            self._cursor -= 1
            self._refresh() #调用 _refresh 更新界面

    def action_cursor_down(self) -> None:
        if self._cursor < len(_PERM_OPTIONS) - 1:
            self._cursor += 1
            self._refresh()

    def action_select(self) -> None:
        _, response = _PERM_OPTIONS[self._cursor]
        self.post_message(self.Responded(response))


    def action_deny(self) -> None:
        self.post_message(self.Responded(PermissionResponse.DENY))
