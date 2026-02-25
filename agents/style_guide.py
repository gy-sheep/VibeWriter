import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from config import ANALYSIS_DIR, STYLE_GUIDES_DIR, VOCAB_TOP_N
from utils.logger import get_logger

logger = get_logger(__name__)

_HUMANIZE_SECTION = """\
## Humanize 정책

- 동일 단어 3회 이상 연속 사용 금지
- "또한", "그리고" 반복 패턴 탐지 후 다양한 접속사로 교체
- 짧은 문장과 긴 문장을 의도적으로 혼용해 리듬감 유지
- "물론입니다", "당연히", "매우 중요합니다" 등 AI 과잉 표현 제거
- 구체적 경험·상황·감정을 최소 1회 이상 포함
- 과도한 1/2/3 단계식 구조화 지양, 자연스러운 서술 흐름 유지
"""


def _mode(values: list[str]) -> str:
    """최빈값을 반환한다. 값이 없으면 빈 문자열을 반환한다."""
    if not values:
        return ""
    return Counter(values).most_common(1)[0][0]


def _top_n(items: list[str], n: int = VOCAB_TOP_N) -> list[str]:
    """빈도 내림차순으로 상위 n개를 반환한다."""
    return [item for item, _ in Counter(items).most_common(n)]


def _aggregate(entries: list[dict]) -> dict:
    """tone_and_manner 데이터를 집계한다."""
    formality, sentence_length, paragraph_structure = [], [], []
    frequent_expressions, technical_terms, avoid_expressions = [], [], []
    opening_style, body_style, closing_style = [], [], []

    for e in entries:
        tm = e.get("tone_and_manner")
        if not isinstance(tm, dict):
            logger.warning("tone_and_manner 필드가 dict가 아님, 스킵: slug=%s", e.get("slug"))
            continue

        ws = tm.get("writing_style") or {}
        vocab = tm.get("vocabulary") or {}
        struct = tm.get("structure") or {}

        if ws.get("formality"):
            formality.append(ws["formality"])
        if ws.get("sentence_length"):
            sentence_length.append(ws["sentence_length"])
        if ws.get("paragraph_structure"):
            paragraph_structure.append(ws["paragraph_structure"])

        frequent_expressions.extend(vocab.get("frequent_expressions") or [])
        technical_terms.extend(vocab.get("technical_terms") or [])
        avoid_expressions.extend(vocab.get("avoid_expressions") or [])

        if struct.get("opening_style"):
            opening_style.append(struct["opening_style"])
        if struct.get("body_style"):
            body_style.append(struct["body_style"])
        if struct.get("closing_style"):
            closing_style.append(struct["closing_style"])

    return {
        "writing_style": {
            "formality": _mode(formality),
            "sentence_length": _mode(sentence_length),
            "paragraph_structure": _mode(paragraph_structure),
        },
        "vocabulary": {
            "frequent_expressions": _top_n(frequent_expressions),
            "technical_terms": _top_n(technical_terms),
            "avoid_expressions": list(dict.fromkeys(avoid_expressions)),
        },
        "structure": {
            "opening_style": _mode(opening_style),
            "body_style": _mode(body_style),
            "closing_style": _mode(closing_style),
        },
    }


_FORMALITY_LABEL = {"formal": "경어체", "casual": "반말/구어체"}
_SENTENCE_LABEL = {
    "short": "짧은 문장 위주",
    "medium": "중간 길이",
    "long": "긴 문장 위주",
}
_PARAGRAPH_LABEL = {
    "short_paragraphs": "짧은 단락 위주",
    "long_paragraphs": "긴 단락 위주",
    "mixed": "짧은 단락과 긴 단락 혼용",
}
_OPENING_LABEL = {
    "question": "질문으로 시작",
    "story": "스토리텔링",
    "direct": "직접 설명",
}
_BODY_LABEL = {
    "step_by_step": "단계별 설명",
    "list": "리스트형",
    "narrative": "서술형",
}
_CLOSING_LABEL = {
    "summary": "핵심 요약",
    "call_to_action": "행동 유도",
    "question": "질문으로 마무리",
}


