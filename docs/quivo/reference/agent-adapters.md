# Reference — Claude Code / Codex CLI 어댑터 동작

> quivo CLI 가 SKILL.md 를 각 에이전트별 위치/형식으로 변환하는 규칙. 스킬 작성자가 알아두면 좋은 세부 내용을 모은 참조 문서.
>
> 1차 출처: `src/quivo/adapters/claude.py`, `src/quivo/adapters/codex.py`, `src/quivo/adapters/base.py`

---

## 1. 두 어댑터의 차이 한눈에

| 항목 | Claude Code | Codex CLI |
|---|---|---|
| 설치 경로 | `.claude/skills/<name>/SKILL.md` | `.codex/prompts/<name>.md` |
| Setup 스크립트 | `.claude/skills/<name>/setup.{sh,ps1}` | `.codex/scripts/<name>/setup.{sh,ps1}` |
| Frontmatter | 보존 | **제거** |
| 본문 헤더 | 추가 안 함 | **`# /<skill-name>` 자동 prepend** |
| Path 치환 | 안 함 | `.claude/skills/<name>/` → `.codex/scripts/<name>/` |
| Policy 주입 | 본문 끝에 appendix | 본문 끝에 appendix (frontmatter 제거 후) |

---

## 2. Claude Code 어댑터

`src/quivo/adapters/claude.py`

### 동작

1. 대상 디렉토리 `.claude/skills/<name>/` 생성
2. `SKILL.md`, `setup.sh`, `setup.ps1` 중 존재하는 파일을 복사
3. `SKILL.md` 는 정책 주입 후 기록 (`_append_policy` 적용)
4. 충돌 검사 (`--force` 없으면 `ConflictError`)

### 결과 구조

```
.claude/skills/req-intake/
  SKILL.md         # 원본 frontmatter + 본문 + (Company Policy appendix)
  setup.sh         # 있으면 그대로 복사
```

### 함의

- frontmatter 가 그대로 살아 있어 Claude Code 의 description 매칭이 정상 동작
- 본문 어느 위치에서든 `.claude/skills/<name>/` 경로 참조 가능

---

## 3. Codex CLI 어댑터

`src/quivo/adapters/codex.py`

### 동작 (`_convert_to_codex_prompt`)

1. **Frontmatter 제거** — `^---\\n...\\n---\\n` 블록을 지움 (regex `re.DOTALL | re.MULTILINE`)
2. **Path 치환** — `.claude/skills/<name>/` → `.codex/scripts/<name>/` (스킬명 정확 매칭 + generic fallback)
3. **헤더 추가** — `# /<skill-name>\\n\\n` 을 맨 위에 prepend
4. **정책 주입** — `_append_policy` 로 본문 끝에 appendix

### 결과 구조

```
.codex/prompts/req-intake.md       # # /req-intake + 본문 + (Company Policy)
.codex/scripts/req-intake/
  SKILL.md                          # 원본 frontmatter + 본문 + (Company Policy), 계약 검증용
  setup.sh                          # 있으면 복사
```

### 함의

- **prompt 파일에서는 frontmatter 가 제거된다** — Codex 슬래시 프롬프트에는 `name`, `description`, `version`, `outputs` 가 노출되지 않음
- 원본 `SKILL.md` 는 `.codex/scripts/<name>/SKILL.md` 에 sidecar 로 보존되어 `pipeline` 같은 계약 검증 스킬이 `outputs:` 를 읽을 수 있다
- 따라서 스킬 directive (Iron Laws, Process, Failure modes) 는 **본문에 있어야** 한다
- frontmatter 는 두 용도로만 살아 있다:
  - quivo CLI 와 `scripts/lint-skills.py` 가 읽음 (메타데이터·검증)
  - Claude Code 가 매칭에 사용
  - Codex 설치본의 sidecar `SKILL.md` 에서 output contract 검증에 사용

---

## 4. Policy 주입 — `_append_policy` 공통 동작

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

## 5. Parity 작성 가이드 — 스킬 저자가 지킬 규칙

| 규칙 | 이유 |
|---|---|
| 모든 directive (MUST/MUST NOT/Iron Laws) 는 **본문에** | frontmatter 가 Codex 에서 사라지기 때문 |
| Claude 전용 UI 요소 (예: `<details>`, 토글 흐름) **회피** | Codex 는 plain markdown 환경 |
| 경로 참조는 `.claude/skills/<name>/` 형식 사용 (자동 치환됨) | 두 에이전트 모두 올바르게 해석 |
| `setup.sh` / `setup.ps1` 외 추가 파일 의존 **금지** (v0.1) | 어댑터가 현재 이 3개만 복사 |
| `description` 은 한 문장에 *무엇 + Use when ~* 모두 포함 | description 매칭 신뢰도. karpathy 패턴 |
| `EXAMPLES.md` 같은 사이드카는 **현재 미지원** (v0.2 이후) | 채택 시 어댑터 확장 필요 |

---

## 6. 확인 명령

스킬 변환 결과를 로컬에서 보고 싶으면:

```bash
# 임시 디렉토리에 배포
quivo init --dir /tmp/test --agent both --force

# Codex 변환 결과 확인
cat /tmp/test/.codex/prompts/req-intake.md

# Claude 그대로 보존 확인
cat /tmp/test/.claude/skills/req-intake/SKILL.md
```

---

## 7. v0.2 이후 확장 아이디어 (현재 미구현)

- `EXAMPLES.md` 분리 + 어댑터가 Codex 측에서 본문에 inline
- `policy_injection: forbidden` 자동 처리
- frontmatter `permissions:` 기반 `.claude/settings.json` 자동 생성
- Claude Code 측 `.cursor-plugin/` 같은 추가 어댑터
