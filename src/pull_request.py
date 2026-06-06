import os
import json
import base64
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_auth_headers() -> dict:
    """Build authenticated request headers using the GitHub personal access token.

    Returns:
        dict: Headers containing the Bearer token and GitHub API accept type.

    Raises:
        EnvironmentError: If GITHUB_PERSONAL_ACCESS_TOKEN is not set.
    """
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError(
            "GITHUB_PERSONAL_ACCESS_TOKEN is not set. "
            "Add it as a repo secret named GITHUB_PERSONAL_ACCESS_TOKEN."
        )
    # never log the token value or the full headers dict
    logger.info("GitHub auth headers built successfully")
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def load_pr_body(issue_number: int) -> str:
    """Load and format the PR body template from pr_body.json.

    Args:
        issue_number: The issue number to inject into the template.

    Returns:
        str: The formatted PR body string.
    """
    pr_body_path = Path(__file__).parent / "prompts" / "pr_body.json"
    template = json.loads(pr_body_path.read_text(encoding="utf-8"))
    body = "\n".join(template["pr_body"])
    return body.replace("{issue_number}", str(issue_number))


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


def push_adr_to_branch(
    owner: str,
    repo: str,
    issue_number: int,
    adr_content: str,
    adr_number: str,
    default_branch: str,
    headers: dict,
) -> str:
    """Create a branch and commit the ADR file to the repository.

    Args:
        owner: The GitHub organization or user that owns the repository.
        repo: The repository name.
        issue_number: The issue number the ADR was generated from.
        adr_content: The generated ADR document as a markdown string.
        adr_number: The zero-padded ADR number (e.g. "001").
        default_branch: The default branch to base the new branch on.
        headers: Authenticated request headers containing the GitHub Bearer token.

    Returns:
        str: The branch name the ADR was committed to.

    Raises:
        ValueError: If branch creation or file commit fails.
    """
    branch_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{default_branch}",
        headers=headers,
    )
    sha = branch_response.json()["object"]["sha"]

    branch_name = f"adr/issue-{issue_number}"
    file_path = f"docs/adr/ADR-{adr_number}.md"

    branch_create_response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
    )
    if branch_create_response.status_code not in (201, 422):
        raise ValueError(f"Branch creation failed: {branch_create_response.json()}")
    if branch_create_response.status_code == 422:
        logger.warning(f"Branch {branch_name} already exists, reusing it")

    file_response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}",
        headers=headers,
        json={
            "message": f"docs: add ADR-{adr_number} for issue #{issue_number}",
            "content": base64.b64encode(adr_content.encode()).decode(),
            "branch": branch_name,
        },
    )
    logger.info(f"File creation: {file_response.status_code}")

    return branch_name


def create_draft_pr(
    owner: str,
    repo: str,
    branch_name: str,
    default_branch: str,
    issue_number: int,
    adr_number: str,
    headers: dict,
) -> str:
    """Create a draft pull request against the default branch.

    Args:
        owner: The GitHub organization or user that owns the repository.
        repo: The repository name.
        branch_name: The branch containing the ADR commit.
        default_branch: The base branch to target.
        issue_number: The issue number the ADR was generated from.
        adr_number: The zero-padded ADR number (e.g. "001").
        headers: Authenticated request headers.

    Returns:
        str: The HTML URL of the created draft pull request.

    Raises:
        ValueError: If PR creation fails.
    """
    pr_response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        json={
            "title": f"ADR-{adr_number}: Issue #{issue_number}",
            "body": load_pr_body(issue_number),
            "head": branch_name,
            "base": default_branch,
            "draft": True,
        },
    )

    logger.info(f"PR response status: {pr_response.status_code}")

    pr_data = pr_response.json()
    if "html_url" not in pr_data:
        raise ValueError(f"PR creation failed: {pr_data}")
    return pr_data["html_url"]


def run_adr_pipeline(
    owner: str,
    repo: str,
    issue_number: int,
    adr_content: str,
) -> str:
    """Orchestrate branch creation, file commit, and draft PR creation.

    Args:
        owner: The GitHub organization or user that owns the repository.
        repo: The repository name.
        issue_number: The issue number the ADR was generated from.
        adr_content: The generated ADR document as a markdown string.

    Returns:
        str: The HTML URL of the created draft pull request.

    Raises:
        ValueError: If any step of the pipeline fails.
    """
    headers = get_auth_headers()

    repo_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}", headers=headers
    )
    repo_data = repo_response.json()
    default_branch = repo_data["default_branch"]

    adr_number = get_next_adr_number(owner, repo, headers)

    branch_name = push_adr_to_branch(
        owner, repo, issue_number, adr_content, adr_number, default_branch, headers
    )

    return create_draft_pr(
        owner, repo, branch_name, default_branch, issue_number, adr_number, headers
    )
