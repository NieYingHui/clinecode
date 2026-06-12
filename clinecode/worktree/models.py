
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Worktree: # 每个Worktree 实例记录的信息
    name: str 
    path: str
    branch: str
    based_on: str
    head_commit: str
    created: datetime = field(default_factory=datetime.now)


@dataclass
class WorktreeSession: # 当 Agent 进入某个 Worktree 时，还需要一组会话信息来记录进入前的状态，退出时才能恢复回去:
    original_cwd: str # 进入前的工作目录
    worktree_path: str # Worktree路径
    worktree_name: str # slug名称
    original_branch: str # 进入前所在的分支
    original_head_commit: str # 进入时的HEADcommitSHA
    session_id: str = "" # 会话ID
    hook_based: bool = False # 是否由Hook 创建



