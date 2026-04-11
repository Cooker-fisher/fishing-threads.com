from __future__ import annotations

import argparse
from pathlib import Path

from scripts.extractors.daiwa_electric_pipeline import run_pipeline


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DAIWA電動リール 10件 dry-run")
    parser.add_argument(
        "--index-json",
        default="samples/daiwa-electric-first10-raw-index-clean.json",
        help="一覧 raw seed JSON のパス",
    )
    parser.add_argument(
        "--crawl-date",
        default="2026-04-11",
        help="取得日。形式: YYYY-MM-DD",
    )
    parser.add_argument(
        "--out-dir",
        default=".",
        help="出力先ディレクトリ",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    outputs = run_pipeline(
        index_json_path=Path(args.index_json),
        crawl_date=args.crawl_date,
        out_dir=Path(args.out_dir),
    )
    print(f"generated={len(outputs)}")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
