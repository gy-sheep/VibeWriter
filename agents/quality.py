"""QualityAgent — 품질 검증 및 humanize.

처리 순서:
  1. draft.md 로드 + 메타 파싱
  2. humanize.apply_all() — 규칙 기반 1차 정제
  3. _check_style()       — 스타일 가이드 준수 체크 (규칙 기반)
  4. _polish()            — LLM 기반 최종 humanize 다듬기
  5. _save_final()        — final.md 저장
"""

import re
import statistics
from pathlib import Path

from config import OUTPUT_DIR
from utils import humanize
from utils.logger import get_logger
from utils.ollama_client import generate

logger = get_logger(__name__)

_POLISH_SYSTEM = """\
당신은 한국어 블로그 에디터입니다. 아래 규칙을 반드시 지키세요:
- 한국어 맞춤법·문법 오류는 반드시 수정하세요. (예: "기다보던" → "기다리던", "됬다" → "됐다")
- 없는 경험이나 사실을 만들어 추가하지 마세요. 원문에 있는 내용만 다듬으세요.
- "내 친구가", "제 지인이" 같이 타인의 경험을 지어낸 문장은 자연스럽게 제거하거나 1인칭 직접 경험으로 바꾸세요.
- 반복 사용된 표현은 다양한 표현으로 자연스럽게 바꾸세요.
- 어색하거나 부자연스러운 문장만 고치세요. 자연스러운 문장은 그대로 두세요.
- 문장 리듬: 비슷한 길이의 문장이 3개 이상 이어지면 짧은 문장 하나를 끼워 변화를 주세요.
- 본문 텍스트만 반환하세요. 제목·설명·주석은 절대 붙이지 마세요.
- 원문 글자 수의 70~130% 범위를 유지하세요.\
"""

_POLISH_USER = """\
{violations_section}아래 블로그 본문을 최소한으로 다듬어 본문 텍스트만 반환하세요. 원문을 최대한 보존하세요.

{body}\
"""

# LLM 응답 길이가 원본 대비 이 비율을 벗어나면 fallback
_POLISH_LENGTH_TOLERANCE = 0.4  # ±40%


