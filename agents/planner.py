import json
import re
from datetime import datetime, timezone
from pathlib import Path

from config import CATEGORIES, OUTPUT_DIR, STYLE_GUIDES_DIR
from utils.logger import get_logger
from utils.ollama_client import generate

logger = get_logger(__name__)

_KEYWORD_PROMPT = """\
다음 블로그 주제에서 SEO에 유리한 핵심 키워드 5개를 추출하세요.
키워드만 쉼표로 구분해 한 줄로 반환하세요. 다른 설명은 포함하지 마세요.

주제: {topic}"""

_CATEGORY_PROMPT = """\
다음 블로그 주제의 카테고리를 아래 허용 목록 중 하나로만 분류하세요.
허용 카테고리: {categories}

카테고리 이름만 반환하세요. 다른 텍스트는 포함하지 마세요.

주제: {topic}
키워드: {keywords}"""

_TITLE_PROMPT = """\
다음 블로그 주제와 키워드를 참고해 SEO에 유리하고 클릭을 유도하는 제목 3개를 만드세요.
{style_context}
제목만 줄바꿈으로 구분해 반환하세요. 번호·기호는 포함하지 마세요.

주제: {topic}
키워드: {keywords}"""

_OUTLINE_PROMPT = """\
다음 블로그 주제로 섹션별 목차(아웃라인)를 작성하세요.
{style_context}
아래 JSON 배열 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
섹션은 5~7개, 각 estimated_chars는 최소 250 이상이며 전체 합계는 1750자 이상이어야 합니다.

[
  {{"section": 1, "title": "...", "type": "opening", "description": "...", "estimated_chars": 300}},
  {{"section": 2, "title": "...", "type": "body", "description": "...", "estimated_chars": 400}},
  {{"section": 3, "title": "...", "type": "closing", "description": "...", "estimated_chars": 300}}
]

type 값은 반드시 "opening", "body", "closing" 중 하나여야 합니다.
첫 섹션은 "opening", 마지막 섹션은 "closing", 나머지는 "body"로 지정하세요.

주제: {topic}
키워드: {keywords}"""

_OUTLINE_FALLBACK = [
    {"section": 1, "title": "들어가며", "type": "opening", "description": "", "estimated_chars": 300},
    {"section": 2, "title": "본론 1", "type": "body", "description": "", "estimated_chars": 400},
    {"section": 3, "title": "본론 2", "type": "body", "description": "", "estimated_chars": 400},
    {"section": 4, "title": "본론 3", "type": "body", "description": "", "estimated_chars": 400},
    {"section": 5, "title": "마무리", "type": "closing", "description": "", "estimated_chars": 300},
]


def _extract_keywords(topic: str) -> list[str]:
    """주제에서 SEO 핵심 키워드 5개를 추출한다. 실패 시 [topic]을 반환한다."""
    prompt = _KEYWORD_PROMPT.format(topic=topic)
    try:
        response = generate(prompt)
        keywords = [k.strip() for k in response.strip().split(",") if k.strip()]
        if keywords:
            return keywords[:7]
    except Exception as e:
        logger.error("키워드 추출 실패: topic=%s, %s", topic, e)
    return [topic]


def _infer_category(topic: str, keywords: list[str]) -> str:
    """주제와 키워드로 카테고리를 추론한다. 허용 목록에 없으면 'etc'를 반환한다."""
    prompt = _CATEGORY_PROMPT.format(
        categories=", ".join(CATEGORIES),
        topic=topic,
        keywords=", ".join(keywords),
    )
    try:
        response = generate(prompt).strip().lower()
        # 완전 단어 매칭으로 허용 카테고리 탐색
        for cat in CATEGORIES:
            if re.search(rf"\b{cat}\b", response):
                return cat
    except Exception as e:
        logger.error("카테고리 추론 실패: topic=%s, %s", topic, e)
    logger.warning("카테고리 추론 결과를 허용 목록에서 찾지 못해 etc 적용: topic=%s", topic)
    return "etc"


def _load_style_guide(category: str) -> tuple[str, Path | None]:
    """카테고리 스타일 가이드를 로드한다. 없으면 빈 문자열과 None을 반환한다."""
    path = STYLE_GUIDES_DIR / f"{category}.md"
    if not path.exists():
        logger.warning("스타일 가이드 없음: category=%s", category)
        print(f"  [warn] 스타일 가이드 없음: {category}.md — 가이드 없이 진행합니다")
        return "", None
    try:
        return path.read_text(encoding="utf-8"), path
    except OSError as e:
        logger.error("스타일 가이드 읽기 실패: path=%s, %s", path, e)
        return "", None


