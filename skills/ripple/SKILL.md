---
name: ripple
description: 구현 후 테스트가 잡지 못하는 사이드 이펙트를 탐지·해결한다. 9개 카테고리(Data Flow / State / Interface / Resource / Concurrency / Distributed / Config / Error / Observability) × 3 severity(CRITICAL/WARNING/INFO). scan → clarify → resolve → check 4단계 흐름 — 구현 직후 또는 PR 머지 전 사용.
version: 0.1.0
scope: general
agents: [claude, codex]
risk: low
policy_injection: required
outputs:
  - path: context/{slug}/ripple-report.md
    min_lines: 20
    required_sections: ["## Summary", "## Findings", "## Clarification History", "## Resolution History", "## Check History"]
---

# Ripple

> **The Iron Law**: Pre-existing 이슈는 out of scope. 모든 finding 은 *현재 diff 의 특정 변경* 에 인과적으로 연결되어야 한다 (delta-anchored). 일반 코드 리뷰는 별도 코드리뷰 스킬·도구의 영역.

You are operating as quivo ripple analyzer. Before reporting any finding, you MUST trace its cause to a specific change in `git diff <baseline>...HEAD`. Findings without a clear causal link to the diff are rejected.

## When to use

코드 변경을 만든 직후 또는 PR 머지 전, *테스트가 검증하지 않는* 사이드 이펙트를 점검할 때. 변경된 코드의 품질이 아니라 *변경이 나머지 코드를 어떻게 위태롭게 만들었는가* 가 관심사. 본 스킬은 *단독 사용 가능* (P6) — 다른 quivo atom 산출물 없어도 git diff 만으로 동작.

4단계 흐름 (각 단계는 독립 호출 가능, 권고 순서 scan → clarify → resolve → check):

| 모드 | 목적 | 입력 | 산출 |
|---|---|---|---|
| `scan` | 탐지 | git diff (+ 선택적 스펙/리뷰 문서) | `ripple-report.md` 의 Findings (초안) |
| `clarify` | **구체화** — 질문으로 cause/risk/why-tests-miss 명확화 | `ripple-report.md` 의 OPEN findings | Findings 본문 정제 + `## Clarification History` 누적 |
| `resolve` | 해결 — 옵션 표 제시·사용자 선택 기록 | clarify 완료된 OPEN findings | `## Resolution History` 갱신 + optional `ripple-fixes.md` (구현 가이드) |
| `check` | 검증 + fix-induced 신규 탐지 | 수정된 코드 + 기존 `ripple-report.md` | Status 갱신 + `## Check History` + 신규 findings |

## Inputs

- **Mode**: `scan` (기본) / `clarify` / `resolve` / `check`
- **Severity 필터**: `critical` 또는 인자 없음 (전체)
- **특정 finding IDs**: `R-001 R-003` (clarify / resolve / check 모드)
- **`--diff`**: scan 모드에서 점진 분석 (이전 scan 이후 변경된 파일만)
- **`--base <branch>`**: baseline 명시 (기본 `main`)
- **`--dry-run`**: resolve 모드에서 옵션만 미리보기, 결정 기록 안 함
- **Source options** (모두 선택사항, P6):
  1. 기술 스펙 문서 (있으면, 예: `context/<slug>/tech-spec.md`) — 기대 동작 대조
  2. 변경 요약/리뷰 문서 (있으면) — 변경 요약 참고
  3. 사용자 인라인 — `--base` 또는 의도 설명
- **항상 필요**: git diff (본 스킬은 git 저장소 + 변경 존재가 전제)
- **Bash**: `git merge-base`, `git diff`, `git log --oneline`, `git show`, `git rev-parse`
- **MCP**: 없음 (선택적 Linear MCP 로 issue 생성 — `ripple-fixes.md` 항목별 — 가능하나 v0.1 에서는 markdown 출력만)

## Process

### Mode: scan (기본)

1. **Baseline 결정** (P1):
   - `--base <branch>` 인자 ?? `main` 기본값.
   - `MERGE_BASE=$(git merge-base HEAD <base>)`. 결과가 비면 사용자에게 base 재확인.

2. **Diff 추출**:
   ```bash
   git diff "${MERGE_BASE}...HEAD" --stat       # 변경 규모
   git diff "${MERGE_BASE}...HEAD" --name-only  # 변경 파일 목록
   git diff "${MERGE_BASE}...HEAD"              # 본문
   ```
   `--diff` 인자 시 이전 `ripple-report.md` 의 마지막 scan 이후 변경 파일만.

