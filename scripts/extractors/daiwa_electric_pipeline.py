from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.extractors.daiwa_electric_detail import run as run_detail


@dataclass
class PipelineResult:
    outputs: list[Path]
    failed_urls: list[str]
    failed_reasons: dict[str, str]


def _read_urls(index_json_path: Path) -> list[str]:
    payload = json.loads(index_json_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        urls = []
        for item in payload:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict):
                url = item.get("url") or item.get("source_url")
                if url:
                    urls.append(url)
        return urls
    return []


def run_pipeline(index_json_path: Path, crawl_date: str, out_dir: Path) -> PipelineResult:
    urls = _read_urls(index_json_path)
    outputs: list[Path] = []
    failed: list[str] = []
    failed_reasons: dict[str, str] = {}
    for url in urls:
        try:
            outputs.append(run_detail(url=url, crawl_date=crawl_date, out_dir=out_dir))
        except Exception as exc:
            failed.append(url)
            failed_reasons[url] = str(exc)
    return PipelineResult(outputs=outputs, failed_urls=failed, failed_reasons=failed_reasons)