def _build_style_context(style_guide: str) -> str:
    """스타일 가이드에서 LLM 프롬프트용 컨텍스트 문자열을 추출한다."""
    if not style_guide:
        return ""
    # 문체·어휘·구조 섹션만 압축 추출 (가이드 전체를 컨텍스트에 넣으면 너무 길어짐)
    lines = []
    in_section = False
    for line in style_guide.splitlines():
        if line.startswith("## "):
            in_section = line.startswith("## 문체") or line.startswith("## 구조")
        if in_section:
            lines.append(line)
    context = "\n".join(lines).strip()
    return f"\n참고할 스타일 가이드:\n{context}\n" if context else ""


def _generate_titles(topic: str, keywords: list[str], style_guide: str) -> list[str]:
    """SEO 제목 후보 3개를 생성한다. 실패 시 [topic]을 반환한다."""
    style_context = _build_style_context(style_guide)
    prompt = _TITLE_PROMPT.format(
        style_context=style_context,
        topic=topic,
        keywords=", ".join(keywords),
    )
    try:
        response = generate(prompt)
        titles = []
        for line in response.strip().splitlines():
            line = re.sub(r"^[\d\.\-\*\s]+", "", line).strip()
            if line:
                titles.append(line)
        if titles:
            return titles[:3]
    except Exception as e:
        logger.error("제목 생성 실패: topic=%s, %s", topic, e)
    return [topic]


def _generate_outline(topic: str, keywords: list[str], style_guide: str) -> list[dict]:
    """섹션별 아웃라인을 생성한다. 파싱 실패 시 기본 아웃라인을 반환한다."""
    style_context = _build_style_context(style_guide)
    prompt = _OUTLINE_PROMPT.format(
        style_context=style_context,
        topic=topic,
        keywords=", ".join(keywords),
    )
    try:
        response = generate(prompt)
        # JSON 배열 추출
        match = re.search(r"\[[\s\S]*\]", response)
        if match:
            outline = json.loads(match.group())
            if isinstance(outline, list) and outline:
                # 필수 필드 검증
                valid = all(
                    isinstance(s, dict) and "section" in s and "title" in s
                    for s in outline
                )
                if valid:
                    return outline
    except Exception as e:
        logger.error("아웃라인 생성 실패: topic=%s, %s", topic, e)

    logger.warning("아웃라인 파싱 실패, 기본 아웃라인 적용: topic=%s", topic)
    fallback = [s.copy() for s in _OUTLINE_FALLBACK]
    for s in fallback:
        s["description"] = topic
    return fallback


def _make_slug(topic: str) -> str:
    """날짜 + 주제 기반 slug를 생성한다."""
    date_prefix = datetime.now().strftime("%Y%m%d")
    cleaned = re.sub(r"[^\w가-힣]", "", topic)[:20]
    if not cleaned:
        cleaned = "untitled"
    return f"{date_prefix}_{cleaned}"


def _save_outline(
    topic: str,
    category: str,
    keywords: list[str],
    title_candidates: list[str],
    outline: list[dict],
    style_guide_path: Path | None,
) -> Path | None:
    """아웃라인 데이터를 JSON 파일로 저장하고 경로를 반환한다."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("output 디렉터리 생성 실패: path=%s, %s", OUTPUT_DIR, e)
        return None

    slug = _make_slug(topic)
    output_path = OUTPUT_DIR / f"{slug}_outline.json"

    data = {
        "topic": topic,
        "category": category,
        "slug": slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "keywords": keywords,
        "title_candidates": title_candidates,
        "style_guide_path": str(style_guide_path) if style_guide_path else None,
        "outline": outline,
    }

    try:
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.error("아웃라인 저장 실패: path=%s, %s", output_path, e)
        return None

    return output_path


def plan(topic: str) -> Path | None:
    """
    주제를 분석해 섹션별 아웃라인 JSON을 생성하고 저장 경로를 반환한다.
    실패 시 None을 반환한다.
    """
    if not topic.strip():
        logger.error("주제가 비어 있습니다.")
        print("  [fail] 주제를 입력하세요.")
        return None

    topic = topic.strip()
    print(f"  키워드 추출 중...")
    keywords = _extract_keywords(topic)
    print(f"  키워드: {', '.join(keywords)}")

    print(f"  카테고리 추론 중...")
    category = _infer_category(topic, keywords)
    print(f"  카테고리: {category}")

    style_guide, style_guide_path = _load_style_guide(category)

    print(f"  제목 후보 생성 중...")
    title_candidates = _generate_titles(topic, keywords, style_guide)

    print(f"  아웃라인 생성 중...")
    outline = _generate_outline(topic, keywords, style_guide)

    result_path = _save_outline(topic, category, keywords, title_candidates, outline, style_guide_path)
    if result_path is None:
        print(f"  [fail] 아웃라인 저장 실패")
        return None

    return result_path
