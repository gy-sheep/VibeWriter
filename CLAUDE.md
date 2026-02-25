# CLAUDE.md

## 핵심 제약 (반드시 준수)

- **LLM**: Ollama 로컬 모델만 사용 — 외부 유료 API 절대 금지
- **저장**: 로컬 파일(JSON/Markdown)만 사용 — DB 없음
- **humanize**: 모든 LLM 생성 텍스트에 `utils/humanize.py` 정책 적용 필수
- **단계별 진행**: Phase별 최소 기능 완성 후 다음 Phase로 이동

## 실행

```bash
uv sync                                   # 의존성 설치
python main.py learn                      # 스타일 학습
python main.py write --topic "주제"       # 블로그 글 생성
uvicorn web.main:app --reload             # 웹 서버 (Phase 3)
```

## 참고 문서

- 아키텍처·Agent·데이터 흐름·Phase 상세: `docs/roadmap/DESIGN_SPEC.md`
- 프로젝트 계획: `docs/roadmap/PROJECT_PLAN.md`
- **git commit 전 반드시 읽기**: `docs/git/COMMIT_CONVENTION.md`
