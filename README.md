# Hekmo (`ܚܶܟܡܬܐ`)

**Lightning fast ADR drafting for busy teams.**

This tool takes a GitHub issue or discussion thread the arguments, the back-and-forth, the eventual consensus and distills it into a clean Architecture Decision Record (ADR), so the reasoning behind a decision doesn't get lost in a comment thread nobody wants to re-read.

---

## Motivation

Most engineering decisions don't happen in a design doc. They happen in a GitHub issue: someone proposes something, three people push back, someone finds a tradeoff nobody considered, and twenty comments later there's a decision — buried in a thread that will never be read again.

`hekmo` exists to close that gap. Point it at an issue, and it reconstructs the *decision*, not the discussion: what was decided, why, what alternatives were rejected, and what the tradeoffs were formatted as a proper ADR you can commit to your repo.

It's built for teams (and solo maintainers) who make real decisions in GitHub threads but don't have time to write them up twice.

---

## Quick start

```bash
pip install hekmo
```

Set two environment variables (see [Configuration](#configuration)):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxx
export DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx
```

Then run:

```bash
hekmo
```

---

## Configuration

`hekmo` needs two credentials, set as environment variables (a `.env` file in your working directory also works, via `python-dotenv`):

| Variable | Purpose | Where to get it |
|---|---|---|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Reads issue/comment data via the GitHub GraphQL API | [github.com/settings/tokens](https://github.com/settings/tokens) — needs `repo` read scope for private repos, no scope needed for public repos |
| `DEEPSEEK_API_KEY` | Powers ADR generation | [platform.deepseek.com](https://platform.deepseek.com) |

---

## Templates

`hekmo` supports multiple ADR formats out of the box, selectable at runtime:

- **Nygard** — the original, lightweight ADR format (Context / Decision / Status / Consequences)
- **MADR** — Markdown Architecture Decision Records, a more structured format with explicit alternatives considered
- *(see `hekmo/utils/templates.json` for the full list and section definitions)*

---

## Example

```bash
$ hekmo

  GitHub org / owner    e.g. pandas-dev
  › nasa
  
  Repository             e.g. pandas
  › earthaccess
  
  Issue Number           e.g. 700
  › 42

  Choose a template (enter a number)
  1 nygard    2 madr    3 alexandrian
  › 1

  ✓ Got: 'Add request timeout to session calls'
  ✓ ADR ready
  ✓ ADR written to adr-42.md
```

---

## Requirements

- Python 3.12+
- A GitHub personal access token
- A DeepSeek API key

## License

MIT
