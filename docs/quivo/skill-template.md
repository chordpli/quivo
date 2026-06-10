# quivo SKILL.md 작성 표준

> **버전**: 0.1.0
> 본 문서는 quivo 의 모든 atom 스킬이 따라야 할 SKILL.md 구조를 정의한다.
> `pipeline` 같은 오케스트레이터 스킬은 별도 표준 (`pipeline-template.md`, v0.2).

---

## 0. 파일 위치

```
skills/<skill-name>/
  SKILL.md       # canonical 정의 (필수)
  EXAMPLES.md    # 긴 예시 (선택, karpathy 패턴)
  setup.sh       # bash 환경 셋업 (선택, quivo 가 자동 복사)
  setup.ps1      # PowerShell (선택)
```

`<skill-name>` 은 kebab-case. 예: `req-intake`, `linear-split`.

---

## 1. Frontmatter — 8필드 표준

```yaml
---
name: req-intake
description: 요구사항을 정리하고 오픈 질문을 추출한다. 새 기능 요구사항이 들어오면 사용.
version: 0.1.0
scope: general
agents: [claude, codex]
risk: low
policy_injection: required
outputs:
  - path: context/{slug}/00-requirements.md
    min_lines: 30
    required_sections: ["## 범위", "## 비범위", "## 오픈 질문"]
---
```

### 필드 명세

| 필드 | 타입 | 필수 | 허용 값 | 설명 |
|---|---|---|---|---|
| `name` | string | yes | kebab-case | 디렉토리명과 일치 |
| `description` | string | yes | 1~2문장 | "무엇 + Use when ~" 형식 권장 (karpathy). description 매칭으로 자동 트리거됨 |
| `version` | string | yes | semver | 스킬 단위 버전. manifest.json 의 version 과 일치 |
| `scope` | enum | yes | `general` \| `company` | general = 도메인 무관, company = 회사 특화 |
| `agents` | string[] | yes | `[claude, codex]` | parity 기본값. 한 에이전트 전용은 정당화 필요 |
| `risk` | enum | yes | `low` \| `medium` \| `high` | high 는 owner 승인 1명 필수 |
| `policy_injection` | enum | yes | `required` \| `optional` \| `forbidden` | 기본 `required`. forbidden 은 외부 공개용 등 예외 |
| `outputs` | array | yes | 아래 outputs 명세 참조 | 산출물 계약 |

### outputs 명세

각 항목은 다음 키를 가진다:

| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `path` | string | yes | 산출 파일 경로. `{slug}` 플레이스홀더는 컨텍스트 슬러그로 치환 |
| `min_lines` | int | no | 최소 줄 수. 부재 시 검증 안 함 |
| `required_sections` | string[] | no | 산출물에 반드시 존재해야 할 마크다운 헤더 |

`outputs` 가 비어 있다면 `[]` 로 명시. 빈 배열도 *"이 스킬은 파일 산출이 없다"* 는 의도된 선언.

---

## 2. Body — 필수 섹션 + 추가 패턴

본 섹션의 모든 패턴은 *모든 atom 본문에* 적용된다. (atom-specific 추가 패턴은 §2.5 참조.)

### 2.1 본문 골격 (모든 atom 공통)

