# Repository Structure

This repository stores only what has already been decided.
It is intentionally minimal.

## Layout
```text
repo/
├─ app/
├─ schema/
├─ prompts/
├─ scripts/
├─ raw/
│  ├─ index/
│  ├─ products/
│  └─ images/
├─ normalized/
├─ derived/
├─ tmp/          # gitignored
├─ logs/         # gitignored
└─ samples/
   └─ html/      # representative samples only
```

## Rules
- `raw` = working source of truth
- `normalized` = regenerable
- `derived` = regenerable
- `tmp` and `logs` are not committed
- `samples/html` is only for representative HTML samples
- full HTML archive is not part of normal operation
- product images do not live in the repo

## Raw units
### Index pages
Save as **1 page = 1 JSON**

Example:
`raw/index/shimano/electric/001.json`

### Product pages
Save as **1 product = 1 JSON**

Example:
`raw/products/shimano/force-master-200.json`
