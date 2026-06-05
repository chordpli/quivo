---
name: author-skill
description: 새 quivo 스킬을 표준에 맞춰 생성한다. 헌법 7원칙 + skill-template § 패턴 + Iron Law / BAD-GOOD / Red Flags 모두 반영한 SKILL.md, skill.yaml, trigger prompt, manifest 등록까지 안내. 새 스킬 만들 때 사용.
version: 0.1.1
scope: general
agents: [claude, codex]
risk: low
policy_injection: required
outputs:
  - path: skills/{new-skill-name}/SKILL.md
    min_lines: 60
    required_sections: ["## When to use", "## Inputs", "## Process", "## Iron Laws", "## Failure modes"]
  - path: skills/{new-skill-name}/skill.yaml
    min_lines: 5
    required_sections: []
  - path: tests/skill-triggering/prompts/{new-skill-name}.txt
    min_lines: 1
    required_sections: []
---

# Author Skill — quivo 스킬 작성 가이드

> **The Iron Law**: `scripts/test-skill.sh <new-name>` 가 통과하기 전에는 PR 머지 금지. lint, version, manifest sha256, trigger prompt, quivo init dry-run 5단계 모두 ✓ 필수.

You are operating as quivo author-skill. Before writing any line of a new SKILL.md, you MUST read `docs/quivo/constitution.md`, `docs/quivo/skill-template.md`, and one or two reference atoms (e.g. `skills/aws-access/SKILL.md`). Never invent a structure not in the template.

## When to use

quivo 카탈로그에 새 스킬을 추가할 때. 또는 기존 스킬을 표준에 맞춰 마이그레이션할 때. 본 스킬은 단독 호출 가능 (P6) — 다른 quivo atom 산출물이 없어도 동작.

## Inputs

- **Primary content needed**: 새 스킬의 *목적*. *언제* 호출되어야 하고, *무엇을* 받아 *무엇을* 만드는지.
- **Source options** (우선순위 순, 모두 선택사항):
  1. 사용자 인라인 설명 — *"<X> 같은 스킬 만들어줘"*
  2. 이미 작성된 초안 (`drafts/<name>.md` 같은 외부 파일)
  3. 기존 스킬 + 변형 — *"기존 스킬과 같은 구조로 Y 스킬"*
- **Fallback**: 위 모두 부재 시 *"무엇을 자동화하고 싶은가"* 부터 묻기.
- **Read (필수)**:
  - `docs/quivo/constitution.md` — 7원칙
  - `docs/quivo/skill-template.md` — §1 frontmatter, §2 본문, §2.5 atom-specific, §3.5 P1-P6
  - `docs/quivo/permissions.md` — MCP/Bash 권한 모델
  - `docs/quivo/reference/agent-adapters.md` — Codex 변환 함의
  - 참고용 기존 스킬 1~2개 (`skills/author-skill/SKILL.md`, `skills/aws-access/SKILL.md`)
- **Bash**: `mkdir -p skills/<name>/`, `scripts/test-skill.sh <name>`, `python3 scripts/lint-skills.py`, `sha256sum` (또는 `shasum -a 256`).
- **MCP**: 없음.

## Process

1. **스킬 목적·이름 확정** (P1 Sync):
   - 사용자에게 *"무엇을 / 언제 / 입력 / 출력"* 한 줄씩 받기. 모호하면 묻기.
   - 이름은 kebab-case. 도메인이 다른 quivo 와 겹치면 안 됨 (`ls skills/` 으로 확인). private 스킬이면 `__` 접두사.

2. **Atom 분류 + 옵션 패턴 검토** (P1):
   - **risk** 결정: low (read/계획만) / medium (write·외부 변경) / high (prod 영향).
   - **scope**: `general` 또는 `company`.
   - **policy_injection**: 기본 `required`. 외부 공개용일 때만 `forbidden`.
   - **agents**: 기본 `[claude, codex]`. 한쪽 전용은 정당화 필요.
   - **§2.5 적용 여부** — 사용자에게 옵션 표 제시:
     | 패턴 | 적용 조건 | 권고? |
     |---|---|---|
     | Steelman | 결정·분기 있음 | yes/no |
     | Option Table | 오픈 질문 있음 | yes/no |
     | Signals of Success | risk=medium/high | yes/no |
     | WHAT/HOW 분리 | 아키텍처 결정 포함 | yes/no |
     | Rationalization Table | PR/리뷰 류 | yes/no |
     | PRD AC | 구현·검증 류 | yes/no |
     | 8 dimensions Checklist | 요구사항 정리 류 | yes/no |

