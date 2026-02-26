# Phase 1 · Step 1~2 개발 기획

> **범위**: 데이터 입력 + 콘텐츠 수집 및 전처리
> **목표**: `blog_urls.txt`에서 URL을 읽어 크롤링 후 본문을 정제된 텍스트로 저장

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 1 | `blog_urls.txt` 읽기, 완료 URL 필터링, 처리 후 `# done` 처리 | `utils/file_manager.py` |
| Step 2 | URL 크롤링 (실패 시 재시도 1회) | `agents/crawler.py` |
| Step 2 | HTML에서 본문 추출, 노이즈 제거 | `agents/parser.py` |

---

## 2. 데이터 흐름

```
data/input/blog_urls.txt
        │
        ▼ (미처리 URL 필터링)
  [CrawlerAgent]
        │ 크롤링 성공 시
        ▼
  data/raw_html/{slug}.html
        │
        ▼
  [ParserAgent]
        │ 본문 추출·정제
        ▼
  data/parsed_posts/{slug}.json
        │
        ▼ (완료 후)
  blog_urls.txt 해당 URL에 # done 처리
```

---

## 3. 파일 명세

### 입력

**`data/input/blog_urls.txt`**
```
https://example.com/post-1
https://example.com/post-2
# done https://example.com/post-3   ← 재처리 스킵
```

### 출력

**`data/raw_html/{slug}.html`**
- `slug`: URL을 파일명으로 변환한 문자열 (예: `example-com-post-1.html`)
- 크롤링 원본 HTML 그대로 저장

**`data/parsed_posts/{slug}.json`**
```json
{
  "url": "https://example.com/post-1",
  "title": "글 제목",
  "content": "정제된 본문 텍스트...",
  "crawled_at": "2026-02-25T10:00:00"
}
```

---

## 4. 모듈 상세

### `utils/file_manager.py`
- `read_urls(path)` → 미처리 URL 리스트 반환 (`# done` 라인 제외)
- `mark_done(path, url)` → 해당 URL 앞에 `# done ` 접두어 추가

### `agents/crawler.py` — CrawlerAgent
- httpx로 URL GET 요청
- 실패 시 1회 재시도, 재시도 후 실패 시 해당 URL 스킵 후 로그 기록
- robots.txt 차단 URL 자동 스킵
- User-Agent 헤더 설정
- **네이버 블로그 특수 처리**: iframe 구조 감지 → iframe src URL로 재요청

### `agents/parser.py` — ParserAgent
- BeautifulSoup4로 HTML 파싱
- 본문 영역 선택자 우선순위:
  1. `.se-main-container` (네이버 스마트에디터)
  2. `#postViewArea` (네이버 구버전)
  3. `article`, `main`, `[class*="content"]` 등 일반 선택자
- 광고·메뉴·푸터·스크립트 태그 제거
- 제목 추출 우선순위: `.se-title-text` → `<h1>` → `<title>` (사이트명 접미사 자동 제거)
- 추출 결과를 JSON으로 저장

### `config.py`
```python
from pathlib import Path

BASE_DIR = Path(__file__).parent

# 경로 (Path 객체)
INPUT_DIR = BASE_DIR / "data/input"
RAW_HTML_DIR = BASE_DIR / "data/raw_html"
PARSED_POSTS_DIR = BASE_DIR / "data/parsed_posts"
BLOG_URLS_FILE = INPUT_DIR / "blog_urls.txt"

# LLM
OLLAMA_MODEL = "gemma3:27b"

# 허용 카테고리 목록 (Phase 1 Step 3에서 사용)
CATEGORIES = ["tech", "travel", "food", "lifestyle", "review", "etc"]

# 크롤러
CRAWL_RETRY = 1
CRAWL_DELAY = 1.0   # 초
CRAWL_TIMEOUT = 10.0  # 초
```

### `main.py`
```
python main.py learn
```
- `blog_urls.txt` 읽기 → CrawlerAgent → ParserAgent 순서로 파이프라인 실행
- Step 1~2 완료 후 완료 URL `# done` 처리

---

## 5. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── __init__.py
│   ├── crawler.py          ← URL 크롤링 (httpx, 재시도, robots.txt, 네이버 iframe 처리)
│   └── parser.py           ← HTML 본문 추출 및 JSON 저장 (BeautifulSoup4)
├── data/
│   ├── input/
│   │   └── blog_urls.txt   ← 학습할 URL 목록 (사용자 작성, 완료 시 # done 처리)
│   ├── raw_html/           ← 크롤링 원본 HTML (.gitignore 적용)
│   └── parsed_posts/       ← 정제된 본문 JSON (.gitignore 적용)
├── utils/
│   ├── __init__.py
│   └── file_manager.py     ← blog_urls.txt 읽기/쓰기 유틸 (read_urls, mark_done)
├── config.py               ← 경로·모델·카테고리·크롤러 설정 (Path 기반)
├── main.py                 ← CLI 진입점 (python main.py learn)
├── pyproject.toml
└── docs/
    ├── dev/
    │   └── phase1-step1-2.md   ← 본 문서
    ├── git/
    ├── prompt/
    └── roadmap/
```

> Phase 1에서 추가된 모듈: `agents/analysis.py`, `agents/style_guide.py`, `utils/ollama_client.py`, `utils/logger.py`
> 이후 단계에서 추가될 모듈: `utils/humanize.py`, `pipelines/learn_pipeline.py`

---

## 6. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| URL 읽기·필터링 | `# done` 처리된 URL이 출력 목록에서 제외되는지 확인 |
| 크롤링 결과 | `data/raw_html/` 에 `.html` 파일 생성 확인 |
| 파싱 결과 | `data/parsed_posts/` 에 `.json` 파일 생성 및 `content` 필드 확인 |
| done 처리 | 처리 완료 후 `blog_urls.txt` 해당 URL에 `# done` 접두어 확인 |
| 실패 처리 | 잘못된 URL 입력 시 스킵 후 다음 URL 진행 확인 |
