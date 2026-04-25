import os
import requests
import logging

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def build_query(owner: str, name: str, issue_number: int, cursor: str | None) -> str:
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

def get_all_comments(owner: str, name: str, issue_number: int) -> dict:
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_PERSONAL_ACCESS_TOKEN is not set")

    headers = {"Authorization": f"Bearer {token}"}
    all_comments = []
    cursor = None

    while True:
        try:
            response = requests.post(
                GITHUB_GRAPHQL_URL,
                json={"query": build_query(owner, name, issue_number, cursor)},
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            raise TimeoutError("GitHub API request timed out")
        except requests.exceptions.HTTPError as e:
            raise ConnectionError(f"GitHub API HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to reach GitHub API: {e}")

        if "errors" in data:
            raise ValueError(f"GraphQL error: {data['errors']}")

        issue = data["data"]["repository"]["issue"]
        if issue is None:
            raise ValueError(f"Issue #{issue_number} not found in {owner}/{name}")

        comments = issue["comments"]
        all_comments.extend(edge["node"] for edge in comments["edges"])

        if not comments["pageInfo"]["hasNextPage"]:
            break
        cursor = comments["pageInfo"]["endCursor"]

    return {"title": issue["title"], "body": issue["body"], "comments": all_comments}

def format_issue_as_markdown(issue_data: dict) -> str:
    lines = []
    lines.append(f"# {issue_data['title']}\n")
    lines.append(f"{issue_data['body']}\n")
    lines.append("---\n")

    for comment in issue_data["comments"]:
        author = comment["author"]["login"]
        body = comment["body"]
        lines.append(f"**@{author}:**\n\n{body}\n")
        lines.append("---\n")

    return "\n".join(lines)

