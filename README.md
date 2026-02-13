# Overtime Report (加班报告生成器)

**Overtime Report** 是一个基于 AI 的高效工具，专门用于分析 Git 提交历史，自动生成详细的开发工作报告。它解决了手动编写日报、周报或加班申请时的繁琐痛点，通过智能归纳和总结，为你节省宝贵的时间。

无论是想生成一份详尽的工作汇报给领导审阅，还是需要一份格式规范的飞书加班申请文档，Overtime Report 都能一键搞定。

---

## ✨ 核心特性

- **🤖 多模型支持**：集成 OpenAI, Anthropic 和 Google 等主流协议。
- **📊 智能 Git 分析**：深度解析 Git Commit 记录，自动过滤无关文件。
- **📝 双重报告模式**：
  - **完整汇报模式 (Full)**：生成包含详细变更点、技术细节和影响范围的深度报告。
  - **飞书申请模式 (Feishu)**：专为飞书加班申请优化，生成精准的“加班原因”和“详细理由”。
- **⚙️ 高度可配置**：支持自定义忽略规则、Diff 长度限制、Commit 作者筛选等。
- **🎨 优雅的 CLI 体验**：基于 Typer 和 Rich 构建，提供现代化的命令行交互和进度展示。
- **🛡️ 灵活的 API 调用**：支持自定义 Base URL 和 Client 伪装，适应各种网络环境。

---

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.9 或更高版本，以及 `uv` 包管理器。

如果尚未安装 `uv`，请参考 [uv 官方文档](https://github.com/astral-sh/uv) 进行安装。

```bash
# 克隆项目
git clone https://github.com/RoyRao2333/overtime-report.git
cd overtime-report

# 安装依赖
uv sync
```

### 2. 配置

首次运行会自动生成默认配置文件 `config.json5`。

详细配置说明请见下文 [配置详解](#-配置详解) 章节。

### 3. 使用方法

使用 `uv run run.py` 即可启动工具。

#### 基本用法

```bash
uv run run.py
```
默认情况下，它会分析当前目录 (`.`) 过去 **7 天** 的 Git 记录，并同时生成 **完整汇报** 和 **飞书加班申请** 两种格式的 Markdown 文件。

#### 命令行参数详解

| 参数       | 简写 | 默认值  | 说明                                                           |
| :--------- | :--- | :------ | :------------------------------------------------------------- |
| `--days`   | N/A  | `7`     | 回溯过去多少天的 Git 记录。例如 `--days 3` 表示分析最近 3 天。 |
| `--path`   | N/A  | `.`     | 指定 Git 仓库的路径。支持绝对路径或相对路径。                  |
| `--full`   | N/A  | `False` | 仅生成完整汇报文档 (`report_full_*.md`)。                      |
| `--feishu` | N/A  | `False` | 仅生成飞书加班文档 (`report_feishu_*.md`)。                    |
| `--help`   | N/A  | N/A     | 显示帮助信息。                                                 |

**示例命令：**

分析 `../my-project` 项目最近 3 天的代码，且只生成飞书申请文案：
```bash
uv run run.py --path ../my-project --days 3 --feishu
```

---

## 🛠 配置详解

项目使用 `config.json5` 进行配置，支持注释，配置项灵活丰富。

| 配置项           | 类型        | 必填 | 默认值                        | 说明                                                                                                                 |
| :--------------- | :---------- | :--- | :---------------------------- | :------------------------------------------------------------------------------------------------------------------- |
| `ignoredFiles`   | `List[str]` | 否   | 见默认配置                    | Git 分析时忽略的文件模式（Glob）。用于过滤掉 lock 文件、生成文件等无关噪音。                                         |
| `maxDiffLines`   | `int`       | 否   | `500`                         | 单个文件允许的最大 Diff 行数。超过此限制会被截断，防止 Token 消耗过大。设为 `-1` 不截断。                            |
| `llmProvider`    | `str`       | 是   | `"OpenAI"`                    | AI 提供商。可选值：`"OpenAI"`, `"Anthropic"`, `"Google"`。                                                           |
| `llmModel`       | `str`       | 是   | `"gpt-5"`                     | 具体使用的模型名称，如 `gpt-4o`, `gemini-pro` 等。                                                                   |
| `llmBaseUrl`     | `str`       | 否   | `"https://api.openai.com/v1"` | LLM API 的基础 URL。用于自定义代理或中转服务。                                                                       |
| `llmApiKey`      | `str`       | 是   | -                             | 你的 LLM API Key。                                                                                                   |
| `disguiseClient` | `str`       | 否   | `""`                          | 伪装 Client Header，用于绕过某些 Provider 的特定限制。可选：`"Codex"`, `"ClaudeCode"`, `"GeminiCLI"`。留空则不伪装。 |
| `author`         | `str`       | 是   | -                             | Git 提交作者邮箱。**非常重要**，工具会根据此邮箱筛选属于你的提交记录。                                               |

**配置示例：**

```json5
{
  // 忽略不重要的文件
  ignoredFiles: [
    "pnpm-lock.yaml",
    "**/dist/**",
    "**/*.svg"
  ],

  // 限制 Diff 大小
  maxDiffLines: 1000,

  // AI 配置
  llmProvider: "Anthropic",
  llmModel: "claude-3-5-sonnet-20240620",
  llmApiKey: "sk-ant-xxxxxxxx",
  llmBaseUrl: "https://api.anthropic.com/v1",

  // 你的 Git 邮箱
  author: "your.email@example.com"
}
```

---

## 🏗 技术栈

本项目基于 Python 构建，采用了以下优秀的开源库：

- **[Typer](https://typer.tiangolo.com/)**: 用于构建现代化、高性能的命令行接口 (CLI)。
- **[Rich](https://rich.readthedocs.io/)**: 在终端中提供漂亮的富文本输出、进度条和日志高亮。
- **[GitPython](https://gitpython.readthedocs.io/)**: 强大的 Git 仓库交互库，用于提取提交历史和 Diff 信息。
- **[JSON5](https://json5.org/)**: 相比标准 JSON，支持注释和更宽松语法的配置文件格式，提升配置体验。
- **LLM SDKs**:
  - `openai`: OpenAI 官方 SDK。
  - `anthropic`: Anthropic Claude 系列模型 SDK。
  - `google-generativeai`: Google Gemini 系列模型 SDK。

---

## 📄 版权说明

MIT License © 2026 Roy Rao
