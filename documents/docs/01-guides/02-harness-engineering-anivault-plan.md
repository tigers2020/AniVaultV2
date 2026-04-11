# AniVault Harness Engineering Plan

## Summary

Document AniVault's harness engineering model as a practical operating guide for the team and future agents. This v1 stays at the documentation layer only: it explains what is already in place, what should be strengthened next, and what remains optional for later adoption.

## Current harness to keep using

- Use `AGENTS.md` as the top-level operating contract for workflow, role handoff, validation order, and reporting.
- Use `.cursor/rules/` as the persistent rule layer that re-establishes project context in new sessions.
- Keep the mandatory work sequence:
  - `research`
  - `plan`
  - human approval
  - implementation
- Keep storing substantial work artifacts in `documents/` or `documents/docs/` so decisions survive session resets.
- Keep Persona Dialogue as the default collaboration frame:
  - `[시몬]` summarizes and assigns
  - owner briefs approach
  - only then implementation begins
- Keep `[테스]` and `[렉스]` as the explicit evaluation path after implementation.

## Harness areas to strengthen next

### Rule delivery

- Continue moving repeated project corrections into `AGENTS.md`, `.cursor/rules/`, or both.
- Prefer repository-stored instructions over chat-only explanations whenever the mistake is likely to recur.

### Memory and handoff

- Update `documents/docs/CURSOR_MEMO.md` when a repeated mistake, project decision, or follow-up rule is discovered.
- Keep using paired `*-research.md` and `*-plan.md` files for non-trivial work so future sessions can reconstruct context quickly.

### Verification discipline

- Continue reporting verification in concrete terms:
  - commands run
  - commands not run
  - reasons
  - remaining risks
- Treat "I think it is done" as insufficient unless supported by checks or an explicit reason why checks were skipped.

### Scope control

- Split larger efforts into smaller approved plans instead of carrying too much state in one long conversation.
- Prefer document-backed checkpoints over implicit conversational continuity.

## Adoption candidates, not current requirements

- Add stronger technical enforcement for dangerous operations where policy text alone is too weak.
- Evaluate whether lightweight hooks would help enforce verification without creating noisy false positives.
- Consider GUI-focused verification tooling only when manual Qt verification becomes a repeated bottleneck.
- Consider generator/evaluator split with sub-agents only for work that is large enough to justify the extra coordination cost.

These are deliberately not mandatory in v1 because the repository already has a solid baseline harness and should avoid adding ceremony without evidence.

## MCP and tool usage policy

- Keep MCP usage optional.
- Prefer local files, CLI inspection, and official documentation when they are enough.
- Use MCP only when it materially improves accuracy or repeated workflows.
- Keep secrets in environment variables only.
- Do not hand risky production writes or dangerous deploy flows to MCP-based automation.

## Team checklist for future work

- Before coding, confirm the task has a research note and a plan note if it is non-trivial.
- Before implementation, confirm human approval exists for the plan.
- During implementation, keep changes within the intended layer boundary.
- After implementation, run or report verification in the required order.
- After any repeated mistake, update the durable instruction layer instead of relying on memory.

## Assumptions and defaults

- This plan documents process only; it does not change code APIs or runtime behavior.
- The repository's current harness is considered a baseline to preserve, not a blank slate.
- Additional enforcement such as hooks, permissions, or richer evaluator tooling should be introduced only after concrete pain is observed.