3. **outputs 계약 결정** (P3):
   - 산출 파일 경로 (`context/{slug}/...` 또는 `skills/...` 또는 산출물 없으면 `[]`).
   - `min_lines`: 빈 산출 방지 임계. 보통 20~80.
   - `required_sections`: 산출 파일에 반드시 있을 마크다운 헤더.

4. **SKILL.md 본문 작성** (P3 — 산출물 기반):
   skill-template.md §2.1 골격 그대로:
   - `# <Skill Title>`
   - `> **The Iron Law**: <한 줄>`
   - Persona 첫줄 (`You are operating as quivo <name>. Before <조건>, you MUST <행동>.`)
   - `## When to use`
   - `## Inputs` (Source options + Fallback + Bash/MCP 명시)
   - `## Process` (번호 매김, P1 sync gate 명시)
   - `## Iron Laws` (3~5개 MUST/MUST NOT, 헌법 7원칙 인용 가능)
   - `### BAD / GOOD` (2~4 쌍, anti-sycophancy)
   - `### Red Flags — STOP` (공통 + skill-specific)
   - `## Failure modes` (원인 → 대응, 재귀 종료 조건 (a/b/c))
   - (선택) `## Signals of Success`
   - (선택) `## Examples` — abstract placeholder (P5)
   - 적용한 §2.5 패턴들도 본문에 녹임

5. **skill.yaml 작성**:
   ```yaml
   name: <new-skill-name>
   version: 0.1.0
   description: "<SKILL.md frontmatter description 의 짧은 버전, ≤200 chars>"
   agents: [claude, codex]
   internal: <true 가 __ 접두사일 때만>
   requires: []
   ```

6. **trigger prompt 작성**:
   `tests/skill-triggering/prompts/<new-skill-name>.txt` — 자연어 1~3 문장, 사용자가 평소 쓸 법한 표현, 스킬 이름 *명시 안 함* (description 매칭 검증용).

7. **manifest.json 등록**:
   ```bash
   python3 - <<PY
   import json, hashlib
   from pathlib import Path
   m = json.load(open('manifest.json'))
   skill_dir = Path('skills/<new-skill-name>')
   combined = b''
   for fname in sorted(['skill.yaml', 'SKILL.md', 'setup.sh', 'setup.ps1']):
       fpath = skill_dir / fname
       if fpath.exists():
           combined += fpath.read_bytes()
   sha = hashlib.sha256(combined).hexdigest()
   m['skills'].append({'name':'<new-skill-name>', 'version':'0.1.0', 'sha256': sha})
   m['skills'].sort(key=lambda x: x['name'])
   json.dump(m, open('manifest.json','w'), indent=2, ensure_ascii=False)
   open('manifest.json','a').write('\n')
   PY
   ```

8. **검증** (P3 — 산출물 기반 강제):
   ```bash
   scripts/test-skill.sh <new-skill-name>
   ```
   5단계 모두 ✓ 가 아니면 Process 4 부터 재귀 (P4 Fix Loop). 통과까지 반복.
   - (선택) 통과 후 description 확정 전 *(선택) Triggering 검증* Phase 1회 권고 — 인접 atom 오발화 점검.

9. **PR 체크리스트 (`skill-template.md §5` 인용)**:
   - [ ] frontmatter 8필드 모두 존재
   - [ ] description 이 "what + when" 형식
   - [ ] outputs path 가 실제 Process 단계와 일치
   - [ ] 본문 5섹션 (When to use / Inputs / Process / Iron Laws / Failure modes) 존재
   - [ ] Iron Law block + Persona + BAD/GOOD + Red Flags 추가됨
   - [ ] Iron Laws 3~5개
   - [ ] `scripts/test-skill.sh <name>` 통과
   - [ ] `manifest.json` 에 등록
   - [ ] dogfooding 1회

10. **결과 보고 + 동기화**:
    - 생성된 파일 경로 목록
    - 적용한 §2.5 패턴 목록
    - test-skill.sh 통과 여부
    - 다음 행동 안내 — *"PR 생성하시겠어요?"* 묻고 사용자 OK 시 git workflow 진행 권유.

## Iron Laws


