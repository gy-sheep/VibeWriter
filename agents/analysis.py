import json
import re
from datetime import datetime, timezone
from pathlib import Path

from config import ANALYSIS_DIR, CATEGORIES
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
