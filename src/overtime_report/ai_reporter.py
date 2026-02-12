from typing import Any, Dict, List, Optional

import openai
from rich.console import Console

from overtime_report.config import config

console = Console()


def generate_report(commits: List[Dict[str, Any]]) -> Optional[str]:
    """
    根据提交记录，使用 AI 生成 Markdown 格式的工作报告。
    """
    if not commits:
        return "没找到符合条件的提交记录。"

    # 各个 AI 客户端的 User-Agent 映射
    ua_mapping = {
        "Codex": "Codex/1.0",
        "ClaudeCode": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude/1.0; https://claude.ai/)",
        "GeminiCLI": "Gemini-CLI/1.0.0",
    }

    prompt = _construct_prompt(commits)
    system_prompt = (
        "你是一个技术专家（Technical Lead）。请将提供的 Git 提交历史总结成一份详细的 Markdown 工作报告。"
        "请按 '功能开发'、'问题修复'、'代码重构' 和 '杂项' 进行分类。"
        "请根据提供的代码差异（diffs）补充技术细节。"
        "报告语气要专业自然，适合作为日报或周报提交。"
    )

    try:
        content = None

        if config.llm_provider == "Anthropic":
            if not config.llm_api_key:
                raise ValueError("配置文件中未设置 LLM_API_KEY，请检查 .env 文件。")

            import anthropic

            # 使用 ClaudeCode 的 UA
            user_agent = ua_mapping["ClaudeCode"]

            client = anthropic.Anthropic(
                api_key=config.llm_api_key,
                base_url=config.llm_base_url,
                default_headers={"User-Agent": user_agent},
            )

            response = client.messages.create(
                model=config.llm_model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text

        elif config.llm_provider == "Google":
            if not config.llm_api_key:
                raise ValueError("配置文件中未设置 LLM_API_KEY，请检查 .env 文件。")

            import google.generativeai as genai
            from google.api_core import client_options

            # 使用 GeminiCLI 的 UA
            user_agent = ua_mapping["GeminiCLI"]

            # Google GenAI SDK 底层使用 gRPC 或 REST。
            # 为了确保 User-Agent 能被正确透传，在使用 REST transport 时，我们需要 patch requests.Session。
            # 这是为了绕过部分 API 对非官方客户端的限制。

            genai.configure(
                api_key=config.llm_api_key,
                transport="rest",
                client_options={"api_endpoint": config.llm_base_url},
            )

            import requests

            old_session = requests.Session

            class CustomSession(requests.Session):
                def request(self, method, url, *args, **kwargs):
                    headers = kwargs.get("headers", {})
                    headers["User-Agent"] = user_agent
                    kwargs["headers"] = headers
                    return super().request(method, url, *args, **kwargs)

            # 临时替换 Session 以注入 Header
            requests.Session = CustomSession

            try:
                model = genai.GenerativeModel(config.llm_model)
                # Google 的 system prompt 放在 content 或 system_instruction 中
                # 较新版本支持 system_instruction
                try:
                    model = genai.GenerativeModel(
                        config.llm_model, system_instruction=system_prompt
                    )
                    response = model.generate_content(prompt)
                except Exception:
                    # Fallback defined model load or if system_instruction not supported
                    model = genai.GenerativeModel(config.llm_model)
                    combined_prompt = f"{system_prompt}\n\n{prompt}"
                    response = model.generate_content(combined_prompt)

                content = response.text
            finally:
                # 恢复 requests.Session
                requests.Session = old_session

        else:  # Default to OpenAI
            if not config.llm_api_key:
                raise ValueError("配置文件中未设置 LLM_API_KEY，请检查 .env 文件。")

            # 使用 Codex 的 UA
            user_agent = ua_mapping["Codex"]

            client = openai.OpenAI(
                api_key=config.llm_api_key,
                base_url=config.llm_base_url,
                default_headers={"User-Agent": user_agent},
            )

            response = client.chat.completions.create(
                model=config.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            content = response.choices[0].message.content

        return content
    except Exception as e:
        console.print(f"\n[red]AI 生成报告时出错了 ({config.llm_provider}): {e}[/red]")
        return None


def _construct_prompt(commits: List[Dict[str, Any]]) -> str:
    """
    Construct the prompt from commit data.
    """
    prompt = "这是分析期间的 Git 提交历史：\n\n"

    for commit in commits:
        prompt += f"commit: {commit['hash']}\n"
        prompt += f"date: {commit['date']}\n"
        prompt += f"message: {commit['message']}\n"
        prompt += "diffs:\n"
        for diff in commit["diffs"]:
            prompt += f"  file: {diff['file']}\n"
            prompt += f"  content:\n{diff['content']}\n"
        prompt += "\n" + "-" * 40 + "\n\n"

    return prompt
