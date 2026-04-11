# Codex Collaboration Rules

This document defines how Codex should be used with this project.

## Position of Codex in this project
Codex is a coding worker, not the product architect.

That means:
- architecture is fixed by docs first
- Codex implements within those rules
- Codex should not silently redefine schema, naming, or project direction

## Why Codex is useful here
OpenAI positions Codex as a coding agent that can work in the cloud and in local tools such as the terminal, IDE, and Codex app, handling tasks like editing files, running commands, and executing tests. It is suited for scoped implementation work, not for replacing project governance. citeturn622702search0turn622702search5

## What Codex should do
Good Codex tasks:
- create or update docs from fixed decisions
- scaffold directory structures
- implement one extractor for one page type
- add tests
- refactor localized code
- generate sample JSON from an agreed schema
- fix contained bugs

## What Codex should not decide alone
- core product direction
- raw / normalized / derived boundaries
- naming system changes
- relation / setup architecture changes
- whether to broaden scope to new tackle categories
- storage policy changes
- repo policy changes

These must be decided in docs first.

## Operating mode
Use Codex in two modes.

### 1. Ask mode
Use when:
- understanding an unfamiliar part of the repo
- checking impact before coding
- reviewing alternatives

### 2. Code mode
Use when:
- the task is already scoped
- target files are known
- acceptance criteria are clear

## Required input to Codex
Every non-trivial task should include:
- goal
- target files
- what must not change
- acceptance criteria
- whether this is docs-only, extractor-only, schema-only, or UI-only

## Task granularity rule
Do not give Codex broad prompts such as:
- `build the site`
- `design the database`
- `make everything consistent`

Instead use narrow tasks such as:
- `implement Shimano electric reel index extractor into scripts/...`
- `add raw JSON example files under docs/raw-examples/`
- `update repo-structure doc to match current folders`

## PR rule for Codex work
Codex-generated work should land by pull request.
One Codex task should ideally map to one PR.

## Review rule for Codex output
Before merging Codex work, check:
- did it follow the documented architecture?
- did it modify only the intended layer?
- did it accidentally normalize raw too early?
- did it introduce heavy assets or noisy files?
- did it rename things without approval?

## Preferred early use in this project
Early Codex usage should focus on:
- docs updates
- raw examples
- extractor scaffolding
- selector-based extraction
- schema validation helpers

Do not start with broad autonomous product-building tasks.

## Summary
Codex should accelerate implementation after decisions are fixed.
It should not be allowed to become the source of truth for project structure.
