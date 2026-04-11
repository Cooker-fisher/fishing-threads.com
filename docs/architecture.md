# Architecture

## What Tsuri-threads is
Tsuri-threads is a connected database site for fishing gear selection.

The main value is not product pages by themselves.
The main value is the ability to move through **relations** and finally reach a **setup**.

## Product principle
- Main actor is not just `entity`
- Main actor is `relation / setup`
- Early focus is electric reels first
- Expansion should stay schema-safe

## Data layers
The project is designed in 3 layers:
- `raw`
- `normalized`
- `derived`

### raw
Keep source facts as close to the original as possible.
Do not normalize too early.

### normalized
Convert raw facts into shared comparable structure.

### derived
Build relation views, setup candidates, and user-facing derived outputs.

## Canonical source of truth
GitHub is the canonical source of truth.

## UI core
Main UI concept:
- horizontal axis = reel size / band
- vertical axis = fish species, sinker load, and other conditions

This is condition-first navigation.

## Main flow
- fish / condition
- required reel band
- maker comparison
- upper/lower model comparison
- setup

## Design constraint
The system must stay maintainable when expanding later to more reel types and eventually more tackle categories.

That means:
- separate raw / normalized / derived
- separate list-page data and product-page data
- keep shared schema before maker-specific logic
- do not let UI decisions pollute raw design
