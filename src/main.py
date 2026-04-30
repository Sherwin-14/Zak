import sys
from issues import get_all_comments, format_issue_as_markdown

def main():
    if len(sys.argv) != 4:
        print("Usage: main.py <owner> <repo> <issue_number>")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    issue_number = int(sys.argv[3])

    print(f"Fetching issue #{issue_number} from {owner}/{repo} ...")
    issue_data = get_all_comments(owner, repo, issue_number)
    markdown = format_issue_as_markdown(issue_data)
    print(markdown)

if __name__ == "__main__":
    main()