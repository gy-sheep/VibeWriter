# VibeWriter — 기획 명세서

> 카테고리별 블로그 글의 톤앤매너를 분석·학습하고,
> 사용자가 입력한 주제에 대해 일관된 스타일의 블로그 글을 자동 생성한다.

---

## 1. 개요

### 1.1 프로젝트 목표
블로그 운영의 전체 프로세스를 AI 기반 멀티 에이전트로 자동화한다.

- 기존 블로그 글을 학습해 **나만의 글쓰기 스타일**을 추출한다
- 주제를 입력하면 학습된 스타일로 **일관된 블로그 글**을 자동 생성한다
- AI 생성 티가 나지 않도록 **humanize 정책**을 전 과정에 적용한다

### 1.2 실행 환경 및 운영 방식

| 모드 | 설명 |
|------|------|
| CLI 모드 | 터미널에서 Claude Code 기반 즉시 실행 |
| Web 모드 | 로컬 서버를 통해 브라우저에서 주제 입력 및 결과 출력 |

---

## 2. 기술 스택 및 개발 원칙

### 2.1 기술 스택

| 분류 | 기술 | 비고 |
|------|------|------|
| Language | Python 3.11+ | |
| LLM Runtime | Ollama | 로컬 모델 (예: Mistral, Llama 3) |
| 팩트 수집 LLM | Gemini API 무료 티어 | ResearchAgent 전용, 유료 전환 금지 |
| Web Framework | FastAPI | 로컬 서버용 |
| CLI 실행 | Claude Code CLI | 개발·테스트용 |
| 크롤링 | BeautifulSoup4 + httpx | 정적 페이지 우선 |
| 데이터 저장 | 로컬 파일 (JSON / Markdown) | DB 없이 파일 기반 |

### 2.2 개발 원칙

- **생성·분석은 로컬 LLM만 사용** — 외부 유료 API 사용 금지
- **팩트 수집은 Gemini API 무료 티어 허용** — ResearchAgent 전용, 유료 전환 금지
- **로컬 실행 전제** — 인터넷 없이도 핵심 기능 동작
- **MVP 우선** — 각 Phase 최소 기능 완성 후 다음 Phase로 진행
- **모듈 단위 설계** — 각 기능을 독립 Agent로 분리
- **humanize 필수** — 모든 생성 결과에 자연스러운 문체 정책 적용

---

## 3. 시스템 아키텍처

### 3.1 멀티 에이전트 구조

```
[사용자 입력]
      │
      ▼
┌─────────────────────┐
│   OrchestratorAgent │  ← 전체 파이프라인 조율
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
[학습 파이프라인]   [생성 파이프라인]
    │                   │
    ├─ CrawlerAgent      ├─ ResearchAgent  ← Gemini + 로컬 LLM
    ├─ ParserAgent       ├─ PlannerAgent
    ├─ AnalysisAgent     ├─ WriterAgent
    └─ StyleGuideAgent   └─ QualityAgent
```

### 3.2 Agent 역할 정의

| Agent | 역할 |
|-------|------|
| **OrchestratorAgent** | 파이프라인 흐름 제어, Agent 간 데이터 전달 |
| **CrawlerAgent** | URL 크롤링 및 HTML 수집 |
| **ParserAgent** | 본문 추출, 노이즈 제거, 정제 |
| **AnalysisAgent** | 카테고리 분류(허용 목록 기반 정규화), 문체·어휘·구조 패턴 분석 |
| **StyleGuideAgent** | 카테고리별 스타일 가이드 생성 및 업데이트 |
| **ResearchAgent** | 주제 관련 팩트 수집·요약 — 로컬 LLM이 쿼리 생성, Gemini API가 응답, 로컬 LLM이 요약 |
| **PlannerAgent** | 주제 분석, 목차 구성, 키워드 선정 (팩트 컨텍스트 활용) |
| **WriterAgent** | 스타일 가이드 + 팩트 컨텍스트 기반 본문 생성 |
| **QualityAgent** | 스타일 일관성 검증, humanize 처리 |

### 3.3 데이터 흐름

```
urls.txt
   │
   ▼
CrawlerAgent ──→ raw_html/
   │
   ▼
ParserAgent ──→ parsed_posts/
   │
   ▼
AnalysisAgent ──→ analysis/
   │
   ▼
StyleGuideAgent ──→ style_guides/
                         │
[주제 입력] ─────────────┘
   │
   ▼
ResearchAgent ──→ output/{slug}_research.json   ← Gemini + 로컬 LLM
   │
   ▼
PlannerAgent ──→ output/{slug}_outline.json
   │
   ▼
WriterAgent ──→ output/{slug}_draft.md
   │
   ▼
QualityAgent ──→ output/{slug}_final.md
```

