from __future__ import annotations

import json
import sys
from pathlib import Path


def load_inventory(path: Path) -> dict[str, list[str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_inventory(inventory: dict[str, list[str]]) -> list[str]:
    paths: list[str] = []
    for group in ("docs", "scripts", "tests"):
        paths.extend(inventory.get(group, []))
    return paths


def check_paths(repo_root: Path, paths: list[str]) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    missing: list[str] = []
    for rel in paths:
        path = repo_root / rel
        if path.exists():
            existing.append(rel)
        else:
            missing.append(rel)
    return existing, missing


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    inventory_path = repo_root / "docs" / "repo-inventory.json"
    if not inventory_path.exists():
        print(f"ERROR: inventory file not found: {inventory_path}")
        return 1

    inventory = load_inventory(inventory_path)
    paths = flatten_inventory(inventory)
    existing, missing = check_paths(repo_root, paths)

    print(f"Checked {len(paths)} inventory entries.")
    print(f"Existing: {len(existing)}")
    print(f"Missing: {len(missing)}")

    if missing:
        print("\nMissing files:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    print("\nInventory check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
