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

## 빠른 시작

### 1. Ollama 설치 및 모델 다운로드

```bash
# macOS - Ollama 설치
brew install ollama

# Ollama 서버 시작 (백그라운드)
ollama serve &

# 모델 다운로드 (약 4.7GB)
ollama pull llama3.1:8b
```

**확인 방법**:
```bash
ollama list  # llama3.1:8b 모델이 있는지 확인
```

### 2. Python 의존성 설치

```bash
# uv 설치 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# 의존성 설치
uv sync
```

### 3. 초기 데이터 준비

학습할 블로그 URL을 `data/input/blog_urls.txt`에 추가합니다:

```bash
# 디렉토리 생성
mkdir -p data/input

# URL 파일 생성 (예제)
cat > data/input/blog_urls.txt << 'EOF'
https://brunch.co.kr/@example/123
https://blog.naver.com/example/123456
https://medium.com/@example/article-title
EOF
```

**지원 플랫폼**: 브런치, 네이버 블로그, Medium 등

### 4. 실행 전 체크리스트

- [ ] Ollama 서버가 실행 중인가? (`pgrep -f "ollama serve"`)
- [ ] llama3.1:8b 모델이 다운로드되어 있는가? (`ollama list`)
- [ ] `data/input/blog_urls.txt`에 URL이 추가되어 있는가?
- [ ] Python 의존성이 설치되어 있는가? (`uv sync`)

### 5. 실행

```bash
# Phase 1: 스타일 학습
uv run python main.py learn

# Phase 2: 블로그 글 생성 (Phase 1 완료 후)
uv run python main.py write --topic "주제 입력"
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
- **Package Manager**: uv (의존성 관리 및 가상환경)
- **Build Backend**: hatchling
- **LLM Runtime**: Ollama (로컬 모델)
- **Web Framework**: FastAPI
- **크롤링**: BeautifulSoup4 + httpx
- **데이터 저장**: 로컬 파일 (JSON / Markdown)

자세한 내용은 [DESIGN_SPEC.md](docs/roadmap/DESIGN_SPEC.md)를 참고하세요.

## 프로젝트 구성

이 프로젝트는 **uv 기반**입니다:
- `pyproject.toml` - PEP 621 표준 형식, hatchling 빌드 백엔드
- `uv.lock` - uv 의존성 잠금 파일 (Git에 포함)
- `.venv/` - uv가 자동 생성하는 가상환경 (Git 제외)
