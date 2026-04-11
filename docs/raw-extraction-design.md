# Raw Extraction Design

## Purpose
Tsuri-threads is a connected database site for fishing gear selection.
The main value is not standalone entity pages, but relation / setup.
This document fixes the raw extraction design for reel data so the project can scale without becoming messy.

## Core Product Direction
- Tsuri-threads is a connected DB site for tackle selection.
- Main focus is relation / setup, not just entity pages.
- Initial scope is electric reels first.
- Canonical source of truth is GitHub.
- Data layers are:
  - `raw`
  - `normalized`
  - `derived`
- Main UI direction:
  - horizontal axis = reel size / band
  - vertical axis = fish species, sinker load, and other conditions
- User flow:
  - fish / condition
  - required reel band
  - maker comparison
  - upper/lower model comparison
  - setup

## Raw Extraction Policy
### Source of truth
- `raw JSON` is the working source of truth.
- HTML is **not** saved by default.
- Save HTML only when:
  - extraction fails
  - structure changed
  - representative samples are needed

### Why
- Raw JSON is lighter and easier to diff.
- HTML-only operation is possible but too slow in practice.
- Full HTML storage for all pages is unnecessary.

## Extraction Strategy
### Deterministic first
Use CSS / DOM extraction for factual fields.
Use LLM only for interpretation fields.

### CSS / DOM extraction handles
- title
- price
- product code / sku
- JAN / UPC
- spec table rows
- notes
- image URLs
- detail page URLs from index pages

### LLM handles only interpretation
- `category_mechanism`
- `category_usage`
- `water_type`
- feature section meaning
- technology labels when needed
- repair of broken / irregular spec structure only when necessary

### Rule
Facts by CSS. Interpretation by LLM.
Do not send entire page bodies to LLM by default.

## Page Unit Separation
### Index raw
Save as **1 page = 1 JSON**.

Path example:
`raw/index/shimano/electric/001.json`

Role:
- collect candidates broadly
- do not over-interpret

Typical fields:
- maker
- category_raw
- series_name_or_model_name
- price_raw
- source_url
- image_url
- badge_raw
- status_raw

### Product raw
Save as **1 product = 1 JSON**.

Path example:
`raw/products/shimano/force-master-200.json`

Role:
- store deep factual product data
- become the base for normalization

## Shared Reel Raw Schema
Raw schema should be built as:
- common core
- subtype core
- extra
- ignore

This must be shared across Shimano / Daiwa / Abu first.
Major Craft / Megabass are later durability tests, not initial schema drivers.

### Common core
- `maker`
- `brand`
- `source_site`
- `source_url`
- `crawl_date`
- `category_raw`
- `category_mechanism`
- `category_usage`
- `water_type`
- `series_name`
- `model_name`
- `variant_name`
- `price_raw`
- `sku_raw`
- `jan_upc_raw`
- `status_raw`
- `description_raw`
- `spec_rows_raw`
- `notes_raw`
- `image_urls`

### Subtype core
Keep subtype raw blocks for reel-specific data.
Examples:
- `electric_raw`
- `spinning_raw`
- `bait_raw`
- `conventional_raw`
- `lever_brake_raw`
- `fly_raw`

### Extra
Useful but non-critical:
- `technology_labels`
- `movie_links`
- `manual_links`
- `compatibility_links`
- `awards`
- `campaign_tags`
- `feature_section_titles`
- `hero_copy`

### Ignore
Do not store:
- breadcrumbs
- news
- SNS blocks
- related articles
- promo banners
- corporate navigation
- store navigation
- list ordering itself

## Spec Storage Rule
Do **not** normalize spec tables too early.
Store spec rows as raw rows first.

Recommended raw shape:

```json
[
  {
    "section": "basic spec",
    "label": "Gear ratio",
    "value": "5.1",
    "unit": null,
    "note": null,
    "source_text": "Gear ratio 5.1"
  }
]
```

Key rule:
- preserve original labels and values first
- normalize later

## Category Design
Keep category in 3 axes.

### 1. Raw category
Keep site-native labels as-is.
- `category_raw`

### 2. Mechanism
Unified mechanism axis:
- `electric`
- `spinning`
- `bait`
- `conventional`
- `lever_brake`
- `fly`
- `unknown`

### 3. Usage
Usage tags such as:
- boat
- offshore
- shore
- surf
- bass
- trout
- wakasagi
- rockfish

### 4. Water type
- `salt`
- `fresh`
- `both`
- `unknown`

## File Naming Rule
### Index raw
`raw/index/{maker}/{category_mechanism}/{page_no}.json`

Example:
`raw/index/shimano/electric/001.json`

### Product raw
`raw/products/{maker}/{product_slug}.json`

Example:
`raw/products/shimano/force-master-200.json`

### Product slug rules
- lowercase only
- use `-` only as separator
- include reel size / hand / HG / PG / XG differences
- do not use series name alone
- append source-based fallback ID if needed

## Required Meta Fields
Every product JSON should include at least:
- `id`
- `maker`
- `brand`
- `source_site`
- `source_url`
- `source_hash`
- `crawl_date`
- `extractor_version`
- `schema_version`

Important:
- `source_hash` separates page changes from extractor changes
- `extractor_version` lets us track extraction logic updates

## Diff Detection Rule
Detect changes at product page level.

Compare at least:
- `source_hash`
- core fields
- `spec_rows_raw`
- `price_raw`
- `status_raw`

### Change levels
#### High
- `status_raw` changed
- `sku_raw` / `jan_upc_raw` changed
- `spec_rows_raw` row add/remove/value changed
- `category_mechanism` changed
- setup-critical capacity / drag / line data changed

#### Medium
- `price_raw` changed
- major `description_raw` change
- image replacement
- feature heading change

#### Low
- note wording tweaks
- ordering changes
- wording normalization
- promo copy changes

### Diff storage example
`diff/{maker}/{product_slug}/{date}.json`

## Images Policy
### Default
- do not store product images inside the repo
- store image metadata only
- keep source image URLs first

### Why
GitHub capacity problems are caused more by:
- images
- full HTML archives
- repeated CSV output commits
- binaries
than by raw JSON itself.

### Current phase
- keep `source_image_url`
- later, if needed, add lightweight `thumb` and `detail` assets outside repo
- do not introduce paid storage by default

## Repo Layout v1
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

Rules:
- `raw` = operational source of truth
- `normalized` = regenerable
- `derived` = regenerable
- `tmp` and `logs` are ignored
- sample HTML only, not full archive

## Operational Choice Fixed
Adopt **A-lightweight operation**.

Meaning:
- raw JSON saved by default
- HTML only when needed
- deterministic extraction first
- GitHub stores code / schema / raw JSON / minimal normalized data
- heavy generated assets are ignored

## Immediate Next Step
Create:
1. list-page raw JSON sample
2. product-page raw JSON sample
3. extractor prompt split into:
   - index page extraction
   - detail page extraction
4. first extractor implementation for Shimano electric reel pages
