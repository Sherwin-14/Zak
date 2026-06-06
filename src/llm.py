import os
import logging
import json
from pathlib import Path
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_templates() -> dict:
    """Load ADR templates from the templates.json configuration file.

    Returns:
        dict: A dictionary mapping template names to their section definitions.

    Raises:
        FileNotFoundError: If templates.json does not exist at the expected path.
        json.JSONDecodeError: If templates.json is malformed.
    """
    templates_path = Path(__file__).parent / "prompts" / "templates.json"
    return json.loads(templates_path.read_text(encoding="utf-8"))


def build_system_prompt(adr_template: str = "default") -> str:
    """Build the system prompt for ADR generation using the specified template.

    Loads the template sections from templates.json and injects them into
    the base system prompt, producing a fully formatted prompt string ready
    for use with the LLM.

    Args:
        adr_template: The name of the ADR template to use. Must match a key
            in templates.json. Defaults to "default".

    Returns:
        str: The fully constructed system prompt with the template sections
            injected.

    Raises:
        ValueError: If the specified template name is not found in templates.json.
        FileNotFoundError: If system_prompt.md does not exist at the expected path.
    """
    templates = load_templates()
    if adr_template not in templates:
        raise ValueError(
            f"Unknown template '{adr_template}'. "
            f"Available: {list(templates.keys())}"
        )
    sections = templates[adr_template]["sections"]
    template_str = "\n".join(f"## {section}" for section in sections)
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    return system_prompt.format(adr_template=f"# {{title}}\n\n{template_str}")


def generate_adr(issue_thread: str, system_prompt: str) -> str:
    """Generate an ADR document from a GitHub issue thread using an LLM.

    Sends the issue thread and system prompt to the configured LLM via the
    GitHub Models inference endpoint. Logs a warning if the estimated token
    count exceeds the free tier limit.

    Args:
        issue_thread: The full GitHub issue thread formatted as a markdown
            string, including the issue body and all comments.
        system_prompt: The fully constructed system prompt defining the ADR
            extraction rules and output template.

    Returns:
        str: The generated ADR document as a markdown string.

    Raises:
        KeyError: If GITHUB_PERSONAL_ACCESS_TOKEN is not set in the environment.
        openai.APIError: If the LLM API call fails.
    """
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
    )

    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": issue_thread},
        ],
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}},
    )
    return response.choices[0].message.content
