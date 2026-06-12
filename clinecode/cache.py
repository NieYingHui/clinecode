from __future__ import annotations

import threading


class FileCache: #用于缓存文件内容
    def __init__(self) -> None:
        self._store: dict[str, str] = {} #使用字典存储文件路径和内容的映射
        self._lock = threading.Lock() #确保多线程环境下的线程安全

    def get(self, path: str) -> str | None:
        with self._lock:
            return self._store.get(path)


    def put(self, path: str, content: str) -> None:
        with self._lock:
            self._store[path] = content


    def invalidate(self, path: str) -> None: #失效
        with self._lock:
            self._store.pop(path, None)


    def clear(self) -> None: #清除缓存
        with self._lock:
            self._store.clear()


    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
