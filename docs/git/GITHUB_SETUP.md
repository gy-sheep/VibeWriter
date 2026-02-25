# GitHub 연동 가이드

## 1. git 초기화

```bash
cd /Users/sgy/develop/vibe-coding/VibeWriter
git init
```

---

## 2. .gitignore 설정

프로젝트 루트에 `.gitignore` 파일 생성:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
*.egg-info/
dist/

# 환경 변수
.env

# 크롤링 원본 데이터 (대용량, 재생성 가능)
data/raw_html/
data/parsed_posts/
data/analysis/

# 아래 항목은 공유 여부에 따라 선택
# data/input/urls.txt      # 개인 URL 목록 → 보통 제외
# data/style_guides/       # 학습 결과 → 공유 시 포함
# data/output/             # 생성 글 → 공유 시 포함

# OS
.DS_Store
```

> **판단 기준**: `data/style_guides/`, `data/output/`은 결과물이므로
> 팀 공유 또는 백업 목적이면 포함, 개인 용도면 제외.

---

## 3. GitHub 원격 저장소 생성

1. [github.com](https://github.com) → New repository
2. Repository name: `VibeWriter`
3. Visibility: Public / Private 선택
4. **README, .gitignore, License 체크 해제** (로컬에서 올리므로)
5. Create repository 클릭

---

## 4. 원격 저장소 연결 및 첫 커밋

```bash
# 스테이징
git add .

# 첫 커밋
git commit -m "chore: 프로젝트 초기 설정"

# 기본 브랜치를 main으로 설정
git branch -M main

# 원격 연결 (URL은 GitHub에서 복사)
git remote add origin https://github.com/<username>/VibeWriter.git

# 푸시
git push -u origin main
```

---

## 5. 브랜치 전략 (권장)

```
main        ← 안정 버전만 머지
dev         ← 개발 통합 브랜치
feat/xxx    ← 기능 개발 (ex: feat/crawler-agent)
fix/xxx     ← 버그 수정
```

```bash
# 개발 브랜치 생성
git checkout -b dev

# 기능 브랜치 예시
git checkout -b feat/phase1-crawler
```

---

## 6. 커밋 메시지

커밋 작성 전 반드시 `docs/git/COMMIT_CONVENTION.md` 참조.

---

## 참고

- `.gitignore` 파일을 나중에 추가하면 이미 추적된 파일은 제외되지 않음
  → 그럴 경우: `git rm -r --cached <경로>` 후 다시 커밋
