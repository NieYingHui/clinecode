
from __future__ import annotations

from pathlib import Path


class FileStateCache: #先读后写"（read-before-edit）的安全机制
    """记录已读取的文件，强制执行“先读后改”原则。

    在每次调用 ReadFile 后存储 { absolute_path: (content, mtime_ns) }。
    EditFile 和 WriteFile 在继续执行前会检查缓存：
      - 条件 1：文件必须已被读取（存在于缓存中）。
      - 条件 2：文件自读取以来未被修改（mtime_ns 匹配）。
    """

    def __init__(self) -> None:
        # 用于存储文件状态。键是文件的绝对路径（字符串） 值是一个元组，包含文件内容（字符串）和修改时间（纳秒级时间戳，整数）
        self._cache: dict[str, tuple[str, int]] = {}

    def record(self, path: str, content: str, mtime_ns: int) -> None:
        """在成功读取后，记录文件的内容和最后修改时间。"""
        self._cache[path] = (content, mtime_ns)

    def check(self, path: str) -> tuple[bool, str]:
        """检查文件是否安全，可供编辑/写入。

        返回 (ok, error_message)。如果 ok 为 True，则 error_message 为空。
        """
        entry = self._cache.get(path)
        if entry is None:
            return False, "Error: file has not been read yet. Read it first before editing."

        _, cached_mtime_ns = entry
        try:
            current_mtime_ns = Path(path).stat().st_mtime_ns
        except OSError:
            # 文件可能已被删除；允许继续写入
            # （WriteFile 会创建该文件，而 EditFile 则会自动失败）。
            return True, ""

        if current_mtime_ns != cached_mtime_ns:
            return False, "Error: file has been modified since last read. Read it again before editing."

        return True, ""

    def update(self, path: str) -> None:
        """在编辑/写入成功后更新缓存条目。"""
        try:
            p = Path(path)
            content = p.read_text(encoding="utf-8")
            mtime_ns = p.stat().st_mtime_ns
            self._cache[path] = (content, mtime_ns)
        except OSError:
            # 如果无法读取该条目，就直接删除过期的条目。
            self._cache.pop(path, None)
