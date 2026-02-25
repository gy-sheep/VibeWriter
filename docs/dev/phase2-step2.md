# Phase 2 · Step 2 개발 기획

> **범위**: 본문 생성
> **목표**: 아웃라인 JSON 로드 → 스타일 가이드 기반 섹션별 LLM 본문 생성 → `draft.md` 저장

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 2 | 아웃라인 JSON 로드 | `agents/writer.py` |
| Step 2 | 카테고리 스타일 가이드 로드 | `agents/writer.py` |
| Step 2 | 섹션별 LLM 본문 생성 (이전 섹션 컨텍스트 포함) | `agents/writer.py` |
| Step 2 | humanize 정책을 프롬프트에 내장 | `agents/writer.py` |
| Step 2 | 섹션 조합 → Markdown draft 구성 | `agents/writer.py` |
| Step 2 | `{slug}_draft.md` 저장 | `agents/writer.py` |
| Step 2 | `main.py` write 파이프라인에 WriterAgent 연결 | `main.py` |

---

## 2. 데이터 흐름

```
data/output/{YYYYMMDD}_{slug}_outline.json
        │
        ▼ (아웃라인 + 스타일 가이드 경로 로드)
  [WriterAgent]
        │ 카테고리 스타일 가이드 경로
        ▼
  data/style_guides/{category}.md  (기존 파일 로드)
        │
        ▼ (섹션별 LLM 생성, 이전 섹션 컨텍스트 포함, humanize 프롬프트 내장)
  [WriterAgent — 섹션 N회 LLM 호출]
        │
        ▼ (섹션 조합 → Markdown 구성)
  data/output/{YYYYMMDD}_{slug}_draft.md
```

---

## 3. 파일 명세

### 입력 1 — 아웃라인 JSON

**`data/output/{YYYYMMDD}_{slug}_outline.json`**
```json
{
  "topic": "맥북 프로 M3 리뷰",
  "category": "review",
  "slug": "20260226_맥북프로M3리뷰",
  "created_at": "2026-02-26T10:00:00+00:00",
  "keywords": ["맥북 프로", "M3 칩", "애플 실리콘", "성능 테스트", "배터리"],
  "title_candidates": [
    "맥북 프로 M3 3개월 써본 솔직 후기",
    "M3 칩 맥북, 정말 그렇게 빠를까?",
    "개발자가 직접 쓴 맥북 프로 M3 리얼 리뷰"
  ],
  "style_guide_path": "data/style_guides/review.md",
  "outline": [
    {"section": 1, "title": "들어가며", "type": "opening", "description": "구매 계기와 첫 인상을 구체적 상황으로 시작", "estimated_chars": 300},
    {"section": 2, "title": "성능 테스트 결과", "type": "body", "description": "벤치마크 수치와 체감 속도 비교", "estimated_chars": 500},
    {"section": 3, "title": "배터리 & 발열", "type": "body", "description": "장시간 사용 시 배터리 소모와 발열 실측", "estimated_chars": 400},
    {"section": 4, "title": "아쉬운 점", "type": "body", "description": "단점과 실제 사용 불편 경험 솔직하게 서술", "estimated_chars": 300},
    {"section": 5, "title": "결론", "type": "closing", "description": "추천 대상과 구매 판단 기준 제시", "estimated_chars": 250}
  ]
}
```

### 입력 2 — 스타일 가이드 (기존 파일)

**`data/style_guides/{category}.md`**
- Phase 1에서 생성된 카테고리별 스타일 가이드
- `style_guide_path`가 `null`이거나 파일이 없으면 빈 문자열로 진행, 경고 출력

### 출력

**`data/output/{YYYYMMDD}_{slug}_draft.md`**
```markdown
# 맥북 프로 M3 3개월 써본 솔직 후기

<!-- meta: topic=맥북 프로 M3 리뷰, category=review, generated_at=2026-02-26T10:05:00+00:00 -->

## 들어가며

[섹션 1 본문 내용]

## 성능 테스트 결과

[섹션 2 본문 내용]

## 배터리 & 발열

[섹션 3 본문 내용]

## 아쉬운 점

[섹션 4 본문 내용]

## 결론

[섹션 5 본문 내용]
```

