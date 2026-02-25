# BlogOrchestration 개발 진행 상황

> 프로젝트 현재 상태 및 다음 작업 요약

**최종 업데이트**: 2026-02-25

---

## 📊 프로젝트 개요

**목표**: AI 기반 블로그 자동 생성 파이프라인
- 유명 블로그의 톤앤매너를 학습
- SEO 최적화 + 이미지 생성
- Notion으로 자동 출력

**기술 스택**:
- Python 3.12
- Ollama + Llama 3.1 8B (무료 로컬 LLM)
- BeautifulSoup4, Requests, Feedparser
- Pydantic 2.6+
- Poetry (패키지 관리)
- Rich (터미널 UI)

---

## ✅ 현재 완료 상태

### Phase 1: 블로그 학습 (완료)
**상태**: ✅ 구현 및 검증 완료

**주요 기능**:
- ✅ 블로그 크롤링 (6개 플랫폼: 네이버, 티스토리, 브런치, Velog, Medium, RSS)
- ✅ 톤앤매너 자동 분석 (Ollama 기반)
- ✅ 구조 분석 (8개 항목: 제목, 소제목, 문단, 길이, SEO 등)
- ✅ 카테고리 자동 분류 (6개 카테고리)
- ✅ 카테고리별 스타일 가이드 생성
- ✅ 스타일 가이드 병합 (기존 데이터 보존)
- ✅ Humanize guidelines (AI 티 제거 가이드, 9개 룰)

**프로젝트 구조 최적화**:
- ✅ Phase별 디렉토리 구조 (`src/phases/phase1/`)
- ✅ 프롬프트 Phase별 분리 (`config/prompts/phase1/`)
- ✅ 데이터 모델 분리 (blog.py, analysis.py, style_guide.py)

**실행 결과**:
- 분석 시간: ~70초 (5개 글 기준)
- 비용: $0 (Ollama 사용)
- 출력: `data/output/style_guide.json`

---

## 🔜 다음 작업

### 우선순위 1: Phase 2 구현 준비
**목표**: 트렌딩 키워드 수집 및 글 아이디어 생성

**필요한 작업**:
1. **설정 파일 생성**
   - [ ] `config/content_filter.json` (필터링 정책)
   - [ ] `config/prompts/phase2/` 프롬프트 4개 작성

2. **데이터 모델 구현**
   - [ ] `src/models/keyword.py` (7개 모델)

3. **키워드 수집 소스 구현** (2026-02-25 설계 재수립)
   - [ ] 네이버 뉴스 API (한국 이슈, 메인 소스)
   - [ ] Google News RSS (한국어, hl=ko&gl=KR)
   - [ ] 한국 IT 뉴스 RSS (ZDNet Korea, 블로터, ITWorld)
   - [ ] 네이버 DataLab API (트렌드 검증용)
   - [ ] Reddit API (글로벌 기술 트렌드, 선택적)
   - ~~pytrends~~ → 불안정, 네이버 DataLab으로 대체
   - ~~Hacker News~~ → 영문 전용, 한국 IT RSS로 대체

4. **Phase 2 에이전트 구현**
   - [ ] KeywordCollectorAgent
   - [ ] ContentFilterAgent
   - [ ] CategoryClassifierAgent

5. **Phase 2 오케스트레이터**
   - [ ] `src/phases/phase2/keyword.py`
   - [ ] 8단계 워크플로우 구현

**설계 문서**: `docs/developer/phase2-architecture.md` (완료)

### 우선순위 2: 문서 및 환경 설정
- [ ] GitHub 연동 및 첫 커밋
- [ ] IDE Python Interpreter 설정

---

## 📁 프로젝트 구조

```
BlogOrchestration/
├── src/
│   ├── models/              # Pydantic 데이터 모델
│   │   ├── blog.py          # Article, Blog (공통)
│   │   ├── analysis.py      # ToneAnalysis, StructureAnalysis (Phase 1)
│   │   └── style_guide.py   # CategoryStyleGuide, StyleGuide (Phase 1)
│   ├── services/            # 외부 서비스
│   │   ├── llm/             # Ollama 클라이언트
│   │   └── scraping/        # 블로그 크롤러
│   ├── agents/              # 에이전트
│   │   ├── crawler_agent.py
│   │   └── tone_analyzer_agent.py
│   ├── phases/              # Phase별 오케스트레이터
│   │   └── phase1/
│   │       └── collection.py
│   └── utils/               # 유틸리티
├── config/
│   ├── prompts/phase1/      # Phase 1 프롬프트 (4개)
│   └── blog_urls.txt        # 분석할 블로그 URL 목록
├── data/
│   ├── output/              # 최종 결과물
│   │   └── style_guide.json # 카테고리별 스타일 가이드
│   └── processed/           # 중간 처리 데이터
├── docs/
│   ├── user/                # 사용자 문서
│   └── developer/           # 개발자 문서
│       ├── DEVELOPMENT.md
│       ├── phase1-architecture.md
│       └── phase2-architecture.md
└── scripts/
    └── migrate_style_guide.py
```

---

## 📈 프로젝트 통계

