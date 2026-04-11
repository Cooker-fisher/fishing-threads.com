# Pull Request Rules

This project uses pull requests as the default update method.
Direct pushes to `main` are avoided.

## Why
- changes stay visible
- fixed decisions and speculative work are easier to separate
- rollback is easier
- architecture drift is easier to catch

## Core rules
- do not push directly to `main`
- use one topic per PR
- do not mix architecture, raw schema, UI, and crawler logic in one PR
- keep PRs reviewable
- include only already-decided items unless the PR is explicitly a proposal

## Allowed PR types
Each PR should mainly belong to one type:
- architecture
- schema
- raw extraction
- normalization
- derived logic
- UI
- content/docs
- operations

## Suggested PR size
Prefer small PRs.
Examples:
- one design doc
- one schema update
- one extractor for one page type
- one normalization change

Avoid giant mixed PRs.

## PR title style
Use direct titles such as:
- `Add raw extraction design doc`
- `Add reel raw examples`
- `Define normalized reel schema v1`
- `Implement Shimano electric index extractor`

## PR body should state
- what is included
- what is intentionally excluded
- whether the PR contains only fixed decisions or includes proposals
- impact on raw / normalized / derived if relevant

## Review rule
Before merge, confirm:
- does this align with relation / setup-first architecture?
- does this preserve raw -> normalized -> derived separation?
- does this introduce unnecessary heavy assets into the repo?
- does this mix too many concerns?

## Merge rule
Merge only when:
- scope is clear
- naming is consistent
- no speculative code was slipped in as if finalized
- repo remains lightweight

## Main branch policy
`main` should reflect the latest reviewed state, not draft thinking.
