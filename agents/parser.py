import json
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

from config import PARSED_POSTS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# 노이즈 제거 대상 태그
_NOISE_TAGS = [
    "script", "style", "nav", "header", "footer",
    "aside", "form", "iframe", "noscript", "ads",
]

# 본문 영역 후보 선택자 (우선순위 순)
_CONTENT_SELECTORS = [
    ".se-main-container",   # 네이버 블로그 스마트에디터
    "#postViewArea",        # 네이버 블로그 구버전
    ".post-content",        # 네이버 블로그 구버전2
    "article",
    "main",
    '[class*="content"]',
    '[class*="post"]',
    '[class*="entry"]',
    '[id*="content"]',
    '[id*="post"]',
    "body",
]


def _extract_title(soup: BeautifulSoup) -> str:
    # 네이버 블로그 스마트에디터 제목
    naver_title = soup.select_one(".se-title-text")
    if naver_title:
        return naver_title.get_text(strip=True)

    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    # <title> 태그 — " : 네이버 블로그" 등 사이트명 접미사 제거
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True).split(" : ")[0].split(" | ")[0].strip()

    return ""


def _extract_content(soup: BeautifulSoup) -> str:
    for selector in _CONTENT_SELECTORS:
        element = soup.select_one(selector)
        if element:
            for noise in element.find_all(_NOISE_TAGS):
                noise.decompose()
            text = element.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text
    return ""


def parse(url: str, html_path: Path) -> Path | None:
    """
    HTML 파일에서 본문을 추출해 parsed_posts 디렉터리에 JSON으로 저장한다.
    본문 추출 실패(200자 미만) 시 None을 반환한다.
    """
    PARSED_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        html = html_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("HTML 파일 읽기 실패: path=%s, %s", html_path, e)
        print(f"  [fail] HTML 파일 읽기 실패: {html_path.name}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    content = _extract_content(soup)

    if not content:
        logger.warning("본문 추출 실패 (200자 미만): url=%s", url)
        print(f"  [skip] 본문 추출 실패: {url}")
        return None

    result = {
        "url": url,
        "title": title,
        "content": content,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }

    output_path = PARSED_POSTS_DIR / html_path.with_suffix(".json").name

    try:
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.error("파싱 결과 저장 실패: path=%s, %s", output_path, e)
        print(f"  [fail] 파싱 결과 저장 실패: {output_path.name}")
        return None

    return output_path
