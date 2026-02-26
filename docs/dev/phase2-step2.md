# Phase 2 · Step 1 개발 기획

> **범위**: 주제 분석 및 목차 구성
> **목표**: 사용자 주제 입력 → 카테고리 추론 + 스타일 가이드 로드 → 섹션별 아웃라인 JSON 생성

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 1 | 주제에서 핵심 키워드 추출 (LLM) | `agents/planner.py` |
| Step 1 | 주제 기반 카테고리 추론 → 허용 목록 정규화 | `agents/planner.py` |
| Step 1 | 해당 카테고리 스타일 가이드 로드 | `agents/planner.py` |
| Step 1 | SEO 고려 제목 후보 3개 생성 (LLM) | `agents/planner.py` |
| Step 1 | 섹션별 목차(아웃라인) 생성 (LLM, 스타일 가이드 반영) | `agents/planner.py` |
| Step 1 | 아웃라인 JSON 저장 | `agents/planner.py` |
| Step 1 | `main.py`에 `write` 서브커맨드 추가 | `main.py` |

---

## 2. 데이터 흐름

```
[사용자 입력: --topic "맥북 프로 M3 리뷰"]
        │
        ▼ (키워드 추출 · 카테고리 추론)
  [PlannerAgent]
        │ 카테고리명 (허용 목록 정규화)
        ▼
  data/style_guides/{category}.md  (기존 파일 로드)
        │
        ▼ (제목 후보 + 아웃라인 생성, 스타일 가이드 컨텍스트 반영)
  [PlannerAgent — LLM 호출]
        │
        ▼
  data/output/{YYYYMMDD}_{slug}_outline.json
```

---

## 3. 파일 명세

### 입력 1 — CLI 인자

```
uv run python main.py write --topic "맥북 프로 M3 리뷰"
```

### 입력 2 — 스타일 가이드 (기존 파일)

**`data/style_guides/{category}.md`**
- Phase 1에서 생성된 카테고리별 스타일 가이드 Markdown 파일
- 해당 카테고리 파일이 없으면 스타일 가이드 없이 진행하고 경고 출력

### 출력

**`data/output/{YYYYMMDD}_{slug}_outline.json`**
```json
{
  "topic": "맥북 프로 M3 리뷰",
  "category": "review",
  "slug": "20260225_맥북프로M3리뷰",
  "created_at": "2026-02-25T10:00:00+09:00",
  "keywords": ["맥북 프로", "M3 칩", "애플 실리콘", "성능 테스트", "배터리"],
  "title_candidates": [
    "맥북 프로 M3 3개월 써본 솔직 후기",
    "M3 칩 맥북, 정말 그렇게 빠를까?",
    "개발자가 직접 쓴 맥북 프로 M3 리얼 리뷰"
  ],
  "style_guide_path": "data/style_guides/review.md",
  "outline": [
    {
      "section": 1,
      "title": "들어가며",
      "type": "opening",
      "description": "구매 계기와 첫 인상을 구체적 상황으로 시작",
      "estimated_chars": 300
    },
    {
      "section": 2,
      "title": "성능 테스트 결과",
      "type": "body",
      "description": "벤치마크 수치와 체감 속도 비교",
      "estimated_chars": 500
    },
    {
      "section": 3,
      "title": "배터리 & 발열",
      "type": "body",
      "description": "장시간 사용 시 배터리 소모와 발열 실측",
      "estimated_chars": 400
    },
    {
      "section": 4,
      "title": "아쉬운 점",
      "type": "body",
      "description": "단점과 실제 사용 불편 경험 솔직하게 서술",
      "estimated_chars": 300
    },
    {
      "section": 5,
      "title": "결론",
      "type": "closing",
      "description": "추천 대상과 구매 판단 기준 제시",
      "estimated_chars": 250
    }
  ]
}
```

- `slug`: 날짜(`YYYYMMDD`) + 주제 한글을 붙여쓰기(공백→제거, 특수문자→제거)
- `keywords`: LLM이 주제에서 추출한 SEO 핵심 키워드 (5개 내외)
- `title_candidates`: SEO 고려 제목 후보 3개 (스타일 가이드 문체 반영)
- `outline[].type`: `"opening"` | `"body"` | `"closing"`
- `outline[].estimated_chars`: 섹션별 목표 글자 수 (총합 1750자 이상 → 완성 글 2000자+ 목표)
- `style_guide_path`: 로드한 스타일 가이드 경로 (없으면 `null`)

---

## 4. 모듈 상세

### `agents/planner.py` — PlannerAgent

#### `plan(topic: str) -> Path | None`

최상위 진입 함수. 아래 단계를 순서대로 실행하고 outline.json 경로를 반환한다.

