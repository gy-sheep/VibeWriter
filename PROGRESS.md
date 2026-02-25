# VibeWriter 개발 진행 상황

> 세션 재시작 시 작업을 이어받기 위한 현재 상태 요약

**최종 업데이트**: 2026-02-25

---

## 현재 완료 상태

### Phase 1 Step 1~4 ✅

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

### Phase 1 Step 3: 카테고리 분석 ✅

**구현된 모듈**:
- `utils/ollama_client.py` — `generate(prompt, model) -> str` / Ollama REST API 래퍼 (llama3.1:8b)
- `agents/analysis.py` — LLM 카테고리 분류, etc fallback, 중복 스킵
- `main.py` — parse 후 analyze() 호출 파이프라인 연결

**검증 완료**:
- travel / tech / lifestyle 카테고리 정확 분류 확인
- 중복 파일 스킵 동작 확인

---

## 다음 작업

### Phase 1 Step 4: 톤앤매너 분석 ✅

**구현된 모듈**:
- `agents/analysis.py` — `add_tone_and_manner()`: LLM 문체·어휘·구조 분석, 중복 스킵, fallback
- `main.py` — `analyze()` 완료 후 `add_tone_and_manner()` 파이프라인 연결

**검증 완료**:
- 7개 파일 `tone_and_manner` 필드 추가 성공
- 중복 스킵 동작 확인

---

## 다음 작업

### Phase 1 Step 5: 스타일 가이드 생성

**현재 브랜치**: `feat/phase1/tone-analysis` (Step 5 작업 전 새 브랜치 생성 권장)

**목표**: `analysis/*.json`의 톤앤매너 데이터를 카테고리별로 집계해 `style_guides/{category}.md` 생성

**구현할 모듈**:
- `agents/style_guide.py` (신규) — 카테고리별 analysis 파일 집계 → 스타일 가이드 Markdown 생성

**핵심 규칙**:
- 동일 카테고리 파일이 여러 개면 합산·평균·빈도 기준으로 집계
- 기존 가이드 존재 시 병합 업데이트 (덮어쓰기 금지)
- humanize 정책 항목 필수 포함

**상세 설계**: `docs/dev/phase1-step5.md` (미작성 — 개발 전 작성 필요)

---

## 프로젝트 구조 (현재)

```
VibeWriter/
├── agents/
│   ├── crawler.py       # 크롤링 (httpx, 네이버 iframe 처리)
│   ├── parser.py        # 본문 추출 (BeautifulSoup4)
│   └── analysis.py      # 카테고리 분류 (LLM, etc fallback)
├── data/
│   ├── input/
│   │   └── blog_urls.txt
│   ├── raw_html/        # .gitignore
│   ├── parsed_posts/    # .gitignore
│   └── analysis/        # .gitignore
├── utils/
│   ├── file_manager.py  # URL 읽기/쓰기
│   └── ollama_client.py # Ollama REST API 래퍼
├── config.py
├── main.py
└── docs/
    ├── dev/
    │   ├── _template.md       # step 문서 작성 포맷
    │   ├── phase1-step1-2.md
    │   └── phase1-step3.md
    └── roadmap/DESIGN_SPEC.md
```

---

## 주요 결정 사항

| 항목 | 결정 | 이유 |
|------|------|------|
| 패키지 관리 | uv 사용 | pyproject.toml (PEP 621) + hatchling 빌드, 빠른 의존성 해결 |
| URL 입력 파일 위치 | `data/input/blog_urls.txt` | 파이프라인 실행 중 변경(# done)되는 데이터 파일 |
| 카테고리 방식 | 허용 목록 기반 정규화 | 자유 분류 시 파일명 불일치 문제 발생 |
| 네이버 블로그 | iframe URL 재요청 | 메인 HTML에 본문 없음 (iframe 구조) |
| 스타일 가이드 저장 | 카테고리별 분리 파일 | WriterAgent가 필요한 카테고리만 LLM 컨텍스트에 로드 |

---

**상세 작업 이력**: `HISTORY.md` 참조