3. **컨텍스트 로드** (선택, P6 Source options):
   - 기술 스펙 문서 → 기대 동작과 실제 변경 대조
   - 변경 요약 문서 → 의도된 변경 vs ripple 영역 식별 도움

4. **9 카테고리별 분석**:

   | 카테고리 | 점검 포인트 |
   |---|---|
   | Data Flow | 입출력 모양 불일치, silent 데이터 손실, 직렬화 갭 |
   | State & Lifecycle | 전역 상태 오염, 자원 누수, 초기화 순서 |
   | Interface Contract | 시그니처 의미 변경, 암묵적 계약 깨짐 |
   | Resource & Performance | 복잡도 회귀, 핫패스 할당, I/O 증폭 |
   | Concurrency | 경쟁 상태, 락 순서, 원자성 가정 |
   | Distributed Coordination | 멱등성 갭, 순서 가정, 파티션 내성 |
   | Configuration & Environment | 누락 키, 환경별 갭, 배포 순서 |
   | Error Propagation | 미처리 실패 모드, silent swallow, 부분 실패 |
   | Observability | trace context 손실, 로깅 갭, 메트릭 깨짐 |

   각 finding 은 *변경의 특정 줄* 에 인과적 링크 + Why Tests Miss It (테스트가 잡지 못하는 이유).

5. **Findings 정리** — 새 또는 갱신:
   - 기존 `ripple-report.md` 가 있고 같은 cause 의 finding 이 있으면 그것 갱신
   - 새 finding 은 다음 ID (R-NNN) 할당
   - severity 는 CRITICAL / WARNING / INFO 셋 중 하나만

6. **`ripple-report.md` 저장** — Summary + Findings + Resolution History + Check History 섹션.

7. **사용자 보고** (P1 동기화 게이트):
   - severity 별 카운트, 카테고리 분포
   - 다음 권고: `clarify` (모호 finding 구체화 — 권장 다음 단계) 또는 *"분석 결과 검토 후 결정"*

### Mode: clarify

scan 결과가 *"이게 정말 문제인지"* 또는 *"무엇이 어떻게 위태로워졌는지"* 가 모호할 때, 사용자에게 *질문을 던져* finding 본문을 구체화한다. **결정은 안 한다 — resolve 의 영역.**

1. **Report 로드** — `ripple-report.md` 의 OPEN findings. 필터 (`critical` / `R-NNN`) 적용.

2. **각 finding 의 모호 차원 점검**:
   - **Cause 모호**: 변경의 *어느 줄/심볼* 이 원인인지 인용이 약함
   - **Risk 모호**: After 가 *"문제 가능"* 수준이지 구체 시나리오 없음
   - **Why Tests Miss It 모호**: "테스트가 부족" 수준이지 *어떤 종류의 테스트* 가 필요했는지 불명확
   - **Severity 근거 모호**: CRITICAL/WARNING/INFO 선택 근거가 약함

3. **사용자에게 *3개 이내 핵심 질문*** (§2.5 B Option Table 형식 권장):
   - 객관식·범위 한정형 우선 (오버로드 방지, P1 Sync)
   - 한 finding 당 한 라운드 — 답 받으면 다음 finding 으로
   - 예시 질문:
     - "이 호출 경로가 prod 에서 *실제로* 호출되는 경우는?" → A/B/C 옵션
     - "변경 후 동작이 의도된 것인가요? (Yes / No / 부분 — 명세 부재)"
     - "이 위험이 실제 사용자 경험에 영향을 주는 시나리오를 한 줄로?"

4. **답변으로 본문 refine** — 각 dimension 갱신:
   - Cause: 파일:라인 인용 보강
   - Before/After: 답변 기반 구체 시나리오 추가
   - Why Tests Miss It: 답변에서 도출된 *없는 테스트 유형* 명시
   - Severity: 근거 보강 (변경 가능, 필요 시 다른 레벨로)

5. **Clarification History 추가** — 본 라운드 기록:
   ```
   #### R-NNN — <timestamp>
   - Q1: <질문>
     A: <사용자 답>
   - Q2: ...
   - 본문 갱신: Cause → ..., Risk → ..., Severity → ...
   ```

6. **사용자 보고** + 다음 권고:
   - 구체화된 finding 수 / 여전히 모호한 finding 수
   - 다음: `resolve` (구체화 완료된 finding 부터 해결 옵션 검토)

### Mode: resolve

1. **Report 로드** — `ripple-report.md` 의 OPEN findings. 필터 (`critical` / `R-NNN`) 적용.

