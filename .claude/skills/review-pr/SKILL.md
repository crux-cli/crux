---
name: review-pr
description: "Review open PRs: CI gate, code review, security review, docs review. Approve or request changes."
args: "[PR#] — optional PR number or URL. If omitted, reviews all open PRs."
---

# PR Review

Review pull requests with a rigorous multi-phase process: CI gate, code review, security audit, and documentation check. Post findings as PR comments, then approve or request changes.

## Invocation

```
/review-pr          # Review all open PRs
/review-pr 42       # Review PR #42 only
```

## Step 0: Resolve Target PRs

If a PR number is provided, use it. Otherwise, list all open PRs:

```bash
gh pr list --state open --json number,title,headRefName --limit 50
```

Run the full review process (Steps 1–5) for each PR sequentially.

## Step 1: CI Gate (Hard Gate)

Check whether all CI checks have passed:

```bash
gh pr checks <PR#>
```

- **All checks pass**: proceed to Step 2.
- **Any check failing**: post a comment and request changes immediately. Do NOT proceed with code review.

Comment on failure:
```
**[CRITICAL]** CI Pipeline

CI checks are failing. Skipping code review until all checks pass.

Failing checks:
- <list each failing check and its status>

Please fix CI failures and push again.
```

Skip to the next PR (if reviewing multiple).

## Step 2: Code Review

Read the full PR diff:

```bash
gh pr diff <PR#>
```

Also read the PR description and any linked issues for context:

```bash
gh pr view <PR#> --json title,body,labels,files
```

### 2.0: Check Linked Issue

If the PR body contains `Closes #<number>` or `Fixes #<number>`, fetch the linked issue:

```bash
gh issue view <ISSUE#> --json number,title,body,labels
```

Use the issue description to:

- **Verify the fix matches the reported problem** — does the PR actually address what the issue describes?
- **Check repro steps are covered** — if the issue includes repro steps, are they addressed by the changes or covered by tests?
- **Validate scope** — does the PR stay within the scope of what the issue requested, or does it include unrelated changes?

If the PR claims to close an issue but the changes don't address it, flag this as a **WARNING** finding.

### 2a. Logic & Correctness

Review every changed file for:

- **Logical errors**: off-by-one, wrong conditionals, missing edge cases, race conditions
- **Error handling**: uncaught exceptions, swallowed errors, missing validation at system boundaries
- **State management**: uninitialized variables, stale state, mutation side effects
- **API contracts**: breaking changes to public interfaces, missing backwards compatibility where needed
- **Resource management**: unclosed files/connections, missing cleanup

### 2b. Test Quality

Review all test changes for:

- **Shortcut detection**: tests that are written to pass rather than to verify behavior — e.g., testing implementation details, asserting on mocks instead of outcomes, trivially true assertions
- **Coverage gaps**: new code paths without corresponding tests, missing edge case tests
- **Test isolation**: tests depending on execution order, shared mutable state, flaky patterns
- **Assertion quality**: meaningful assertions vs. trivially true checks, proper error message checks, boundary value testing

### 2c. Code Style (per CONTRIBUTING.md)

- Python 3.11+ modern syntax (`list[str]`, `str | None`)
- Type annotations on public functions
- Line length: 120 characters
- Atomic file writes (temp file + rename) for JSON/TOML saves
- Ruff rules compliance: E/F/W, I, UP, B, SIM, S

## Step 3: Security Review

Examine the diff for security issues. This is a thorough review — check every changed line.

### 3a. Secrets & Credentials

- API keys, tokens, passwords, private keys in code or config
- Hardcoded connection strings with credentials
- `.env` files or secrets committed to the repo
- Hardcoded URLs with embedded auth tokens

### 3b. Injection Vulnerabilities

- **Command injection**: unsanitized input passed to subprocess calls or shell execution
- **SQL injection**: string concatenation in queries instead of parameterized queries
- **Path traversal**: user input used in file paths without sanitization
- **XSS**: unescaped user input rendered in HTML/templates
- **Template injection**: user input in format strings or template engines

### 3c. Dependency Security

- New dependencies added — check if they are well-maintained and trustworthy
- Pinned versions vs. unpinned (prefer pinned)
- Known vulnerabilities in added packages

### 3d. Unsafe Operations

- File operations without proper error handling or atomic writes
- Unsafe deserialization (e.g., loading untrusted serialized objects)
- Use of eval/exec with untrusted data
- Weak cryptographic algorithms (MD5, SHA1 for security purposes)
- Hardcoded salts, IVs, or crypto keys

### 3e. Auth & Permissions

- Missing authentication checks on new endpoints/commands
- Privilege escalation paths
- Overly permissive file permissions
- CORS misconfigurations

## Step 4: Documentation Review

Check that all documentation is consistent with the PR changes.

### 4a. README.md

- If new features or commands were added, is README updated?
- If existing features changed, does README reflect the change?
- Are usage examples accurate?

### 4b. docs/ Pages

- For new CLI commands: is there a corresponding `docs/cli/<command>.md`?
- For API changes: is the relevant `docs/api/*.md` page updated?
- For new guides or concepts: are they added to `docs/guides/` or `docs/getting-started/`?
- Do navigation references (mkdocs.yml or index pages) include new pages?

### 4c. CHANGELOG.md

- Is there a changelog entry for user-facing changes?
- Does the entry accurately describe what changed?

### 4d. CLI Help Text

- If commands were added or modified, does the command's help text match the docs?
- Is the skill file (`src/crux_cli/data/skills/crux/SKILL.md`) updated if commands changed?

## Step 5: Verdict

Collect all findings from Steps 2–4. Classify each finding by severity:

| Severity | Meaning | Blocks merge? |
|----------|---------|---------------|
| **CRITICAL** | Security vulnerability, data loss risk, broken logic | Yes |
| **WARNING** | Code smell, missing tests, incomplete docs | No |
| **NIT** | Style, naming, minor suggestion | No |

### 5a. Post Review

Submit a single PR review via `gh pr review` that includes:

1. **Inline comments** on specific lines for each finding (use `gh api` to post review comments on specific files/lines)
2. **Summary comment** with a findings table:

```markdown
## PR Review Summary

| # | Severity | Category | Finding |
|---|----------|----------|---------|
| 1 | CRITICAL | Security | API key hardcoded in config.py:42 |
| 2 | WARNING  | Tests    | No test for error path in sync.py:89 |
| 3 | NIT      | Style    | Unused import in utils.py:3 |

**Verdict**: <APPROVE / REQUEST CHANGES>
```

### 5b. Decision

```bash
# If ANY critical finding exists:
gh pr review <PR#> --request-changes --body "<summary>"

# If only warnings/nits (no criticals):
gh pr review <PR#> --comment --body "<summary>"

# If clean (no findings at all):
gh pr review <PR#> --approve --body "All checks pass. Code, security, and docs look good."
```

## Notes

- This skill requires `gh` CLI authenticated with repo access
- For large PRs (>1000 lines), focus on the most critical files first
- When reviewing multiple PRs, post results for each before moving to the next
- If a PR has already been reviewed and no new commits were pushed, skip it
