"""
crawl_spec_labels.py — スペックラベル収集クローラー

製品ページを巡回してスペック表のラベル名一覧を収集する。
LLM / AI 不使用。urllib + html.parser のみ。

403 など取得不可のページは即座にスキップ（リトライしない）。
リクエスト間には --delay 秒のスリープを挟み、サーバーに負荷をかけない。

使い方:
    # バックグラウンド実行
    python -m scripts.crawl_spec_labels \
        --urls samples/crawl-urls.json \
        --delay 3 \
        --out-dir docs &

    # フォアグラウンドで小規模テスト
    python -m scripts.crawl_spec_labels \
        --urls samples/crawl-urls.json \
        --max-pages 5

出力:
    <out-dir>/spec-label-inventory.json  ← 収集結果（URL × ラベル一覧）
    raw_html/<slug>.html                 ← 取得済み HTML の保存
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_TIMEOUT = 20  # seconds
_MAX_RETRIES = 2
_RETRY_BACKOFF = [2, 4]  # seconds; same length as _MAX_RETRIES


class FetchResult:
    __slots__ = ("url", "html", "status", "error")

    def __init__(
        self,
        url: str,
        html: str | None = None,
        status: int = 0,
        error: str | None = None,
    ):
        self.url = url
        self.html = html
        self.status = status
        self.error = error

    @property
    def ok(self) -> bool:
        return self.html is not None


def fetch(url: str) -> FetchResult:
    """
    単一 URL の取得。
    - 403 / 404 など HTTP エラー → 即リターン（リトライしない）
    - ネットワークエラー → _MAX_RETRIES 回まで指数バックオフでリトライ
    - ローカルファイルパス → ファイル読み込み
    """
    parsed = urlparse(url)
    if parsed.scheme in ("", "file"):
        path = Path(parsed.path if parsed.scheme == "file" else url)
        try:
            return FetchResult(url=url, html=path.read_text(encoding="utf-8"), status=200)
        except OSError as e:
            return FetchResult(url=url, error=str(e), status=0)

    req = Request(url, headers=_HEADERS)

    for attempt in range(_MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=_TIMEOUT) as resp:
                raw = resp.read()
                html = raw.decode("utf-8", errors="replace")
                return FetchResult(url=url, html=html, status=resp.status)
        except HTTPError as e:
            # HTTP エラー（403, 404 等）はリトライしない
            return FetchResult(url=url, error=f"HTTP {e.code}", status=e.code)
        except URLError as e:
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF[attempt])
                continue
            return FetchResult(url=url, error=str(e.reason), status=0)
        except Exception as e:  # noqa: BLE001
            return FetchResult(url=url, error=str(e), status=0)

    return FetchResult(url=url, error="max retries exceeded", status=0)


# ---------------------------------------------------------------------------
# HTML spec-table label extractor
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")


def _nws(s: str) -> str:
    return _WS.sub(" ", s).strip()


class _TableParser(HTMLParser):
    """
    HTML を解析してスペック表のラベル候補を収集する。

    判定ルール:
      - <table> 内の <th> テキスト、または各 <tr> 最初の <td> テキストをラベル候補とする。
      - 空文字・数値のみ・50 文字超は除外。
      - <table> 内に「自重」「ギア比」「ドラグ」等のキーワードが 1 つ以上あれば
        スペックテーブルとみなして全ラベルを収集対象に含める。
    """

    _SPEC_KEYWORDS = frozenset([
        "自重", "ギア比", "ギヤ比", "ドラグ", "ベアリング",
        "糸巻", "巻糸", "ハンドル", "電源", "スプール",
    ])

    def __init__(self) -> None:
        super().__init__()
        self._tables: list[dict[str, Any]] = []  # {labels, is_spec}
        self._in_table = 0
        self._in_th = False
        self._in_td = False
        self._td_count_in_row = 0
        self._buf = ""

    # ---- tag handlers -------------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag = tag.lower()
        if tag == "table":
            self._in_table += 1
            if self._in_table == 1:
                self._tables.append({"raw_labels": [], "is_spec": False})
        elif tag == "tr":
            self._td_count_in_row = 0
        elif tag == "th" and self._in_table:
            self._in_th = True
            self._buf = ""
        elif tag == "td" and self._in_table:
            self._td_count_in_row += 1
            if self._td_count_in_row == 1:
                self._in_td = True
                self._buf = ""

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "table":
            self._in_table = max(0, self._in_table - 1)
        elif tag == "th" and self._in_th:
            self._flush(is_th=True)
            self._in_th = False
        elif tag == "td" and self._in_td:
            self._flush(is_th=False)
            self._in_td = False

    def handle_data(self, data: str) -> None:
        if self._in_th or self._in_td:
            self._buf += data

    # ---- helpers ------------------------------------------------------------

    def _flush(self, *, is_th: bool) -> None:
        text = _nws(self._buf)
        self._buf = ""
        if not text or len(text) > 50:
            return
        if not self._tables:
            return
        current = self._tables[-1]
        current["raw_labels"].append(text)
        # スペックテーブル判定
        for kw in self._SPEC_KEYWORDS:
            if kw in text:
                current["is_spec"] = True
                break

    def spec_labels(self) -> list[str]:
        """スペックテーブルと判定されたテーブルからラベルをまとめて返す"""
        labels: list[str] = []
        seen: set[str] = set()
        for tbl in self._tables:
            if not tbl["is_spec"]:
                continue
            for label in tbl["raw_labels"]:
                # 数値のみ・記号のみは除外
                if re.fullmatch(r"[\d\.\-/,\s]+", label):
                    continue
                if label not in seen:
                    seen.add(label)
                    labels.append(label)
        return labels


def extract_spec_labels(html: str) -> list[str]:
    """HTML 文字列からスペック表のラベル候補を抽出して返す"""
    parser = _TableParser()
    try:
        parser.feed(html)
    except Exception:  # noqa: BLE001
        pass
    return parser.spec_labels()


# ---------------------------------------------------------------------------
# Slug helper (for raw HTML filename)
# ---------------------------------------------------------------------------

def _url_slug(url: str) -> str:
    parsed = urlparse(url)
    path_part = (parsed.netloc + parsed.path).replace("/", "_").strip("_")
    path_part = re.sub(r"[^\w\-]", "_", path_part)
    path_part = re.sub(r"_+", "_", path_part).strip("_")
    if len(path_part) > 80:
        h = hashlib.md5(url.encode()).hexdigest()[:8]
        path_part = path_part[:72] + "_" + h
    return path_part or hashlib.md5(url.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Main crawl loop
# ---------------------------------------------------------------------------

def crawl(
    urls: list[str],
    out_dir: Path,
    raw_html_dir: Path,
    delay: float,
    max_pages: int | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    raw_html_dir.mkdir(parents=True, exist_ok=True)

    for i, url in enumerate(urls):
        if max_pages is not None and i >= max_pages:
            print(f"[crawl] --max-pages {max_pages} reached, stopping.")
            break

        print(f"[crawl] ({i + 1}/{len(urls)}) {url}")
        result = fetch(url)

        entry: dict[str, Any] = {"url": url, "status": result.status}

        if not result.ok:
            entry["error"] = result.error
            entry["labels"] = []
            print(f"  -> SKIP: {result.error}")
        else:
            # 生 HTML を保存
            slug = _url_slug(url)
            html_path = raw_html_dir / f"{slug}.html"
            html_path.write_text(result.html, encoding="utf-8")
            entry["raw_html_path"] = str(html_path)

            labels = extract_spec_labels(result.html)
            entry["labels"] = labels
            print(f"  -> OK ({len(result.html):,} bytes), labels: {labels}")

        results.append(entry)

        # 次リクエストまでスリープ（最終URLは不要）
        if i < len(urls) - 1:
            time.sleep(delay)

    # インベントリ保存
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = out_dir / "spec-label-inventory.json"
    inventory_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[crawl] inventory saved: {inventory_path}")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_urls(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        urls = []
        for item in data:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict):
                u = item.get("url") or item.get("source_url")
                if u:
                    urls.append(u)
        return urls
    raise ValueError(f"Expected JSON array in {path}")


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="電動リール製品ページからスペック表ラベルを収集するクローラー (LLM 不使用)"
    )
    p.add_argument(
        "--urls",
        required=True,
        metavar="SEED_JSON",
        help="URL リストを含む JSON ファイル（文字列配列、または {url:...} オブジェクト配列）",
    )
    p.add_argument(
        "--out-dir",
        default="docs",
        metavar="DIR",
        help="spec-label-inventory.json の出力先（デフォルト: docs）",
    )
    p.add_argument(
        "--raw-html-dir",
        default="raw_html",
        metavar="DIR",
        help="取得した HTML の保存先（デフォルト: raw_html）",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=3.0,
        metavar="SEC",
        help="リクエスト間のスリープ秒数（デフォルト: 3）",
    )
    p.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="取得上限ページ数（省略時: 無制限）",
    )
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    seed_path = Path(args.urls)
    urls = _load_urls(seed_path)
    print(f"[crawl] {len(urls)} URL(s) loaded from {seed_path}")

    crawl(
        urls=urls,
        out_dir=Path(args.out_dir),
        raw_html_dir=Path(args.raw_html_dir),
        delay=args.delay,
        max_pages=args.max_pages,
    )


if __name__ == "__main__":
    main()