0. `topic.strip()` 빈 문자열이면 에러 로그 + `None` 반환 (early return)
1. `_extract_keywords(topic)` → keywords 리스트
2. `_infer_category(topic, keywords)` → category 문자열
3. `_load_style_guide(category)` → `(style_guide_text, style_guide_path)` 튜플
4. `_build_style_context(style_guide_text)` → 프롬프트용 컨텍스트 문자열
5. `_generate_titles(topic, keywords, style_guide_text)` → title_candidates 리스트
6. `_generate_outline(topic, keywords, style_guide_text)` → outline 리스트
7. `_save_outline(...)` → `Path | None`

실패 시 `None` 반환, 에러 로그 출력.

---

#### `_extract_keywords(topic: str) -> list[str]`

- LLM에 주제를 전달해 SEO 핵심 키워드 5개 내외를 추출한다.
- 프롬프트 설계:
  - 시스템: "키워드만 쉼표로 구분해 반환하라. 다른 설명 없이."
  - 유저: `f"주제: {topic}\n키워드 5개를 추출하라."`
- LLM 응답을 쉼표 기준으로 분리, 공백 제거 후 반환.
- 파싱 실패 시 `[topic]` 반환 (fallback).

---

#### `_infer_category(topic: str, keywords: list[str]) -> str`

- LLM에 주제와 키워드를 전달해 카테고리를 추론한다.
- 허용 목록(`CATEGORIES`)을 프롬프트에 명시해 반드시 그 중 하나를 선택하도록 유도.
- 프롬프트 설계:
  - 시스템: `f"다음 카테고리 중 하나만 반환하라: {', '.join(CATEGORIES)}. 다른 텍스트 없이."`
  - 유저: `f"주제: {topic}\n키워드: {', '.join(keywords)}"`
- LLM 응답을 소문자로 정규화 → `re.search(rf"\b{cat}\b", response)` 완전 단어 매칭으로 허용 목록 탐색.
- 허용 목록에 없으면 `"etc"` 반환 (fallback).

---

#### `_load_style_guide(category: str) -> tuple[str, Path | None]`

- `STYLE_GUIDES_DIR / f"{category}.md"` 파일을 읽어 `(내용 문자열, Path)` 튜플로 반환.
- 파일이 없으면 경고 로그 출력 후 `("", None)` 반환.

---

#### `_build_style_context(style_guide: str) -> str`

- 스타일 가이드 전체 텍스트에서 `## 문체`, `## 구조` 섹션만 추출해 LLM 프롬프트용 컨텍스트 문자열로 반환.
- 가이드가 빈 문자열이면 `""` 반환.
- 제목 생성·아웃라인 생성 프롬프트에 공통으로 사용해 토큰 낭비를 줄인다.

---

#### `_generate_titles(topic: str, keywords: list[str], style_guide: str) -> list[str]`

- LLM에 주제·키워드·스타일 가이드를 전달해 제목 후보 3개를 생성한다.
- 프롬프트 설계:
  - 스타일 가이드가 있으면 문체 항목(격식 수준, 자주 쓰는 표현)을 컨텍스트로 포함.
  - "SEO에 유리하고 클릭을 유도하는 블로그 제목 3개를 줄바꿈으로 구분해 반환하라."
- LLM 응답을 줄 단위로 분리, 번호·기호 제거 후 최대 3개 반환.
- 파싱 결과가 0개면 `[topic]` 반환 (fallback).

---

#### `_generate_outline(topic: str, keywords: list[str], style_guide: str) -> list[dict]`

- LLM에 주제·키워드·스타일 가이드를 전달해 섹션별 목차를 생성한다.
- 프롬프트 설계:
  - 스타일 가이드의 `구조(Structure)` 항목(도입부·본문·마무리 유형)을 컨텍스트로 포함.
  - 출력 형식: JSON 배열만 반환하도록 명시.
  ```
  다음 JSON 배열 형식으로만 응답하라:
  [
    {"section": 1, "title": "...", "type": "opening", "description": "...", "estimated_chars": 300},
    ...
  ]
  ```
  - 섹션 수: 5~7개, 총 estimated_chars 합계 1750 이상.
