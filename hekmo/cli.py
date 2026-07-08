import logging
import sys
from pathlib import Path

import click
import pyfiglet
from rich.align import Align
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from hekmo.exceptions import HekmoError
from hekmo.issues import format_issue_as_markdown, get_all_comments
from hekmo.llm import build_system_prompt, generate_adr, load_templates

logging.disable(logging.CRITICAL)

console = Console(highlight=False)

SUBTITLE = "Lightning fast ADR drafting for busy teams"


def print_banner() -> None:
    """Print the CLI banner with ASCII art and subtitle."""
    art = pyfiglet.figlet_format("Hekmo", font="slant")
    console.print()
    console.print(Align.center(Text(art.rstrip(), style="bold cyan")))
    console.print()
    console.print(Align.center(Text(SUBTITLE, style="dim white")))
    console.print()


def step(msg: str) -> None:
    """Print a step indicator message.

    Args:
        msg: The message to display.
    """
    console.print(f"\n[bold cyan]·[/bold cyan] [white]{msg}[/white]")


def ok(msg: str) -> None:
    """Print a success message with a green checkmark.

    Args:
        msg: The success message to display.
    """
    console.print(f"[bold green]✓[/bold green] {msg}")


def fail(msg: str) -> None:
    """Print a failure message with a red cross.

    Args:
        msg: The failure message to display.
    """
    console.print(f"[bold red]✗[/bold red] {msg}")


def spinner(label: str, fn, *args, **kwargs):
    """Run a function while displaying a spinner in the terminal.

    Args:
        label: The text shown next to the spinner.
        fn: The callable to execute.
        *args: Positional arguments passed to fn.
        **kwargs: Keyword arguments passed to fn.

    Returns:
        The return value of fn.
    """
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"[dim]{label}[/dim]"),
        transient=True,
        console=console,
    ) as p:
        p.add_task("")
        result = fn(*args, **kwargs)

    return result


def ask(label: str, hint: str = "", default: str = "", required: bool = True) -> str:
    """Prompt the user for a text value.

    Args:
        label: The bold label shown above the prompt.
        hint: Optional dim hint shown next to the label.
        default: Fallback value if the user enters nothing.

    Returns:
        The user's input, or the default if input was empty.
    """
    while True:
        console.print(
            f"\n [bold white]{label}[/bold white]"
            + (f"[dim]{hint}[/dim]" if hint else "")
        )
        val = click.prompt(
            "  › ", default="", show_default=False, prompt_suffix=""
        ).strip()
        result = val or default
        if result or not required:
            return result
        console.print("\n [red]This field is required.[/red]")


def ask_int(label: str, hint: str = "") -> int:
    """Prompt the user for an integer value, retrying on invalid input.

    Args:
        label: The bold label shown above the prompt.
        hint: Optional dim hint shown next to the label.

    Returns:
        The validated integer entered by the user.
    """
    while True:
        console.print(
            f"\n [bold white]{label}[/bold white]"
            + (f"[dim]{hint}[/dim]" if hint else "")
        )
        raw = click.prompt(
            "  › ", default="", show_default=False, prompt_suffix=""
        ).strip()
        if raw.isdigit():
            return int(raw)
        console.print("[red]Please enter a number.[/red]")


def ask_template() -> str:
    """Prompt the user to select an ADR template by number.

    Displays available templates in a compact multi-column layout
    and validates the selection.

    Returns:
        The key of the selected template (e.g. 'madr', 'nygard').
    """
    TEMPLATES_DATA = load_templates()
    items = list(TEMPLATES_DATA.items())
    console.print(
        "\n [bold white]Choose a template[/bold white] [dim](enter a number)[/dim]"
    )
    rows = [items[i : i + 3] for i in range(0, len(items), 3)]
    for row in rows:
        line = "".join(
            f" [dim]{i + 1 + rows.index(row) * 3}[/dim] {key:<18}"
            for i, (key, _) in enumerate(row)
        )
        console.print(line)

    console.print()
    while True:
        val = click.prompt(
            "  › ", default="1", show_default=False, prompt_suffix=""
        ).strip()
        if val.isdigit():
            idx = int(val) - 1
            if 0 <= idx < len(items):
                return items[idx][0]
        console.print("\n [red]Please enter a valid number.[/red]")


@click.command()
def cli():
    """hekmo — fast ADR drafting from GitHub issues."""
    print_banner()

    owner = ask("GitHub org / owner  ", "e.g. pandas-dev")
    repo = ask("Repository  ", "e.g. pandas")
    issue_no = ask_int("Issue Number  ", "e.g. 700")

    try:
        template = ask_template()
        issue_data = spinner("fetching ...", get_all_comments, owner, repo, issue_no)
        console.print()
        ok(f"Got: {issue_data.get('title', '')!r}")
        console.print()
        markdown = format_issue_as_markdown(issue_data)
        system_prompt = build_system_prompt(template)
        adr = spinner("Scrumdiddlyumpting ... ", generate_adr, markdown, system_prompt)

    except HekmoError as e:
        console.print()
        fail(e.message)
        if e.hint:
            console.print(f"[dim]  {e.hint}[/dim]")
        sys.exit(1)

    ok("ADR ready")

    filename = f"adr-{issue_no}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(adr)
    except OSError as e:
        console.print()
        fail(f"Could not write ADR to {filename}.")
        console.print(f"[dim]  {e}[/dim]")
        sys.exit(1)

    console.print()
    console.print(f"[green]✓ ADR written to[/green] [dim]{Path.cwd() / filename}[/dim]")
