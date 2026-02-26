# Phase 2 · Step 3 개발 기획

> **범위**: 품질 검증 및 humanize
> **목표**: draft.md 로드 → AI 티 제거(규칙 기반) + LLM 최종 다듬기 → final.md 저장

---

## 1. 구현 범위

| Step | 기능 | 담당 모듈 |
|------|------|----------|
| Step 3 | AI 과잉 표현 제거, 반복 접속사 탐지/교체 (규칙 기반) | `utils/humanize.py` |
| Step 3 | 외국 문자 제거 — 한자·키릴·아랍 등 비한글 스크립트 (규칙 기반) | `utils/humanize.py` |
| Step 3 | 반복 어구 탐지 — 2어절 bi-gram 빈도 집계 (규칙 기반) | `utils/humanize.py` |
| Step 3 | 스타일 가이드 준수 항목 체크 4종 (규칙 기반) | `agents/quality.py` |
| Step 3 | LLM 기반 최종 humanize 다듬기 (맞춤법 교정·반복 표현·문장 리듬) | `agents/quality.py` |
| Step 3 | final.md 저장 | `agents/quality.py` |
| Step 3 | `main.py` write 파이프라인에 QualityAgent 연결 | `main.py` |

---

## 2. 데이터 흐름

```
data/output/{slug}_draft.md
        │
        ▼ (규칙 기반 AI 표현 제거·접속사 다양화)
  [humanize.apply_all()]
        │ 1차 정제 텍스트
        ▼ (스타일 가이드 준수 체크 → 위반 항목 목록)
  [QualityAgent._check_style()]
        │ 체크 결과 + 1차 정제 텍스트
        ▼ (LLM: 문장 리듬·경험 앵커·어투 최종 다듬기)
  [QualityAgent._polish()]
        │ 최종 Markdown
        ▼
data/output/{slug}_final.md
```

---

## 3. 파일 명세

### 입력 1 — draft.md (Step 2 출력)

**`data/output/{YYYYMMDD}_{slug}_draft.md`**
```markdown
# 제주 여행 3박4일 솔직 후기

<!-- meta: topic=제주 여행 3박4일 후기, category=travel, generated_at=... -->

## 들어가며

공항에서 내리자마자 느낀 건 습한 바람이었다...

## 첫째 날: 동쪽 해안 드라이브

...
```

### 입력 2 — 스타일 가이드 (outline.json의 style_guide_path로 로드)

**`data/style_guides/{category}.md`**

### 출력

**`data/output/{YYYYMMDD}_{slug}_final.md`**
- draft.md와 동일한 slug 사용, 파일명만 `_draft` → `_final` 변경
- Markdown 구조(제목, 섹션) 유지, 본문 텍스트만 정제

---

## 4. 모듈 상세

### `utils/humanize.py`

규칙 기반 텍스트 정제. LLM 없이 regex로 처리한다.

#### `remove_foreign_chars(text: str) -> str`

로컬 LLM이 한국어 본문에 혼입한 외국 문자를 제거한다.

- 제거 대상:
  - CJK 한자 (중국어·일본어): U+4E00–U+9FFF 등
  - 키릴 문자 (러시아어 등): U+0400–U+04FF
  - 아랍·히브리·태국 문자
  - 비표준 라틴 확장 문자를 포함한 단어 (베트남어 등)
- Markdown 헤더(`#`)·HTML 주석(`<!--`)은 건드리지 않는다.

---

#### `detect_repetitive_phrases(text: str, min_repeats: int = 3, min_len: int = 6) -> list[str]`

전체 본문에서 `min_repeats`회 이상 반복되는 2어절 bi-gram 어구를 반환한다.

- Markdown 헤더·HTML 주석 제외 후 순수 본문만 분석.
- 빈도 내림차순 정렬, 최대 5개 반환.
- `_check_style()`에서 LLM polish 위반 항목으로 전달하는 데 사용한다.

---

#### `remove_ai_phrases(text: str) -> str`

AI 과잉 표현을 탐지해 제거 또는 교체한다.

- 제거 대상 패턴 (대소문자·어미 변형 고려):
  ```python
  AI_PHRASES = [
      r"물론(입니다|이죠|이에요|이지요)[,.]?\s*",
      r"당연(히|하게도)[,.]?\s*",
      r"매우 중요(합니다|해요|하죠)[.!]?\s*",
      r"효율적으로\s*",
      r"본질적으로\s*",
      r"중요한 점은\s*",
  ]
  ```
