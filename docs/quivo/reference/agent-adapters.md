# Reference — Claude Code / Codex CLI 어댑터 동작

> quivo CLI 가 SKILL.md 를 각 에이전트별 위치/형식으로 변환하는 규칙. 스킬 작성자가 알아두면 좋은 세부 내용을 모은 참조 문서.
>
> 1차 출처: `src/quivo/adapters/base.py`, `src/quivo/adapters/claude.py`, `src/quivo/adapters/codex.py`, `src/quivo/context.py`, `src/quivo/cleanup.py`

---

## 1. 두 어댑터의 차이 한눈에

| 항목 | Claude Code | Codex CLI |
|---|---|---|
| 설치 경로 | `.claude/skills/q-<name>/SKILL.md` | `.agents/skills/q-<name>/SKILL.md` |
| Setup 스크립트 | `.claude/skills/q-<name>/setup.{sh,ps1}` | `.agents/skills/q-<name>/setup.{sh,ps1}` |
| Frontmatter | 허용 키만 유지 + 나머지는 `metadata:` 아래로 | 허용 키만 유지 + 나머지는 `metadata:` 아래로 |
| Path 치환 | `.claude/skills/<n>/` → `.claude/skills/q-<n>/` | `.claude/skills/<n>/` → `.agents/skills/q-<n>/` |
| Policy 주입 | 본문 끝에 appendix | 본문 끝에 appendix |
| 컨텍스트 파일 | `CLAUDE.md` 관리 블록 | `AGENTS.md` 관리 블록 |

