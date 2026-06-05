# quivo 권한 매핑 규약

> **버전**: 0.1.0
> 본 문서는 스킬이 요구하는 도구/MCP 권한이 어떻게 선언·부여·강제되는지를 정의한다.
>
> 헌법 #7 (Policy as SSOT) 의 운영 규약. 상세 어댑터 동작은 `reference/agent-adapters.md` 참조.

---

## 1. 3계층 권한 모델

권한은 세 단계를 거쳐 흐른다: 스킬이 선언하고 → 조직이 부여하고 → 실행 환경이 강제한다.

1. **SKILL.md 본문 `## Inputs` 섹션 — 선언**
   스킬 저자가 자신의 스킬이 필요로 하는 도구/MCP를 자연어로 명시한다. 예: "Linear MCP 호출 필요". 본문에 두는 이유는 헌법 #3 (Parity) — Codex 변환 시 frontmatter는 제거되므로.

2. **`.quivo/policy.md` — 부여 의도**
   조직 owner가 어떤 스킬에 어떤 권한을 줄지 마크다운 표로 선언한다. 예: "linear-split → linear_mcp 허용". 부여되지 않은 권한은 허용되지 않은 것이다.

3. **`.claude/settings.json` (또는 Codex 측 동등 설정) — 기술적 강제**
   실제 실행 환경에서 허용·거부를 강제하는 JSON. v0.1 에서는 엔지니어가 매핑 카탈로그를 참조해 직접 편집한다. v0.2 에서는 quivo CLI 가 1·2 단계를 읽어 자동 생성한다.

세 계층은 책임이 다르다: 1번은 "내가 무엇이 필요한가"의 선언, 2번은 "조직이 무엇을 허락하는가"의 의도, 3번은 "환경이 무엇을 막을 수 있는가"의 강제. 이 셋이 어긋나면 (예: 본문에는 MCP 필요라 적혀 있으나 policy.md 표에 없음) PR 머지 거부 대상이 된다.

---

## 2. SKILL.md 본문 선언 규칙

`## Inputs` 섹션에 *필요한 도구/MCP* 를 명시한다. 파일 입력과 동급으로 적는다.

```markdown
## Inputs

- 요구사항 원문 (자연어)
- **MCP**: Linear (issue 생성/조회)
- **Bash**: `git worktree add`, `git status`
- **Read**: `~/.quivo/policy.md` (정책 확인)
```

### 규칙

