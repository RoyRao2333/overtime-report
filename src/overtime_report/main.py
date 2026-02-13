from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from overtime_report.ai_reporter import generate_full_report, generate_feishu_report
from overtime_report.git_analyzer import get_commit_history

app = typer.Typer(help="加班报告生成器 CLI")
console = Console()


@app.command()
def generate(
    days: int = typer.Option(7, help="回溯过去多少天。"),
    path: Path = typer.Option(Path("."), help="Git 仓库的路径。"),
    full: bool = typer.Option(False, "--full", help="仅生成完整汇报文档"),
    feishu: bool = typer.Option(False, "--feishu", help="仅生成飞书加班文档"),
):
    """
    根据 Git 历史生成开发工作报告。
    """
    from overtime_report.config import config
    
    # 默认行为：如果未指定任何标志，则生成所有报告
    if not full and not feishu:
        full = True
        feishu = True
        
    console.print(f"[bold blue]开始生成加班报告[/bold blue]")
    console.print(f"正在分析仓库：{path.absolute()}")
    console.print(f"时间范围：最近 {days} 天")
    console.print(f"作者：{config.author}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="正在分析 Git 历史...", total=None)
        # 使用配置中的 author
        commits = get_commit_history(path, days, config.author)
        progress.update(task, completed=True)

    if not commits:
        console.print("[yellow]没找到合适的提交记录来生成报告。[/yellow]")
        return

    console.print(f"[green]找到了 {len(commits)} 条提交记录。[/green]")

    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    # 生成完整报告
    if full:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="正在生成完整会议总结报告 (Full)...", total=None)
            full_report_content = generate_full_report(commits)
            progress.update(task, completed=True)

        if full_report_content:
            output_file_full = output_dir / f"report_full_{timestamp}.md"
            try:
                with open(output_file_full, "w", encoding="utf-8") as f:
                    f.write(full_report_content)
                console.print(f"[bold green]完整报告生成成功！[/bold green]")
                console.print(f"保存路径：[underline]{output_file_full.absolute()}[/underline]")
            except Exception as e:
                console.print(f"[red]保存完整报告时出错：{e}[/red]")
    
    # 生成飞书报告
    if feishu:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="正在生成飞书加班申请报告 (Feishu)...", total=None)
            feishu_report_content = generate_feishu_report(commits)
            progress.update(task, completed=True)

        if feishu_report_content:
            output_file_feishu = output_dir / f"report_feishu_{timestamp}.md"
            try:
                with open(output_file_feishu, "w", encoding="utf-8") as f:
                    f.write(feishu_report_content)
                console.print(f"[bold green]飞书报告生成成功！[/bold green]")
                console.print(f"保存路径：[underline]{output_file_feishu.absolute()}[/underline]")
            except Exception as e:
                console.print(f"[red]保存飞书报告时出错：{e}[/red]")


if __name__ == "__main__":
    app()
