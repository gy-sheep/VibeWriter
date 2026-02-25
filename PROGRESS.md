# VibeWriter 개발 진행 상황

> 세션 재시작 시 작업을 이어받기 위한 현재 상태 요약

**최종 업데이트**: 2026-02-26 (Phase 2 완료)

---

## 현재 완료 상태

### Phase 1 전체 ✅

### Phase 1 Step 1~2: 데이터 입력 + 콘텐츠 수집 및 전처리 ✅

**구현된 모듈**:
- `config.py` — 경로·모델·카테고리 목록·크롤러 설정 (Path 기반)
- `utils/file_manager.py` — `read_urls()`, `mark_done()` (blog_urls.txt 읽기/쓰기)
- `agents/crawler.py` — httpx 크롤링, 재시도 1회, robots.txt 스킵, 네이버 블로그 iframe 처리
- `agents/parser.py` — BeautifulSoup4 본문 추출, 네이버 스마트에디터 선택자, 제목 정규화
- `main.py` — CLI 진입점 (`python main.py learn`)

### Phase 1 Step 3: 카테고리 분석 ✅

**구현된 모듈**:
- `utils/ollama_client.py` — `generate(prompt, model) -> str` / Ollama REST API 래퍼 (llama3.1:8b)
- `agents/analysis.py` — LLM 카테고리 분류, etc fallback, 중복 스킵

### Phase 1 Step 4: 톤앤매너 분석 ✅

**구현된 모듈**:
- `agents/analysis.py` — `add_tone_and_manner()`: LLM 문체·어휘·구조 분석, 중복 스킵, fallback

### Phase 1 Step 5: 스타일 가이드 생성 ✅

**구현된 모듈**:
- `agents/style_guide.py` — 카테고리별 analysis 파일 집계 → `data/style_guides/{category}.md` 생성
- `config.py` — `VOCAB_TOP_N = 15` 추가

**검증 완료**:
- 12개 URL 학습 → lifestyle / review / tech / travel 4개 스타일 가이드 생성 성공
- 중복 URL 재실행 시 skip 처리 확인
- `data/style_guides/{category}.md` 파일 생성 확인

### 전체 품질 개선 ✅

**구현된 모듈**:
- `utils/logger.py` — 신규: 모듈별 logger (콘솔 WARNING+, 파일 DEBUG+, `logs/vibewriter.log`)
- 전 모듈 예외 처리 강화: IOError / JSONDecodeError / TimeoutException / HTTPStatusError 등

### Phase 2 Step 1: 주제 분석 및 목차 구성 ✅

**구현된 모듈**:
- `agents/planner.py` — 키워드 추출, 카테고리 추론(완전 단어 매칭), 스타일 가이드 로드, 아웃라인 생성
  - 빈 주제 early return, `mkdir` OSError 처리, slug `untitled` fallback 등 방어 코드 완비
- `main.py` — `write --topic` 서브커맨드 추가

**출력**: `data/output/{YYYYMMDD}_{slug}_outline.json`

### Phase 2 Step 3: 품질 검증 및 humanize ✅

**구현된 모듈**:
- `utils/humanize.py` (신규) — 규칙 기반 텍스트 정제
  - `remove_foreign_chars()`: 한자·키릴·아랍 등 외국 문자 제거
  - `remove_ai_phrases()`: AI 과잉 표현 regex 제거
  - `diversify_conjunctions()`: 반복 접속사 탐지·교체
  - `detect_repetitive_phrases()`: 2어절 bi-gram 반복 어구 탐지
- `agents/quality.py` (신규) — 품질 검증 및 LLM polish
  - `_check_style()`: 문장 길이 단조로움·AI 표현 잔존·반복 접속사·반복 어구 4항목 체크
  - `_polish()`: 섹션별 LLM 다듬기 (맞춤법·반복 표현·문장 리듬), 길이 이탈 ±40% fallback
  - `quality_check()`: 최상위 진입점, final.md 저장
- `agents/writer.py` — `_SYSTEM_PROMPT` 강화
  - 가짜 경험(타인 이야기) 생성 금지
  - 외국 문자 혼입 금지
  - 반복 표현 금지
  - 한국어 맞춤법·문법 정확성 요구
- `main.py` — `write` 파이프라인에 `quality_check()` 연결

**출력**: `data/output/{YYYYMMDD}_{slug}_final.md`

