import json
import re
from datetime import datetime, timezone
from pathlib import Path

from config import OUTPUT_DIR
from utils.logger import get_logger
from utils.ollama_client import generate

logger = get_logger(__name__)

_SYSTEM_PROMPT = """\
당신은 한국어 블로그 작가입니다.
다음 규칙을 반드시 따르세요:
- 지정된 글자 수에 근접한 본문을 생성하세요.
- 본문 텍스트만 반환하고 섹션 제목·번호는 포함하지 마세요.
- AI 생성 티가 나는 표현을 피하세요:
  "물론입니다", "당연히", "매우 중요합니다", "효율적으로" 등의 과잉 표현 금지.
  모든 문장 길이를 일정하게 맞추지 마세요. 짧은 문장과 긴 문장을 자연스럽게 섞으세요.
  1·2·3처럼 단계식으로 과도하게 구조화하지 마세요.
  제품·주제에 대한 직접적인 관찰과 사용 경험만 서술하세요.
  친구·지인·타인의 이야기를 지어내지 마세요. 없는 사람의 경험을 만들어 쓰지 마세요.
- 반복 표현 금지: 이미 앞 섹션에서 사용한 비교 표현("이전 모델보다", "개선되었습니다" 등)을
  같은 섹션에서 3회 이상 반복하지 마세요. 다양한 표현으로 변형하세요.
- 한국어만 사용하세요. 영어·한자·기타 외국 문자를 한국어 문장 안에 섞지 마세요.
- 올바른 한국어 맞춤법과 문법을 사용하세요. 조사·어미를 정확히 쓰세요.\
"""

_SECTION_PROMPT = """\
블로그 주제: {topic}
섹션 제목: {section_title}
섹션 유형: {section_type}
섹션 설명: {section_description}
목표 글자 수: 약 {estimated_chars}자
{style_context}{type_hint}{prev_context}
위 섹션의 본문을 작성하세요.\
"""

_TYPE_HINTS = {
    "opening": "\n[유의사항] 구체적인 상황이나 경험으로 시작하세요. 독자를 바로 끌어들이는 도입부를 작성하세요.\n",
    "closing": "\n[유의사항] 추천 대상과 구매·선택 판단 기준을 제시하고 개인적인 총평을 포함하세요.\n",
    "body": "",
}


