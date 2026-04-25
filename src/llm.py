from pathlib import Path

PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"
DEFAULT_TEMPLATE = "Use the standard Nygard format: Title, Status, Context, Decision, Consequences."

def build_system_prompt(adr_template: str = "default") -> str:
    template_instruction = (
        DEFAULT_TEMPLATE
        if adr_template == "default"
        else f"Use exactly this template provided by the user:\n\n{adr_template}"
    )

    return PROMPT_PATH.read_text().format(adr_template=template_instruction)