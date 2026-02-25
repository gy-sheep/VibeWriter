# Phase 1 · Step 5 개발 기획

> **범위**: 스타일 가이드 생성
> **목표**: `analysis/*.json`의 톤앤매너 데이터를 카테고리별로 집계해 `data/style_guides/{category}.md` 생성

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 5 | `analysis/*.json` 전체 순회 → 카테고리별 그룹핑 | `agents/style_guide.py` |
| Step 5 | `tone_and_manner` 필드 집계 (빈도·모드 기반) | `agents/style_guide.py` |
| Step 5 | 카테고리별 스타일 가이드 Markdown 생성 | `agents/style_guide.py` |
| Step 5 | 기존 가이드 존재 시 전체 재집계 후 덮어쓰기 업데이트 | `agents/style_guide.py` |
| Step 5 | `main.py` 파이프라인에 `generate_style_guides()` 연결 | `main.py` |

---

## 2. 데이터 흐름

```
data/analysis/{slug}.json  (tone_and_manner 포함, N개)
        │
        ▼ (카테고리별 그룹핑)
  [StyleGuideAgent]
        │ tone_and_manner 필드 집계
        │   - writing_style: formality/sentence_length/paragraph_structure → 최빈값(mode)
        │   - vocabulary: 배열 필드 → 빈도 기준 상위 N개 합산
        │   - structure: opening/body/closing_style → 최빈값(mode)
        ▼
  data/style_guides/{category}.md  (카테고리별 1개)
```

---

## 3. 파일 명세

### 입력

**`data/analysis/{slug}.json`** (Step 4 출력)
```json
{
  "slug": "example-com-post-1",
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "category": "tech",
  "analyzed_at": "2026-02-25T10:00:00+00:00",
  "tone_and_manner": {
    "writing_style": {
      "formality": "casual",
      "sentence_length": "short",
      "paragraph_structure": "mixed"
    },
    "vocabulary": {
      "frequent_expressions": ["그래서", "하지만", "결국"],
      "technical_terms": ["API", "배포", "CI/CD"],
      "avoid_expressions": []
    },
    "structure": {
      "opening_style": "question",
      "body_style": "step_by_step",
      "closing_style": "summary"
    }
  }
}
```

### 출력

**`data/style_guides/{category}.md`** — 예: `tech.md`

```markdown
# tech 스타일 가이드

> 분석 글 수: 5개 | 최종 업데이트: 2026-02-25

---

## 문체 (Writing Style)

| 항목 | 가이드 |
|------|--------|
| 격식 수준 | casual (반말/구어체) |
| 문장 길이 | short (짧은 문장 위주) |
| 단락 구성 | mixed (짧은 단락과 긴 단락 혼용) |

---

## 어휘 (Vocabulary)

### 자주 쓰는 표현 (빈도 순)
그래서, 하지만, 결국, 사실, 그런데

### 전문 용어
API, 배포, CI/CD, Docker, Git

### 피해야 할 표현
(없음)

---

## 구조 (Structure)

| 항목 | 가이드 |
|------|--------|
| 도입부 | question (질문으로 시작) |
| 본문 | step_by_step (단계별 설명) |
| 마무리 | summary (핵심 요약) |

---

## Humanize 정책

- 동일 단어 3회 이상 연속 사용 금지
- "또한", "그리고" 반복 패턴 탐지 후 다양한 접속사로 교체
- 짧은 문장과 긴 문장을 의도적으로 혼용해 리듬감 유지
- "물론입니다", "당연히", "매우 중요합니다" 등 AI 과잉 표현 제거
- 구체적 경험·상황·감정을 최소 1회 이상 포함
- 과도한 1/2/3 단계식 구조화 지양, 자연스러운 서술 흐름 유지
```

- `분석 글 수`: 해당 카테고리 analysis 파일 중 `tone_and_manner` 필드가 있는 파일 수
- 어휘 배열: 전체 파일의 배열 값을 합산 후 등장 횟수 기준 내림차순 정렬, 상위 15개
- 단일값 필드(formality 등): 전체 파일에서 가장 많이 등장한 값(최빈값, mode)

---

## 4. 모듈 상세

