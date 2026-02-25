# Phase 1 · Step 4 개발 기획

> **범위**: 톤앤매너 분석
> **목표**: `analysis/{slug}.json`을 읽어 LLM으로 문체·어휘·구조 패턴을 분석하고 동일 파일에 톤앤매너 필드 추가

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 4 | `analysis/*.json` 순회 → 원본 본문 읽어 톤앤매너 분석 | `agents/analysis.py` |
| Step 4 | 문체·어휘·구조 패턴 LLM 분석 → 기존 파일에 병합 | `agents/analysis.py` |
| Step 4 | 파싱 실패 시 기본값 fallback, 종료 금지 | `agents/analysis.py` |

---

## 2. 데이터 흐름

```
data/analysis/{slug}.json (Step 3 출력)
        │
        ▼ (전체 파일 순회)
  [AnalysisAgent]
        │ 해당 slug의 parsed_posts/*.json 읽기
        │ LLM에 톤앤매너 분석 요청
        ▼
  JSON 응답 파싱
        │ 파싱 실패 시 기본값 사용
        ▼
  기존 analysis/{slug}.json에 톤앤매너 필드 병합
```

---

## 3. 파일 명세

### 입력

**`data/analysis/{slug}.json`** (Step 3 출력)
```json
{
  "slug": "example-com-post-1",
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "category": "tech",
  "analyzed_at": "2026-02-25T10:00:00"
}
```

**`data/parsed_posts/{slug}.json`** (Step 2 출력, 본문 참조용)
```json
{
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "content": "정제된 본문 텍스트...",
  "crawled_at": "2026-02-25T10:00:00"
}
```

### 출력

**`data/analysis/{slug}.json`** (톤앤매너 필드 추가)
```json
{
  "slug": "example-com-post-1",
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "category": "tech",
  "analyzed_at": "2026-02-25T10:00:00",
  "tone_and_manner": {
    "writing_style": {
      "formality": "casual",
      "sentence_length": "medium",
      "paragraph_structure": "short_paragraphs"
    },
    "vocabulary": {
      "frequent_expressions": ["그래서", "사실", "결국"],
      "technical_terms": ["API", "프레임워크", "디버깅"],
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

- `tone_and_manner.writing_style.formality`: `"formal"` (경어) / `"casual"` (반말)
- `tone_and_manner.writing_style.sentence_length`: `"short"` / `"medium"` / `"long"`
- `tone_and_manner.writing_style.paragraph_structure`: `"short_paragraphs"` / `"long_paragraphs"` / `"mixed"`
- `tone_and_manner.vocabulary.frequent_expressions`: 자주 사용하는 접속사·부사 등 (최대 10개)
- `tone_and_manner.vocabulary.technical_terms`: 전문 용어 또는 특정 분야 단어 (최대 10개)
- `tone_and_manner.structure.opening_style`: `"question"` (질문) / `"story"` (스토리텔링) / `"direct"` (직접 설명)
- `tone_and_manner.structure.body_style`: `"step_by_step"` (단계별) / `"list"` (리스트형) / `"narrative"` (서술형)
- `tone_and_manner.structure.closing_style`: `"summary"` (요약) / `"call_to_action"` (행동 유도) / `"question"` (질문)

---

## 4. 모듈 상세

### `agents/analysis.py` — AnalysisAgent 확장

**톤앤매너 분석 함수 추가**

- `analyze_tone_and_manner(content: str) -> dict`
  - LLM으로 문체·어휘·구조 패턴 분석
  - 프롬프트에 JSON 응답 형식 명시
  - 응답 파싱: `json.loads()` 우선 시도, 실패 시 기본값 반환
  - 기본값:
    ```python
    {
        "writing_style": {
            "formality": "casual",
            "sentence_length": "medium",
            "paragraph_structure": "mixed"
        },
        "vocabulary": {
            "frequent_expressions": [],
            "technical_terms": [],
            "avoid_expressions": []
        },
        "structure": {
            "opening_style": "direct",
            "body_style": "narrative",
            "closing_style": "summary"
        }
    }
    ```

**톤앤매너 분석 프롬프트 설계**

```
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
   - frequent_expressions: 자주 사용하는 접속사·부사 (최대 10개)
   - technical_terms: 전문 용어 또는 특정 분야 단어 (최대 10개)
   - avoid_expressions: 사용하지 않는 표현 (있다면)

3. structure:
   - opening_style: "question" (질문 시작), "story" (스토리텔링), "direct" (직접 설명)
   - body_style: "step_by_step" (단계별), "list" (리스트형), "narrative" (서술형)
   - closing_style: "summary" (요약), "call_to_action" (행동 유도), "question" (질문)

반드시 아래 JSON 형식으로만 응답하세요:
{
  "writing_style": {...},
  "vocabulary": {...},
  "structure": {...}
}
```

**파일 업데이트 로직**

- `data/analysis/{slug}.json`을 읽어서 `tone_and_manner` 필드가 이미 있으면 스킵
- 없으면 `data/parsed_posts/{slug}.json`에서 본문(`content`) 읽기
- `analyze_tone_and_manner(content)` 호출
- 반환된 톤앤매너 데이터를 기존 JSON에 병합 후 저장

---

## 5. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── __init__.py
│   ├── crawler.py
│   ├── parser.py
│   └── analysis.py         ← 톤앤매너 분석 함수 추가 (수정)
├── data/
│   ├── input/
│   ├── raw_html/
│   ├── parsed_posts/       ← 본문 참조용
│   └── analysis/           ← {slug}.json에 tone_and_manner 필드 추가
├── utils/
│   ├── __init__.py
│   ├── file_manager.py
│   └── ollama_client.py
├── config.py
├── main.py
└── docs/dev/
    ├── _template.md
    ├── phase1-step1-2.md
    ├── phase1-step3.md
    └── phase1-step4.md     ← 본 문서
```

---

## 6. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| 톤앤매너 필드 추가 | `data/analysis/*.json`에 `tone_and_manner` 필드 존재 확인 |
| formality 분석 | 경어 글 → `"formal"`, 반말 글 → `"casual"` 확인 |
| frequent_expressions | 실제 본문에서 자주 등장하는 표현이 포함되었는지 확인 |
| 파싱 실패 fallback | 비정상 LLM 응답 시에도 기본값으로 저장되고 종료되지 않는지 확인 |
| 중복 방지 | 이미 `tone_and_manner` 필드가 있는 파일은 재분석하지 않음 확인 |
| 파이프라인 연결 | `python main.py learn` 실행 → Step 3 완료 후 Step 4 자동 실행 확인 |