**검증 완료**:
- 제주 여행 3박4일 후기 → final.md 생성, 한자·비표준 라틴·키릴 문자 제거 확인
- 반복 어구 탐지("이전 모델보다", "CPU와 GPU가") 정상 동작 확인
- LLM 길이 이탈 fallback 정상 동작 확인
- 전체 파이프라인 단일 명령어로 동작 확인

### Phase 2 Step 2: 본문 생성 ✅

**구현된 모듈**:
- `agents/writer.py` (신규) — 아웃라인 로드, 스타일 가이드 기반 섹션별 LLM 본문 생성, draft.md 저장
  - `_load_outline`: JSON 파싱 + 필수 필드 검증, fallback
  - `_load_style_guide`: OSError fallback (빈 문자열로 계속 진행)
  - `_build_style_context`: 문체·어휘·구조 섹션 추출 (planner와 달리 어휘 포함)
  - `_generate_section`: prev_context(최대 200자), opening/closing type_hint 삽입, description fallback
  - `_assemble_draft`: title_candidates[0] 제목, 메타 주석, ## 섹션 조합
  - `_save_draft`: OSError 처리
- `main.py` — `cmd_write()`에 `write(outline_path)` 연결

**출력**: `data/output/{YYYYMMDD}_{slug}_draft.md`

**검증 완료**:
- 제주 여행 3박4일 후기 → 2876자, 6개 섹션 draft.md 생성 성공
- outline.json + draft.md 파이프라인 단일 명령어로 동작 확인

---

## 다음 작업

### Phase 3: 웹 인터페이스 구축

**목표**: 브라우저에서 학습·생성 기능을 사용할 수 있는 로컬 웹 UI

**구현할 내용**:
- `web/main.py` — FastAPI 앱 진입점
- `web/routers/` — learn / write API 라우터
- `web/templates/` — Jinja2 HTML 템플릿
- WebSocket 또는 SSE로 진행 상태 실시간 표시
- 생성된 글 Markdown 렌더링 화면

**실행**: `uv run uvicorn web.main:app --reload`

**상세 설계**: `docs/dev/phase3-step1.md` (개발 전 작성 필요)

---

## 프로젝트 구조 (현재)

```
VibeWriter/
├── agents/
│   ├── crawler.py       # 크롤링 (httpx, 네이버 iframe 처리)
│   ├── parser.py        # 본문 추출 (BeautifulSoup4)
│   ├── analysis.py      # 카테고리 분류 + 톤앤매너 분석 (LLM)
│   ├── style_guide.py   # 스타일 가이드 생성 (카테고리별 집계)
│   ├── planner.py       # 주제 분석 + 아웃라인 생성 (LLM)
│   ├── writer.py        # 섹션별 본문 생성 · draft.md 저장 (LLM)
│   └── quality.py       # 스타일 체크 + LLM polish · final.md 저장
├── data/
│   ├── input/
│   │   └── blog_urls.txt
│   ├── raw_html/        # .gitignore
│   ├── parsed_posts/    # .gitignore
│   ├── analysis/        # .gitignore
│   ├── style_guides/    # {category}.md
│   └── output/          # {YYYYMMDD}_{slug}_outline.json (.gitignore)
├── utils/
│   ├── file_manager.py  # URL 읽기/쓰기
│   ├── ollama_client.py # Ollama REST API 래퍼
│   ├── logger.py        # 로깅 유틸 (콘솔+파일)
│   └── humanize.py      # 규칙 기반 AI 표현 제거·외국 문자 제거·접속사 다양화
├── logs/                # .gitignore
├── config.py
├── main.py
└── docs/
    ├── dev/
    │   ├── _template.md
    │   ├── phase1-step1-2.md
    │   ├── phase1-step3.md
    │   ├── phase1-step5.md
    │   └── phase2-step1.md
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
| 어휘 집계 상위 N | `VOCAB_TOP_N = 15` | 글 수 증가 시 노이즈 방지, config에서 조정 가능 |
| 로깅 | 콘솔 WARNING+ / 파일 DEBUG+ | 평시 출력 최소화, 문제 발생 시 로그 파일로 상세 추적 |
| 카테고리 매칭 | `re.search(\b{cat}\b)` 완전 단어 매칭 | 부분 문자열 오탐 방지 (예: "tech review" → "tech" 오매칭) |

---

**상세 작업 이력**: `HISTORY.md` 참조