- MUST: 모르는 부분은 추측하지 않는다. 잘 모르는 영역은 사용자에게 명시적으로 묻는다 (P1 Sync, 헌법 #4 Evidence Over Assertion).
- MUST: `scripts/test-skill.sh <name>` 통과 전에는 *"완료"* 주장 금지 (헌법 #4 Evidence + The Iron Law).
- MUST: skill-template.md 의 구조를 그대로 따른다. 자체 발명한 섹션·필드 추가 금지 (헌법 #3 Parity).
- MUST: 새 스킬은 다른 quivo 의 *실행* 을 전제하지 않는다 (P6 Independence). Source options 패턴 필수.
- MUST: 본 스킬은 산출물을 *작성*만 한다. PR 생성·푸시는 사용자 명시 OK 후에만 (P1).
- MUST NOT: 사용자가 *"어떤 스킬"* 인지 명확히 하지 않은 상태에서 임의로 frontmatter 채우기 (P1 — 추정 금지).
- MUST: `description` 은 인접 atom 과의 *경계* 를 명시한다. 같은 도메인 스킬과 키워드가 겹치면 오발화한다. 모호하면 *(선택) Triggering 검증* Phase 로 확인.

### BAD / GOOD

- BAD: 사용자가 *"<X> 자동화 스킬 만들어줘"* 한 줄만 줬는데 즉시 SKILL.md 작성 시작.
- GOOD: Process 1 *"무엇을 / 언제 / 입력 / 출력"* 4개 항목 한 줄씩 받은 후에만 frontmatter 작성 시작.

- BAD: §2.5 패턴을 *전부* 적용해 SKILL.md 가 500줄 이상 비대화.
- GOOD: Process 2 표로 *해당 atom 에 진짜 필요한* 패턴만 yes 표시 → 본문에 녹임.

- BAD: SKILL.md 만 만들고 skill.yaml / trigger prompt / manifest 등록 생략 — *"나중에 하지 뭐"*.
- GOOD: Process 5~7 셋트로 항상 함께 생성. test-skill.sh 가 누락을 즉시 잡음.

- BAD: test-skill.sh 가 빨갛게 실패했는데 *"마이너한 거니까 PR 올리자"*.
- GOOD: Process 8 재귀 — 통과까지 반복. 통과 못 하는 이유 자체가 새 헌법 항목이 필요한 신호일 수 있음.

### Red Flags — STOP

다음 신호가 출력에 나타나려 하면 *즉시 stop* 하고 사용자에게 보고:

- "이 정도면 표준에 가까우니까" — skill-template 의 *그대로* 가 아니면 STOP.
- "manifest 는 나중에 갱신" / "skill.yaml 은 생략 가능" — 검증 우회 시도.
- test-skill.sh 실패를 *"환경 문제"* 로 합리화하려는 시도 — 환경 차이는 검증 로직 보강 케이스이지 우회 사유 아님.
- 사용자에게 묻지 않고 기존 스킬과 *비슷한 이름* 으로 자동 결정 — 충돌·중복 위험.

## Failure modes

- **사용자 의도가 모호** → Process 1 의 4개 항목 묻기. 답 안 받으면 진행 보류.
- **이름 충돌** (`skills/<name>/` 이미 존재) → 다른 이름 제안 + 기존 스킬 마이그레이션 의도인지 확인.
- **기존 스킬을 모방하다 표준에서 벗어남** → skill-template.md §2.1 골격으로 강제 회귀. 변형 합리화 금지.
- **`scripts/test-skill.sh` 실패** → 실패 단계 확인 후 Process 4~7 의 해당 부분 재실행. 3회 연속 동일 실패 시 사용자에게 보고.
- **manifest.json 병합 충돌** (다른 PR 의 신규 스킬과 동시) → 사용자에게 보고 + 재실행 권유. 자동 conflict resolve 금지.
- **인접 atom 오발화** (trigger 쿼리에서 다른 스킬이 발화) → *(선택) Triggering 검증* Phase 3 으로. 양쪽 description 에 상호 배제 키워드 추가. 한쪽만 고치면 재발.
- **재귀 종료 조건**:
  - (a) test-skill.sh 5단계 모두 ✓ + 사용자 *"PR 진행"* 명시 → 종료
  - (b) 사용자 *"일단 멈춤"* → 부분 산출물 보존 (skills/<name>/ 디렉토리는 유지)
  - (c) 사용자 *"폐기"* → `skills/<name>/`, `tests/skill-triggering/prompts/<name>.txt` 삭제, manifest.json rollback. *반드시 사용자 확인 후*.

## Signals of Success

새 스킬이 의도대로 작동하는지 확인하는 신호:

- **test-skill.sh 5단계 모두 ✓** — 즉시 측정 가능.
- **`quivo init --agent both --dir /tmp/test` 가 새 스킬을 정상 설치** — Claude 측 SKILL.md + Codex 측 prompt 양쪽 생성.
- **CI `lint.yml` 통과** — PR 머지 가능 신호.
- **첫 사용 후 사용자가 *"다시 호출하지 않고도 같은 자동화 다시 했음"*** — dogfooding 성공.
- 부정 신호:
  - "test-skill.sh 한두 번 통과 못 함" — 5단계 중 한두 개 fix 잊은 신호.
  - "trigger prompt 호출 시 다른 스킬이 발화함" — description 모호. 재작성 필요.

## (선택) Triggering 검증 — description 최적화

> **언제**: Process 8 (test-skill.sh) 통과 후, description 을 *확정하기 전* 1회. risk 무관 권고.
>
> **왜**: `description` 은 스킬 발화의 *유일한* 트리거 신호다. test-skill.sh `[4/5]` 는 trigger prompt *파일 존재* 만 확인할 뿐, 그 프롬프트가 *실제로 이 스킬을* 발화시키는지, 인접 atom 을 오발화시키지 않는지는 검증하지 않는다. 이 Phase 가 그 빈틈을 메운다.
>
> 본 Phase 는 *경량* 이다 — 파이썬 벤치마크 런타임·A/B 토큰 측정·HTML 뷰어 없이, 트리거 쿼리 세트로 판정만 한다.

1. **트리거 쿼리 20개 작성** (should 10 + should-not 10):
   - **should-trigger 10** — 사용자가 이 스킬을 원할 법한 *다양한* 표현. 도메인 어휘, 줄임말, 우회 표현, 다른 언어 혼용 포함. `tests/skill-triggering/prompts/<name>.txt` 의 1줄은 이 10개 중 대표 1개여야 한다.
   - **should-not-trigger 10** — *인접 스킬* 과 헷갈릴 표현. 특히 같은 도메인의 다른 atom (예: 같은 도메인의 두 atom 이 키워드를 공유하는 경우). 경계를 시험하는 함정 쿼리.
   - (선택) `tests/skill-triggering/prompts/<name>.trigger-eval.json` 사이드카로 저장 가능. test-skill.sh 가 강제하지 않으므로 필수는 아님.

2. **판정** (P3 — 산출물 기반):
   - 각 쿼리에 대해 *description 만 보고* 발화 여부를 판정. 사용자/리뷰어가 직접, 또는 별도 에이전트에게 "이 description 의 스킬이 이 쿼리에 발화하는가?" 를 물어 판정.
   - 결과를 표로: `| 쿼리 | 기대 | 판정 | 일치? |`.

3. **재작성** (오발화·미발화가 1개라도 있으면):
   - description 형식은 *"무엇(명사) + Use when(트리거 상황)"* 유지.
   - 인접 스킬과 *구별되는* 키워드를 description 에 명시해 경계를 세운다. 경계 키워드가 없으면 오발화는 반복된다.
   - **상호 보정**: 인접 atom 과 키워드가 겹쳐 오발화하면 *양쪽* description 을 함께 고친다. 한쪽만 고치면 재발.

4. **재판정 → 확정**: should 10/10 발화 + should-not 0/10 발화가 되면 description 확정. 안 되면 3 으로 재귀 (P4).

5. **결과 반영**: 확정된 description 을 SKILL.md frontmatter + skill.yaml 양쪽에 동일 적용. (불일치 시 lint 의 description 일관성과 무관하나, 두 파일 동기화는 작성자 책임.)

> **범위 밖 (의도적 제외)**: with/without 스킬 A/B 벤치마크, variance(mean±stddev) 측정, 토큰·시간 프로파일링, eval-viewer HTML — 이들은 *마크다운 스킬* 이 아니라 파이썬 런타임이라 quivo 헌법 #2(Self-Contained)·parity 와 충돌한다. 정말 필요하면 별도 `skill-eval` 스킬로 분리한다 (현재 미도입).

## Examples

> Examples 는 의존성 없는 추상 골격이다. 실제 호출 시 `<placeholder>` 자리를 도메인 값으로 치환한다.

### 입력 (사용자 메시지)

```
<X> 영역을 자동화하는 새 quivo 스킬 만들어줘.
사용 예: <한두 줄 시나리오>.
```

### 산출 골격

```
skills/<new-name>/
  SKILL.md             # 작성된 본문 (8필드 + 5섹션 + Iron Law block + Persona + BAD/GOOD + Red Flags)
  skill.yaml           # 5필드 (name/version/description/agents/internal/requires)

tests/skill-triggering/prompts/<new-name>.txt   # 자연어 1~3 문장

manifest.json          # 해당 행 추가, 알파벳 정렬
```

### 동기화 보고 (사용자에게 출력)

```
새 스킬 작성 완료: <new-name>
  - SKILL.md (<N> lines, 적용 패턴: <list>)
  - skill.yaml v0.1.0
  - trigger prompt
  - manifest.json 갱신

scripts/test-skill.sh <new-name>:
  [1/5] lint ✓
  [2/5] skill.yaml version ✓
  [3/5] manifest sha256 ✓
  [4/5] trigger prompt ✓
  [5/5] quivo init dry-run ✓

다음 단계: PR 생성하시겠어요? (git workflow 가이드 필요하면 알려주세요)
```
