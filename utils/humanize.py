"""규칙 기반 humanize 유틸리티.

LLM 없이 regex 치환만으로 AI 생성 티를 줄인다.
- remove_foreign_chars   : 로컬 LLM이 혼입한 한자·비표준 라틴 문자 제거
- remove_ai_phrases      : AI 과잉 표현 제거
- diversify_conjunctions : 반복 접속사 다양화
- apply_all              : 위 규칙 일괄 적용
"""

import random
import re
from collections import Counter

# 로컬 LLM이 한국어 텍스트 안에 혼입하는 외국 문자 패턴
# - CJK 통합 한자 (중국어·일본어): U+4E00–U+9FFF, U+3400–U+4DBF, U+F900–U+FAFF
# - 키릴 문자 (러시아어 등): U+0400–U+04FF
# - 아랍 문자: U+0600–U+06FF
# - 기타 비라틴 스크립트: 태국어(U+0E00-U+0E7F), 히브리어(U+0590-U+05FF)
# - 비표준 라틴 확장 문자를 포함한 단어 (베트남어 등): U+0100–U+024F, U+1E00–U+1EFF
#   단, Markdown 헤더(#으로 시작하는 줄)와 HTML 주석은 건드리지 않는다.
_FOREIGN_SCRIPT_PATTERN = re.compile(
    r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff"  # CJK 한자
    r"\u0400-\u04ff"                              # 키릴 문자
    r"\u0600-\u06ff"                              # 아랍 문자
    r"\u0590-\u05ff"                              # 히브리 문자
    r"\u0e00-\u0e7f]+"                            # 태국 문자
)
# 비표준 라틴 확장 문자를 포함한 단어: ASCII 영숫자 + 라틴 확장 문자로만 구성된 토큰
# \S* 대신 [a-zA-Z0-9...] 범위를 명시해 한국어 문자가 함께 제거되는 것을 방지한다.
_LATIN_EXT_WORD = re.compile(r"[a-zA-Z0-9\u0100-\u024f\u1e00-\u1eff]*[\u0100-\u024f\u1e00-\u1eff][a-zA-Z0-9\u0100-\u024f\u1e00-\u1eff]*")


def remove_foreign_chars(text: str) -> str:
    """로컬 LLM이 한국어 본문에 혼입한 한자·비표준 라틴 문자를 제거한다.

    Markdown 헤더(# 으로 시작하는 줄)와 HTML 주석(<!-- ... -->)은 건드리지 않는다.
    """
    if not text or not text.strip():
        return text

    lines = text.splitlines(keepends=True)
    result: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        # Markdown 헤더·HTML 주석은 그대로 보존
        if stripped.startswith("#") or stripped.startswith("<!--"):
            result.append(line)
            continue
        line = _FOREIGN_SCRIPT_PATTERN.sub("", line)
        line = _LATIN_EXT_WORD.sub("", line)
        # 제거 후 생긴 연속 공백 정리
        line = re.sub(r"[ \t]{2,}", " ", line)
        result.append(line)

    return "".join(result)


# AI 과잉 표현 패턴 — 각 패턴은 매치 전체를 빈 문자열로 치환한다.
_AI_PHRASE_PATTERNS: list[re.Pattern] = [
    re.compile(r"물론\s*(입니다|이죠|이에요|이지요)[,.]?\s*", re.IGNORECASE),
    re.compile(r"당연\s*(히|하게도)[,.]?\s*", re.IGNORECASE),
    re.compile(r"매우\s*중요\s*(합니다|해요|하죠)[.!]?\s*", re.IGNORECASE),
    re.compile(r"효율적으로\s*", re.IGNORECASE),
    re.compile(r"본질적으로\s*", re.IGNORECASE),
    re.compile(r"중요한\s*점은\s*", re.IGNORECASE),
    re.compile(r"주목할\s*만한\s*점은\s*", re.IGNORECASE),
    re.compile(r"명심해야\s*(할|하는)\s*(것은|점은)\s*", re.IGNORECASE),
]