2. **각 finding 순회** (CRITICAL → WARNING → INFO):
   - **Cause + Side Effect 제시** — finding 의 Before/After/Why Tests Miss It 요약
   - **해결 옵션 2~4개 생성** — 다음 표 형식 (§2.5 B Option Table):

     | # | 옵션 | 작업량 | 리스크 | 추천도 |
     |---|---|---|---|---|
     | A | <Minimal fix 한 줄> | <hours> | <단어> | ★★ |
     | B | <Structural fix 한 줄> | <hours> | <단어> | ★★★ |
     | C | Skip (ACCEPTED RISK) | 0 | <단어> | ★ |

   - **Steelman 게이트** (§2.5 A) — 추천 옵션에 대해 *반대 입장 1줄 반박* 제시. 반박이 유효해 보이면 옵션 재검토.
   - **사용자 결정** — A/B/C 선택, 자유 답변, 또는 skip. `--dry-run` 이면 기록 안 함.

3. **결정 기록**:
   - `ripple-report.md` 의 Resolution History 섹션에 `R-NNN: <선택> — <이유>` 추가
   - 해당 finding 의 Status 갱신 (RESOLVED / SKIPPED / ACCEPTED RISK / IN PROGRESS)

4. **`ripple-fixes.md` 생성/갱신** — 각 선택의 *구현 가이드*:
   - 영향 파일 / 변경 방향 / 검증 방법
   - 구현 단계(또는 구현 스킬)가 이 파일을 소비해 fix 를 적용 가능

5. **결과 보고** — 결정한 findings 수, 다음 행동 (수정 적용 → `ripple check`) 안내.

### Mode: check

1. **Report 로드**.

2. **각 OPEN finding 재검증**:
   - 현재 코드에서 cause 가 여전히 유효한가 (`git diff` / `git show <commit>` 로 변경 추적)
   - 유효 → STILL OPEN
   - 무효 (수정됨) → RESOLVED + 해결 commit 인용

3. **Fix-induced 신규 분석** (P4 Fix Loop 의 핵심):
   - 마지막 scan/check 이후의 새 변경 (fix commits) 도 동일한 9 카테고리 분석
   - 새 finding 발견 시 R-NNN+1 부터 ID 할당, Status: OPEN (fix-induced)

4. **Check History 기록** — `ripple-report.md` 에 사이클 추가:
   ```
   #### Check N (timestamp)
   - Re-checked: <N> findings
   - RESOLVED: <list>
   - STILL OPEN: <list>
   - NEW (fix-induced): <list>
   ```

5. **수렴 판단** + 사용자 보고:
   - OPEN 0 + 신규 0 → 수렴 (PR 머지 가능 신호)
   - 신규 > OPEN 줄어든 양 → 발산 (분할 PR 권유)
   - 그 외 → 계속 fix → check 사이클

## Iron Laws

