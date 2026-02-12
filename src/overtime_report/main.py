from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from overtime_report.ai_reporter import generate_report
from overtime_report.git_analyzer import get_commit_history

app = typer.Typer(help="加班报告生成器 CLI")
console = Console()


@app.command()
def generate(
    days: int = typer.Option(7, help="回溯过去多少天。"),
    author: Optional[str] = typer.Option(
        None, help="用于过滤提交的作者邮箱。默认使用 git config user.email。"
    ),
    path: Path = typer.Option(Path("."), help="Git 仓库的路径。"),
):
    """
    根据 Git 历史生成开发工作报告。
    """
    console.print(f"[bold blue]开始生成加班报告[/bold blue]")
    console.print(f"正在分析仓库：{path.absolute()}")
    console.print(f"时间范围：最近 {days} 天")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="正在分析 Git 历史...", total=None)
        commits = get_commit_history(path, days, author)
        progress.update(task, completed=True)

    if not commits:
        console.print("[yellow]没找到合适的提交记录来生成报告。[/yellow]")
        return

    console.print(f"[green]找到了 {len(commits)} 条提交记录。[/green]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="正在呼叫 AI 生成报告...", total=None)
        report_content = generate_report(commits)
        progress.update(task, completed=True)

    if report_content is None:
        return

    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    output_file = output_dir / f"report_{timestamp}.md"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        console.print(f"[bold green]报告生成成功！[/bold green]")
        console.print(f"保存路径：[underline]{output_file.absolute()}[/underline]")
    except Exception as e:
        console.print(f"[red]保存报告时出错：{e}[/red]")


if __name__ == "__main__":
    app()