# 접속사별 교체 후보 목록
_CONJUNCTION_ALTS: dict[str, list[str]] = {
    "또한": ["그리고", "아울러", "더불어"],
    "하지만": ["그런데", "그러나", "다만"],
    "그래서": ["따라서", "그러므로", "덕분에"],
    "그리고": ["또한", "아울러", "더불어"],
    "그러나": ["하지만", "그런데", "다만"],
    "따라서": ["그래서", "그러므로", "결국"],
}

# 문장 시작 접속사를 탐지하는 패턴 (행 앞 또는 마침표·느낌표·물음표 뒤 공백)
_SENTENCE_START = re.compile(r"(?:^|(?<=[.!?]\s))(" + "|".join(re.escape(c) for c in _CONJUNCTION_ALTS) + r")(?=\s)", re.MULTILINE)


def remove_ai_phrases(text: str) -> str:
    """AI 과잉 표현을 탐지해 제거한다."""
    if not text or not text.strip():
        return text
    for pattern in _AI_PHRASE_PATTERNS:
        text = pattern.sub("", text)
    # 문장 앞뒤 공백 및 중복 공백·빈 줄 정리
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)  # 각 행 앞 공백 제거
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def diversify_conjunctions(text: str, seed: int | None = None) -> str:
    """동일 접속사가 짧은 범위에서 반복되면 대안 표현으로 교체한다.

    문단 단위로 순회하며, 같은 접속사가 연속 2회 이상 등장하는 경우
    두 번째 등장부터 후보 표현 중 하나로 랜덤 교체한다.
    """
    if not text or not text.strip():
        return text

    rng = random.Random(seed)
    paragraphs = text.split("\n\n")
    result_paragraphs: list[str] = []

    for paragraph in paragraphs:
        # Markdown 헤더·코드블록·HTML 주석은 건드리지 않는다.
        if paragraph.startswith("#") or paragraph.startswith("```") or paragraph.startswith("<!--"):
            result_paragraphs.append(paragraph)
            continue

        recent: dict[str, int] = {}  # 접속사 → 최근 등장 위치(문장 index)
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        new_sentences: list[str] = []

        for idx, sentence in enumerate(sentences):
            m = re.match(r"^(" + "|".join(re.escape(c) for c in _CONJUNCTION_ALTS) + r")(\s)", sentence)
            if m:
                conj = m.group(1)
                last_idx = recent.get(conj, -99)
                if idx - last_idx <= 4:  # 4문장 이내 재등장 시 교체
                    alt = rng.choice(_CONJUNCTION_ALTS[conj])
                    sentence = alt + m.group(2) + sentence[m.end():]
                recent[conj] = idx
            new_sentences.append(sentence)

        result_paragraphs.append(" ".join(new_sentences))

    return "\n\n".join(result_paragraphs)


def detect_repetitive_phrases(text: str, min_repeats: int = 3, min_len: int = 6) -> list[str]:
    """전체 본문에서 min_repeats회 이상 반복되는 2어절 이상의 어구를 반환한다.

    Markdown 헤더·HTML 주석은 제외하고 순수 본문 텍스트만 분석한다.
    quality_check에서 LLM polish 지시에 활용한다.
    """
    body_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("<!--") or not stripped:
            continue
        body_lines.append(stripped)
    body = " ".join(body_lines)

    # 한국어 어절(공백 구분 토큰) 추출
    tokens = re.findall(r"[가-힣a-zA-Z0-9]+", body)
    if len(tokens) < 4:
        return []

    # 2어절 bi-gram 생성 후 빈도 집계
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    counts = Counter(bigrams)

    repeated = [
        phrase for phrase, cnt in counts.items()
        if cnt >= min_repeats and len(phrase) >= min_len
    ]
    # 빈도 내림차순 정렬, 최대 5개 반환
    repeated.sort(key=lambda p: -counts[p])
    return repeated[:5]


def apply_all(text: str) -> str:
    """모든 humanize 규칙을 순서대로 적용한다."""
    if not text or not text.strip():
        return text
    text = remove_foreign_chars(text)
    text = remove_ai_phrases(text)
    text = diversify_conjunctions(text)
    return text