- 각 패턴을 빈 문자열로 치환 후 공백 정리.
- 처리 결과가 원문과 동일하면 원문 그대로 반환.

---

#### `diversify_conjunctions(text: str) -> str`

동일 접속사가 3문장 이내에 2회 이상 연속 등장하는 패턴을 탐지해 후보 중 하나로 교체한다.

- 대상 접속사 및 교체 후보:
  ```python
  CONJUNCTION_ALTS = {
      "또한": ["그리고", "아울러", "더불어"],
      "하지만": ["그런데", "그러나", "다만"],
      "그래서": ["따라서", "그러므로", "덕분에"],
      "물론": ["사실", "실제로"],
  }
  ```
- 문단 단위로 분리 후 문장 순회.
- 같은 접속사가 연속 2회 이상 등장하면 두 번째부터 후보 중 랜덤 선택으로 교체.
- 랜덤 시드: 고정값 없음 (매 실행마다 다를 수 있음).

---

#### `apply_all(text: str) -> str`

모든 규칙을 순서대로 적용하고 최종 텍스트를 반환한다.

```python
def apply_all(text: str) -> str:
    text = remove_foreign_chars(text)
    text = remove_ai_phrases(text)
    text = diversify_conjunctions(text)
    return text
```

- 입력이 빈 문자열이면 빈 문자열 반환 (early return).

---

### `agents/quality.py` — QualityAgent

#### `quality_check(draft_path: Path) -> Path | None`

최상위 진입 함수. 아래 단계를 순서대로 실행하고 final.md 경로를 반환한다.

0. `draft_path.exists()` 확인. 없으면 에러 로그 + `None` 반환.
1. `_load_draft(draft_path)` → `(markdown, meta)` 튜플
2. `_extract_sections(markdown)` → 섹션별 텍스트 딕셔너리
3. `humanize.apply_all(body_text)` → 규칙 기반 1차 정제
4. `_load_style_guide(meta["style_guide_path"])` → 스타일 가이드 텍스트
5. `_check_style(sections, style_guide)` → 위반 항목 목록
6. `_polish(markdown_after_humanize, meta, violations)` → 최종 Markdown
7. `_save_final(draft_path, final_markdown)` → `Path | None`

실패 시 `None` 반환, 에러 로그 출력.

---

#### `_load_draft(path: Path) -> tuple[str, dict] | None`

- draft.md 전체 텍스트 읽기.
- HTML 주석(`<!-- meta: ... -->`)에서 topic, category, style_guide_path 파싱.
- 파싱 실패 시 meta 값은 빈 문자열로 fallback (파이프라인은 계속 진행).
- OSError 시 `None` 반환.

---

#### `_extract_sections(markdown: str) -> dict[str, str]`

- `## ` 기준으로 섹션 분리.
- `{"섹션제목": "본문텍스트", ...}` 딕셔너리 반환.
- humanize 적용 단위(섹션별 처리)에 사용.

---

#### `_check_style(sections: dict, style_guide: str) -> list[str]`

규칙 기반으로 스타일 가이드 준수 여부를 체크한다. LLM 미사용.

체크 항목:

| 항목 | 체크 방법 | 위반 기준 |
|------|----------|----------|
| 문장 길이 단조로움 | 전체 문장 길이 표준편차 | 표준편차 < 15자 |
| AI 과잉 표현 잔존 | `remove_ai_phrases` 적용 전/후 diff | 제거 항목 1개 이상 |
| 반복 접속사 | `diversify_conjunctions` 탐지 결과 | 교체 항목 1개 이상 |
| 반복 어구 | `detect_repetitive_phrases` 탐지 결과 | 3회 이상 반복 어구 존재 시 |

- 스타일 가이드가 빈 문자열이면 체크 없이 `[]` 반환.
- 위반 항목을 문자열 목록으로 반환 (LLM 프롬프트에 주입용).

---

#### `_polish(markdown: str, meta: dict, violations: list[str]) -> str`

LLM에 1차 정제된 전문(全文)을 전달해 최종 humanize 다듬기를 요청한다.

- 프롬프트 설계 (`_POLISH_SYSTEM`):
  ```
  - 한국어 맞춤법·문법 오류는 반드시 수정하세요.
  - 없는 경험이나 사실을 만들어 추가하지 마세요.
  - "내 친구가", "제 지인이" 같이 타인의 경험을 지어낸 문장은 제거하거나 1인칭으로 바꾸세요.
  - 반복 사용된 표현은 다양한 표현으로 바꾸세요.
  - 어색하거나 부자연스러운 문장만 고치세요.
  - 문장 리듬: 비슷한 길이의 문장이 3개 이상 이어지면 짧은 문장을 끼워 변화를 주세요.
  - 본문 텍스트만 반환. 원문 글자 수의 70~130% 유지.
  ```
