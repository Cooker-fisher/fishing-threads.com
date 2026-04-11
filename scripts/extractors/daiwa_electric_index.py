from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen


WS_PATTERN = re.compile(r"\s+")


def normalize_ws(text: str) -> str:
    return WS_PATTERN.sub(" ", text or "").strip()


@dataclass
class FetchedHTML:
    url: str
    html: str
    status_code: int


def fetch_html(url: str, timeout: int = 20) -> FetchedHTML:
    parsed = urlparse(url)
    if parsed.scheme in {"", "file"}:
        local_path = Path(parsed.path if parsed.scheme == "file" else url)
        html = local_path.read_text(encoding="utf-8")
        return FetchedHTML(url=str(local_path), html=html, status_code=200)

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        return FetchedHTML(url=url, html=html, status_code=getattr(resp, "status", 200))
