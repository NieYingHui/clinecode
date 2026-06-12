
from __future__ import annotations

from enum import StrEnum

# 使用StrEnum 而不是普通字符串常量，让loader 在校验时可以用集合操作快速判断事件名是否合法:
class LifecycleEvent(StrEnum):
    # 会话（Session）级别
    SESSION_START = "session_start"
    SESSION_END = "session_end"


    # 轮次（Turn）级别
    TURN_START = "turn_start"
    TURN_END = "turn_end"


    # 工具（Tool）级别 
    PRE_TOOL_USE = "pre_tool_use" # pre_tool_use最特殊，它是唯一能拦截工具执行的事件。
    POST_TOOL_USE = "post_tool_use"

    # 消息（Message）级别
    PRE_SEND = "pre_send"
    POST_RECEIVE = "post_receive"

    # 系统（System）级别 
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    ERROR = "error"
    COMPACT = "compact"
    PERMISSION_REQUEST = "permission_request"
    FILE_CHANGE = "file_change"
    COMMAND_EXECUTE = "command_execute"

