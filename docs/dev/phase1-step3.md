# Phase 1 · Step 3 개발 기획

> **범위**: 카테고리 분석
> **목표**: `parsed_posts/*.json`을 읽어 LLM으로 카테고리를 분류하고 `analysis/{slug}.json`으로 저장

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 3 | `parsed_posts/*.json` 순회 → LLM 카테고리 분류 | `agents/analysis.py` |
| Step 3 | 카테고리 허용 목록 검증, 허용 외 → `etc` fallback | `agents/analysis.py` |
| Step 3 | Ollama REST API 호출 래퍼 | `utils/ollama_client.py` |

---

## 2. 데이터 흐름

```
data/parsed_posts/{slug}.json
        │
        ▼ (전체 파일 순회)
  [AnalysisAgent]
        │ LLM에 카테고리 분류 요청
        ▼
  CATEGORIES 허용 목록 검증
        │ 허용 목록 외 또는 파싱 실패 → "etc"
        ▼
  data/analysis/{slug}.json
```

---

## 3. 파일 명세

### 입력

**`data/parsed_posts/{slug}.json`** (Step 2 출력)
```json
{
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "content": "정제된 본문 텍스트...",
  "crawled_at": "2026-02-25T10:00:00"
}
```

### 출력

**`data/analysis/{slug}.json`**
```json
{
  "slug": "example-com-post-1",
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "category": "tech",
  "analyzed_at": "2026-02-25T10:00:00"
}
```

- `slug`: URL에서 scheme 제거 → `/`, `.`, `?`, `=` 등 특수문자를 `-`로 치환 → 소문자
- `category`: `config.py`의 `CATEGORIES` 목록 중 하나 (`"etc"` 포함)

---

## 4. 모듈 상세

### `utils/ollama_client.py`

- `generate(prompt: str, model: str = OLLAMA_MODEL) -> str`
- `POST http://localhost:11434/api/generate` 호출 (httpx 동기)
- 요청 바디: `{"model": "...", "prompt": "...", "stream": false}`
- 응답에서 `response` 필드 추출 후 반환
- 예외 처리:
  - `ConnectError` → `SystemExit` (Ollama 미실행 시 명확한 메시지 출력)
  - `TimeoutException` → `RuntimeError` (응답 시간 초과)
  - `HTTPStatusError` → `RuntimeError` (HTTP 오류 상태 코드)
  - `response` 필드 없음 → `ValueError`
- 모든 요청/응답은 `utils/logger.py`로 DEBUG 레벨 기록

### `agents/analysis.py` — AnalysisAgent

**카테고리 분류 프롬프트 설계**

```
다음 블로그 글을 읽고, 아래 카테고리 중 정확히 하나를 선택하세요.
허용 카테고리: tech, travel, food, lifestyle, review, etc

목록에 없는 카테고리는 절대 사용하지 말고 "etc"를 선택하세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{"category": "tech"}

제목: {title}
본문 (일부): {content[:800]}
```

- LLM 응답에서 `json.loads()` 우선 파싱, 실패 시 정규식으로 카테고리 값 추출
- 추출 실패 또는 허용 목록 외 값 → `"etc"` fallback
- `data/analysis/{slug}.json`이 이미 존재하면 스킵 (중복 방지)

---

## 5. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── __init__.py
│   ├── crawler.py
│   ├── parser.py
│   └── analysis.py         ← 카테고리 분류 (신규)
├── data/
│   ├── input/
│   ├── raw_html/
│   ├── parsed_posts/
│   └── analysis/           ← {slug}.json 저장 (신규, .gitignore 적용)
├── utils/
│   ├── __init__.py
│   ├── file_manager.py
│   └── ollama_client.py    ← Ollama REST API 래퍼 (신규)
├── config.py
├── main.py
└── docs/dev/
    ├── _template.md
    ├── phase1-step1-2.md
    └── phase1-step3.md     ← 본 문서
```

---

## 6. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| Ollama 연결 | `generate("안녕")` 직접 호출 → 응답 문자열 출력 확인 |
| 카테고리 분류 | `data/analysis/*.json`의 `category` 필드가 `CATEGORIES` 목록 내 값인지 확인 |
| etc fallback | 경계 케이스(잡담·생활 글 등)가 `"etc"`로 분류되는지 확인 |
| 중복 방지 | 동일 slug 재실행 시 기존 파일 유지, LLM 재호출 없음 확인 |
| 파이프라인 연결 | `python main.py learn` 실행 → Step 2 완료 후 Step 3 자동 실행 확인 |
