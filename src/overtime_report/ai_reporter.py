from typing import Any, Dict, List, Optional

import openai
from rich.console import Console

from overtime_report.config import config

console = Console()


def _call_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    调用 LLM 生成内容的通用方法。
    """
    # 各个 AI 客户端的 User-Agent 映射
    ua_mapping = {
        "Codex": "Codex/1.0",
        "ClaudeCode": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude/1.0; https://claude.ai/)",
        "GeminiCLI": "Gemini-CLI/1.0.0",
    }

    # 根据配置决定是否添加 User-Agent
    user_agent = None
    if config.disguise_client:
        user_agent = ua_mapping.get(config.disguise_client)

    try:
        content = None

        if config.llm_provider == "Anthropic":
            import anthropic

            client_kwargs = {
                "api_key": config.llm_api_key,
                "base_url": config.llm_base_url,
            }
            if user_agent:
                client_kwargs["default_headers"] = {"User-Agent": user_agent}

            client = anthropic.Anthropic(**client_kwargs)

            response = client.messages.create(
                model=config.llm_model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = response.content[0].text

        elif config.llm_provider == "Google":
            import google.generativeai as genai

            # Google GenAI SDK 底层使用 gRPC 或 REST。
            # 为了确保 User-Agent 能被正确透传，在使用 REST transport 时，我们需要 patch requests.Session。
            # 这是为了绕过部分 API 对非官方客户端的限制。

            genai.configure(
                api_key=config.llm_api_key,
                transport="rest",
                client_options={"api_endpoint": config.llm_base_url},
            )

            import requests

            # 只有在需要伪装 User-Agent 时才 Patch Session
            if user_agent:
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
                # Google 的 system prompt 放在 content 或 system_instruction 中
                # 较新版本支持 system_instruction
                try:
                    model = genai.GenerativeModel(
                        config.llm_model, system_instruction=system_prompt
                    )
                    response = model.generate_content(user_prompt)
                except Exception:
                    # Fallback defined model load or if system_instruction not supported
                    model = genai.GenerativeModel(config.llm_model)
                    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = model.generate_content(combined_prompt)

                content = response.text
            finally:
                # 恢复 requests.Session
                if user_agent:
                    requests.Session = old_session

        else:  # Default to OpenAI
            client_kwargs = {
                "api_key": config.llm_api_key,
                "base_url": config.llm_base_url,
            }
            if user_agent:
                client_kwargs["default_headers"] = {"User-Agent": user_agent}

            client = openai.OpenAI(**client_kwargs)

            response = client.chat.completions.create(
                model=config.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
            )
            content = response.choices[0].message.content

        return content
    except Exception as e:
        console.print(f"\n[red]AI 生成内容时出错了 ({config.llm_provider}): {e}[/red]")
        return None


def generate_full_report(commits: List[Dict[str, Any]]) -> Optional[str]:
    """
    生成会议总结风格的完整报告。
    """
    if not commits:
        return "没找到符合条件的提交记录。"

    prompt = _construct_prompt(commits)
    system_prompt = (
        "Role: Technical Lead. Task: Summarize git history into a Markdown weekly report for leadership.\n"
        "Output Language: Natural, colloquial Chinese (avoid translation tone).\n"
        "Requirements:\n"
        "1. Focus on key achievements and technical implementation details based on diffs. Avoid trivial logs.\n"
        "2. Categorize by: '功能开发', '问题修复', '代码重构', '杂项'.\n"
        "3. CONSTRAINT: Output ONLY the report body. NO conversational filler (e.g., 'Here is the report')."
    )
    
    return _call_llm(system_prompt, prompt)


def generate_feishu_report(commits: List[Dict[str, Any]]) -> Optional[str]:
    """
    生成飞书加班申请风格的报告。
    """
    if not commits:
        return "没找到符合条件的提交记录。"

    prompt = _construct_prompt(commits)
    system_prompt = (
        "Role: Employee. Task: Generate Feishu overtime application text from git history.\n"
        "Output Language: Natural, colloquial Chinese.\n"
        "CRITICAL FORMAT RULES:\n"
        "1. Use strict H1 headers (`#`).\n"
        "2. Output ONLY the following structure. NO conversational filler.\n"
        "3. For the results list, use plain numbers (`1.`, `2.`) ONLY. DO NOT use bullets (`-` or `*`).\n"
        "\n"
        "# 加班事由\n"
        "[One sentence summary]\n"
        "\n"
        "# 加班原因及成果预估\n"
        "加班原因：[Reason based on workload/urgency]\n"
        "\n"
        "成果预估：\n"
        "1. [Result 1]\n"
        "2. [Result 2]\n"
        "..."
    )

    return _call_llm(system_prompt, prompt)


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
