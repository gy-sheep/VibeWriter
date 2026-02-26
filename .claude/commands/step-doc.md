새로운 Phase/Step 개발 문서를 작성한다. 아래 순서를 따른다.

## 준비 단계

1. `docs/dev/_template.md` 를 읽어 문서 작성 포맷을 파악한다.

2. `PROGRESS.md` 를 읽어 현재 다음 작업(Phase/Step)이 무엇인지 확인한다.

3. 사용자가 명시하지 않은 경우, PROGRESS.md의 "다음 작업" 기준으로 문서를 작성할 Phase/Step을 제안하고 확인을 받는다.

## 작성 단계

4. `docs/dev/` 디렉터리를 확인해 기존 step 문서의 네이밍 패턴을 파악한다.
   - 패턴: `phase{N}-step{N}.md`

5. _template.md 포맷을 엄격히 따라 새 문서를 작성한다.
   - PROGRESS.md와 DESIGN_SPEC.md를 참고해 구현 목표·배경·설계 내용을 채운다.
   - 구현 전 단계이므로 "구현 결과" 섹션은 비워두거나 TBD로 표시한다.

6. `docs/dev/phase{N}-step{N}.md` 로 저장한다.

## 완료

7. 작성된 문서 경로와 주요 섹션 목차를 사용자에게 보고한다.