def _load_outline(path: Path) -> dict | None:
    """아웃라인 JSON 파일을 읽고 파싱한다. 실패 시 None을 반환한다."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("아웃라인 파일 없음: path=%s", path)
        return None
    except json.JSONDecodeError as e:
        logger.error("아웃라인 JSON 파싱 실패: path=%s, %s", path, e)
        return None
    except OSError as e:
        logger.error("아웃라인 파일 읽기 실패: path=%s, %s", path, e)
        return None

    for field in ("topic", "category", "outline"):
        if field not in data:
            logger.error("아웃라인 필수 필드 누락: field=%s, path=%s", field, path)
            return None

    return data


def _load_style_guide(style_guide_path: str | None) -> str:
    """스타일 가이드 파일을 읽는다. 없거나 실패하면 빈 문자열을 반환한다."""
    if not style_guide_path:
        return ""
    try:
        return Path(style_guide_path).read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("스타일 가이드 읽기 실패: path=%s, %s", style_guide_path, e)
        print(f"  [warn] 스타일 가이드 읽기 실패: {style_guide_path} — 가이드 없이 진행합니다")
        return ""


def _build_style_context(style_guide: str) -> str:
    """스타일 가이드에서 문체·어휘·구조 섹션을 추출해 프롬프트용 컨텍스트를 구성한다."""
    if not style_guide:
        return ""
    lines = []
    in_section = False
    for line in style_guide.splitlines():
        if line.startswith("## "):
            in_section = (
                line.startswith("## 문체")
                or line.startswith("## 어휘")
                or line.startswith("## 구조")
            )
        if in_section:
            lines.append(line)
    context = "\n".join(lines).strip()
    return f"\n참고할 스타일 가이드:\n{context}\n" if context else ""


def _build_prev_context(prev_contents: list[str]) -> str:
    """직전 1~2 섹션의 본문 요약(최대 200자)을 컨텍스트로 구성한다."""
    if not prev_contents:
        return ""
    recent = prev_contents[-2:]
    excerpts = []
    for content in recent:
        excerpt = content.strip()[:200]
        if len(content.strip()) > 200:
            excerpt += "…"
        excerpts.append(excerpt)
    combined = "\n---\n".join(excerpts)
    return f"\n[이전 섹션 내용 요약]\n{combined}\n"


def _generate_section(
    section: dict,
    topic: str,
    style_context: str,
    prev_contents: list[str],
) -> str:
    """섹션 하나의 본문을 LLM으로 생성한다. 실패 시 section.description을 반환한다."""
    section_type = section.get("type", "body")
    type_hint = _TYPE_HINTS.get(section_type, "")
    prev_context = _build_prev_context(prev_contents)

    prompt = f"{_SYSTEM_PROMPT}\n\n{_SECTION_PROMPT.format(
        topic=topic,
        section_title=section.get('title', ''),
        section_type=section_type,
        section_description=section.get('description', ''),
        estimated_chars=section.get('estimated_chars', 300),
        style_context=style_context,
        type_hint=type_hint,
        prev_context=prev_context,
    )}"

    fallback = section.get("description") or section.get("title", "")

    try:
        response = generate(prompt).strip()
        if not response:
            logger.warning("섹션 LLM 응답 빈 문자열: section=%s", section.get("title"))
            print(f"  [warn] 섹션 '{section.get('title')}' LLM 응답 없음 — description으로 대체")
            return fallback
        return response
    except Exception as e:
        logger.error("섹션 생성 실패: section=%s, %s", section.get("title"), e)
        print(f"  [warn] 섹션 '{section.get('title')}' 생성 실패 — description으로 대체")
        return fallback


def _assemble_draft(outline: dict, contents: list[str]) -> str:
    """아웃라인과 섹션 본문 목록으로 최종 Markdown을 조합한다."""
    title_candidates = outline.get("title_candidates") or []
    title = title_candidates[0] if title_candidates else outline.get("topic", "")

    generated_at = datetime.now(timezone.utc).isoformat()
    meta = (
        f"<!-- meta: topic={outline.get('topic', '')}, "
        f"category={outline.get('category', '')}, "
        f"generated_at={generated_at} -->"
    )

    parts = [f"# {title}", "", meta, ""]

    for section, content in zip(outline.get("outline", []), contents):
        parts.append(f"## {section.get('title', '')}")
        parts.append("")
        parts.append(content)
        parts.append("")

    return "\n".join(parts)


def _save_draft(outline: dict, markdown: str) -> Path | None:
    """draft.md를 OUTPUT_DIR에 저장하고 경로를 반환한다. 실패 시 None을 반환한다."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("output 디렉터리 생성 실패: path=%s, %s", OUTPUT_DIR, e)
        return None

    slug = outline.get("slug", "untitled")
    draft_path = OUTPUT_DIR / f"{slug}_draft.md"

    try:
        draft_path.write_text(markdown, encoding="utf-8")
    except OSError as e:
        logger.error("draft 저장 실패: path=%s, %s", draft_path, e)
        return None

    return draft_path


def write(outline_path: Path) -> Path | None:
    """
    아웃라인 JSON을 읽어 스타일 가이드 기반으로 섹션별 본문을 생성하고
    draft.md를 저장한다. 실패 시 None을 반환한다.
    """
    if not outline_path.exists():
        logger.error("아웃라인 파일 없음: path=%s", outline_path)
        print(f"  [fail] 아웃라인 파일 없음: {outline_path}")
        return None

    outline = _load_outline(outline_path)
    if outline is None:
        return None

    topic = outline["topic"]
    style_guide = _load_style_guide(outline.get("style_guide_path"))
    style_context = _build_style_context(style_guide)

    sections = outline.get("outline", [])
    contents: list[str] = []

    print(f"  본문 생성 중... (총 {len(sections)}개 섹션)")
    for i, section in enumerate(sections, 1):
        print(f"  섹션 {i}/{len(sections)}: {section.get('title', '')}")
        content = _generate_section(section, topic, style_context, contents)
        contents.append(content)

    markdown = _assemble_draft(outline, contents)
    draft_path = _save_draft(outline, markdown)
    return draft_path
