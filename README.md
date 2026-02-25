# VibeWriter

> 카테고리별 블로그 글의 톤앤매너를 분석·학습하고,
> 사용자가 입력한 주제에 대해 일관된 스타일의 블로그 글을 자동 생성한다.

## 개요

블로그 운영의 전체 프로세스를 AI 기반 멀티 에이전트로 자동화하는 시스템.

- 기존 블로그 글을 학습해 **나만의 글쓰기 스타일**을 추출
- 주제를 입력하면 학습된 스타일로 **일관된 블로그 글** 자동 생성
- AI 생성 티가 나지 않도록 **humanize 정책** 전 과정 적용

## 요구사항

- Python 3.11+
- [Ollama](https://ollama.ai) (로컬 LLM 런타임)

## 설치

```bash
# 의존성 설치
pip install -e .

# 또는 uv 사용 시
uv sync
```

## 사용법

```bash
# Phase 1: 스타일 학습
python main.py learn

# Phase 2: 블로그 글 생성
python main.py write --topic "주제 입력"
```

## 개발 Phase

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 스타일 학습 파이프라인 | 진행 예정 |
| Phase 2 | 블로그 생성 파이프라인 | 진행 예정 |
| Phase 3 | 웹 인터페이스 | 진행 예정 |
| Phase 4 | 고도화 | 추후 결정 |

## 기술 스택

- **Language**: Python 3.11+
- **LLM Runtime**: Ollama (로컬 모델)
- **Web Framework**: FastAPI
- **크롤링**: BeautifulSoup4 + httpx
- **데이터 저장**: 로컬 파일 (JSON / Markdown)

자세한 내용은 [DESIGN_SPEC.md](docs/roadmap/DESIGN_SPEC.md)를 참고하세요.
