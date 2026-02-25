import json
import re
from datetime import datetime, timezone
from pathlib import Path

from config import ANALYSIS_DIR, CATEGORIES, PARSED_POSTS_DIR
from utils.ollama_client import generate

_CATEGORY_PROMPT = """\
다음 블로그 글을 읽고, 아래 카테고리 중 정확히 하나를 선택하세요.
허용 카테고리: {categories}

목록에 없는 카테고리는 절대 사용하지 말고 "etc"를 선택하세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{{"category": "tech"}}

제목: {title}
본문 (일부): {content}"""


def _parse_category(response: str) -> str:
    """LLM 응답에서 카테고리 값을 추출한다. 실패 시 'etc'를 반환한다."""
    try:
        data = json.loads(response.strip())
        return data.get("category", "etc")
    except json.JSONDecodeError:
        pass

    # JSON 파싱 실패 시 정규식으로 카테고리 값 추출
    match = re.search(r'"category"\s*:\s*"([^"]+)"', response)
    if match:
        return match.group(1)

    return "etc"


def analyze(json_path: Path) -> Path | None:
    """
    parsed_posts JSON 파일을 읽어 카테고리를 분류하고 analysis 디렉터리에 저장한다.
    이미 분석된 파일은 스킵한다. 실패 시 None을 반환한다.
    """
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = ANALYSIS_DIR / json_path.name
    if output_path.exists():
        print(f"  [skip] 이미 분석됨: {json_path.name}")
        return output_path

    post = json.loads(json_path.read_text(encoding="utf-8"))
    title = post.get("title", "")
    content = post.get("content", "")[:800]

    prompt = _CATEGORY_PROMPT.format(
        categories=", ".join(CATEGORIES),
        title=title,
        content=content,
    )

    try:
        response = generate(prompt)
    except Exception as e:
        print(f"  [fail] LLM 호출 실패: {e}")
        return None

    raw_category = _parse_category(response)
    category = raw_category if raw_category in CATEGORIES else "etc"

    result = {
        "slug": json_path.stem,
        "url": post.get("url", ""),
        "title": title,
        "category": category,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


_TONE_PROMPT = """\
다음 블로그 글을 읽고 문체, 어휘, 구조 패턴을 분석하세요.

제목: {title}
본문:
{content}

아래 항목을 분석해서 JSON 형식으로 응답하세요:

1. writing_style:
   - formality: "formal" (경어) 또는 "casual" (반말)
   - sentence_length: "short" (짧은 문장), "medium" (중간), "long" (긴 문장)
   - paragraph_structure: "short_paragraphs", "long_paragraphs", "mixed"

2. vocabulary:
   - frequent_expressions: 자주 사용하는 접속사·부사 (최대 10개, 배열)
   - technical_terms: 전문 용어 또는 특정 분야 단어 (최대 10개, 배열)
   - avoid_expressions: 사용하지 않는 표현 (있다면, 배열)

3. structure:
   - opening_style: "question" (질문 시작), "story" (스토리텔링), "direct" (직접 설명)
   - body_style: "step_by_step" (단계별), "list" (리스트형), "narrative" (서술형)
   - closing_style: "summary" (요약), "call_to_action" (행동 유도), "question" (질문)

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{{"writing_style": {{}}, "vocabulary": {{}}, "structure": {{}}}}"""

_TONE_DEFAULT: dict = {
    "writing_style": {
        "formality": "casual",
        "sentence_length": "medium",
        "paragraph_structure": "mixed",
    },
    "vocabulary": {
        "frequent_expressions": [],
        "technical_terms": [],
        "avoid_expressions": [],
    },
    "structure": {
        "opening_style": "direct",
        "body_style": "narrative",
        "closing_style": "summary",
    },
}


def _parse_tone(response: str) -> dict:
    """LLM 응답에서 톤앤매너 dict를 추출한다. 실패 시 기본값을 반환한다."""
    try:
        data = json.loads(response.strip())
        if all(k in data for k in ("writing_style", "vocabulary", "structure")):
            return data
    except json.JSONDecodeError:
        pass

    # JSON 블록만 추출 시도
    match = re.search(r'\{[\s\S]*\}', response)
    if match:
        try:
            data = json.loads(match.group())
            if all(k in data for k in ("writing_style", "vocabulary", "structure")):
                return data
        except json.JSONDecodeError:
            pass

    return _TONE_DEFAULT.copy()


def add_tone_and_manner(analysis_path: Path) -> bool:
    """
    analysis JSON에 tone_and_manner 필드를 추가한다.
    이미 필드가 있으면 스킵한다. 성공 시 True, 실패 시 False를 반환한다.
    """
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))

    if "tone_and_manner" in analysis:
        print(f"  [skip] 톤앤매너 이미 분석됨: {analysis_path.name}")
        return True

    slug = analysis.get("slug", analysis_path.stem)
    parsed_path = PARSED_POSTS_DIR / f"{slug}.json"
    if not parsed_path.exists():
        print(f"  [fail] parsed_posts 파일 없음: {slug}.json")
        return False

    post = json.loads(parsed_path.read_text(encoding="utf-8"))
    title = post.get("title", "")
    content = post.get("content", "")[:2000]

    prompt = _TONE_PROMPT.format(title=title, content=content)

    try:
        response = generate(prompt)
    except Exception as e:
        print(f"  [fail] LLM 호출 실패 (톤앤매너): {e}")
        analysis["tone_and_manner"] = _TONE_DEFAULT.copy()
        analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    analysis["tone_and_manner"] = _parse_tone(response)
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return True
