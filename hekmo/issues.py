import os
import requests

from hekmo.exceptions import (
    GitHubError,
    GitHubNotFoundError,
    TokenMissingError,
)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def build_query(owner: str, name: str, issue_number: int, cursor: str | None) -> str:
    """Build a GraphQL query to fetch a GitHub issue and its comments.

    Uses cursor-based pagination to support threads of any length. If a cursor
    is provided, the query fetches the next page of comments starting after
    that cursor.

    Args:
        owner: The GitHub organization or user that owns the repository.
        name: The repository name.
        issue_number: The issue number to fetch.
        cursor: The pagination cursor from the previous page's endCursor.
            Pass None to fetch from the beginning.

    Returns:
        str: A fully constructed GraphQL query string.
    """
    after = f', after: "{cursor}"' if cursor else ""
    return f"""
        query {{
          repository(owner: "{owner}", name: "{name}") {{
            issue(number: {issue_number}) {{
              title
              body
              comments(first: 100{after}) {{
                pageInfo {{ hasNextPage endCursor }}
                edges {{
                  node {{
                    author {{ login }}
                    body
                    createdAt
                  }}
                }}
              }}
            }}
          }}
        }}
    """


def extract_issue(data: dict, owner: str, repo: str, issue_number: int) -> dict:
    """Extract and validate the issue object from a GitHub GraphQL API response.

    Validates the response structure and raises descriptive errors if the
    owner, repository, or issue cannot be resolved.

    Args:
        data: The raw JSON response from the GitHub GraphQL API.
        owner: The GitHub organization or user that owns the repository.
        repo: The repository name.
        issue_number: The issue number that was requested.

    Returns:
        dict: The issue object containing title, body, and comments.

    Raises:
        GitHubNotFoundError: If the issue number is invalid, or if the owner,
              repository, or issue cannot be resolved.
        GitHubError: If the API response is malformed or contains GraphQL
              errors.
    """
    if not isinstance(issue_number, int) or issue_number < 1:
        raise GitHubNotFoundError(
            f"Invalid issue number: {issue_number}.",
            "Must be a positive integer.",
        )

    if "errors" in data:
        raise GitHubError(f"GitHub API error: {data['errors'][0]['message']}")

    if "data" not in data or data["data"] is None:
        raise GitHubError("Unexpected API response from GitHub.")

    repository = data["data"]["repository"]
    if repository is None:
        raise GitHubNotFoundError(
            f"Owner '{owner}' not found.",
            "Check the org/username spelling.",
        )

    issue = repository["issue"]
    if issue is None:
        raise GitHubNotFoundError(
            f"Issue #{issue_number} not found in {owner}/{repo}.",
            "Check the repo name and issue number.",
        )

    return issue


def get_all_comments(owner: str, name: str, issue_number: int) -> dict:
    """Fetch all comments for a GitHub issue using cursor-based pagination.

    Iterates through all pages of comments until the full thread is retrieved.
    Handles threads of any length without risk of skipping comments.

    Args:
        owner: The GitHub organization or user that owns the repository.
        name: The repository name.
        issue_number: The issue number to fetch.

    Returns:
        dict: A dictionary containing:
            - title (str): The issue title.
            - body (str): The issue body.
            - comments (list): A list of comment nodes, each containing
              author login, body, and createdAt timestamp.

    Raises:
        TokenMissingError: If GITHUB_PERSONAL_ACCESS_TOKEN is not set.
        GitHubError: If the GitHub API returns an HTTP error or is
            unreachable.
        GitHubNotFoundError: If the API response is malformed or the issue cannot
            be resolved.
    """
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise TokenMissingError(
            "GITHUB_PERSONAL_ACCESS_TOKEN is not set.",
            "Export it in your shell before running hekmo.",
        )

    headers = {"Authorization": f"Bearer {token}"}
    all_comments = []
    cursor = None

    while True:
        try:
            response = requests.post(
                GITHUB_GRAPHQL_URL,
                json={"query": build_query(owner, name, issue_number, cursor)},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout as e:
            raise GitHubError("GitHub API request timed out.") from e
        except requests.exceptions.RequestException as e:
            raise GitHubError("Unexpected error contacting GitHub.") from e
        except ValueError as e:
            raise GitHubError("Failed to parse GitHub's response.") from e

        issue = extract_issue(data, owner, name, issue_number)
        comments = issue["comments"]
        all_comments.extend(edge["node"] for edge in comments["edges"])

        if not comments["pageInfo"]["hasNextPage"]:
            break
        cursor = comments["pageInfo"]["endCursor"]

    return {"title": issue["title"], "body": issue["body"], "comments": all_comments}


def format_issue_as_markdown(issue_data: dict) -> str:
    """Format a GitHub issue and its comments as a markdown string.

    Produces a clean, structured markdown document with the issue title,
    body, and all comments formatted with author attribution and timestamps.
    Handles deleted accounts gracefully by substituting 'unknown' for
    null author fields.

    Args:
        issue_data: A dictionary containing title, body, and comments,
            as returned by get_all_comments.

    Returns:
        str: The full issue thread formatted as a markdown string, ready
            to be passed to the LLM for ADR generation.
    """
    lines = []
    lines.append(f"# {issue_data['title']}\n")
    lines.append(f"{issue_data['body'] or ''}\n")
    lines.append("---\n")

    for comment in issue_data["comments"]:
        author = comment["author"]["login"] if comment.get("author") else "unknown"
        body = comment["body"]
        created_at = comment.get("createdAt", "unknown date")
        lines.append(f"**@{author}** _{created_at}_:\n\n{body}\n")
        lines.append("---\n")

    return "\n".join(lines)
