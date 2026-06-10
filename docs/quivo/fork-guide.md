# Fork Guide — 회사용 quivo 만들기

> quivo 를 포크해 **회사 전용 스킬 배포 레포**로 만드는 단계별 가이드.
> 한 번 세팅하면, 회사 엔지니어 전원이 같은 버전의 스킬을 Claude Code·Codex 등에 설치해 쓴다.

---

## 큰 그림

```
chordpli/quivo  ── fork ──▶  my-company/quivo
   (템플릿)                     (회사 소유, 자유롭게 수정)
                                  │
                                  ├─ skills/ 에 회사 스킬 추가
                                  ├─ .quivo/policy.md 에 회사 정책
                                  ├─ skills/VERSION 올리고 push
                                  │
                                  ▼  Release Skills Bundle 워크플로
                              skills-vX.Y.Z 릴리스 (skills-bundle.tar.gz)
                                  │
                                  ▼  엔지니어 머신
                              quivo init / quivo sync
                                  → .claude/skills/, .agents/skills/ ...
```

핵심: 포크하면 업스트림과 끊긴다. 그게 **의도**다 — 회사가 자기 스킬을 완전히 소유한다.

---

## 사전 준비

- Python 3.10+, [`uv`](https://docs.astral.sh/uv/)
- 회사 GitHub 조직 (public 또는 private 레포 생성 권한)

---

## 1. 포크

`chordpli/quivo` → `my-company/quivo` 로 **포크 또는 클론**:

- **public** 으로 운영 → 포크해도 되고 클론해도 된다.
- **private** 으로 운영 → 포크로는 안 된다 (공개 레포의 포크는 항상 public). **클론 후 새 private 레포로 push** 한다:
  ```bash
  git clone https://github.com/chordpli/quivo.git my-company-quivo
  cd my-company-quivo
  git remote set-url origin https://github.com/my-company/quivo.git   # 미리 만든 private 레포
  git push -u origin main
  ```

private 배포도 완전히 지원된다(§6).

> 이 가이드 전체에서 `my-company` 는 **자리표시자**다 — 네 GitHub org/사용자명으로 바꿔라.
> (`{my-company}`·`<my-company>` 같은 괄호 표기는 쓰지 않는다: `<`/`>` 는 셸 리다이렉션이라 복붙 시 깨진다.)

## 2. GitHub Actions 켜기

포크된 레포는 Actions 가 **기본 비활성**이다. 레포 → **Actions** 탭 → 활성화.
이게 꺼져 있으면 릴리스 워크플로가 돌지 않는다.

## 3. CLI 가 내 포크를 보게 하기

레포 루트 [`quivo.yml`](../../quivo.yml) 한 줄만 바꾼다:

```yaml
repo: my-company/quivo
```

해석 우선순위: `QUIVO_REPO` 환경변수 > `quivo.yml` 의 `repo:` > CLI 내장 기본값.
즉 엔지니어는 아무것도 export 하지 않아도 `quivo.yml` 덕에 올바른 소스를 본다.

## 4. 회사 스킬로 채우기

1. **예시 정리** — 필요 없으면 `skills/aws-access/` 를 지운다. `author-skill` 은 남겨두면 새 스킬 작성에 도움이 된다.
2. **새 스킬 추가** — 에이전트에게 `author-skill` 을 호출해 표준에 맞춰 작성하게 한다.
   작성 표준은 [`docs/quivo/`](./) 에 있다:
   - [`constitution.md`](./constitution.md) — 7원칙
   - [`skill-template.md`](./skill-template.md) — frontmatter 8필드 + 본문 5섹션
   - [`permissions.md`](./permissions.md) — MCP/Bash 권한 모델
   - [`reference/agent-adapters.md`](./reference/agent-adapters.md) — Claude/Codex 변환 규칙
   - [`reference/env-config.md`](./reference/env-config.md) — 환경값 분리 패턴
3. **회사 정책** — [`.quivo/policy.md`](../../.quivo/policy.md) 의 자리표시자를 회사 규칙으로 채운다.
   이 내용이 설치되는 **모든 스킬 본문 끝에 자동 주입**된다.
4. **환경 설정 템플릿** — 스킬이 인프라값을 쓰면 [`.quivo/config.example.yml`](../../.quivo/config.example.yml) 에 섹션을 추가한다. 엔지니어는 이걸 `.quivo/config.yml`(gitignored)로 복사해 채운다.

> 새 스킬마다 `scripts/test-skill.sh <name>` 5단계(lint / version / manifest sha256 / trigger prompt / quivo init dry-run)를 통과시킨다.

## 5. 버전 올리고 릴리스

```bash
echo "0.2.0" > skills/VERSION   # semver 증가
git add -A && git commit -m "skills: add <new-skill>" && git push
```

`skills/**` 변경이 `main` 에 push 되면 [`Release Skills Bundle`](../../.github/workflows/release-skills.yml)
워크플로가 자동으로:
- `manifest.json`(스킬별 sha256) 생성
- `skills-bundle.tar.gz` 빌드 (`skills/` + manifest + `.quivo/policy.md` + config example)
- `skills-v0.2.0` 태그로 GitHub Release 발행 (내 레포에)

수동 실행: Actions → Release Skills Bundle → Run workflow (version 입력 가능).

## 6. 엔지니어 설치

```bash
# 권장: CLI 를 PATH 에 설치 (이후 어디서든 quivo)
uv tool install git+https://github.com/my-company/quivo.git    # 또는: pipx install git+...
quivo init           # 최신 skills-v* 릴리스를 받아 현재 프로젝트에 설치
quivo sync           # 스킬 콘텐츠만 최신으로 새로고침
quivo update         # quivo CLI 자체를 최신 cli-v* 로 업그레이드

# 대안: 설치 없이 alias (매 실행 시 재해석)
echo 'alias quivo="uvx --from git+https://github.com/my-company/quivo.git quivo"' >> ~/.zshrc && source ~/.zshrc
```

---

## 배포 모드

| 모드 | 동작 | private 처리 | 적합 |
|------|------|--------------|------|
| **A. Releases** (기본) | 포크가 `skills-v*` 번들 발행 → CLI 다운로드+캐시(`~/.quivo/cache/`) | 엔지니어가 read 토큰 1회 | 다수 배포, 불변 버전 핀, sha256 무결성, 오프라인 캐시 |
| **B. Local/clone** | 레포 클론 후 로컬에서 바로 설치 | 기존 git 인증 그대로(토큰 불필요) | 메인테이너, 소규모 |

```bash
# 모드 B — 릴리스 없이 로컬 체크아웃에서 설치
export QUIVO_LOCAL_SKILLS=/path/to/quivo/skills
quivo init --agent both
```

## private 레포

완전히 지원된다.

- **릴리스 빌드**: private 레포에서도 `GITHUB_TOKEN`(워크플로 자동 주입)으로 동작.
- **다운로드**: CLI 가 asset API + Bearer 토큰으로 받는다. 엔지니어는 read 토큰을 1회만 제공:
  - `export GH_TOKEN=...` (또는 `GITHUB_TOKEN`), 또는
  - CLI 가 권한 오류 시 자동으로 묻고 `~/.quivo/token`(mode 0600)에 저장, 또는
  - 모드 B(클론)로 토큰 자체를 생략.

---

## 멀티 LLM

같은 `SKILL.md` 하나가 어댑터를 통해 각 하네스 형식으로 변환된다.

| 하네스 | 설치 위치 | 상태 |
|--------|-----------|------|
| Claude Code | `.claude/skills/q-<name>/SKILL.md` | 지원 |
| Codex CLI | `.agents/skills/q-<name>/SKILL.md` (open agent skills 표준) | 지원 |
| (그 외) | 어댑터 추가로 확장 | 로드맵 — [open-source-plan.md](./open-source-plan.md) |

새 하네스 지원은 `src/quivo/adapters/` 에 `BaseAdapter` 구현 1개를 추가하면 된다.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-------------|
| `No published release with tag prefix 'skills-v'` | 아직 릴리스가 없음. §5 로 첫 릴리스 발행, 또는 모드 B 사용 |
| 릴리스 워크플로가 안 돔 | 포크 Actions 비활성(§2). 또는 `skills/**` 변경이 없었음 |
| `GitHub API 404` (private) | read 토큰 미제공(§6). `GH_TOKEN` 설정 |
| 엔지니어가 옛 스킬을 봄 | `quivo sync` 로 새로고침. 캐시는 `~/.quivo/cache/<tag>/` |
| 잘못된 레포에서 당겨옴 | `quivo.yml` 의 `repo:` 확인(§3), 또는 `QUIVO_REPO` env 가 덮어쓰고 있는지 확인 |