```markdown
# <Skill Title>

> **The Iron Law**: <한 줄 — 이 스킬이 절대 깨지 않을 핵심 규칙. 본문에서 *시각적으로 가장 강조* 되는 문장>

You are operating as <역할 — 예: "quivo implement worker / tech-spec author">. Before <조건 — 예: "writing any code">, you MUST <행동 — 예: "verify build commands and read the relevant phase artifact">.

## When to use

(언제 호출되어야 하는가. frontmatter description 보다 상세. 1~3문장. *독립적으로 사용 가능 (P6)* 명시 권고.)

## Inputs

(이 스킬이 가정하는 입력. P6 Source options 패턴 — §3.5 참조.)

## Process

(스킬이 따라가야 할 단계. 명령형, 번호 매김. P1 Sync 게이트 명시.)
1. ...
2. ...

## Iron Laws

(이 스킬에서 절대 깨면 안 되는 규칙. constitution.md 의 7원칙 인용 가능. 3~5개 권고.)
- MUST: ...
- MUST NOT: ...

### BAD / GOOD

(Anti-Sycophancy — 자주 발생하는 잘못된 진행 vs 옳은 진행 2~4 쌍.)
- BAD: <자주 발생하는 잘못된 패턴>
- GOOD: <대신 해야 할 것>
- BAD: <또 다른 패턴>
- GOOD: ...

### Red Flags — STOP

행동 단위의 합리화·우회 시도가 보이려 하면 *즉시 stop* 하고 사용자에게 보고.
- (skill-specific 행동 신호 2~3개 — 예: "이 정도 변경은 안전" / "다음에 확인해도 되겠지" / "이전과 비슷하니까")

> 주의: *"추측건대" "아마도" "정확히는 모르지만"* 같은 어구는 STOP 트리거가 아니다.
> 그런 어구가 *나오기 전에* "추측 금지, 모르면 사용자에게 묻기" Iron Law 가 발동해
> 이미 질문으로 전환되어야 한다. Red Flags 는 행동 패턴 차단용이지 어구 차단용이 아님.

## Failure modes

(예상 가능한 실패와 대응)
- 입력 부족 → ...
- 권한 없음 (Linear MCP 등) → ...
- 산출물 검증 실패 → ...

## Examples (선택)

(짧은 예시 인라인. 길면 EXAMPLES.md 로 분리)
```

### Iron Laws 작성 규칙

- 본 스킬 고유의 게이트만 작성. constitution 의 7원칙은 자동 주입되므로 중복 금지.
- 명령형 (MUST / MUST NOT). karpathy 톤.
- 3~5개 권고. 10개 넘으면 본질을 잃었다는 신호.

### Failure modes 작성 규칙

