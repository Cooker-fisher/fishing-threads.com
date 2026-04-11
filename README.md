# fishing-threads.com

Tsuri-threads / fishing-threads.com is a connected database site for fishing tackle selection.

The project is designed around **relations and setups**, not just isolated product pages.

## Fixed direction
- Focus: connected DB for fishing gear selection
- Main value: relation / setup
- Initial scope: electric reels first
- Canonical source of truth: GitHub
- Data layers:
  - `raw`
  - `normalized`
  - `derived`
- Main UI idea:
  - horizontal axis = reel size / band
  - vertical axis = fish species, sinker load, and other conditions
- Main user flow:
  - fish / condition
  - required reel band
  - maker comparison
  - upper/lower model comparison
  - setup

## Current docs
- `docs/architecture.md`
- `docs/repo-structure.md`
- `docs/raw-extraction-design.md`

## Current repository policy
- Keep only what is already decided
- Do not add speculative code
- Raw JSON is the working source of truth
- HTML is saved only when needed
- Heavy generated assets should not live in the repo
