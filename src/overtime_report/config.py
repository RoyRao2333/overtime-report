import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import json5
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE_NAME = "config.json5"


@dataclass
class Config:
    ignored_files: List[str]
    max_diff_lines: int
    llm_model: str
    llm_base_url: str
    disguise_client: str
    llm_provider: str
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY")


DEFAULT_CONFIG_CONTENT = """{
  // Git 分析时忽略的文件（支持 glob 模式匹配）
  "ignoredFiles": [
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "**/node_modules/**",
    "**/.git/**",
    "**/*.svg",
    "dist/**",
    "coverage/**",
    "__pycache__/**",
    "*.pyc"
  ],

  // 单个文件允许的最大 Diff 行数
  // 如果超过此限制，Diff 内容将被截断
  // 设置为 -1 则表示不截断
  "maxDiffLines": 500,

  // AI Provider
  // 可选值: "OpenAI", "Anthropic", "Google"
  "llmProvider": "OpenAI",

  // 使用的 LLM 模型名称 (例如: "gpt-5", "claude-3-opus-20240229", "gemini-pro")
  "llmModel": "gpt-5",

  // LLM API 的基础 URL
  "llmBaseUrl": "https://api.openai.com/v1",

  // 伪装 Client，用于绕过 Provider 限制
  // 可选值: "Codex", "ClaudeCode", "GeminiCLI"
  "disguiseClient": "Codex"
}"""


def load_config() -> Config:
    """
    从 config.json5 加载配置。
    如果不存在，则创建带有默认值和注释的配置文件。
    """
    # 解析配置文件路径
    root_path = Path(__file__).resolve().parents[2]
    config_path = root_path / CONFIG_FILE_NAME

    if not config_path.exists():
        # Write default content with comments
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_CONTENT)

        print(f"首次运行，配置文件 {CONFIG_FILE_NAME} 不存在，已为您创建默认配置文件。")
        print(f"请根据您的需求修改配置文件 ({config_path}) 后再次运行程序。")
        sys.exit(0)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json5.load(f)
    except Exception as e:
        print(f"Warning: Failed to load {CONFIG_FILE_NAME} ({e}). Using defaults.")
        # Fallback to parsing the default content string
        data = json5.loads(DEFAULT_CONFIG_CONTENT)

    # Ensure all keys exist by merging with defaults
    default_data = json5.loads(DEFAULT_CONFIG_CONTENT)
    for key, value in default_data.items():
        if key not in data:
            data[key] = value

    return Config(
        ignored_files=data["ignoredFiles"],
        max_diff_lines=data["maxDiffLines"],
        llm_model=data["llmModel"],
        llm_base_url=data["llmBaseUrl"],
        disguise_client=data.get("disguiseClient", "Codex"),
        llm_provider=data.get("llmProvider", "OpenAI"),
    )


# Global configuration instance
config = load_config()
