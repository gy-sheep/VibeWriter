# CLAUDE.md

## 핵심 제약 (반드시 준수)

- **LLM**: 생성·분석은 Ollama 로컬 모델 사용 — 외부 유료 API 절대 금지
- **팩트 수집**: Gemini API 무료 티어 허용 (ResearchAgent 전용, 유료 전환 금지)
- **저장**: 로컬 파일(JSON/Markdown)만 사용 — DB 없음
- **humanize**: 모든 LLM 생성 텍스트에 `utils/humanize.py` 정책 적용 필수
- **단계별 진행**: Phase별 최소 기능 완성 후 다음 Phase로 이동

## 코드 품질 규칙

- 신규 구현 또는 수정 후 반드시 `/check` 로 방어 코드를 검증한다

## 실행

```bash
uv sync                                          # 의존성 설치
uv run python main.py learn                      # 스타일 학습
uv run python main.py write --topic "주제"        # 블로그 글 생성
uv run uvicorn web.main:app --reload             # 웹 서버 (Phase 3)
```

## 참고 문서

- **세션 시작 시 반드시 읽기**: `PROGRESS.md` (현재 상태 및 다음 작업 — 구현에 필요한 정보 포함)
- 전체 파이프라인 흐름 한눈에 보기: `docs/roadmap/PIPELINE_OVERVIEW.md`
- 아키텍처·Agent·데이터 흐름·Phase 상세: `docs/roadmap/DESIGN_SPEC.md`
- 프로젝트 계획: `docs/roadmap/PROJECT_PLAN.md`
- **git commit 전 반드시 읽기**: `docs/git/COMMIT_CONVENTION.md`
- `docs/dev/_template.md`: step 문서 작성 포맷 — **step 문서 신규 작성 시 반드시 이 파일을 읽고 포맷을 따른다**
- `docs/dev/phase{N}-step{N}.md`: Step별 상세 설계 (기록용, 필요 시에만 참조)

## 문서 관리

- **Phase/Step 구현 완료 시**: `PROGRESS.md` 업데이트를 제안한다
- **세션 종료 감지 시** ("오늘은 여기까지", "커밋하고 끝낼게" 등): `PROGRESS.md` 업데이트 여부를 확인한다
- **`/commit` 실행 시**: 커밋 전에 `PROGRESS.md` 반영 여부를 자동으로 확인한다
- 업데이트 시 완료된 내용은 `HISTORY.md`로 이동하고, `PROGRESS.md`는 다음 작업 기준으로 유지한다
