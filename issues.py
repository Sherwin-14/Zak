import os
import requests
import logging

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def get_all_comments(owner: str, name: str, issue_number: int) -> list[dict]:
    load_dotenv() 
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_PERSONAL_ACCESS_TOKEN is not set")
  
    headers = {"Authorization": f"Bearer {token}"}
    all_comments = []
    cursor = None

    while True:
        after = f', after: "{cursor}"' if cursor else ""
        query = f"""
        query {{
          repository(owner: "{owner}", name: "{name}") {{
            issue(number: {issue_number}) {{
              title
              body
              comments(first: 100{after}) {{
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
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

        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query},
            headers=headers
        ).json()

        issue = response["data"]["repository"]["issue"]
        comments = issue["comments"]

        all_comments.extend(edge["node"] for edge in comments["edges"])

        if not comments["pageInfo"]["hasNextPage"]:
            break

        cursor = comments["pageInfo"]["endCursor"]

    return all_comments

comments = get_all_comments("earthaccess-dev", "earthaccess", 929)

print(str(list(map(lambda x: f"author: {x['author']['login']} {x['body']}", comments))))