- 제목: `title_candidates[0]` 사용 (없으면 `topic` 그대로)
- 메타 주석: Markdown HTML 주석 형식으로 삽입 (후속 Step에서 파싱 용도)
- 각 섹션은 `## {section.title}` 헤더 + 본문 텍스트로 구성

---

## 4. 모듈 상세

### `agents/writer.py` — WriterAgent

#### `write(outline_path: Path) -> Path | None`

최상위 진입 함수. 아래 단계를 순서대로 실행하고 `draft.md` 경로를 반환한다.

0. `outline_path` 존재 여부 확인 → 없으면 에러 로그 + `None` 반환 (early return)
1. `_load_outline(outline_path)` → outline dict
2. `_load_style_guide(outline["style_guide_path"])` → style_guide 문자열
3. `_build_style_context(style_guide)` → 프롬프트용 컨텍스트 문자열
4. 섹션 순회: `_generate_section(section, topic, style_context, prev_contents)` → 각 섹션 본문
5. `_assemble_draft(outline, contents)` → 최종 Markdown 문자열
6. `_save_draft(outline, markdown)` → `Path | None`

실패 시 `None` 반환, 에러 로그 출력.

---

#### `_load_outline(path: Path) -> dict | None`

- `path.read_text(encoding="utf-8")` → `json.loads()` 파싱.
- 파일 없음: `FileNotFoundError` 로그 후 `None` 반환.
- JSON 파싱 실패: `json.JSONDecodeError` 로그 후 `None` 반환.
- 필수 필드(`topic`, `category`, `outline`) 중 하나라도 없으면 에러 로그 후 `None` 반환.

---

#### `_load_style_guide(style_guide_path: str | None) -> str`

- `style_guide_path`가 `None`이면 빈 문자열 반환.
- `Path(style_guide_path).read_text(encoding="utf-8")` 시도.
- 파일 없음 또는 `OSError`: 경고 로그 출력 후 빈 문자열 반환.

---

#### `_build_style_context(style_guide: str) -> str`

- `planner.py`의 `_build_style_context`와 동일한 로직 사용.
- 단, writer 프롬프트에는 `## 문체`, `## 어휘`, `## 구조` 세 섹션을 모두 포함한다 (planner는 문체·구조만).
- 가이드가 빈 문자열이면 `""` 반환.

---

#### `_generate_section(section: dict, topic: str, style_context: str, prev_contents: list[str]) -> str`

섹션 하나의 본문을 LLM으로 생성한다.

**프롬프트 설계:**

```
시스템:
당신은 한국어 블로그 작가입니다.
다음 규칙을 반드시 따르세요:
- 지정된 글자 수에 근접한 본문을 생성하세요.
- 본문 텍스트만 반환하고 섹션 제목·번호는 포함하지 마세요.
- AI 생성 티가 나는 표현을 피하세요:
  "물론입니다", "당연히", "매우 중요합니다", "효율적으로" 등의 과잉 표현 금지.
  모든 문장 길이를 일정하게 맞추지 마세요. 짧은 문장과 긴 문장을 자연스럽게 섞으세요.
  1·2·3처럼 단계식으로 과도하게 구조화하지 마세요.
  구체적인 경험, 감각, 상황 묘사를 포함하세요.

유저:
블로그 주제: {topic}
섹션 제목: {section.title}
섹션 유형: {section.type}  (opening/body/closing)
섹션 설명: {section.description}
목표 글자 수: 약 {section.estimated_chars}자
{style_context}
{prev_context}

위 섹션의 본문을 작성하세요.
```

- `prev_context`: 직전 1~2 섹션의 본문 요약(최대 200자 truncate)을 포함해 흐름 일관성 유지. 첫 섹션이면 생략.
- `section.type == "opening"`: 구체적 상황·경험으로 시작하도록 프롬프트에 명시.
- `section.type == "closing"`: 추천 대상·총평·개인 의견 포함하도록 명시.
- LLM 응답이 빈 문자열이면 경고 로그 + `section.description` 반환 (fallback).
- `generate()` 실패(예외): 에러 로그 + `section.description` 반환 (fallback).

---

#### `_assemble_draft(outline: dict, contents: list[str]) -> str`

