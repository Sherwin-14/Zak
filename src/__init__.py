import click
import logging
import pyfiglet

from rich.console import Console

from rich.align import Align
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from issues import get_all_comments, format_issue_as_markdown
from llm import build_system_prompt, generate_adr, load_templates

logging.disable(logging.CRITICAL)

console = Console(highlight=False)

SUBTITLE = "Fast ADR drafting that turns GitHub chaos into documented decisions"


def print_banner() -> None:
    art = pyfiglet.figlet_format("zak", font="starwars")
    console.print()
    console.print(Align.center(Text(art.rstrip(), style="bold cyan")))
    console.print()
    console.print(Align.center(Text(SUBTITLE, style="dim white")))
    console.print()


def ask(label: str, hint: str = "", default: str = "") -> str:
    console.print(
        f"\n  [bold white]{label}[/bold white]"
        + (f"  [dim]{hint}[/dim]" if hint else "")
    )
    val = click.prompt("  › ", default="", show_default=False, prompt_suffix="").strip()
    return val or default


def ask_int(label: str, hint: str = "") -> int:
    while True:
        console.print(
            f"\n  [bold white]{label}[/bold white]"
            + (f"  [dim]{hint}[/dim]" if hint else "")
        )
        raw = click.prompt(
            "  › ", default="", show_default=False, prompt_suffix=""
        ).strip()
        if raw.isdigit():
            return int(raw)
        console.print("  [red]Please enter a number.[/red]")


def ask_template() -> str:
    TEMPLATES_DATA = load_templates()
    items = list(TEMPLATES_DATA.items())  # list of (key, data)
    console.print("\n  [bold white]Choose a template[/bold white]")
    for i, (key, data) in enumerate(items, start=1):
        sections = data["sections"]
        # Build a short description from the first few sections
        if len(sections) <= 3:
            desc = ", ".join(sections)
        else:
            desc = f"{sections[0]}, {sections[1]}, … +{len(sections)-2} more"
        console.print(f"    [cyan]{i}[/cyan]  {key} — {desc}")

    while True:
        val = click.prompt(
            "  › ", default="1", show_default=False, prompt_suffix=""
        ).strip()
        if val.isdigit():
            idx = int(val) - 1
            if 0 <= idx < len(items):
                return items[idx][0]
        console.print("  [red]Please enter a valid number.[/red]")


def step(msg: str) -> None:
    console.print(f"\n  [bold cyan]·[/bold cyan] [white]{msg}[/white]")


def ok(msg: str) -> None:
    console.print(f"  [bold green]✓[/bold green] {msg}")


def fail(msg: str) -> None:
    console.print(f"  [bold red]✗[/bold red] {msg}")


def spinner(label: str, fn, *args, **kwargs):
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"  [dim]{label}[/dim]"),
        transient=True,
        console=console,
    ) as p:
        p.add_task("")
        return fn(*args, **kwargs)


@click.command()
def cli():
    """zak — fast ADR drafting from GitHub issues and discussions."""
    print_banner()

    console.print("  [bold]Tell me about the issue[/bold]")

    owner = ask("GitHub org / owner", "e.g. pandas-dev")
    repo = ask("Repository", "e.g. pandas")
    issue_no = ask_int("Issue Number", "number only")
    template = ask_template()
    issue_data = spinner("fetching…", get_all_comments, owner, repo, issue_no)
    ok(f"Got: {issue_data.get('title', '')!r}")

    step("Generating ADR")
    markdown = format_issue_as_markdown(issue_data)
    system_prompt = build_system_prompt(template)
    adr = spinner("Scrumdiddlyumpting", generate_adr, markdown, system_prompt)
    ok("ADR ready")

    filename = f"adr-{issue_no}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(adr)

    console.print(f"\n  [green]✓ ADR written to {filename}[/green]")
    console.print(f"  [dim]Location: {Path.cwd() / filename}[/dim]")
    console.print("\n  [bold cyan]Done.[/bold cyan]\n")


if __name__ == "__main__":
    cli()
