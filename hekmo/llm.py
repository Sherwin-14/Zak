import json
import logging
import os
from pathlib import Path

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
)

from hekmo.exceptions import (
    LLMAuthError,
    LLMConnectionError,
    LLMError,
    LLMTimeoutError,
    TemplateError,
    TokenMissingError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_templates() -> dict:
    """Load ADR templates from the templates.json configuration file.

    Returns:
        dict: A dictionary mapping template names to their section definitions.

    Raises:
        TemplateError: If templates.json does not exist at the expected path
        or is malformed.
    """
    templates_path = Path(__file__).parent / "utils" / "templates.json"
    try:
        return json.loads(templates_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise TemplateError(
            "templates.json is missing or corrupted.",
            "This may indicate a broken installation, try reinstalling hekmo.",
        ) from e


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
        TemplateError: If the template name is unknown, templates.json is
            missing/corrupted, or system_prompt.md is missing.
    """
    templates = load_templates()
    sections = templates[adr_template]["sections"]
    template_str = "\n".join(f"## {section}" for section in sections)

    prompt_path = Path(__file__).parent / "utils" / "system_prompt.md"
    try:
        system_prompt = prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise TemplateError(
            "system_prompt.md is missing.",
            "This may indicate a broken installation — try reinstalling hekmo.",
        ) from e

    return system_prompt.format(adr_template=f"# {{title}}\n\n{template_str}")


def generate_adr(issue_thread: str, system_prompt: str) -> str:
    """Generate an ADR document from a GitHub issue thread using an LLM.

    Sends the issue thread and system prompt to the configured LLM provider
    (currently DeepSeek V4 Pro) for structured ADR extraction.

    Args:
        issue_thread: The full GitHub issue thread formatted as a markdown
            string, including the issue body and all comments.
        system_prompt: The fully constructed system prompt defining the ADR
            extraction rules and output template.

    Returns:
        str: The generated ADR document as a markdown string.

    Raises:
        TokenMissingError: If DEEPSEEK_API_KEY is not set in the environment.
        LLMAuthError: If the API key is invalid or expired.
        LLMTimeoutError: If the request times out.
        LLMConnectionError: If the LLM provider is unreachable.
        LLMError: If the request fails for any other reason (e.g. context
            window exceeded, malformed response).
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise TokenMissingError(
            "DEEPSEEK_API_KEY is not set.",
            "Export it in your shell before running hekmo.",
        )

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
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
    except AuthenticationError as e:
        raise LLMAuthError(
            "DeepSeek API key expired or invalid.",
            "Check your DEEPSEEK_API_KEY.",
        ) from e
    except APITimeoutError as e:
        raise LLMTimeoutError("DeepSeek API request timed out.") from e
    except APIConnectionError as e:
        raise LLMConnectionError(
            "Could not reach DeepSeek.", "Check your network connection."
        ) from e
    except BadRequestError as e:
        raise LLMError(
            "DeepSeek rejected the request.",
            "The thread may be too long for the model's context window try a shorter thread.",
        ) from e
    except Exception as e:
        raise LLMError(f"Failed to generate ADR: {e}") from e