- 섹션 단위로 LLM 호출 (전문 1회 전달 시 로컬 모델 컨텍스트 한계로 잘림 방지).
- 응답 길이가 원본 대비 ±40% 초과 시 자동 fallback (원본 반환).
- LLM 응답이 빈 문자열이면 입력 markdown 그대로 반환 (fallback).
- LLM 예외 발생 시 에러 로그 + 입력 markdown 반환 (fallback).

---

#### `_save_final(draft_path: Path, markdown: str) -> Path | None`

- `draft_path`에서 `_draft` → `_final` 으로 파일명 변경.
- `final_path.write_text(markdown, encoding="utf-8")`.
- OSError 시 에러 로그 + `None` 반환.

---

#### 실패 처리

| 상황 | 처리 방식 |
|------|----------|
| draft_path 없음 | 에러 로그 + `None` 반환 |
| draft.md 읽기 실패 | OSError 로그 + `None` 반환 |
| meta 파싱 실패 | 경고 로그 + 빈 dict로 계속 진행 |
| 스타일 가이드 없음 | 스타일 체크 스킵, 경고 출력 |
| LLM 응답 없음/예외 | 에러 로그 + 1차 정제 결과 그대로 저장 |
| final.md 저장 실패 | OSError 로그 + `None` 반환 |

---

### `main.py` — write 파이프라인 확장

```python
# Step 3 이후 cmd_write()
from agents.quality import quality_check

def cmd_write(topic: str) -> None:
    print(f"주제: {topic}\n")

    outline_path = plan(topic)
    if not outline_path:
        print("\n  [fail] 아웃라인 생성 실패 — 중단")
        sys.exit(1)
    print(f"\n  아웃라인 생성 완료: {outline_path}")

    draft_path = write(outline_path)
    if not draft_path:
        print("  [fail] 초안 생성 실패 — 중단")
        sys.exit(1)
    print(f"  초안 생성 완료: {draft_path}")

    final_path = quality_check(draft_path)   # ← Step 3에서 추가
    if final_path:
        print(f"  품질 검증 완료: {final_path}")
    else:
        print("  [warn] 품질 검증 실패 — draft를 최종 결과로 사용")
```

- `quality_check` 실패 시 파이프라인을 중단하지 않는다. draft_path를 최종 결과로 간주.

---

## 5. 구현 후 프로젝트 구조

```
VibeWriter/
├── agents/
│   ├── crawler.py
│   ├── parser.py
│   ├── analysis.py
│   ├── style_guide.py
│   ├── planner.py
│   ├── writer.py
│   └── quality.py          ← 품질 검증·LLM humanize (신규)
├── utils/
│   ├── file_manager.py
│   ├── ollama_client.py
│   ├── logger.py
│   └── humanize.py         ← 규칙 기반 AI 표현 제거·접속사 다양화 (신규)
├── data/
│   └── output/             ← {slug}_draft.md + {slug}_final.md
├── config.py
├── main.py                 ← quality_check() 연결
└── docs/dev/
    └── phase2-step4.md     ← 본 문서
```

---

## 6. 검증 방법

| 항목 | 확인 방법 |
|------|----------|
| 기본 동작 | `uv run python main.py write --topic "제주 여행 3박4일 후기"` → `data/output/` 에 `_final.md` 생성 확인 |
| AI 표현 제거 | draft.md에 "물론입니다", "매우 중요합니다" 수동 삽입 후 실행 → final.md에서 제거 확인 |
| 접속사 다양화 | draft.md 특정 섹션에 "또한" 3회 삽입 후 실행 → final.md에서 2번째부터 교체 확인 |
| LLM fallback | `_polish()`에서 예외 발생 유도 → 에러 로그 출력 + 1차 정제 결과로 final.md 저장 확인 |
| draft 없는 경우 | 존재하지 않는 draft_path 전달 → 에러 로그 출력 + `None` 반환 확인 |
| 파이프라인 연속 실행 | `main.py write` 단일 명령 → outline → draft → final 3파일 순차 생성 확인 |
| 최종 글자 수 | `wc -m data/output/*_final.md` → 2000자 이상 확인 |
