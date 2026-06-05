# quivo Constitution

> **버전**: 0.1.0
> **상태**: Draft
> **변경 절차**: PR 머지 + Round 검토 (Codex + Claude). 모든 변경은 버전 bump와 `CHANGELOG.md` 항목.

quivo 의 모든 스킬·도구·문서가 따르는 **불변 원칙**. 스킬 실행 직전에 컨텍스트에 주입되거나, 사람이 quivo를 검토할 때 기준점이 된다.

---

## 1. Atoms Before Orchestration

각 스킬은 **단독으로 실행 가능**해야 한다. `pipeline` 같은 오케스트레이터에 의존해 동작하는 스킬은 v0.1에 받지 않는다.

- **MUST**: 입력과 출력이 한 스킬 안에서 명시되어야 한다.
- **MUST NOT**: 다른 *공개 (public)* 스킬의 상태/실행을 전제하지 않는다.
- **MAY**: *private (`__` prefix) 스킬* 은 *내부 헬퍼* 역할을 한다. 공개 스킬이 private 스킬을 *내부적으로 호출* 하는 것은 허용된다 (예: 공개 스킬이 `__auth-helper` 같은 private 스킬의 인증 단계를 내부 호출). 단 사용자는 *공개 스킬 하나만* 호출하면 되어야 하며, private 스킬의 존재를 알 필요는 없다.
- **이유**: 첫 사용자가 한 스킬만으로 가치를 얻을 수 있어야 한다. 파이프라인은 그 위에 얹는 layer다. private 스킬은 사용자에게 노출되지 않는 *재사용 가능한 단계* 로 격하된다 (스킬은 맞지만 외부 호출 대상이 아님).

## 2. Self-Contained

quivo는 **OMC, ralph, autopilot 같은 외부 런타임을 요구하지 않는다**. Claude Code 또는 Codex CLI 둘 중 하나만 있으면 동작한다.

- **MUST**: 모든 스킬은 vanilla Claude Code / Codex CLI 환경에서 검증된다.
- **MAY**: OMC 사용자가 wrapping 하는 건 자유.
- **이유**: 모든 엔지니어가 특정 런타임(OMC 등)을 설치하리란 기대는 비현실적. 첫 사용자도 1급 시민.

## 3. Parity Between Claude Code and Codex CLI

스킬은 두 에이전트에서 **행동 의도가 동일**해야 한다. 파일 형태가 동일할 필요는 없다.

- **MUST**: SKILL.md 가 canonical 원본. `quivo init --agent codex` 가 자동 변환 (frontmatter 제거 + `# /<skill-name>` 헤더).
- **MUST**: 본문에 Claude-specific UI 요소(예: `<details>` 의존 흐름)를 두지 않는다.
- **이유**: 팀마다 다른 에이전트를 써도 동일한 정책·동일한 산출물.

## 4. Evidence Over Assertion (Iron Law)

"완료/통과/동작 확인" 류의 주장은 **검증 가능한 산출물(파일, 명령 출력, 테스트 결과)** 없이는 금지된다.

- **MUST**: 스킬이 산출물을 만들었다고 주장할 때, 산출물의 경로와 최소 크기(또는 필수 섹션)를 SKILL.md `outputs:` 에 미리 선언한다.
- **MUST**: `pipeline` 은 phase 전환 직전에 각 atom의 `outputs:` 계약을 검증한다.
- **이유**: superpowers의 verification-before-completion 원칙 차용. 거짓 완료는 시간을 가장 많이 잡아먹는다.

## 5. Surgical Scope

각 스킬은 **요청 범위 밖의 변경을 만들지 않는다**.

- **MUST NOT**: 무관한 파일 수정, 무관한 리팩토링, 무관한 추측성 개선.
- **MUST**: 변경 전, 영향 받는 파일 목록을 사용자에게 보여주거나 `context/{slug}/` 산출물에 기록한다.
- **이유**: Karpathy 원칙 차용. AI의 가장 흔한 실수가 "이왕 만진 김에 더 만지기".

## 6. Skip Is Allowed, But Logged

파이프라인 phase는 모두 **권고**다. 사용자/AI가 판단해 건너뛸 수 있다. 단 **건너뜀은 기록**한다.

- **MUST**: skip 시 `context/{slug}/STATUS.md` 에 phase 이름 + skip 사유.
- **MUST NOT**: 파이프라인이 사용자 의지에 반해 phase를 강제 실행하지 않는다.
- **이유**: spec-kit 의 게이트 강제는 좋지만 사람의 판단 권한이 더 우선. 단 감사 가능성은 유지.

## 7. Policy as Single Source of Truth

회사 정책은 `.quivo/policy.md` 한 곳에서 관리되고, **모든 스킬에 자동 주입**된다.

- **MUST**: 정책은 스킬 본문 규칙을 **재정의하지 않는다** (appendix 위치 고정).
- **MUST**: 정책 충돌 시 우선순위 = 스킬 본문 > policy.md.
- **MUST**: 권한 부여(예: MCP 사용)는 policy.md 에 카테고리별로 선언, quivo CLI가 settings.json에 반영(v0.2).
- **이유**: 정책이 사방에 흩어지면 일관성·감사가 무너진다. 단일 진실 소스 유지.

---

## 메타 — 헌법 자체의 운영 규칙

- 본 헌법은 **모든 스킬 작성·리뷰의 기준점**이다. 스킬이 헌법 조항과 충돌하면 PR 머지 거부.
- 새 원칙 추가/기존 원칙 수정은 PR 필수. 본 문서 `## N` 헤더는 안정 ID로 취급한다 (재번호 금지, 폐기는 `[DEPRECATED]` 표시).
- 본 헌법은 LLM이 읽고 자동 적용할 수 있도록 **명령형·간결**하게 유지한다. 1페이지를 넘기지 않는다.
- quivo v0.1 시점의 7원칙은 다음 사고/실패 사례가 누적되어도 **억지로 늘리지 않는다**. 원칙 추가는 진짜 패턴이 보일 때만.

---

## 빠른 참조 (스킬 작성자가 외워야 할 7줄)

1. 스킬은 단독으로 동작한다 (atoms before orchestration).
2. quivo 는 OMC 없이도 동작한다 (self-contained).
3. Claude Code 와 Codex CLI 양쪽에서 동일 행동 (parity).
4. 검증 없는 완료 주장은 금지 (evidence over assertion).
5. 요청 범위 밖을 만지지 않는다 (surgical scope).
6. Skip 가능, 단 STATUS.md 에 기록 (skip is logged).
7. 정책은 policy.md 한 곳, 스킬 본문이 우선 (policy SSOT).