- LLM 응답에서 JSON 배열 파싱:
  1. 마크다운 코드블록(` ```json `) 제거
  2. `\[\s*\{[\s\S]*\}\s*\]` 패턴으로 `[{...}]` 형태의 JSON 배열만 추출 (대괄호 오매칭 방지)
- 파싱 실패 시 기본 아웃라인 반환 (fallback):
  ```python
  [
    {"section": 1, "title": "들어가며",  "type": "opening", "description": topic, "estimated_chars": 300},
    {"section": 2, "title": "본론 1",   "type": "body",    "description": topic, "estimated_chars": 400},
    {"section": 3, "title": "본론 2",   "type": "body",    "description": topic, "estimated_chars": 400},
    {"section": 4, "title": "본론 3",   "type": "body",    "description": topic, "estimated_chars": 400},
    {"section": 5, "title": "마무리",   "type": "closing", "description": topic, "estimated_chars": 300},
  ]
  ```

---

#### `_save_outline(topic: str, category: str, keywords: list[str], title_candidates: list[str], outline: list[dict], style_guide_path: Path | None) -> Path | None`

- `slug`: `datetime.now().strftime("%Y%m%d")` + 주제 한글 압축 (공백·특수문자 제거, 최대 20자). 압축 결과가 빈 문자열이면 `"untitled"` 대체.
- 저장 경로: `OUTPUT_DIR / f"{slug}_outline.json"`
- `OUTPUT_DIR` 없으면 자동 생성 (`mkdir`). 생성 실패 시 `OSError` 로그 후 `None` 반환.
- JSON 직렬화 후 UTF-8로 저장

---

#### 실패 처리

| 상황 | 처리 방식 |
|------|----------|
| 빈·공백 전용 주제 입력 | `plan()` 진입 시 early return → `None` 반환 |
| LLM 응답 타임아웃 | 에러 로그 출력 → fallback 또는 `None` 반환 |
| JSON 파싱 실패 | 경고 로그 + fallback 아웃라인 사용 |
| 스타일 가이드 없음 | 경고 출력 후 빈 문자열로 계속 진행 |
| OUTPUT_DIR 생성 실패 | OSError 로그 → `None` 반환 |

---

### `main.py` — `write` 서브커맨드 추가

```python
def cmd_write(topic: str) -> None:
    print(f"주제: {topic}")
    outline_path = plan(topic)
    if outline_path:
        print(f"아웃라인 생성 완료: {outline_path}")
    else:
        print("아웃라인 생성 실패")

# main() 내 subparsers에 추가
write_parser = subparsers.add_parser("write", help="주제를 입력해 블로그 아웃라인을 생성한다")
write_parser.add_argument("--topic", required=True, help="블로그 주제")
```

---

## 5. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── crawler.py
│   ├── parser.py
│   ├── analysis.py
│   ├── style_guide.py
│   └── planner.py          ← 주제 분석 · 아웃라인 생성 (신규)
├── data/
│   ├── input/
│   ├── raw_html/
│   ├── parsed_posts/
│   ├── analysis/
│   ├── style_guides/
│   └── output/             ← {slug}_outline.json 저장 (신규, .gitignore 적용)
├── utils/
│   ├── file_manager.py
│   ├── ollama_client.py
│   └── logger.py
├── config.py               ← OUTPUT_DIR 이미 정의됨 (추가 불필요)
├── main.py                 ← write 서브커맨드 + cmd_write() 추가
└── docs/dev/
    ├── _template.md
    ├── phase1-step1-2.md
    ├── phase1-step3.md
    ├── phase1-step5.md
    └── phase2-step2.md     ← 본 문서
```

---

## 7. 이후 변경 이력

### Phase 2 Step 2 구현 시 `main.py` 변경 (2026-02-26)

Step 2(`agents/writer.py`) 구현 완료 후 `cmd_write()`가 아래와 같이 확장됨.
원본(위 스니펫)은 Step 1 시점의 구현이며, 현재 코드는 아래와 같이 변경됨.

```python
# Step 2 이후 현재 코드 (main.py)
def cmd_write(topic: str) -> None:
    print(f"주제: {topic}\n")

    outline_path = plan(topic)
    if not outline_path:
        print("\n  [fail] 아웃라인 생성 실패 — 중단")
        sys.exit(1)

    print(f"\n  아웃라인 생성 완료: {outline_path}")

    draft_path = write(outline_path)     # ← Step 2에서 추가
    if draft_path:
        print(f"  초안 생성 완료: {draft_path}")
    else:
        print("  [fail] 초안 생성 실패")
        sys.exit(1)
```

**변경 요약**:
- `write(outline_path)` 호출 추가 (`agents/writer.py` import)
- 실패 시 `sys.exit(1)` 처리 통일
- 출력 메시지 들여쓰기 및 표현 통일

---

## 6. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| 기본 동작 | `uv run python main.py write --topic "제주 여행 3박4일 후기"` 실행 → `data/output/` 에 `_outline.json` 생성 확인 |
| 카테고리 추론 | 여행 주제 → `travel`, 기술 주제 → `tech` 등 올바른 카테고리 추론 확인 |
| 스타일 가이드 반영 | 해당 카테고리 가이드 존재 시 `style_guide_path` 필드에 경로 기록 확인 |
| 스타일 가이드 없는 경우 | 해당 카테고리 `.md` 파일 삭제 후 실행 → 경고 출력 후 `style_guide_path: null`로 정상 완료 확인 |
| 아웃라인 글자 수 | `outline[].estimated_chars` 합계 ≥ 1750 확인 |
| 제목 후보 | `title_candidates` 3개 생성 확인 |
| JSON 파싱 실패 fallback | LLM이 잘못된 형식 반환 시에도 기본 3섹션 아웃라인으로 저장 확인 |
| 파이프라인 연결 | `main.py write` 서브커맨드로 `plan()` 호출 후 반환 경로 출력 확인 |
