from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from clinecode.teams.progress import TeammateProgress


class BackendType(str, Enum): # backendType决定队员在哪里运行
    TMUX = "tmux" # "tmux"和"iterm2"意味着队员在独立的终端 pane里作为单独进程运行，和 Lead 完全隔离
    ITERM2 = "iterm2"
    IN_PROCESS = "in-process" # "in-process"意味着队员和 Lead 跑在同一个进程内，更轻量但隔离性弱。


@dataclass
class TeammateInfo:
    name: str # 队员名称,由lead分配
    agent_id: str # 对应的Agent实例ID
    agent_type: str # 使用的Agent
    model: str  # 定义模型
    worktree_path: str # 可覆盖所在的worktree路径
    backend_type: str  # BackendType value 执行后端
    is_active: bool | None = None # 活跃状态
    progress: Optional[TeammateProgress] = None # 是否需要Lead审批

    def to_dict(self) -> dict:
        # Exclude progress (runtime-only, contains threading.Lock)
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "model": self.model,
            "worktree_path": self.worktree_path,
            "backend_type": self.backend_type,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TeammateInfo:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _sanitize_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "team"



@dataclass
class AgentTeam:
    name: str # 团队名称
    lead_agent_id: str  # 谁是负责人
    members: list[TeammateInfo] = field(default_factory=list)  # 花名册
    config_path: str = ""  # 持久化位置
    description: str = ""

    def get_member(self, name: str) -> TeammateInfo | None:
        for m in self.members:
            if m.name == name or m.agent_id == name:
                return m
        return None


    def add_member(self, member: TeammateInfo) -> None:
        self.members.append(member)

    def remove_member(self, name: str) -> bool:
        for i, m in enumerate(self.members):
            if m.name == name or m.agent_id == name:
                self.members.pop(i)
                return True
        return False


    def set_member_active(self, name: str, is_active: bool | None) -> bool:
        member = self.get_member(name)
        if member is None:
            return False
        member.is_active = is_active
        return True

    def all_idle(self) -> bool:
        return all(m.is_active is False for m in self.members)


    def active_members(self) -> list[TeammateInfo]:
        return [m for m in self.members if m.is_active is not False]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "lead_agent_id": self.lead_agent_id,
            "members": [m.to_dict() for m in self.members],
            "config_path": self.config_path,
            "description": self.description,
        }


    @classmethod
    def from_dict(cls, data: dict) -> AgentTeam:
        members = [TeammateInfo.from_dict(m) for m in data.get("members", [])]
        return cls(
            name=data["name"],
            lead_agent_id=data["lead_agent_id"],
            members=members,
            config_path=data.get("config_path", ""),
            description=data.get("description", ""),
        )

    def save(self) -> None:
        path = Path(self.config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, config_path: str) -> AgentTeam:
        data = json.loads(Path(config_path).read_text(encoding="utf-8"))
        team = cls.from_dict(data)
        team.config_path = config_path
        return team


def resolve_team_dir(team_name: str) -> Path:
    slug = _sanitize_name(team_name)
    return Path.home() / ".clinecode" / "teams" / slug


def unique_team_name(team_name: str) -> str:
    slug = _sanitize_name(team_name)
    base_dir = Path.home() / ".clinecode" / "teams"
    if not (base_dir / slug).exists():
        return slug
    counter = 2
    while (base_dir / f"{slug}-{counter}").exists():
        counter += 1
    return f"{slug}-{counter}"