- MUST: 모르는 부분은 추측하지 않는다. 잘 모르는 영역은 사용자에게 명시적으로 묻는다 (P1 Sync, 헌법 #4 Evidence Over Assertion).
- MUST: 모든 finding 은 git diff 의 *특정 변경* 에 인과적으로 연결되어야 한다 (delta-anchored). Pre-existing 이슈를 finding 으로 추가하지 않는다.
- MUST: severity 는 CRITICAL / WARNING / INFO 셋 중 하나로만. *"medium"* / *"중간"* 같은 임의 레이블 금지.
- MUST: resolve 모드에서 사용자 선택 *없이* 자동으로 fix 를 적용하지 않는다. 본 스킬은 *결정 기록 + 가이드 생성* 만, 실제 코드 수정은 구현 단계(별도 구현 스킬/직접 수정)에 위임.
- MUST: clarify 모드는 *질문만* 한다. 옵션 제시·결정 기록은 resolve 의 영역. clarify 에서 fix 옵션을 제시하지 않는다 (역할 분리).
- MUST: clarify 의 사용자 답변은 finding 의 *본문* (Cause/Before/After/Why-Tests-Miss/Severity) 을 정제할 뿐, *추가 finding 을 만들지 않는다*. 새 finding 은 scan 또는 check 의 결과만.
- MUST: check 모드에서 fix-induced 신규 발견을 누락하지 않는다 — 수정도 새로운 diff 이므로 동일 9 카테고리로 재분석.
- MUST: 9 카테고리·3 severity 는 고정. 임의로 새 카테고리·severity 레이블을 추가하지 않는다 (헌법 #5 Surgical Scope).
- MUST NOT: 본 스킬은 *general code review* 가 아니다. 코드 품질·스타일·디자인 결함·기존 코드 안티패턴은 별도 코드리뷰 스킬·외부 리뷰의 영역.
- MUST: 본 스킬은 다른 quivo 의 *실행* 을 전제하지 않는다 (P6 Independence). 기술 스펙 문서 등은 *있으면* 사용, 없으면 git diff 단독으로 동작.

### BAD / GOOD

- BAD: diff 와 무관한 파일에서 발견한 잠재 버그를 finding 으로 등록.
- GOOD: 그 파일이 *변경되었거나*, 변경된 다른 파일이 *이 파일의 가정을 깬* 경우만 finding. 인과 링크 명시.

- BAD: severity 를 *"중간"* 같은 모호한 단어로 부여.
- GOOD: CRITICAL (prod 데이터 손실/보안/장애) / WARNING (버그·성능 회귀·운영 이슈) / INFO (검토 권장, 의도된 것일 수도) 중 하나 + 그 근거.

- BAD: resolve 에서 *"옵션 A 가 명백히 정답"* 으로 단일 옵션만 제시.
- GOOD: 2~4 옵션 + 트레이드오프 표 + Steelman 반박 1줄까지 제시 후 사용자 선택.

- BAD: check 에서 OPEN 만 확인하고 fix 자체의 사이드 이펙트는 분석 안 함.
- GOOD: 매 check 에서 마지막 사이클 이후 새 diff 를 동일 9 카테고리로 재분석. fix-induced 신규 finding 을 OPEN 으로 추가.

- BAD: resolve 에서 finding 의 *"low priority"* 라고 사용자 OK 없이 SKIPPED 처리.
- GOOD: INFO 도 사용자에게 보여주고 명시적 *"skip"* 결정을 받아 ACCEPTED RISK 로 기록.

### Red Flags — STOP

행동 단위의 합리화·우회 시도가 보이려 하면 *즉시 stop* 하고 사용자에게 보고:

- "이 정도면 fix 효과만 보면 되겠죠" — check 의 fix-induced 분석 생략 신호
- "변경 안 됐어도 보여주는 게 좋을 것 같아" — pre-existing 이슈를 finding 으로 끌어들이려는 신호. 헌법 #5 위반.
- "9 카테고리에 없는 새 카테고리 만들자" — 카테고리는 고정. 새 발견은 기존 카테고리에 매핑.
- "옵션 A 가 정답이니 사용자 선택은 형식적" — Steelman 게이트 생략 신호
- resolve 에서 사용자 OK 없이 코드 수정 시도 — 본 스킬은 *결정 기록* 만.

## Failure modes

- **git 저장소 아님 / `git diff` 실패** → 사용자에게 보고 후 중단. 본 스킬은 git diff 가 필수.
- **base branch 식별 실패** (`merge-base` 결과 비어있음) → 사용자에게 `--base <branch>` 명시 요청.
- **diff 가 비어있음** (변경 없음) → "분석할 ripple 없음" 보고 후 종료 (실패 아님, 정상 종료).
- **diff 가 너무 큼** (예: >500 파일 / >10000 줄) → 사용자에게 `--diff` 점진 분석 또는 PR 분할 권유. 한 번에 모두 분석 시 신뢰도 저하.
- **스펙/리뷰 문서 부재** → diff 만으로 진행. 의도 추정 어려운 항목은 [NEEDS CLARIFICATION] 마커로 보류 + 사용자에게 인라인 의도 확인 요청.
- **resolve — 사용자가 모든 옵션 거부** → finding Status: ACCEPTED RISK 로 기록 (risk 수용 명시).
- **resolve — 사용자가 자유 답변 (옵션 외)** → 자유 답변 그대로 기록, 단 *측정 가능한 행동* 인지 검증 (모호하면 옵션 표로 다시 분해 권유).
- **check — fix-induced 신규 발견 폭증** (>10 신규) → 사용자에게 보고 + 변경 폭이 너무 큼을 시사. PR 분할 또는 finding 그룹화 권유.
- **`ripple-report.md` 손상 / 파싱 실패** → 사용자에게 보고 + scan 모드 새로 실행으로 재생성 옵션 제시 (기존 Resolution / Check History 손실 경고).
- **재귀 종료 조건**:
  - (a) scan / resolve / check 한 사이클 완료 + 사용자 *"다음 단계"* 명시 → 종료
  - (b) check 후 OPEN 0 + 신규 0 → 수렴, 머지 가능 신호 보고 후 종료
  - (c) 사용자 *"중단"* → 부분 산출물 보존 후 종료

## Signals of Success

- `ripple-report.md` 의 OPEN findings 가 매 check 사이클마다 *단조 감소*.
- check 한 사이클에서 신규 0 + 기존 OPEN 0 → 수렴 (PR 머지 가능 신호).
- PR 머지 후 *변경 영역과 관련된* prod 회귀가 발생하지 않음 — 부정 신호의 부재.
- 부정 신호:
  - 매 check 마다 신규 finding 이 끝없이 추가됨 → 변경 폭이 너무 큰 신호, PR 분할 권유.
  - resolve 에서 거의 모든 옵션이 *"skip"* 으로 결정됨 → severity 인플레이션 의심, scan 재실행 권유.
  - finding 들이 인과 링크 없이 *"잠재 위험"* 으로만 표현됨 → 본 스킬의 delta-anchored 원칙 위반, 재scan 권유.

## Examples

> Examples 는 의존성 없는 추상 골격이다. 실제 호출 시 `<placeholder>` 자리를 도메인 값으로 치환한다.

### 입력 패턴

```
# scan (기본 base = main)
ripple scan

# scan, CRITICAL 만
ripple scan critical

# scan, 점진 분석
ripple scan --diff --base develop

# clarify (모호 finding 구체화) — scan 직후 권장
ripple clarify

# clarify, 특정 finding 만
ripple clarify R-001

# resolve, CRITICAL 부터 (clarify 완료 후 권장)
ripple resolve critical

# resolve, 특정 finding
ripple resolve R-001 R-003

# check 사이클
ripple check
```

### finding 산출 골격 (`ripple-report.md`)

```markdown
# Ripple Report: <slug>

> Baseline: <branch> (merge-base <sha-7>)
> Scanned at: <ISO timestamp>

## Summary

- CRITICAL: <N>
- WARNING: <N>
- INFO: <N>
- 카테고리 분포: <Data Flow: N> / <State: N> / ...
- Scan 사이클: <N>회

## Findings

#### R-NNN: <한 줄 요약>

- **Category**: <카테고리 1> / <카테고리 2>
- **Severity**: CRITICAL | WARNING | INFO
- **Cause**: <변경 인용 — `<file>:<line>` + 변경 내용>
- **Before**: <변경 전 상태와 가정>
- **After**: <변경 후 상태와 위험>
- **Why Tests Miss It**: <기존 테스트가 못 잡는 이유>
- **Recommendation**: <첫 권고 — resolve 모드에서 옵션 표로 확장됨>
- **Status**: OPEN | RESOLVED | SKIPPED | ACCEPTED RISK | IN PROGRESS

## Clarification History

#### R-NNN — <timestamp>
- Q1: <질문>
  A: <사용자 답>
- Q2: <질문>
  A: <사용자 답>
- 본문 갱신: Cause → <보강 인용>, Risk → <구체 시나리오>, Severity → <조정 시 새 레벨 + 근거>

## Resolution History

- **R-NNN** <timestamp>: 옵션 B 선택 — <짧은 사유>
- **R-NNN** <timestamp>: ACCEPTED RISK — <사유>

## Check History

#### Check 1 — <timestamp>
- Re-checked: <N> findings
- RESOLVED: <list of IDs>
- STILL OPEN: <list>
- NEW (fix-induced): <list>
```

### Option Table (resolve 모드 사용자 대화)

```
**R-NNN — <한 줄 요약>**

Cause: <인용> (in <file>:<line>)
Before: <상태>
After: <상태와 위험>

해결 옵션:

| # | 옵션 | 작업량 | 리스크 | 추천도 |
|---|---|---|---|---|
| A | <Minimal fix> | <hours> | <단어> | ★★ |
| B | <Structural fix> | <hours> | <단어> | ★★★ |
| C | Skip (ACCEPTED RISK) | 0 | <단어> | ★ |

> **Steelman**: 옵션 B 에 대한 반박 — <한 줄>

선택해 주세요 (A/B/C / 자유 답변 / skip):
```

### 동기화 보고

```
[ripple scan] context/<slug>/ripple-report.md (사이클 <N>)
  - CRITICAL: <N> | WARNING: <N> | INFO: <N>
  - 카테고리 분포: <짧은 요약>
  - 추천 다음 행동:
    (a) resolve critical — CRITICAL 부터 해결 옵션 검토
    (b) resolve — 전체 OPEN 순회
    (c) PR 분할 — 변경 폭이 너무 클 때
    (d) 보류
```
