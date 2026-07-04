<h1 align="center">Hekmo (`ܚܶܟܡܬܐ`)</h1>

**Lightning fast ADR drafting for busy teams.**

This tool takes a GitHub issue or discussion thread the arguments, the back-and-forth, the eventual consensus and distills it into a clean Architecture Decision Record (ADR), so the reasoning behind a decision doesn't get lost in a comment thread nobody wants to re-read.

----

### Requirements

- Python 3.12+
- A GitHub PAT (personal access token)
- A DeepSeek API key

----

### Quick start

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
----

### Configuration

`Hekmo` needs two credentials, set as environment variables (a `.env` file in your working directory also works, via `python-dotenv`):

| Variable | Purpose | Where to get it |
|---|---|---|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Reads issue/comment data via the GitHub GraphQL API | [github.com/settings/tokens](https://github.com/settings/tokens) — needs `repo` read scope for private repos, no scope needed for public repos |
| `DEEPSEEK_API_KEY` | Powers ADR generation | [platform.deepseek.com](https://platform.deepseek.com) |

----

### Templates

`Hekmo` supports multiple ADR formats out of the box, selectable at runtime:

- **Nygard** — the original, lightweight ADR format (Context / Decision / Status / Consequences)
- **MADR** — Markdown Architecture Decision Records, a more structured format with explicit alternatives considered
- *(see `Hekmo/utils/templates.json` for the full list and section definitions)*

----

### Example

```bash
$ Hekmo

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
----

### Motivation

Most engineering decisions don't happen in a design doc. They happen in a GitHub issue: someone proposes something, three people push back, someone finds a tradeoff nobody considered, and twenty comments later there's a decision buried in a thread that will never be read again.

This isn't just anecdotal. A 2023 mining-software-repositories study of ADR usage across open-source GitHub projects ([Buchgeher et al., IEEE Access](https://ieeexplore.ieee.org/document/10155430)) found that ADR adoption remains low overall, and that roughly half of repositories that do adopt the practice contain only one to five ADRs total, a pattern the authors read as teams trying ADRs and then not sustaining them. The study also found that where ADRs do stick, it's a deliberate, sustained team effort over time, not a one-off habit.

That gap decisions get made, but the record-keeping doesn't survive contact with real engineering velocity is exactly what Hekmo targets. The reasoning already exists in the thread. Hekmo exists to lower the cost of turning it into a document, so that writing the ADR is a five-minute command instead of a task that quietly falls off everyone's list after the first few tries.

----

### Best Practices and Architecture

#### Garbage in, garbage out

`hekmo` extracts and structures what's actually written in a thread — it doesn't infer intent that isn't there. The quality of the ADR is a direct function of the quality of the discussion:

- Threads with a clear proposal, real pushback, and a stated resolution produce strong ADRs.
- Threads that are mostly status updates, "+1"s, or tangents give the model little to work with — the output will be thin or generic.
- If you're planning to generate an ADR from an issue, state the final decision and reasoning explicitly in a closing comment, rather than leaving the conclusion implied.

#### Traceability by design

`hekmo`'s system prompt is built around one rule: every sentence in the generated ADR should be traceable back to something actually said in the thread. This is deliberate — it keeps output trustworthy rather than a plausible-sounding hallucination, at the cost of not papering over a genuinely thin discussion with invented rationale.

#### Model support

`hekmo` currently uses **DeepSeek V4 Pro** exclusively for ADR generation. Your `DEEPSEEK_API_KEY` must have access to this model — other DeepSeek models and other providers are not yet supported. As with any LLM-backed tool, `hekmo` is subject to the context window limits of the underlying model.

If you're adopting this on a team. The highest-leverage improvement isn't tuning prompts or switching models it's raising the quality of the input itself:

- Better threads produce more factually grounded ADRs with less hallucination.
- This compounds: better threads mean less manual cleanup on *every* ADR, not just one.
- Encourage contributors to write detailed, decision-oriented comments, and treat thread quality as part of the process, not an afterthought.

**The ADR is only ever as good as the conversation that produced it**

----

### License

Eclipse Public License - v 2.0