def _render_markdown(category: str, agg: dict, count: int) -> str:
    ws = agg["writing_style"]
    vocab = agg["vocabulary"]
    struct = agg["structure"]
    today = datetime.now().strftime("%Y-%m-%d")

    freq_expr = ", ".join(vocab["frequent_expressions"]) or "(없음)"
    tech_terms = ", ".join(vocab["technical_terms"]) or "(없음)"
    avoid_expr = ", ".join(vocab["avoid_expressions"]) or "(없음)"

    formality_val = f"{ws['formality']} ({_FORMALITY_LABEL.get(ws['formality'], ws['formality'])})"
    sentence_val = f"{ws['sentence_length']} ({_SENTENCE_LABEL.get(ws['sentence_length'], ws['sentence_length'])})"
    paragraph_val = f"{ws['paragraph_structure']} ({_PARAGRAPH_LABEL.get(ws['paragraph_structure'], ws['paragraph_structure'])})"
    opening_val = f"{struct['opening_style']} ({_OPENING_LABEL.get(struct['opening_style'], struct['opening_style'])})"
    body_val = f"{struct['body_style']} ({_BODY_LABEL.get(struct['body_style'], struct['body_style'])})"
    closing_val = f"{struct['closing_style']} ({_CLOSING_LABEL.get(struct['closing_style'], struct['closing_style'])})"

    return f"""\
# {category} 스타일 가이드

> 분석 글 수: {count}개 | 최종 업데이트: {today}

---

## 문체 (Writing Style)

| 항목 | 가이드 |
|------|--------|
| 격식 수준 | {formality_val} |
| 문장 길이 | {sentence_val} |
| 단락 구성 | {paragraph_val} |

---

## 어휘 (Vocabulary)

### 자주 쓰는 표현 (빈도 순)
{freq_expr}

### 전문 용어
{tech_terms}

### 피해야 할 표현
{avoid_expr}

---

## 구조 (Structure)

| 항목 | 가이드 |
|------|--------|
| 도입부 | {opening_val} |
| 본문 | {body_val} |
| 마무리 | {closing_val} |

---

{_HUMANIZE_SECTION}"""


def generate_style_guides() -> list[Path]:
    """
    analysis 디렉터리의 모든 JSON 파일을 카테고리별로 집계해
    style_guides/{category}.md 파일을 생성한다.
    생성된 파일 경로 목록을 반환한다.
    """
    STYLE_GUIDES_DIR.mkdir(parents=True, exist_ok=True)

    if not ANALYSIS_DIR.exists():
        logger.warning("analysis 디렉터리가 없습니다: %s", ANALYSIS_DIR)
        print("  [warn] analysis 디렉터리가 없습니다.")
        return []

    # 카테고리별 그룹핑
    groups: dict[str, list[dict]] = {}
    for path in sorted(ANALYSIS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.error("analysis 파일 읽기 실패, 스킵: path=%s, %s", path, e)
            print(f"  [warn] 읽기 실패, 스킵: {path.name}")
            continue

        if "tone_and_manner" not in data:
            logger.warning("tone_and_manner 없음, 스킵: %s", path.name)
            print(f"  [warn] tone_and_manner 없음, 스킵: {path.name}")
            continue

        category = data.get("category", "etc")
        groups.setdefault(category, []).append(data)

    if not groups:
        logger.warning("집계할 데이터가 없습니다.")
        print("  [warn] 집계할 데이터가 없습니다.")
        return []

    generated: list[Path] = []
    for category, entries in sorted(groups.items()):
        agg = _aggregate(entries)
        content = _render_markdown(category, agg, len(entries))
        out_path = STYLE_GUIDES_DIR / f"{category}.md"

        try:
            out_path.write_text(content, encoding="utf-8")
        except OSError as e:
            logger.error("스타일 가이드 저장 실패: path=%s, %s", out_path, e)
            print(f"  [fail] 스타일 가이드 저장 실패: {out_path.name}")
            continue

        print(f"  [done] 스타일 가이드 생성: {out_path.name} ({len(entries)}개 글 기반)")
        generated.append(out_path)

    return generated
