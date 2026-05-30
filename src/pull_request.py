import os
import base64
import requests
import logging

logger = logging.getLogger(__name__)


def get_next_adr_number(owner: str, repo: str, headers: dict) -> str:
    """Determine the next sequential ADR number for a repository.

    Checks the docs/adr directory in the target repository and returns
    the next available ADR number as a zero-padded three-digit string.
    Returns "001" if the directory does not exist or is empty.

    Args:
        owner: The GitHub organization or user that owns the repository.
        repo: The repository name.
        headers: Authenticated request headers containing the GitHub Bearer token.

    Returns:
        str: The next ADR number as a zero-padded string (e.g. "001", "002").
    """
    contents_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/docs/adr",
        headers=headers,
    )
    if contents_response.status_code == 200:
        existing = len(contents_response.json())
        return str(existing + 1).zfill(3)
    return "001"


def create_draft_pr(owner: str, repo: str, issue_number: int, adr_content: str) -> str:
    """Create a draft pull request containing a generated ADR document.

    Creates a new branch, commits the ADR markdown file to docs/adr/,
    and opens a draft pull request against the default branch. The PR
    body includes a human review checklist and attribution to Zak.

    Args:
        owner: The GitHub organization or user that owns the repository.
        repo: The repository name.
        issue_number: The issue number the ADR was generated from.
            Used to name the branch, file, and PR title.
        adr_content: The generated ADR document as a markdown string.

    Returns:
        str: The HTML URL of the created draft pull request.

    Raises:
        ValueError: If the PR creation response is empty or does not
            contain an html_url, indicating the PR creation failed.
    """
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    repo_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}", headers=headers
    )
    default_branch = repo_response.json()["default_branch"]

    branch_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{default_branch}",
        headers=headers,
    )
    sha = branch_response.json()["object"]["sha"]

    adr_number = get_next_adr_number(owner, repo, headers)
    branch_name = f"adr/issue-{issue_number}"
    pr_title = f"ADR-{adr_number}: Issue #{issue_number}"
    file_path = f"docs/adr/ADR-{adr_number}-issue-{issue_number}.md"

    requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
    )

    requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}",
        headers=headers,
        json={
            "message": f"docs: add ADR-{adr_number} for issue #{issue_number}",
            "content": base64.b64encode(adr_content.encode()).decode(),
            "branch": branch_name,
        },
    )

    pr_response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        json={
            "title": pr_title,
            "body": (
                f"## 🏗️ ADR Draft\n\n"
                f"**[Zak](https://github.com/Sherwin-14/zak)** just drafted an Architectural Decision Record "
                f"from the discussion in Issue #{issue_number}. Your decision is documented, structured, and ready for review.\n\n"
                f"---\n\n"
                f"### Before you merge\n"
                f"> ⚠️ **AI-generated content — human review required before merging.**\n\n"
                f"- [ ] Read through the entire ADR carefully.\n"
                f"- [ ] Verify the AI has not misrepresented any decisions or participants.\n"
                f"- [ ] Correct any inaccuracies before this becomes part of your documentation.\n\n"
                f"---\n\n"
                f"*AI can make mistakes. You make the call.* 🚀"
            ),
            "head": branch_name,
            "base": default_branch,
            "draft": True,
        },
    )

    logger.info(f"PR response status: {pr_response.status_code}")
    logger.info(f"PR response body: {pr_response.text}")

    if not pr_response.text:
        raise ValueError(
            f"Empty response from GitHub. Status code: {pr_response.status_code}"
        )

    pr_data = pr_response.json()
    if "html_url" not in pr_data:
        raise ValueError(f"PR creation failed: {pr_data}")
    return pr_data["html_url"]
