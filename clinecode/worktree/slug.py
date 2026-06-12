
from __future__ import annotations

import re

MAX_SLUG_LENGTH = 64
_SEGMENT_RE = re.compile(r"^[a-zA-Z0-9._-]+$")

# 可能传入类似·/../etc/passwd的名称。一旦你把它拼到路径里，Worktree 就可能被创建到系统目录下。这是经典的路径遍历攻击。
def validate_slug(name: str) -> str | None:
    if not name:
        return "name cannot be empty"
    if len(name) > MAX_SLUG_LENGTH:
        return f"name too long (max {MAX_SLUG_LENGTH} characters)"


    segments = name.split("/")
    for seg in segments:
        if not seg:
            return "name contains empty segment"
        if seg in (".", ".."):
            return "name must not contain '.' or '..' as a segment"
        if not _SEGMENT_RE.match(seg):
            return f"invalid segment: {seg!r} (allowed: letters, digits, '.', '-', '_')"


    return None


def flatten_slug(name: str) -> str:
    return name.replace("/", "+")