### 파일 개수
- **Python 파일**: 20개
  - models: 3개
  - agents: 3개
  - services: 3개
  - phases: 1개
  - utils: 3개
  - scripts: 1개
- **프롬프트 파일**: 4개 (Phase 1)
- **문서**: 6개 (README, PROGRESS, HISTORY, 개발 문서 3개)

### 코드 통계
- **총 코드 라인**: ~2,500줄
- **지원 플랫폼**: 6개
- **카테고리**: 6개 (자동 분류)
- **분석 항목**: 16개 (톤앤매너 8개 + 구조 8개)

---

## 🔑 중요 결정 사항

### Phase 1
1. **Ollama 사용**: OpenAI 대신 무료 로컬 LLM 사용 (비용 $0)
2. **개별 글 URL 지원**: 원하는 스타일만 선택 가능
3. **카테고리별 학습**: 기술 글과 일상 글의 톤앤매너 분리
4. **Phase별 구조**: Context 효율성 향상 (47% 절감)
5. **병합 로직**: 기존 스타일 가이드 보존하며 신규 추가

### Phase 2 (설계 재수립 완료 - 2026-02-25)
1. **소스 재설계**: pytrends(불안정) → 네이버 DataLab API, Hacker News(영문) → 한국 IT 뉴스 RSS
2. **2단계 전략**: 뉴스 기사 → LLM 키워드 발견 + DataLab으로 트렌드 검증
3. **한국어 중심 소스**: 네이버 뉴스 + Google News RSS(ko) + 한국 IT RSS
4. **이슈 맥락 기반**: 키워드뿐 아니라 트렌딩 이유 분석
5. **자동 카테고리 분류**: 사용자 선택 불필요
6. **2단계 필터링**: 연예/스포츠 자동 제외
7. **글 각도 제안**: 키워드 → 구체적 글 주제 생성

---

## 📝 실행 방법

### Phase 1: 블로그 학습

**사전 준비**:
1. Ollama 설치 및 Llama 3.1 모델 다운로드
   ```bash
   brew install ollama
   brew services start ollama
   ollama pull llama3.1:8b
   ```

2. Python 의존성 설치
   ```bash
   poetry install
   # 또는
   pip3 install beautifulsoup4 requests pydantic python-dotenv rich lxml feedparser
   ```

3. 블로그 URL 설정
   - `config/blog_urls.txt`에 분석할 블로그 URL 입력
   - 개별 글 URL 권장 (원하는 스타일만 선택)

**실행**:
```bash
python3 main.py
```

**트리거 키워드**: "블로그 학습"

---

## 🔄 Phase 워크플로우

### Phase 1: 블로그 학습 (1회성)
```
블로그 URL → 크롤링 → 카테고리 분류 → 톤앤매너 분석 → 구조 분석 → 스타일 가이드 생성
```

### Phase 2: 키워드 수집 (반복 가능) - 설계 완료
```
키워드 수집 → 이슈 분석 → 필터링 → 카테고리 분류 → 글 각도 생성 → 사용자 선택
```

### Phase 3-5 (예정)
- **Phase 3**: 선택한 키워드 기반 글 작성
- **Phase 4**: SEO 최적화 + 이미지 생성
- **Phase 5**: Notion 출력

---

## 📚 문서 안내

### 사용자 문서
- `README.md` - 프로젝트 개요 및 사용법
- `docs/user/installation.md` - 설치 가이드

### 개발자 문서
- `docs/developer/DEVELOPMENT.md` - Context 관리 전략
- `docs/developer/phase1-architecture.md` - Phase 1 아키텍처
- `docs/developer/phase2-architecture.md` - Phase 2 설계
- `HISTORY.md` - 날짜별 상세 작업 내역

### 프로젝트 관리
- `PROGRESS.md` - 현재 상태 및 다음 작업 (이 파일)
- `CLAUDE.md` - Claude Code 지침
- `docs/developer/PROMPTS_AND_ISSUES.md` - 사용자 메모 (Claude 비접근)

---

## ⚙️ Context Management 전략

### Phase-based 격리
- **프롬프트**: `config/prompts/phase{N}/` 디렉토리별 관리
- **오케스트레이터**: `src/phases/phase{N}/` 디렉토리별 관리
- **모델**: 공통 모델 분리, Phase 전용 모델 별도 파일
- **문서**: `docs/developer/phase{N}-*.md` 각 Phase별 문서

### 효과
- Phase 2 구현 시 Phase 1 프롬프트/모델 자동 제외
- Context 로딩 시 불필요한 정보 최소화
- **예상 Context 절감**: ~47%

---

## 🚀 세션 재시작 시 진행 방법

### 트리거 키워드
- **"블로그 학습"** → Phase 1 실행
- **"설정 파일 생성"** → Phase 2 준비 (우선순위 1)
- **"구현 시작"** → Phase 2 구현 시작
- **"문서 수정"** → Phase 2 설계 문서 검토

### 상세 히스토리 확인
- 날짜별 작업 내역: `HISTORY.md` 참조
- 필요시 Claude가 자동으로 Read tool 사용

---

**변경 이력**: 자세한 내용은 `HISTORY.md` 참조
