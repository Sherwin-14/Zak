import logging
from issues import get_all_comments, format_issue_as_markdown
from llm import build_system_prompt, generate_adr
from pull_request import create_draft_pr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    owner = input("Enter org/owner: ").strip()
    repo = input("Enter repo name: ").strip()
    issue_number = int(input("Enter issue number: ").strip())
    adr_template = (
        input("Enter ADR template (default/madr) [default]: ").strip() or "default"
    )

    logger.info(f"Fetching issue #{issue_number} from {owner}/{repo}...")
    issue_data = get_all_comments(owner, repo, issue_number)
    markdown = format_issue_as_markdown(issue_data)

    logger.info("Generating ADR...")
    system_prompt = build_system_prompt(adr_template)
    adr = generate_adr(markdown, system_prompt)

    # print("\n" + "="*60)
    # print("GENERATED ADR")
    # print("="*60 + "\n")
    # print(adr)

    pr_url = create_draft_pr(owner, repo, issue_number, adr)
    logger.info(f"Draft PR created: {pr_url}")


if __name__ == "__main__":
    main()
