import sys
import os
from issues import get_all_comments, format_issue_as_markdown

def main():
    if len(sys.argv) != 4:
        print("Usage: main.py <owner> <repo> <issue_number>")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    issue_number = int(sys.argv[3])

    print(f"Fetching issue #{issue_number} from {owner}/{repo} ...")
    
    try:
        issue_data = get_all_comments(owner, repo, issue_number)
        markdown = format_issue_as_markdown(issue_data)
        
        # FIX: Actually save the file to disk so the Action can find it
        output_filename = "issue_thread.md"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(markdown)
            
        print(f"Successfully saved to {output_filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()