def _load_draft(path: Path) -> tuple[str, dict] | None:
    """draft.md 전체 텍스트와 메타 정보를 반환한다. 실패 시 None을 반환한다."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("draft 읽기 실패: path=%s, %s", path, e)
        return None

    meta: dict = {}
    m = re.search(r"<!--\s*meta:\s*(.+?)\s*-->", text)
    if m:
        for pair in m.group(1).split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                meta[k.strip()] = v.strip()
    else:
        logger.warning("draft 메타 주석 없음: path=%s", path)

    return text, meta


def _load_style_guide(style_guide_path: str) -> str:
    """스타일 가이드 파일을 읽는다. 없거나 실패하면 빈 문자열을 반환한다."""
    if not style_guide_path:
        return ""
    try:
        return Path(style_guide_path).read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("스타일 가이드 읽기 실패: path=%s, %s", style_guide_path, e)
        return ""


def _extract_body_text(markdown: str) -> str:
    """Markdown에서 헤더·HTML 주석을 제외한 순수 본문 텍스트를 추출한다."""
    lines = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        if stripped:
            lines.append(stripped)
    return " ".join(lines)


def _check_style(markdown: str, style_guide: str) -> list[str]:
    """규칙 기반으로 스타일 가이드 준수 여부를 체크하고 위반 항목 목록을 반환한다."""
    violations: list[str] = []

    body = _extract_body_text(markdown)
    if not body:
        return violations

    # 1. 문장 길이 단조로움 체크
    sentences = [s.strip() for s in re.split(r"[.!?]", body) if s.strip()]
    if len(sentences) >= 5:
        lengths = [len(s) for s in sentences]
        try:
            stdev = statistics.stdev(lengths)
            if stdev < 15:
                violations.append(
                    f"문장 길이가 단조롭습니다 (표준편차 {stdev:.1f}자). "
                    "짧은 문장과 긴 문장을 자연스럽게 섞어주세요."
                )
        except statistics.StatisticsError:
            pass

    # 2. AI 과잉 표현 잔존 체크
    cleaned = humanize.remove_ai_phrases(body)
    if cleaned != body:
        violations.append("AI 과잉 표현이 남아 있습니다. 자연스러운 표현으로 교체해주세요.")

    # 3. 반복 접속사 체크
    diversified = humanize.diversify_conjunctions(body, seed=0)
    if diversified != body:
        violations.append("동일 접속사가 반복됩니다. 다양한 접속사를 사용해주세요.")

    # 4. 반복 어구 체크
    repeated = humanize.detect_repetitive_phrases(markdown)
    if repeated:
        phrases = ", ".join(f'"{p}"' for p in repeated)
        violations.append(f"아래 어구가 과도하게 반복됩니다. 다양한 표현으로 바꾸세요: {phrases}")

    return violations


def _polish_section(title: str, body: str, violations: list[str]) -> str:
    """섹션 본문 하나를 LLM으로 다듬는다. 실패하거나 길이 이탈 시 원본 body를 반환한다."""
    if violations:
        violations_section = (
            "[개선 필요 항목]\n"
            + "\n".join(f"- {v}" for v in violations)
            + "\n\n"
        )
    else:
        violations_section = ""

    prompt = _POLISH_SYSTEM + "\n\n" + _POLISH_USER.format(
        violations_section=violations_section,
        body=body,
    )

    try:
        response = generate(prompt).strip()
        if not response:
            logger.warning("polish LLM 응답 빈 문자열: section=%s", title)
            return body

        # 길이 이탈 검사: 원본 대비 ±40% 초과 시 fallback
        original_len = len(body.strip())
        response_len = len(response)
        if original_len > 0:
            ratio = response_len / original_len
            if ratio < (1 - _POLISH_LENGTH_TOLERANCE) or ratio > (1 + _POLISH_LENGTH_TOLERANCE):
                logger.warning(
                    "polish 길이 이탈 fallback: section=%s, 원본=%d, 응답=%d (%.1f%%)",
                    title, original_len, response_len, ratio * 100,
                )
                return body

        return response
    except Exception as e:
        logger.error("polish LLM 호출 실패: section=%s, %s", title, e)
        return body


def _polish(markdown: str, violations: list[str]) -> str:
    """섹션 단위로 LLM polish를 적용하고 Markdown 전문을 재조합해 반환한다."""
    # 헤더(# 또는 ##)를 기준으로 분리
    # 패턴: \n## 또는 문자열 시작 ## / # 보존
    parts = re.split(r"(\n#{1,2} [^\n]+)", markdown)

    result: list[str] = []
    current_header = ""

    for part in parts:
        if re.match(r"\n#{1,2} ", part):
            current_header = part
            result.append(part)
        else:
            # HTML 주석·빈 내용은 그대로 유지
            stripped = part.strip()
            if not stripped or stripped.startswith("<!--"):
                result.append(part)
                continue
            # 섹션 본문: LLM polish 적용
            polished = _polish_section(current_header.strip(), part, violations)
            # 앞뒤 개행 유지
            leading = part[: len(part) - len(part.lstrip("\n"))]
            trailing = part[len(part.rstrip("\n")):]
            result.append(leading + polished + trailing)

    return "".join(result)


def _save_final(draft_path: Path, markdown: str) -> Path | None:
    """draft_path에서 _draft → _final로 바꾼 경로에 final.md를 저장한다."""
    final_name = draft_path.name.replace("_draft.", "_final.")
    if final_name == draft_path.name:
        # '_draft' 가 파일명에 없는 경우 fallback
        final_name = draft_path.stem + "_final" + draft_path.suffix
    final_path = draft_path.parent / final_name

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        final_path.write_text(markdown, encoding="utf-8")
    except OSError as e:
        logger.error("final.md 저장 실패: path=%s, %s", final_path, e)
        return None

    return final_path


def quality_check(draft_path: Path) -> Path | None:
    """
    draft.md를 읽어 humanize 및 품질 검증 후 final.md를 저장한다.
    실패 시 None을 반환한다.
    """
    if not draft_path.exists():
        logger.error("draft 파일 없음: path=%s", draft_path)
        print(f"  [fail] draft 파일 없음: {draft_path}")
        return None

    result = _load_draft(draft_path)
    if result is None:
        return None
    markdown, meta = result

    # 1차 정제 (규칙 기반)
    print("  humanize 적용 중...")
    markdown = humanize.apply_all(markdown)

    # 스타일 가이드 로드 및 체크
    style_guide_path = meta.get("style_guide_path", "")
    style_guide = _load_style_guide(style_guide_path)
    violations = _check_style(markdown, style_guide)

    if violations:
        print(f"  스타일 위반 {len(violations)}건 감지 → LLM polish 진행")
        for v in violations:
            print(f"    - {v}")
    else:
        print("  스타일 체크 통과 → LLM polish 진행")

    # LLM 최종 다듬기
    print("  LLM polish 중...")
    markdown = _polish(markdown, violations)

    # 저장
    final_path = _save_final(draft_path, markdown)
    return final_path
