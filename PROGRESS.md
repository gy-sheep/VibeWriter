# VibeWriter 개발 진행 상황

> 세션 재시작 시 작업을 이어받기 위한 현재 상태 요약

**최종 업데이트**: 2026-02-25

---

## 현재 완료 상태

### Phase 1 Step 1~2: 데이터 입력 + 콘텐츠 수집 및 전처리 ✅

**구현된 모듈**:
- `config.py` — 경로·모델·카테고리 목록·크롤러 설정 (Path 기반)
- `utils/file_manager.py` — `read_urls()`, `mark_done()` (blog_urls.txt 읽기/쓰기)
- `agents/crawler.py` — httpx 크롤링, 재시도 1회, robots.txt 스킵, 네이버 블로그 iframe 처리
- `agents/parser.py` — BeautifulSoup4 본문 추출, 네이버 스마트에디터 선택자, 제목 정규화
- `main.py` — CLI 진입점 (`python main.py learn`)

**검증 완료**:
- 브런치, 네이버 블로그 크롤링 및 본문 추출 확인
- `# done` 처리, 실패 URL 스킵 동작 확인

---

## 다음 작업

### Phase 1 Step 3: 카테고리 분석

**목표**: `parsed_posts/`의 JSON을 읽어 카테고리 자동 분류

**구현할 모듈**:
- `utils/ollama_client.py` — Ollama LLM 래퍼
- `agents/analysis.py` — AnalysisAgent: 카테고리 분류 + 문체·어휘·구조 패턴 분석

**핵심 규칙**:
- 카테고리는 `config.py`의 `CATEGORIES` 목록에서만 선택
- 허용 목록 외 카테고리는 `etc`로 분류
- 분류 결과는 `data/analysis/{slug}.json`으로 저장

**참고 문서**: `docs/dev/phase1-step1-2.md`

---

## 프로젝트 구조 (현재)

```
VibeWriter/
├── agents/
│   ├── crawler.py       # 크롤링 (httpx, 네이버 iframe 처리)
│   └── parser.py        # 본문 추출 (BeautifulSoup4)
├── data/
│   ├── input/
│   │   └── blog_urls.txt
│   ├── raw_html/        # .gitignore
│   └── parsed_posts/    # .gitignore
├── utils/
│   └── file_manager.py  # URL 읽기/쓰기
├── config.py
├── main.py
└── docs/
    ├── dev/phase1-step1-2.md
    └── roadmap/DESIGN_SPEC.md
```

---

## 주요 결정 사항

| 항목 | 결정 | 이유 |
|------|------|------|
| URL 입력 파일 위치 | `data/input/blog_urls.txt` | 파이프라인 실행 중 변경(# done)되는 데이터 파일 |
| 카테고리 방식 | 허용 목록 기반 정규화 | 자유 분류 시 파일명 불일치 문제 발생 |
| 네이버 블로그 | iframe URL 재요청 | 메인 HTML에 본문 없음 (iframe 구조) |
| 스타일 가이드 저장 | 카테고리별 분리 파일 | WriterAgent가 필요한 카테고리만 LLM 컨텍스트에 로드 |

---

**상세 작업 이력**: `HISTORY.md` 참조
