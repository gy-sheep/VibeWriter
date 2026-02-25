# VibeWriter 개발 히스토리

> 날짜별 상세 작업 내용 및 변경 이력

---

## 2026-02-25 — Phase 1 Step 1~2 구현 완료 ✅

### 프로젝트 초기 설정
- `pyproject.toml` 생성 (httpx, beautifulsoup4, fastapi, uvicorn, python-dotenv)
- `CLAUDE.md` 최소화 (핵심 제약만 명시, 참고 문서 링크 방식 채택)
- `docs/git/COMMIT_CONVENTION.md` 작성
- `.claude/commands/commit.md` 커스텀 슬래시 명령어 생성

### 설계 결정 사항 확정 (DESIGN_SPEC.md 업데이트)
- `urls.txt` → `blog_urls.txt` 파일명 변경
- 카테고리 정규화 정책 추가: `config.py`의 허용 목록에서만 선택, 미해당 시 `etc`
- AnalysisAgent 역할에 허용 목록 기반 정규화 명시

### Phase 1 Step 1~2 구현
**구현 파일**:
- `config.py`: 경로(Path 기반), Ollama 모델, 허용 카테고리 목록, 크롤러 설정
- `utils/file_manager.py`: `read_urls()` (# done 필터링), `mark_done()` (# done 접두어 추가)
- `agents/crawler.py`: httpx GET, 재시도 1회, robots.txt 검사, User-Agent 설정
- `agents/parser.py`: BeautifulSoup4, 본문 선택자 우선순위, 노이즈 태그 제거, JSON 저장
- `main.py`: `python main.py learn` CLI

**네이버 블로그 대응** (이슈 → 해결):
- 원인: 네이버 블로그는 메인 HTML에 본문 없음 (iframe 구조, body text 21자)
- 해결: `_resolve_naver_url()` 추가 — iframe src 추출 후 재요청
- 파서 선택자 추가: `.se-main-container`, `#postViewArea`, `.post-content`
- 제목 추출 개선: `.se-title-text` 우선, `<title>` 태그 사이트명 접미사 제거

### 커스텀 슬래시 명령어
- `.claude/commands/commit.md` — 커밋 자동화
- `.claude/commands/sync-docs.md` — 코드 변경 시 관련 문서 자동 업데이트

### 개발 기획 문서 작성
- `docs/dev/phase1-step1-2.md` — 구현 범위, 데이터 흐름, 파일 명세, 모듈 상세, 프로젝트 구조, 검증 방법

---