---

## 4. 디렉터리 구조

```
VibeWriter/
├── agents/                   # Agent 구현체
│   ├── orchestrator.py
│   ├── crawler.py
│   ├── parser.py
│   ├── analysis.py
│   ├── style_guide.py
│   ├── researcher.py         # 팩트 수집 (Gemini API + 로컬 LLM)
│   ├── planner.py
│   ├── writer.py
│   └── quality.py
├── pipelines/                # 파이프라인 조합
│   ├── learn_pipeline.py     # 학습 파이프라인
│   └── write_pipeline.py     # 생성 파이프라인
├── data/
│   ├── input/
│   │   └── blog_urls.txt     # 학습할 블로그 URL 목록
│   ├── raw_html/             # 크롤링 원본
│   ├── parsed_posts/         # 정제된 본문
│   ├── analysis/             # 분석 결과
│   ├── style_guides/         # 카테고리별 스타일 가이드
│   └── output/               # 최종 생성 글
├── web/                      # FastAPI 웹 인터페이스 (Phase 3)
│   ├── main.py
│   ├── routers/
│   └── templates/
├── utils/
│   ├── ollama_client.py      # Ollama LLM 래퍼
│   ├── file_manager.py       # 파일 읽기/쓰기 유틸
│   ├── logger.py             # 로깅 유틸 (콘솔 WARNING+, 파일 DEBUG+)
│   └── humanize.py           # humanize 정책 유틸 (Phase 2)
├── config.py                 # 설정값 (모델명, 경로, 허용 카테고리 목록 등)
├── main.py                   # CLI 진입점
├── docs/
│   └── roadmap/
│       ├── PROJECT_PLAN.md   # 스케치 문서 (사용자 작성)
│       └── DESIGN_SPEC.md    # 기획 명세서 (본 문서)
└── README.md
```

---

## 5. 개발 Phase

### Phase 1 : 스타일 학습 파이프라인 구축
> 목표: 블로그 URL을 입력하면 카테고리별 스타일 가이드를 자동 생성

**Step 1. 데이터 입력**
- `data/input/blog_urls.txt` 파일에서 URL 목록 읽기
- 학습 완료된 URL은 자동으로 주석 처리 (`# done`)

**Step 2. 콘텐츠 수집 및 전처리**
- CrawlerAgent: URL 순회 크롤링, 실패 시 재시도 1회
- 네이버 블로그 등 iframe 구조 페이지는 iframe URL로 재요청하여 실제 본문 수집
- ParserAgent: 본문 텍스트 추출, 광고·메뉴 등 노이즈 제거

**Step 3. 카테고리 분석**
- AnalysisAgent: 글 내용 기반 카테고리 자동 분류
- 카테고리는 `config.py`에 정의된 허용 목록에서만 선택 (자유 분류 금지)
- 허용 목록에 없는 경우 `etc`로 분류
- 카테고리별 글 클러스터링 (파일 분류 저장)

**Step 4. 톤앤매너 분석**
- 문체 분석: 경어/반말, 문장 길이, 단락 구성
- 어휘 패턴: 자주 쓰는 단어·표현, 금지 표현
- 구조 패턴: 도입부·본문·마무리 구성 방식

**Step 5. 스타일 가이드 생성**
- StyleGuideAgent: 카테고리별 스타일 가이드 Markdown 작성
- 기존 가이드 존재 시 중복 제거 후 병합 업데이트
- humanize 정책 항목 필수 포함

**완료 기준:**
- [ ] 10개 URL 학습 → 스타일 가이드 파일 생성 성공
- [ ] 동일 URL 재학습 시 중복 처리됨
- [ ] `data/style_guides/{category}.md` 파일 생성 확인

---

### Phase 2 : 블로그 생성 파이프라인 구축
> 목표: 주제를 입력하면 학습된 스타일로 완성된 블로그 글 생성

**Step 0. 팩트 수집 (ResearchAgent)** ← 신규 추가
- [로컬 LLM] 주제에서 검색 쿼리 10개 자동 생성
- [Gemini API 무료] 각 쿼리로 응답 수집 (10회 호출)
- [로컬 LLM] 수집된 응답 요약·중복 제거·핵심 팩트 선별
- `data/output/{slug}_research.json` 저장

**Step 1. 주제 분석 및 목차 구성**
- PlannerAgent: 주제 키워드 추출, SEO 고려 제목 후보 생성
- 카테고리 자동 추론 → 해당 스타일 가이드 로드
- 팩트 컨텍스트(research.json) 반영하여 섹션별 목차(아웃라인) 생성