### `agents/style_guide.py` — StyleGuideAgent

#### `generate_style_guides() -> list[Path]`

- `ANALYSIS_DIR`의 모든 `.json` 파일을 순회한다
- `tone_and_manner` 필드가 없는 파일은 경고 출력 후 스킵한다
- `category` 값으로 그룹핑, 카테고리별 `_aggregate()` 호출
- 생성된 가이드 파일 경로 목록 반환

#### `_aggregate(category: str, files: list[dict]) -> dict`

카테고리에 속한 분석 데이터를 집계한다.

| 필드 | 집계 방식 |
|------|----------|
| `formality` | 최빈값 (동률 시 첫 번째) |
| `sentence_length` | 최빈값 |
| `paragraph_structure` | 최빈값 |
| `frequent_expressions` | 전체 항목 합산 → 빈도 내림차순 → 상위 15개 |
| `technical_terms` | 전체 항목 합산 → 빈도 내림차순 → 상위 15개 |
| `avoid_expressions` | 전체 항목 합산 → 중복 제거 (순서 무관) |
| `opening_style` | 최빈값 |
| `body_style` | 최빈값 |
| `closing_style` | 최빈값 |

#### `_render_markdown(category: str, agg: dict, count: int) -> str`

집계 결과를 Markdown 문자열로 렌더링한다.

- humanize 정책 섹션은 DESIGN_SPEC.md의 핵심 정책 7가지를 고정 텍스트로 포함
- 날짜는 `datetime.now()` 기준 `YYYY-MM-DD` 형식

#### `_write_guide(category: str, content: str) -> Path`

- `STYLE_GUIDES_DIR / f"{category}.md"` 경로에 저장
- 디렉터리 없으면 자동 생성 (`mkdir(parents=True, exist_ok=True)`)
- 항상 전체 재집계 결과로 파일을 갱신 (소스는 analysis 파일이므로 재생성이 곧 병합)

#### 실패 처리

- analysis 파일 읽기 실패 → 해당 파일 스킵, 에러 출력 후 계속
- 카테고리별 유효 파일이 0개 → 가이드 파일 미생성, 경고 출력

---

## 5. 설정 추가 (`config.py`)

```python
STYLE_GUIDES_DIR = DATA_DIR / "style_guides"
VOCAB_TOP_N = 15  # 어휘 상위 N개 추출
```

---

## 6. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── crawler.py
│   ├── parser.py
│   ├── analysis.py
│   └── style_guide.py      ← 스타일 가이드 생성 (신규)
├── data/
│   ├── input/
│   ├── raw_html/
│   ├── parsed_posts/
│   ├── analysis/
│   └── style_guides/       ← {category}.md 저장 (신규, .gitignore 적용)
├── utils/
│   ├── file_manager.py
│   └── ollama_client.py
├── config.py               ← STYLE_GUIDES_DIR, VOCAB_TOP_N 추가
├── main.py                 ← generate_style_guides() 파이프라인 연결
└── docs/dev/
    ├── _template.md
    ├── phase1-step1-2.md
    ├── phase1-step3.md
    └── phase1-step5.md     ← 본 문서
```

---

## 7. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| 가이드 파일 생성 | `python main.py learn` 실행 후 `data/style_guides/` 디렉터리에 `{category}.md` 존재 확인 |
| 카테고리 분리 | 복수 카테고리 URL 학습 후 카테고리별 파일이 각각 생성되는지 확인 |
| 집계 정확성 | 동일 카테고리 파일 2개 이상일 때 `frequent_expressions`가 합산되는지 확인 |
| 재실행 병합 | 새 URL 추가 학습 후 재실행 시 기존 가이드가 최신 데이터로 갱신되는지 확인 |
| tone_and_manner 누락 스킵 | `tone_and_manner` 없는 파일 포함 시 해당 파일만 스킵, 나머지 정상 처리 확인 |
| humanize 섹션 | 생성된 `.md` 파일에 humanize 정책 항목이 포함되어 있는지 확인 |
| 파이프라인 연결 | `python main.py learn` 실행 → Step 4 완료 후 Step 5 자동 실행 확인 |