- **MUST**: MCP 사용 시 `**MCP**:` 접두사로 표기. lint-skills 가 이 패턴을 검색해 manifest 생성.
- **MUST**: 특정 bash 명령이 필요하면 `**Bash**:` 접두사 + 명령 패턴.
- **MUST NOT**: 본문 어딘가에 묻혀서 적지 말 것. `Inputs` 섹션 외에 흩어지면 lint·정책 매핑이 어려움.
- frontmatter 에 `permissions:` 같은 9번째 필드를 추가하지 않는다 — Codex 변환 시 frontmatter 가 사라지기 때문 (헌법 #3).

---

## 3. `.quivo/policy.md` 부여 의도 형식

권한 부여는 카테고리별 표로 관리.

```markdown
# Company Policy (example)

## MCP 권한 부여

| 스킬 | 허용 MCP | 비고 |
|---|---|---|
| linear-split | linear (read+write) | issue 자동 생성 허용. dry-run 옵션 권장. |
| pr-review-pack | linear (read) | 상태 조회만 |
| (모든 스킬) | (없음, 기본) | MCP 호출 시 명시적 허용 필요 |

## Bash 권한 부여

| 스킬 | 허용 명령 |
|---|---|
| worktree-plan | git status, git branch, git log |
| (v0.2) implementation | git worktree add, git checkout |

## Prod 변경 절차

(별도 섹션 — Decision #3 의 4개 카테고리 중 하나)
- Prod DB 변경: DBA 승인 + Linear 티켓 + 롤백 플랜
- Prod 배포: 변경관리 절차 통과
- ...

## 코드/PR 규칙

(별도 섹션)
- 커밋 메시지 형식: `<scope>: <subject>`
- PR 리뷰어 최소 1명
- ...

## 도메인 규칙 (회사별)

(별도 섹션)
- `aws-access` 호출 전 SG IP 등록 확인
- ...
```

### 규칙

- **MUST**: 새 스킬이 MCP/특수 권한을 요구하면 PR 리뷰어가 본 문서에 행 추가를 요구한다.
- **MUST NOT**: 표에 없는 권한은 부여된 것이 아니다. 누락은 거부와 동치.
- **MAY**: 부여 + 조건부 (예: "dry-run 옵션 사용 시에만") 명시 가능.

---

## 4. `settings.json` 기술적 강제

### v0.1 — 수동

엔지니어가 본 문서의 ["권한 → settings 매핑 카탈로그"](#7-권한--settings-매핑-카탈로그) 를 참조해 직접 편집.

```jsonc
// .claude/settings.json
{
  "permissions": {
    "allow": [
      "mcp__plugin_linear_linear__*",
      "Bash(git status:*)",
      "Bash(git worktree add:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)"
    ]
  }
}
```

```jsonc
// .codex/* (Codex CLI 권한 설정 — Codex CLI 매뉴얼 따름)
```

### v0.2 — 자동

`quivo init` 이 다음 흐름으로 settings.json 생성:

1. 설치할 스킬들의 SKILL.md `Inputs` 섹션 파싱
2. `.quivo/policy.md` 에서 부여 확인
3. 매칭되는 settings.json 항목 추가
4. 미부여 권한은 *경고 + 사용자에게 정책 추가 요청*

별도 quivo CLI 변경 PR 트랙. v0.1 출시 후 진행.

---

## 5. Failure mode 템플릿 — 권한 누락 시

스킬 본문 `## Failure modes` 섹션에 반드시 권한 누락 케이스 포함:

```markdown
## Failure modes

- **MCP 호출 거부 (Linear MCP 권한 없음)** →
  1. 사용자에게 보고: "현재 환경에서 Linear MCP 가 비활성화됨"
  2. 대체 동작: Linear payload (제목/설명/AC) 를 markdown 으로 출력
  3. 사용자가 수동으로 Linear 에 입력하도록 안내
  4. 산출 파일 (`context/{slug}/03-linear-plan.md`) 에 "manual mode" 표시
```

### 규칙

- **MUST**: 권한 없을 때 *읽기 전용 모드 / 수동 fallback / 명확한 가이드* 중 하나로 degrade.
- **MUST NOT**: 권한 없는 상태에서 추측해서 진행 (헌법 #4 위반).
- **MUST NOT**: 권한 우회 시도 (settings.json 직접 편집 권유 등).

---

## 6. PR 리뷰 체크리스트

새 스킬이 권한을 요구하는 PR 머지 전:

- [ ] SKILL.md `Inputs` 에 필요한 MCP/Bash 명시
- [ ] `.quivo/policy.md` 의 권한 부여 표에 해당 행 추가 (또는 기존 행 재사용)
- [ ] `Failure modes` 에 권한 누락 케이스 + degrade 동작 명시
- [ ] [매핑 카탈로그](#7-권한--settings-매핑-카탈로그) 에 새 권한 추가 (해당 시)
- [ ] dogfooding: 권한 있는 환경 + 권한 없는 환경 각각 1회 실행

---

## 7. 권한 → settings 매핑 카탈로그

자주 쓰이는 권한의 settings.json 변환 reference. PR 으로 추가/수정.

| Inputs 선언 | Claude `.claude/settings.json` | Codex CLI |
|---|---|---|
| `**MCP**: Linear (read+write)` | `"allow": ["mcp__plugin_linear_linear__*"]` | (Codex CLI 매뉴얼) |
| `**MCP**: Linear (read only)` | `"allow": ["mcp__plugin_linear_linear__get_*", "mcp__plugin_linear_linear__list_*"]` | |
| `**Bash**: git worktree add` | `"allow": ["Bash(git worktree add:*)"]` | |
| `**Bash**: git status, git branch` | `"allow": ["Bash(git status:*)", "Bash(git branch:*)"]` | |
| `**Read**: ~/.quivo/policy.md` | (default 허용, deny 없으면 OK) | |

---

## 8. 헌법 연결

| 헌법 원칙 | 본 규약의 강제점 |
|---|---|
| #2 Self-Contained | 권한 없는 환경에서도 degrade 모드로 동작 |
| #3 Parity | 선언은 본문에 (Codex parity), JSON 변환은 어댑터 책임 |
| #4 Evidence | 권한 누락 시 추측 금지, 명시적 fallback |
| #7 Policy SSOT | 권한 부여는 `.quivo/policy.md` 한 곳에서만 |
