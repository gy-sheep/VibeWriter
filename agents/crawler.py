import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from config import (
    CRAWL_DELAY,
    CRAWL_RETRY,
    CRAWL_TIMEOUT,
    CRAWL_USER_AGENT,
    RAW_HTML_DIR,
)


def _resolve_naver_url(url: str, html: str) -> str:
    """네이버 블로그 URL인 경우 iframe 내부 실제 콘텐츠 URL로 변환한다."""
    parsed = urlparse(url)
    if "blog.naver.com" not in parsed.netloc:
        return url

    soup = BeautifulSoup(html, "html.parser")
    iframe = soup.find("iframe", src=True)
    if iframe:
        src = iframe["src"]
        if src.startswith("/"):
            src = f"{parsed.scheme}://{parsed.netloc}{src}"
        return src
    return url


def _url_to_slug(url: str) -> str:
    """URL을 파일명으로 사용 가능한 slug로 변환한다."""
    parsed = urlparse(url)
    slug = (parsed.netloc + parsed.path).strip("/").replace("/", "-").replace(".", "-")
    return slug or "unknown"


def _is_allowed_by_robots(url: str, user_agent: str) -> bool:
    """robots.txt 규칙에 따라 해당 URL 크롤링 허용 여부를 반환한다."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True  # robots.txt 읽기 실패 시 허용으로 간주


def crawl(url: str) -> Path | None:
    """
    URL을 크롤링해 raw_html 디렉터리에 저장하고 저장 경로를 반환한다.
    실패 시 CRAWL_RETRY 횟수만큼 재시도하며, 최종 실패 시 None을 반환한다.
    """
    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)

    if not _is_allowed_by_robots(url, CRAWL_USER_AGENT):
        print(f"  [skip] robots.txt 차단: {url}")
        return None

    headers = {"User-Agent": CRAWL_USER_AGENT}
    attempts = 0

    while attempts <= CRAWL_RETRY:
        try:
            response = httpx.get(url, headers=headers, timeout=CRAWL_TIMEOUT, follow_redirects=True)
            response.raise_for_status()

            # 네이버 블로그: iframe 내부 URL로 재요청
            actual_url = _resolve_naver_url(url, response.text)
            if actual_url != url:
                response = httpx.get(actual_url, headers=headers, timeout=CRAWL_TIMEOUT, follow_redirects=True)
                response.raise_for_status()

            slug = _url_to_slug(url)
            output_path = RAW_HTML_DIR / f"{slug}.html"
            output_path.write_text(response.text, encoding="utf-8")

            time.sleep(CRAWL_DELAY)
            return output_path

        except Exception as e:
            attempts += 1
            if attempts <= CRAWL_RETRY:
                print(f"  [retry] {url} — {e}")
                time.sleep(CRAWL_DELAY)
            else:
                print(f"  [fail] {url} — {e}")
                return None