- 제목: `outline["title_candidates"][0]` (없거나 빈 경우 `outline["topic"]` 사용).
- 메타 주석: `<!-- meta: topic=..., category=..., generated_at=... -->` (ISO 8601 UTC).
- 섹션별 `## {title}\n\n{content}\n\n` 형식으로 조합.
- 최종 Markdown 문자열 반환.

---

#### `_save_draft(outline: dict, markdown: str) -> Path | None`

- 저장 경로: `OUTPUT_DIR / f"{outline['slug']}_draft.md"`
- `OUTPUT_DIR` 없으면 `mkdir(parents=True, exist_ok=True)`. 실패 시 `OSError` 로그 + `None` 반환.
- `path.write_text(markdown, encoding="utf-8")`. 실패 시 `OSError` 로그 + `None` 반환.
- 성공 시 `Path` 반환.

---

#### 실패 처리

| 상황 | 처리 방식 |
|------|----------|
| 아웃라인 파일 없음 | 에러 로그 → `None` 반환 |
| JSON 파싱 실패 | 에러 로그 → `None` 반환 |
| 필수 필드 누락 | 에러 로그 → `None` 반환 |
| 스타일 가이드 없음 | 경고 출력 후 빈 문자열로 계속 진행 |
| 섹션 LLM 생성 실패 | 경고 로그 + `section.description`으로 fallback, 나머지 섹션 계속 진행 |
| LLM 응답 빈 문자열 | 경고 로그 + `section.description` fallback |
| OUTPUT_DIR 생성 실패 | OSError 로그 → `None` 반환 |

---

### `main.py` — write 파이프라인 확장

```python
def cmd_write(topic: str) -> None:
    print(f"주제: {topic}")

    outline_path = plan(topic)
    if not outline_path:
        print("  [fail] 아웃라인 생성 실패 — 중단")
        return

    print(f"  아웃라인 생성 완료: {outline_path}")

    draft_path = write(outline_path)
    if draft_path:
        print(f"  초안 생성 완료: {draft_path}")
    else:
        print("  [fail] 초안 생성 실패")
```

- `write` 함수를 `agents/writer.py`에서 import.
- `plan()` 실패 시 즉시 반환 (writer 호출 생략).

---

## 5. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── crawler.py
│   ├── parser.py
│   ├── analysis.py
│   ├── style_guide.py
│   ├── planner.py
│   └── writer.py           ← 섹션별 본문 생성 · draft.md 저장 (신규)
├── data/
│   ├── input/
│   ├── raw_html/
│   ├── parsed_posts/
│   ├── analysis/
│   ├── style_guides/
│   └── output/             ← {slug}_outline.json + {slug}_draft.md (.gitignore)
├── utils/
│   ├── file_manager.py
│   ├── ollama_client.py
│   └── logger.py
├── config.py
├── main.py                 ← cmd_write()에 write() 연결 (수정)
└── docs/dev/
    ├── _template.md
    ├── phase1-step1-2.md
    ├── phase1-step3.md
    ├── phase1-step5.md
    ├── phase2-step1.md
    └── phase2-step2.md     ← 본 문서
```

---

## 6. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| 기본 동작 | `uv run python main.py write --topic "제주 여행 3박4일 후기"` → `data/output/` 에 `_draft.md` 생성 확인 |
| 전체 글자 수 | `_draft.md` 전체 본문 글자 수 ≥ 2000자 확인 |
| 섹션 구성 | 아웃라인 섹션 수와 `_draft.md`의 `##` 헤더 수 일치 확인 |
| 제목 반영 | `_draft.md` 첫 줄이 `title_candidates[0]`과 일치 확인 |
| 스타일 가이드 반영 | 스타일 가이드가 있는 카테고리로 생성 → 문체가 가이드 기준에 근접하는지 육안 확인 |
| 섹션 fallback | `generate()` 실패를 임시 mock으로 시뮬레이션 → 해당 섹션에 `description` 텍스트 삽입 후 나머지 섹션 정상 진행 확인 |
| 아웃라인 없는 경우 | 존재하지 않는 경로 전달 → 에러 로그 출력 후 `None` 반환 확인 |
| 파이프라인 연결 | `main.py write` 한 번 실행으로 outline.json + draft.md 두 파일 모두 생성 확인 |
