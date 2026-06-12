# ClineCode

一个基于终端的 AI 编程助手，提供智能代码补全、对话式编程和自动化任务执行能力。

## 特性

- 🤖 **AI 驱动的代码助手** - 支持 Anthropic Claude 和 OpenAI GPT 模型
- 💬 **对话式编程** - 通过自然语言描述需求生成代码
- 🎯 **智能代码补全** - 上下文感知的代码建议
- 🔧 **MCP 协议支持** - 可扩展的工具和模型上下文协议
- 📝 **会话管理** - 持久化的对话历史和项目上下文
- 🎨 **现代化 TUI** - 基于 Textual 的终端用户界面
- 🔒 **权限控制** - 灵活的权限模式和安全检查

## 技术栈

- **Python** 3.11+
- **TUI 框架**: Textual
- **异步处理**: asyncio
- **包管理**: uv
- **AI 模型**: Anthropic Claude / OpenAI GPT
- **协议支持**: MCP (Model Context Protocol)

## 安装

### 前置要求

- Python 3.11 或更高版本
- uv 包管理器（推荐）

### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 安装 ClineCode

```bash
# 克隆仓库
git clone https://github.com/yourusername/clinecode-python.git
cd clinecode-python

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
```

## 构建项目

### 开发环境设置

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/clinecode-python.git
cd clinecode-python

# 2. 安装所有依赖（包括开发依赖）
uv sync --all-extras

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 验证安装
clinecode --help
```

### 构建分发包

```bash
# 安装构建工具
uv pip install build

# 构建包
python -m build

# 产物在 dist/ 目录下
ls dist/
```

## 使用方法

### 启动 ClineCode

```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 启动交互式界面
clinecode

# 或使用非交互模式执行单个提示
clinecode -p "解释这段代码的作用"
```

### 权限模式

ClineCode 支持多种权限模式：

```bash
# 默认模式 - 需要确认所有操作
clinecode --mode default

# 接受编辑模式 - 自动接受文件编辑
clinecode --mode acceptEdits

# 计划模式 - 只规划不执行
clinecode --mode plan

# 绕过权限 - 谨慎使用
clinecode --mode bypassPermissions
```

### 配置

配置文件位于 `.clinecode/config.yaml`：

```yaml
# 示例配置
permission_mode: default
model: claude-3-5-sonnet-20241022
max_tokens: 4096
temperature: 0.7
```

## 开发指南

### 项目结构

```
clinecode-python/
├── clinecode/              # 主包
│   ├── __main__.py        # 入口点
│   ├── agent.py           # AI 代理核心
│   ├── app.py             # TUI 应用
│   ├── config.py          # 配置管理
│   ├── commands/          # 命令处理
│   ├── tools/             # 工具实现
│   ├── mcp/               # MCP 协议
│   ├── memory/            # 记忆系统
│   ├── permissions/       # 权限控制
│   └── skills/            # 技能系统
├── tests/                 # 测试用例
├── pyproject.toml         # 项目配置
└── README.md              # 项目文档
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_agent.py

# 带覆盖率报告
pytest --cov=clinecode

# 详细输出
pytest -v
```

### 代码规范

- **Commit message**: 使用英文
- **变量命名**: snake_case
- **类型标注**: PEP 604 语法（`X | Y` 而非 `Union[X, Y]`）
- **导入排序**: 使用 isort
- **代码格式化**: 使用 black

### 添加新功能

1. 创建功能分支：`git checkout -b feature/your-feature`
2. 实现功能并编写测试
3. 确保所有测试通过：`pytest`
4. 提交更改：`git commit -m "Add your feature"`
5. 推送分支：`git push origin feature/your-feature`
6. 创建 Pull Request


## 常见问题

### Q: 如何切换 AI 模型？

A: 在 `.clinecode/config.yaml` 中修改 `model` 字段，或在启动时使用环境变量。

### Q: 支持哪些编程语言？

A: ClineCode 支持所有主流编程语言，通过 MCP 工具可以扩展语言支持。

### Q: 如何添加自定义工具？

A: 在 `clinecode/tools/` 目录下创建新工具，参考现有工具的实现。

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支
3. 提交更改
4. 推送到你的 Fork
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 问题反馈：[GitHub Issues](https://github.com/yourusername/clinecode-python/issues)
- 讨论交流：[GitHub Discussions](https://github.com/yourusername/clinecode-python/discussions)

---

**注意**：本项目处于早期开发阶段，API 可能会有变化。

