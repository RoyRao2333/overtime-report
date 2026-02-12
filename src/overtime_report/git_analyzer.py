import fnmatch
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import git
from rich.console import Console

from overtime_report.config import config

console = Console()


def get_commit_history(
    repo_path: Path, days: int, author_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    根据筛选条件获取 Git 提交历史。
    """
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        console.print(f"[red]出错了：{repo_path} 不是一个有效的 Git 仓库。[/red]")
        return []

    if not author_email:
        reader = repo.config_reader()
        try:
            author_email = reader.get_value("user", "email")
        except:
            console.print(
                "[yellow]警告：无法自动检测到 git user.email。请使用 --author 参数指定。[/yellow]"
            )
            return []

    # 计算日期范围
    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    commits_data = []

    # 遍历 commits 并手动过滤，以获得更好的控制

    try:
        # 限制遍历范围
        commits = repo.iter_commits(since=since_date)
    except Exception as e:
        console.print(f"[red]遍历提交记录时出错：{e}[/red]")
        return []

    for commit in commits:
        if author_email not in commit.author.email:
            continue

        commit_info = {
            "hash": commit.hexsha[:8],
            "date": datetime.fromtimestamp(commit.committed_date).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "message": commit.message.strip(),
            "diffs": [],
        }

        # 获取 Diff (如果是首次提交，则对比空树)
        parents = commit.parents
        if parents:
            diffs = parents[0].diff(commit, create_patch=True)
        else:
            diffs = commit.diff(git.NULL_TREE, create_patch=True)

        for diff in diffs:
            file_path = diff.b_path or diff.a_path
            if not file_path:
                continue

            # 检查文件是否被忽略
            if _is_ignored(file_path):
                continue

            # 获取 Diff 内容并解码
            try:
                diff_text = diff.diff.decode("utf-8", errors="replace")
            except Exception:
                diff_text = "[Binary or Non-UTF8 Content]"

            # 如果内容过长则截断
            diff_text = _truncate_diff(diff_text)

            commit_info["diffs"].append({"file": file_path, "content": diff_text})

        if commit_info["diffs"]:
            commits_data.append(commit_info)

    return commits_data


def _is_ignored(file_path: str) -> bool:
    """检查文件路径是否匹配忽略模式。"""
    for pattern in config.ignored_files:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def _truncate_diff(diff_text: str) -> str:
    """如果 Diff 内容超过最大行数则进行截断。"""
    if config.max_diff_lines < 0:
        return diff_text

    lines = diff_text.splitlines()
    if len(lines) > config.max_diff_lines:
        return "\n".join(lines[: config.max_diff_lines]) + "\n...[Truncated]"
    return diff_text
