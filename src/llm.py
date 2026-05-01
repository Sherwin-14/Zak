import os
import json
from pathlib import Path
from openai import OpenAI

def load_templates() -> dict:
    templates_path = Path(__file__).parent / "prompts" / "templates.json"
    return json.loads(templates_path.read_text(encoding="utf-8"))

def build_system_prompt(adr_template: str = "default") -> str:
    templates = load_templates()
    
    if adr_template not in templates:
        raise ValueError(f"Unknown template '{adr_template}'. Available: {list(templates.keys())}")
    
    sections = templates[adr_template]["sections"]
    template_str = "\n".join(f"## {section}" for section in sections)
    
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    return system_prompt.format(adr_template=f"# {{title}}\n\n{template_str}")


def generate_adr(issue_thread: str, system_prompt: str) -> str:
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    )

    response = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "gpt-4.1"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": issue_thread},
        ],
        temperature=0,
        max_tokens=4096,
    )

    return response.choices[0].message.content