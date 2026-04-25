import os
from pathlib import Path

DEFAULT_TEMPLATE = "Use the standard Nygard format: Title, Status, Context, Decision, Consequences."

def build_system_prompt(adr_template: str = "default") -> str:
    template_instruction = (
        DEFAULT_TEMPLATE
        if adr_template == "default"
        else f"Use exactly this template provided by the user:\n\n{adr_template}"
    )

    action_root = os.environ["GITHUB_ACTION_PATH"]
    prompt_path = Path(action_root) / "src" / "prompts" / "system_prompt.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt not found at {prompt_path}")

    return prompt_path.read_text().format(adr_template=template_instruction)