- 각 항목은 *원인 → 대응* 형식.
- "사용자에게 묻는다" 가 가장 안전한 대응. "추정해서 진행한다" 는 금지 (Iron Law #4 위반).
- 권한 없음 케이스는 반드시 명시 (policy.md 권한 부여와 연결).

---

## 2.5 Atom-specific 추가 패턴 (해당 atom 만 적용)

### A. Steelman 게이트 (결정 직전)

설계·분기·옵션 선택을 하는 atom 에 적용 (`tech-spec`, `pr-review-pack`, `linear-split` 분할 그래뉼래리티 결정 등).

```markdown
N. **Steelman 반론** (P1 Sync — 결정 직전):
   - 선택한 옵션에 대해, *반대 입장에서 한 줄 반박* 을 사용자에게 제시.
   - 반박이 여전히 유효해 보이면 옵션 재검토. 무효화되면 진행.
```

### B. Option Table (오픈 질문 표준)

요구사항·기획·기술결정·작업분할에서 오픈 질문이 발생하는 atom 에 적용.

```markdown
| # | 질문 | 옵션 A | 옵션 B | 옵션 C | Implications |
|---|---|---|---|---|---|
| 1 | <질문> | <짧은 답> | <짧은 답> | <짧은 답> | <각 옵션이 후속 phase 에 미치는 영향> |
```

규칙: 한 번에 *3개 이내* 의 질문 (오버로드 방지). 옵션은 *상호 배제* 적이어야 함.

### C. Signals of Success (관찰 지표)

`risk: medium` 권고 / `risk: high` 필수. 산출물이 *실제로 작동* 하는지 확인할 관찰 가능한 신호.

```markdown
## Signals of Success

산출물이 의도대로 작동하는지 확인하는 신호:
- <관찰 가능한 사실 1 — 예: "PR description 에 변경 파일이 모두 나열됨">
- <관찰 가능한 사실 2 — 예: "CI 가 통과 후 reviewer 가 별다른 질문 없이 머지">
- <부정 신호 — 예: "reviewer 가 \"무엇을 했는지\" 묻는다 = 실패">
```

### D. WHAT/HOW 분리 (tech-spec 류)

`tech-spec` 본문 안에서 *무엇을* 만들 것인가와 *어떻게* 만들 것인가를 시각적으로 분리. 후속 phase 가 입력 받을 때 혼동 방지.

```markdown
## 아키텍처

### WHAT — 외부에서 보이는 행동
- <기능 1: 사용자/시스템이 무엇을 할 수 있게 되는가>

### HOW — 내부 구현 결정
- <컴포넌트 A: 왜 이 선택, 트레이드오프>
```

### E. Rationalization Table (pr-review-pack 류)

자기 합리화 패턴 차단. PR 본문/리뷰 요청에 흔히 나오는 *변명 → 진짜 해야 할 것* 매핑.

```markdown
### Rationalization Table

리뷰어/사용자에게 다음 변명 패턴이 등장하면 *해당 변명 대신 옆 행동으로* 전환:

| 변명 (BAD) | 해야 할 것 (GOOD) |
|---|---|
| "이건 단순한 변경이라 테스트 불필요" | 가장 간단한 1개 테스트라도 추가 |
| "급해서 일단 머지하고 나중에 보강" | 보강 작업을 Linear 이슈로 분리 + 머지 |
| "리뷰어가 확인할 거예요" | reviewer 가 확인할 *수 있도록* 증거를 PR 본문에 첨부 |
```

### F. PRD Acceptance Criteria (implement 류)

`implement-log.md` 에 *측정 가능한* AC 명시 강제.

```markdown
## <Task ID> AC (Acceptance Criteria)
- [ ] <검증 가능한 행동 1 — 예: "POST /users 가 201 + 생성된 user ID 반환">
- [ ] <검증 가능한 행동 2>
- [ ] <CI 통과 / 테스트 N 개 추가>
```

"AC 통과 전 done 주장 금지" 를 Iron Law 로.

### G. Requirements Quality Checklist 8 dimensions (req-intake)

req-intake 산출물 (`00-requirements.md`) 의 자체 검증 룰. Iron Law / Process step 으로 강제.

```markdown
### Requirements Quality Check (8 dimensions)

작성 완료 전 다음을 자체 검증:
1. **명확성** — 모호한 형용사("빠르게", "사용성 좋게") 없음
2. **측정 가능성** — 성공/실패가 객관적 관찰 가능
3. **완전성** — 핵심 happy path + 1~2 분기 모두 포함
4. **일관성** — 범위 vs 비범위 모순 없음
5. **검증 가능성** — 각 항목을 실제로 어떻게 확인할지 답할 수 있음
6. **추적 가능성** — 원문 어느 부분이 근거인지 추론 가능
7. **단일 출처성** — 동일 사실이 다른 형태로 두 번 반복되지 않음
8. **오픈 질문 명시성** — 추정 대신 질문으로 표시
```

---

## 3. 완전한 예시 — `req-intake`

```markdown
---
name: req-intake
description: 요구사항을 정리하고 오픈 질문을 추출한다. 새 기능 요구사항이 들어오면 사용.
version: 0.1.0
scope: general
agents: [claude, codex]
risk: low
policy_injection: required
outputs:
  - path: context/{slug}/00-requirements.md
    min_lines: 30
    required_sections: ["## 범위", "## 비범위", "## 오픈 질문"]
---

# Requirements Intake

## When to use

자연어 요구사항이 들어왔을 때 (사용자 메시지, 이메일 인용, Linear 이슈 본문 등) 첫 단계로 호출한다. 후속 phase (`product-brief`) 진입 전 필수.

## Inputs

- 요구사항 원문 (자연어, 길이 무관)
- 컨텍스트 슬러그 (없으면 사용자에게 묻기, 또는 제목 기반 생성)

## Process

1. 사용자에게 슬러그 확인. 없으면 짧은 슬러그 (3~5단어 kebab-case) 제안.
2. `context/<NNN-slug>/` 디렉토리 생성 (NNN 은 자동 증가).
3. 요구사항을 다음 섹션으로 정리:
   - `## 범위` — 무엇을 만들 것인가
   - `## 비범위` — 명시적으로 제외할 것
   - `## 오픈 질문` — 사용자 확인이 필요한 부분
4. `context/<NNN-slug>/00-requirements.md` 에 저장.
5. 산출물 경로 + 오픈 질문 개수를 보고.

## Iron Laws

- MUST: 오픈 질문이 0개이면 "정말 없는가" 다시 검토. 거의 항상 1개 이상 있다.
- MUST NOT: 비범위를 임의로 추정해 채우지 말 것. 명확한 신호 없으면 오픈 질문으로 옮긴다.
- MUST: 슬러그는 영어 또는 ASCII-safe. 한국어 슬러그는 금지 (파일 시스템 호환성).

## Failure modes

- 요구사항이 너무 모호 → 즉시 사용자에게 3개 이내의 핵심 질문. 추정 진행 금지.
- `context/` 디렉토리 쓰기 권한 없음 → 명확히 보고, 사용자에게 chmod 또는 다른 경로 제안.
- 슬러그 충돌 (이미 존재) → 사용자에게 다른 이름 제안 또는 이어쓰기 여부 확인.

## Examples

(생략 — EXAMPLES.md 로 분리 가능)
```

---

## 3.5. 작성 원칙 — 운영 룰 5가지

본 5가지는 모든 quivo atom 이 *런타임 동작* 으로 갖춰야 할 행동 패턴이다. 본문 (Process / Iron Laws / Failure modes) 에 녹여 작성한다.

### P1. Sync Through Questions — 매 단계 사용자 동기화

- 모호함이 있으면 **추정 진행 금지**. 즉시 사용자에게 묻는다 (질문은 3개 이내, 객관식·범위 한정형 우선).
- Process 단계 사이에 *암묵적 가정* 이 생기면 그 가정을 *명시적 확인* 으로 바꾼다.
- Iron Law 예시: `MUST: 사용자 확인 없이 다음 단계로 넘어가지 않는다 (모호함 = 추정 X, 질문 O)`.

### P2. Parallelize When Possible — 병렬 가능한 작업은 병렬로

- Process 단계가 서로 독립적이면 명시적으로 "병렬 실행 가능" 으로 표시.
- 큰 작업은 git worktree 분리 권유 가능 (Process 단계나 결과 보고에 안내).
- Iron Law 예시: `MUST: 의존성 없는 단계는 병렬 실행을 우선 검토한다`.

### P3. Document Every Step — 산출물 기반 진행

- 각 Process 단계는 **검증 가능한 산출물** (파일, 출력, 보고) 을 만든다.
- `outputs:` frontmatter 는 이 산출물의 계약 (path + min_lines + required_sections).
- 단계 사이 사용자 확인은 산출물을 *보여준 후* 받는다 (구두 합의 금지).

### P4. Fix Loop, Never Halt — 에러 시 재귀로 해결

- 에러·검증 실패·요구사항 누락 시 **멈추지 않고** 원인 분석 → 수정 → 재검증 루프.
- 다음 중 하나가 성립할 때까지 반복:
  - 문제 해결 (산출물 검증 통과)
  - 빌드/테스트 통과
  - 요구사항 모두 충족
  - 사용자가 명시적으로 중단 지시
- Failure modes 섹션에 "재귀 종료 조건" 명시. 무한 루프 방지를 위해 매 사이클 사용자에게 진행 상황 보고.

### P5. Abstract Examples — 의존성 없는 예시

- `## Examples` 섹션의 예시는 *구체 도메인 의존성* 없이 작성.
- 좋음: "feature-name", "<core-question-1>", placeholder 형식.
- 나쁨: "video-upload-resume", "CREW 계정", "Linear 워크플로 ID 12345".
- 이유: 예시가 특정 도메인에 묶이면 다른 도메인 사용자가 적용 어려움.

### P6. Independence — 단독 실행 가능 (헌법 #1)

- 각 스킬은 **다른 스킬 산출물에 의존하면 안 된다**. 입력은 *우선순위 있는 source 목록* + *fallback 으로 사용자 직접 입력*.
- "필수 입력" 으로 다른 phase 의 산출 파일을 적지 않는다. 대신 "이런 종류의 정보가 필요하다" 라고 *콘텐츠 단위* 로 적고, 그 콘텐츠를 얻는 방법을 여러 source 로 제시한다.

**Inputs 작성 표준 (P6 적용)**:

```markdown
## Inputs

- **Primary content needed**: <필요한 정보의 종류 — 콘텐츠 단위 설명>
- **Source options** (우선순위 순, 모두 선택사항):
  1. `context/<slug>/<file>.md` 가 존재하면 사용 (이전 phase 산출물 — 가장 빠른 경로)
  2. 사용자가 인라인으로 제공한 텍스트
  3. (선택) Slack thread URL — Slack MCP (read) 로 fetch
  4. (선택) Linear issue URL/ID — Linear MCP (read) 로 fetch
- **Fallback**: 위 모두 부재 시 사용자에게 *"어떤 정보를 줄 수 있는지"* 묻고 인라인 처리.
- **MCP** (모두 선택): Slack (read), Linear (read)
```

**Iron Law 예시**:
- `MUST: 본 스킬은 다른 스킬의 *실행* 을 전제하지 않는다. 산출 파일이 없으면 사용자에게 묻고 인라인 처리.`

**Failure mode 예시**:
- `이전 phase 산출 파일 부재 + 사용자 인라인 입력도 없음` → "어떤 형태로 정보를 줄 수 있는지" 사용자에게 묻기. 추측 진행 금지.

**왜 이게 중요한가**: 사용자는 파이프라인 일부만 사용하거나 다른 순서로 호출할 수 있다. 모든 스킬을 강제로 1번부터 거치게 만들면 quivo 가 무거워진다.

### 본문 반영 가이드

- **Iron Laws** 에 P1, P3, P4 의 핵심 룰을 1줄씩 포함 (해당 스킬에 적용 가능 시).
- **Process** 단계 중 병렬 가능 지점은 명시 (P2).
- **Failure modes** 마지막에 "재귀 종료 조건" 항목 (P4).
- **Examples** 작성 시 placeholder 형식 사용 (P5).

---

## 4. Claude / Codex 변환 — 핵심만

스킬 저자가 외워야 할 3가지:

1. **모든 directive 는 본문에**. frontmatter 는 메타데이터·매칭용 — validator 허용 키(`name`/`description`/`license`/`allowed-tools`/`metadata`) 외의 키(`version`, `outputs` 등)는 설치 시 `metadata:` 아래로 이동한다. 지시문은 반드시 본문에.
2. **Claude 전용 UI 요소 회피** (예: `<details>` 토글). 두 에이전트에서 동일하게 보여야 함.
3. **경로 참조는 `.claude/skills/<name>/` 형식**. 설치 시 에이전트별 `q-` prefix 경로(Claude `.claude/skills/q-<name>/`, Codex `.agents/skills/q-<name>/`)로 자동 치환되고, 호출명도 `q-<name>` 이 된다.

상세 어댑터 동작, `_append_policy`, `EXAMPLES.md` 같은 사이드카 지원 여부 등은 **[`reference/agent-adapters.md`](reference/agent-adapters.md)** 참조.

---

## 5. 작성 체크리스트 (PR 머지 전)

가장 빠른 검증: `scripts/test-skill.sh <skill-name>` 한 줄로 1~7 항목 모두 자동 검사. 마지막 두 항목 (8~9) 은 수동.

- [ ] (1) frontmatter 8필드 모두 존재 — *test-skill.sh [1/5]*
- [ ] (2) `description` 이 "what + when" 형식 (lint 안 잡지만 PR 리뷰 시 확인)
- [ ] (3) `outputs:` 의 경로가 실제 Process 단계와 일치
- [ ] (4) 본문 5개 섹션 (When to use / Inputs / Process / Iron Laws / Failure modes) 존재 — *test-skill.sh [1/5]*
- [ ] (5) Iron Law block + Persona 첫줄 + BAD/GOOD + Red Flags 모두 본문에 있음
- [ ] (6) `skill.yaml` version 이 SKILL.md frontmatter version 과 일치 — *test-skill.sh [2/5]*
- [ ] (7) `manifest.json` 에 등록 + sha256 최신 — *test-skill.sh [3/5]*
- [ ] (8) `tests/skill-triggering/prompts/<name>.txt` 존재 — *test-skill.sh [4/5]*
- [ ] (9) `quivo init --agent both` dry-run 성공 — *test-skill.sh [5/5]*
- [ ] (10) dogfooding 1회 (실제 호출 → 산출물 확인) — *수동*

신규 스킬 작성은 `author-skill` 메타 atom 을 호출하면 1~9를 자동 안내한다.

---

## 6. constitution 과의 연결

본 표준은 헌법(`constitution.md`)을 강제하는 도구다:

| 헌법 원칙 | 본 표준의 강제 메커니즘 |
|---|---|
| #1 Atoms | 각 SKILL.md 가 단독 호출 가능한 구조 (Inputs/Outputs 명시) |
| #2 Self-Contained | OMC 의존 자제, `agents: [claude, codex]` 기본 |
| #3 Parity | frontmatter 자동 변환 + Claude-only UI 금지 |
| #4 Evidence | `outputs:` 계약 + lint-skills 검증 |
| #5 Surgical | Process 단계에서 영향 범위 명시 의무 |
| #6 Skip logged | Failure modes 의 skip 케이스 처리 |
| #7 Policy SSOT | `policy_injection: required` 기본값 |

새 스킬을 작성할 때 본 표준을 따르지 않으면 PR 머지 거부.
