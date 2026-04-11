# AniVault Harness Engineering Research

## Goal

Turn the long harness-engineering script into an internal AniVault reference that explains what harness engineering means in this repository, why it matters, and which parts are already present in our working setup.

## Working definition for AniVault

In AniVault, harness engineering means designing the environment around an AI coding agent so the agent is more likely to produce correct work and less likely to repeat avoidable mistakes.

This repository already treats harness engineering as an operating principle rather than a buzzword:

- `AGENTS.md` defines the high-level workflow, role handoff, and planning gate.
- `.cursor/rules/` stores persistent project rules that are reloaded in new sessions.
- `documents/` stores research, plan, and memo artifacts so work can survive session resets.
- Persona Dialogue splits briefing, implementation, testing, and verification responsibilities.
- Validation is structural, not optional: `pytest -> ruff check . -> mypy src -> black .`.

## Confirmed repository facts that map to harness engineering

### 1. Rule delivery already exists

The repository has a layered rule system instead of relying on one-off prompts:

- `AGENTS.md` sets project-wide operating gates.
- `.cursor/rules/anivault-root.mdc` defines self-check steps, domain vocabulary, and DO/DON'T rules.
- `.cursor/rules/anivault-cursor-usage.mdc` requires planning-first behavior and memo usage.
- `.cursor/rules/anivault-persona-dialogue.mdc` defines the mandatory three-step handoff before coding.

This directly addresses the "new session loses memory" problem by re-injecting stable project context every time a new session starts.

### 2. Planning and implementation are intentionally separated

The repository explicitly forbids jumping from request to implementation on substantial work:

- Research must be captured in `documents/`.
- A plan markdown document must be created before implementation.
- Human review and approval must happen before code changes begin.

This is a harness decision, not just a documentation habit. It reduces drift, hidden assumptions, and premature code edits.

### 3. Memory is externalized into files

AniVault does not assume the agent will remember prior mistakes:

- `documents/CURSOR_MEMO.md` is the long-lived place for repeat mistakes and follow-up notes.
- `documents/docs/*-research.md` and `*-plan.md` preserve decisions across sessions.

This is a direct mitigation for session handoff loss. The memory lives in the repo, not in the temporary chat context.

### 4. Evaluation is separated from generation

The project already uses role separation that mirrors generator/evaluator thinking:

- `[시몬]` coordinates and enforces gates.
- A domain/application/adapter/gui owner explains the implementation direction.
- `[테스]` is responsible for tests.
- `[렉스]` is responsible for the verification pipeline.

Even when handled in a single conversation, the process intentionally separates implementation from evaluation. This helps counter the common failure mode where the same agent writes code and then too quickly declares success.

### 5. Verification is expected to be concrete

AniVault requires explicit verification reporting:

- Run order is defined in `AGENTS.md`.
- If checks are not run, the report must state the skipped command, the reason, and the remaining risk.
- If `black .` changes files, that must be reported separately from "verification passed."

This reduces self-evaluation bias by forcing observable verification results instead of vague confidence statements.

### 6. Tool usage is constrained by policy

AniVault's MCP guidance is selective:

- Local files, CLI, and official docs are preferred when they are sufficient.
- MCP is only justified when it adds real repetition or accuracy benefits.
- Secrets must stay in environment variables, not JSON config.
- Dangerous writes such as production DB mutation or risky auto-deploy are explicitly discouraged.

This is harness engineering in the "shape the environment, not only the prompt" sense: the tool surface is intentionally narrowed.

## Translating the script's three failure patterns into AniVault risks

### Session handoff memory loss

Risk in AniVault:

- A new agent session may miss prior decisions, approved scope, or known pitfalls.

Current mitigation:

- `AGENTS.md`
- `.cursor/rules/`
- `documents/CURSOR_MEMO.md`
- paired research/plan documents in `documents/docs/`

Practical meaning:

- Stable project rules must live in files, not only in chat.

### Context overload and premature stopping

Risk in AniVault:

- Large changes can drift when too much context accumulates in a single session.
- An agent may stop after a plausible partial result without closing the real task.

Current mitigation:

- mandatory research and plan artifacts
- explicit scope framing before implementation
- short completion reports that name changed files and verification status

Practical meaning:

- Break work into document-backed chunks instead of treating the entire task as one long conversational thread.

### Self-evaluation trap

Risk in AniVault:

- The same agent can overrate unfinished or weak results if no separate evaluation step exists.

Current mitigation:

- `[테스]` and `[렉스]` verification flow
- required command reporting
- bias toward tests and structural validation over "looks good" summaries

Practical meaning:

- Success must be justified by checks, not by the author's own confidence.

## AniVault-specific harness principles confirmed by current docs

- Use structure to prevent mistakes: rules, tests, layered boundaries, and approval gates.
- Preserve context in repo artifacts so the next session starts from facts instead of guesses.
- Prefer policy-enforced behavior over polite reminders when the risk is high.
- Treat repeated AI mistakes as repository design problems, not only model problems.

## Gaps and non-goals

The source script mentions several harness tactics that are not fully implemented here today:

- hard technical permission enforcement beyond documented operating rules
- automatic hooks that force checks before every completion
- browser-style end-to-end tooling such as Playwright for GUI verification
- dedicated sub-agent evaluator workflows as a default practice

These should be treated as adoption candidates, not as current repository facts.

## Conclusion

AniVault already has a meaningful harness: persistent rules, planning gates, repo-backed memory, role separation, and an explicit verification pipeline. The main value of this research note is not to introduce a new concept, but to name the existing operating system clearly enough that future contributors can extend it deliberately.