두 어댑터 모두 [open agent skills standard](https://agentskills.io) 형식의
SKILL.md 를 거의 그대로 설치한다. 설치 로직은 `BaseAdapter.install()` 하나로
공유되고, 어댑터별로는 설치 루트·경로 치환 대상·컨텍스트 파일명만 다르다.

### `q-` prefix (네임스페이스)

spec-kit 의 `speckit-<name>` 패턴을 차용해, 설치되는 스킬은 디렉토리명과
frontmatter `name:` 모두 `q-<name>` 으로 네임스페이스된다. 대상 프로젝트가
직접 만든 스킬과 절대 충돌하지 않는다. 호출명도 따라간다:

- Claude Code: `/q-ripple`
- Codex CLI: `$q-ripple`

스킬명은 validator 의 `^[a-z0-9-]+$` 요건에 맞게 정규화된다 — 소문자화,
비허용 문자(`_` 등)는 `-` 로 치환 (예: `__aws-access` → `q-aws-access`).

### Frontmatter 정규화

에이전트 스킬 validator 가 허용하는 top-level frontmatter 키는
**`name`, `description`, `license`, `allowed-tools`, `metadata`** 뿐이다.
Codex 는 그 외 키가 있으면 스킬을 invalid 로 보고 **discovery 에서 제외**한다.

그래서 두 어댑터 모두 설치 시 frontmatter 를 재작성한다:

- 허용 키는 그대로 유지 (`name:` 은 `q-<name>` 으로 치환)
- 그 외 키(`version`, `scope`, `agents`, `risk`, `policy_injection`,
  `outputs` …)는 표준이 허용하는 자유 형식 키인 **`metadata:` 아래로 이동**
  (기존 `metadata:` 가 있으면 병합)

```yaml
# 소스                          # 설치본
---                             ---
name: ripple                    name: q-ripple
description: ...                description: ...
version: 0.1.0                  metadata:
risk: low                         version: 0.1.0
outputs: [...]                    risk: low
---                               outputs: [...]
                                ---
```

---

## 2. Claude Code 어댑터

`src/quivo/adapters/claude.py` — `skills_root_parts=(".claude","skills")`, `context_file="CLAUDE.md"`

### 결과 구조

```
.claude/skills/q-req-intake/
  SKILL.md         # frontmatter(name: q-req-intake) + 본문(경로 치환) + (Company Policy appendix)
  setup.sh         # 있으면 경로 치환 후 기록 (실행 권한 보존)
```

### 함의

- frontmatter 가 그대로 살아 있어 Claude Code 의 description 매칭이 정상 동작
- 본문의 `.claude/skills/<name>/` 참조는 `q-` prefix 경로로 자동 치환됨

---

## 3. Codex CLI 어댑터

`src/quivo/adapters/codex.py` — `skills_root_parts=(".agents","skills")`, `context_file="AGENTS.md"`

Codex 는 open agent skills 표준을 채택해 다음 위치에서 스킬을 읽는다:

| 범위 | 경로 |
|---|---|
| REPO | `$CWD/.agents/skills` (CWD 부터 저장소 루트까지 상향 스캔) |
| USER | `$HOME/.agents/skills` |
| ADMIN | `/etc/codex/skills` |
| SYSTEM | Codex 번들 |

quivo 는 대상 프로젝트의 **REPO 범위** (`<target>/.agents/skills/q-<name>/`)에 설치한다.

### 결과 구조

```
.agents/skills/q-req-intake/
  SKILL.md         # frontmatter(name: q-req-intake) + 본문(경로 치환) + (Company Policy appendix)
  setup.sh         # 있으면 경로 치환 후 기록 (실행 권한 보존)
```

### 함의

- frontmatter 가 validator 허용 키만 갖도록 정규화되므로 Codex discovery 와
  description 기반 implicit invocation 이 동작
- 명시 호출은 `$q-req-intake` 형식 (Codex 의 `$` 멘션 / `/skills` 선택기).
  `/이름` 슬래시 명령이 필요하면 `~/.codex/prompts/<name>.md` 가 별도로
  필요한데, quivo 는 의도적으로 만들지 않는다 (스킬이 배포 단위)
- `pipeline` 같은 계약 검증 스킬은 설치본에서 `metadata.outputs` 를 읽는다
  (소스의 `outputs:` 가 설치 시 `metadata:` 아래로 이동)
- 스킬을 끄려면 `~/.codex/config.toml` 에 `[[skills.config]]` 항목으로
  `enabled = false` 지정 (삭제 불필요)
- `agents/openai.yaml` (표시 이름, `allow_implicit_invocation` 정책, 도구 의존성)
  은 v0.1 미지원 — 채택 시 어댑터 확장 필요

---

## 4. 컨텍스트 파일 관리 — `src/quivo/context.py`

spec-kit 의 `context_file` 개념을 차용. `quivo init` / `quivo sync` 가 대상
프로젝트 루트의 에이전트 컨텍스트 파일에 **관리 블록**을 만들어 설치된 스킬
목록(호출명·버전·description)을 유지한다.

- Claude Code → `CLAUDE.md`, Codex CLI → `AGENTS.md`
- 블록은 `<!-- quivo:skills:begin -->` / `<!-- quivo:skills:end -->` 마커로 구분
- 마커 밖의 기존 내용은 절대 건드리지 않는다. 블록이 있으면 교체, 없으면 끝에 append, 파일이 없으면 생성
- 멱등 — 재실행해도 블록은 1개

---

## 5. 레거시 정리 — `src/quivo/cleanup.py`

구버전 quivo 레이아웃(`.codex/prompts/<name>.md` + `.codex/scripts/<name>/`,
prefix 없는 `.claude/skills/<name>/`, `.agents/skills/<name>/`)을
`quivo init` / `quivo sync` 가 자동 제거한다. 대상은 `.quivo-lock.json` 에
기록된 quivo 관리 스킬뿐이므로 프로젝트 자체 스킬은 건드리지 않는다.

`quivo sync` 는 버전이 같아도 **현재 레이아웃에 설치본이 없으면** 재설치한다
(missing 감지). 따라서 구버전 레이아웃 프로젝트는 `quivo sync` 한 번으로
새 레이아웃으로 수렴한다.

`.quivo-lock.json` 의 스킬 항목에는 설치된 파일 목록(`files`)이 기록된다 —
spec-kit 의 매니페스트 기반 제거를 차용한 것으로, 향후 uninstall 에 쓰인다.

---

## 6. Policy 주입 — `_append_policy` 공통 동작

`src/quivo/adapters/base.py`

```
[원본 본문]
\n\n---\n\n
## Company Policy (from .quivo/policy.md)\n\n
[policy.md 내용]\n
```

두 어댑터 모두 동일 형식으로 본문 끝에 부착. target `.quivo/policy.md` 가 있으면 우선 사용하고, 없으면 번들 `.quivo/policy.md` 를 사용한다. `--no-policy` 지정 시 생략.

`policy_injection: forbidden` frontmatter 가 있는 스킬은 quivo CLI 가 이 단계를 skip 해야 함 (v0.1 미구현 — quivo 측 별도 트랙).

---

## 7. Parity 작성 가이드 — 스킬 저자가 지킬 규칙

| 규칙 | 이유 |
|---|---|
| 모든 directive (MUST/MUST NOT/Iron Laws) 는 **본문에** | frontmatter 는 메타데이터·매칭용 — 비허용 키는 설치 시 `metadata:` 아래로 이동하므로 지시문을 frontmatter 에 두면 안 됨 |
| 스킬명은 `^[a-z0-9-]+$` 만 사용 (`_` 금지) | validator 요건. 위반 시 설치 시점에 자동 정규화되지만 소스부터 맞추는 게 안전 |
| Claude 전용 UI 요소 (예: `<details>`, 토글 흐름) **회피** | Codex 는 plain markdown 환경 |
| 경로 참조는 `.claude/skills/<name>/` 형식 사용 (자동 치환됨) | 설치 시 에이전트별 `q-` prefix 경로로 올바르게 변환 |
| 스킬명을 본문에서 자기 참조할 때는 호출명이 `q-<name>` 이 됨을 유의 | 설치본의 호출명은 prefix 포함 |
| `setup.sh` / `setup.ps1` 외 추가 파일 의존 **금지** (v0.1) | 어댑터가 현재 이 3개만 설치 |
| `description` 은 한 문장에 *무엇 + Use when ~* 모두 포함 | 두 에이전트 모두 description 매칭으로 implicit invocation. Codex 는 스킬 목록이 길면 description 을 축약하므로 핵심 트리거 단어를 앞쪽에 |
| `EXAMPLES.md` 같은 사이드카는 **현재 미지원** (v0.2 이후) | 채택 시 어댑터 확장 필요 |

---

## 8. 확인 명령

스킬 변환 결과를 로컬에서 보고 싶으면:

```bash
# 임시 디렉토리에 배포
quivo init --dir /tmp/test --agent both --force

# Codex 설치 결과 확인 (frontmatter 보존 + q- prefix)
cat /tmp/test/.agents/skills/q-req-intake/SKILL.md

# Claude 설치 결과 확인
cat /tmp/test/.claude/skills/q-req-intake/SKILL.md

# 컨텍스트 파일 관리 블록 확인
cat /tmp/test/CLAUDE.md /tmp/test/AGENTS.md
```

---

## 9. v0.2 이후 확장 아이디어 (현재 미구현)

- `references/`, `assets/`, `scripts/` 하위 디렉토리 복사 (표준 스킬 레이아웃 완전 지원)
- `agents/openai.yaml` 생성 — Codex 앱 표시 메타데이터, `allow_implicit_invocation` 정책
- `quivo uninstall` — lock 의 `files` 매니페스트 기반 제거
- `EXAMPLES.md` 사이드카 지원
- `policy_injection: forbidden` 자동 처리
- frontmatter `permissions:` 기반 `.claude/settings.json` 자동 생성
- `.cursor-plugin/` 같은 추가 어댑터
