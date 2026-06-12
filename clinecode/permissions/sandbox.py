
from __future__ import annotations

import tempfile #获取系统的临时文件目录路径
from pathlib import Path


class PathSandbox: #制文件操作只能在特定的目录（"沙箱"）内进行


    def __init__( #初始化沙箱允许访问的根路径列表
        self,
        project_root: str, #项目的主目录
        extra_allowed: list[str] | None = None, #可选的字符串列表，包含其他允许访问的路径
    ) -> None:
        root = Path(project_root).resolve() #转换为绝对路径（resolve() 会解析符号链接并消除 ..）
        self._allowed_roots: list[Path] = [root, Path(tempfile.gettempdir()).resolve()] #默认包含两个路径：项目根目录和系统临时目录
        if extra_allowed:
            for p in extra_allowed:
                self._allowed_roots.append(Path(p).resolve())


    @property
    def project_root(self) -> Path: #获取项目根目录
        return self._allowed_roots[0]


    def check(self, path: str) -> tuple[bool, str]: #检查给定的路径是否在沙箱允许的范围内
        p = Path(path).expanduser() #将路径中的 ~ 展开为用户主目录
        if not p.is_absolute(): #如果输入的路径是相对路径
            p = self.project_root / p
        abs_path = p.absolute() #获取绝对路径

        try:
            real_path = abs_path.resolve(strict=True) #会解析路径中的所有符号链接，strict=True 表示如果路径不存在，抛出异常
        except OSError: #目标文件不存在
            ancestor = abs_path
            while not ancestor.exists(): #逐级向上寻找最近的一个存在的父目录
                parent = ancestor.parent
                if parent == ancestor:
                    return False, f"无法解析路径: {path}"
                ancestor = parent
            try:
                resolved_ancestor = ancestor.resolve(strict=True)
            except OSError:
                return False, f"无法解析路径: {path}"
            real_path = resolved_ancestor / abs_path.relative_to(ancestor)

        for root in self._allowed_roots: #遍历所有允许的根路径（_allowed_roots）
            try:
                real_path.relative_to(root)
                return True, ""
            except ValueError:
                continue

        return False, f"路径 {path} 超出沙箱范围"