**Step 2. 본문 생성**
- WriterAgent: 스타일 가이드 + 아웃라인 + 팩트 컨텍스트 기반 섹션별 본문 생성
- Ollama 로컬 모델 사용, 섹션 단위로 분할 생성

**Step 3. 품질 검증 및 humanize**
- QualityAgent:
  - 스타일 가이드 준수 여부 체크
  - AI 생성 티 제거 (반복 표현, 과도한 접속사 등)
  - 가독성 개선 (문장 길이 조정, 단락 분리)
- 최종 Markdown 파일로 저장

**완료 기준:**
- [ ] 주제 입력 → 2000자 이상 블로그 글 생성 성공
- [ ] 생성 글이 해당 카테고리 스타일 가이드 항목 80% 이상 준수
- [ ] `data/output/{YYYYMMDD}_{slug}_draft.md` 파일 저장 확인

---

### Phase 3 : 웹 인터페이스 구축
> 목표: 브라우저에서 학습·생성 기능을 사용할 수 있는 로컬 웹 UI

**주요 기능:**
- URL 목록 입력 및 학습 실행 화면
- 학습 진행 상태 실시간 표시
- 주제 입력 및 글 생성 실행
- 생성된 글 미리보기 (Markdown 렌더링)
- 스타일 가이드 조회 화면

**기술:**
- FastAPI + Jinja2 (또는 단순 HTML/JS)
- WebSocket 또는 SSE로 진행 상태 스트리밍

**완료 기준:**
- [ ] 브라우저에서 URL 입력 → 학습 완료까지 UI로 확인
- [ ] 브라우저에서 주제 입력 → 생성 글 화면 출력

---

### Phase 4 : 고도화 (추후 결정)
> 기능 안정화 후 요구사항에 따라 추가

- 다중 블로그 프로필 관리 (여러 블로그 스타일 분리)
- 예약 생성 스케줄링
- 이미지 삽입 위치 제안
- 네이버 블로그 / 티스토리 자동 업로드 연동

---

## 6. humanize 정책

### AI 생성 글이 자연스럽게 보이도록 전 과정에 다음 정책을 적용한다.

| 항목 | 적용 방법 |
|------|----------|
| 반복 어휘 제거 | 동일 단어 3회 이상 연속 사용 금지 |
| 접속사 다양화 | "또한, 또한, 또한" 패턴 탐지 후 교체 |
| 문장 길이 변화 | 짧은 문장·긴 문장 혼용 (단조로운 리듬 방지) |
| 구어체 혼입 | 원본 블로그 어투에 맞는 자연스러운 표현 사용 |
| AI 과잉 표현 제거 | "물론입니다", "당연히", "매우 중요합니다" 등 패턴 제거 |


### AI 티가 나는 글의 다음과 같은 전형적 특징을 피한다.
  1. 과도한 구조화
      - 1, 2, 3 단계식 정리
      - 항상 균형 잡힌 문단 길이
   2. 추상어 남용
       - “효율성”, “중요성”, “본질적으로”
   3. 과잉 친절
       - 불필요한 정의 반복
   4. 경험 부재
       - 구체적 상황·실패·감정이 없음
   5. 리듬의 단조로움
       - 모든 문장이 일정한 길이

### 핵심 정책 7가지
  1. 경험 앵커(anchor) 삽입
  2. 미세한 비논리 허용
  3. 문장 길이 리듬 깨기
  4. 감각 정보 추가
  5. 애매함과 확신을 섞기
  6. 불완전한 구조 유지
  7. 개인적 관점의 편향 허용

---

## 7. 개발 우선순위 및 MVP 정의

| 우선순위 | 기능 | Phase |
|---------|------|-------|
| P0 (필수) | URL 크롤링 → 스타일 가이드 생성 | Phase 1 |
| P0 (필수) | 주제 입력 → 블로그 글 생성 | Phase 2 |
| P1 (중요) | CLI에서 전체 파이프라인 실행 | Phase 1~2 |
| P2 (선택) | 웹 인터페이스 | Phase 3 |
| P3 (후순위) | 자동 업로드, 스케줄링 | Phase 4 |

**MVP 완료 기준:**
> Phase 1 + Phase 2 CLI 동작이 안정적으로 완료되면 MVP로 간주한다.

---

## 8. 리스크 및 제약사항

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 로컬 LLM 성능 한계 | 글 품질 저하 | Mistral / Llama 3 모델 비교 후 선택 |
| 크롤링 차단 (robots.txt) | 데이터 수집 실패 | User-Agent 설정, 딜레이 추가, 차단 URL 스킵 |
| 스타일 가이드 품질 | 생성 글 일관성 부족 | 가이드 검증 단계 별도 추가 |
| 로컬 리소스 부족 | 속도 저하 | 배치 크기 조정, 경량 모델 옵션 제공 |
