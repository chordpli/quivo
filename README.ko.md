<h1 align="center">quivo</h1>

<p align="center">
  <b>AI 코딩 에이전트용 스킬을 포크해서 배포하는 멀티 LLM 스킬 저장소.</b><br>
  회사의 스킬을 한 레포에 담아 Claude Code, Codex 등 여러 도구에 같은 버전으로 동기화합니다.
</p>

<p align="center">
  <a href="./README.md">English</a> · 한국어 · <a href="./docs/GUIDE.ko.md">길라잡이</a>
</p>

---

## quivo란?

**quiver**는 화살통입니다. **quivo**는 현대적인 코딩 에이전트를 움직이는
마크다운+프론트매터 기반 capability package, 즉 *스킬*을 담고 배포하는 도구입니다.
한 번 작성한 스킬 세트를 모든 엔지니어의 도구에 같은 형태로 전달하는 것이 목표입니다.

quivo는 처음부터 **포크해서 쓰기** 좋게 만들어졌습니다. 이 레포를 가져와 예제 스킬을
회사 스킬로 교체하면 다음을 얻습니다.

- **하나의 레포**: 스킬이 한 곳에 있고, 버전 관리와 변경 이력이 남습니다.
- **모두에게 같은 버전**: 엔지니어가 `quivo sync`를 실행하면 같은 스킬 세트를 받습니다.
- **여러 에이전트 지원**: 같은 `SKILL.md`를 Claude Code, Codex CLI, 그리고 어댑터를 통해
  다른 LLM 실행 환경에도 설치할 수 있습니다.
- **회사별 커스터마이징**: 각 스킬 본문을 고치지 않고도 설치 시점에 회사 정책과 환경 설정을
  주입할 수 있습니다.

---

## 빠른 시작

필요한 것: Python 3.10+, [`uv`](https://docs.astral.sh/uv/)
(`curl -LsSf https://astral.sh/uv/install.sh | sh`).

CLI 화면 예시와 로컬 테스트까지 따라 하는 자세한 절차는 **[길라잡이](./docs/GUIDE.ko.md)**를 참고하세요.

**권장 설치 방식**: `quivo` 명령을 PATH에 설치한 뒤 어디서든 사용합니다.

```bash
uv tool install git+https://github.com/chordpli/quivo.git
quivo init
```

`pipx`를 선호한다면 다음처럼 설치할 수도 있습니다.

```bash
pipx install git+https://github.com/chordpli/quivo.git
quivo init
```

나중에 CLI를 업그레이드하려면 `quivo update`를 실행합니다.
또는 `uv tool install --force git+...` 형태로 다시 설치할 수 있습니다.

**설치 없이 바로 시도하기**:

```bash
uvx --from git+https://github.com/chordpli/quivo.git quivo init
```

**`uvx` 실행 형태를 alias로 등록하기**:

```bash
echo 'alias quivo="uvx --from git+https://github.com/chordpli/quivo.git quivo"' >> ~/.zshrc && source ~/.zshrc
quivo init
```

`quivo init`은 현재 프로젝트에 번들 예제 스킬을 설치합니다.

- Claude Code: `.claude/skills/<name>/`
- Codex CLI: `.codex/prompts/<name>.md` + `.codex/scripts/<name>/`

---

## 회사용으로 포크하기

1. `chordpli/quivo`를 `my-company/quivo`로 포크하거나 클론합니다. 비공개 저장소로 쓰려면
   새 private repo를 만든 뒤 push하세요. GitHub에서 public repo를 fork하면 fork도 public입니다.
   아래의 `my-company`는 예시이므로 회사 GitHub org나 사용자명으로 바꾸면 됩니다.
2. 포크한 저장소에서 GitHub Actions를 켭니다. 포크에서는 Actions가 기본적으로 꺼져 있습니다.
3. [`quivo.yml`](./quivo.yml)의 한 줄을 회사 저장소로 바꿉니다.
   ```yaml
   repo: my-company/quivo
   ```
4. `skills/` 아래에 회사 스킬을 추가합니다. 번들된
   [`author-skill`](./skills/author-skill)을 가이드로 삼을 수 있습니다.
   변경 후 `skills/VERSION`을 올리고 `main`에 push합니다.
5. 릴리스합니다. [`Release Skills Bundle`](./.github/workflows/release-skills.yml)
   workflow가 `skills-bundle.tar.gz`를 만들고 회사 저장소에 `skills-v*` GitHub Release를 발행합니다.
6. 엔지니어는 회사 저장소에서 설치합니다.
   ```bash
   uvx --from git+https://github.com/my-company/quivo.git quivo init
   ```

전체 단계별 가이드는 **[docs/quivo/fork-guide.md](./docs/quivo/fork-guide.md)**에 있습니다.

---

## 배포 모드

포크한 스킬을 각 엔지니어의 머신에 전달하는 방식입니다. 팀에 맞는 방식을 고르면 됩니다.

| 모드 | 방식 | 비공개 저장소 | 적합한 경우 |
|------|------|---------------|-------------|
| **A. Releases** (기본) | 포크가 `skills-v*` 번들을 만들고 CLI가 다운로드 및 캐시 | 엔지니어가 read token을 한 번 제공 | 많은 엔지니어, 고정된 불변 버전, sha256 무결성, 오프라인 캐시 |
| **B. Local / clone** | 레포를 클론하고 디스크에서 바로 설치 | 기존 git 인증 사용 | 유지보수자, 소규모 팀 |

```bash
# 모드 B: 릴리스 없이 로컬 체크아웃에서 설치
export QUIVO_LOCAL_SKILLS=/path/to/quivo/skills
quivo init --agent both
```

비공개 포크의 Release 방식도 바로 사용할 수 있습니다. `GH_TOKEN` 또는 `GITHUB_TOKEN`을
설정하거나, CLI가 처음 한 번 토큰을 물어보게 두면 됩니다. 저장된 토큰은 `~/.quivo/token`에
권한 `0600`으로 보관됩니다.

---

## 명령어

| 명령어 | 기능 |
|--------|------|
| `quivo init` | 현재 프로젝트에 스킬 설치 (`--agent claude\|codex\|both`, `--dir`, `--force`, `--release TAG`, `--no-policy`) |
| `quivo sync` | 설치된 스킬 **내용**을 최신 릴리스로 갱신 |
| `quivo update` | quivo **CLI 자체**를 최신 `cli-v*` 릴리스로 업그레이드 |
| `quivo list` | 설치된 스킬 목록 표시 |
| `quivo doctor` | 도구, 버전, 캐시, 정책 파일 상태 점검 |

`quivo update`는 CLI를 업그레이드하고, `quivo sync`는 스킬을 갱신합니다.
릴리스 태그도 두 갈래입니다: CLI는 `cli-v*`, 스킬 번들은 `skills-v*`를 사용합니다.

---

## 회사별 커스터마이징

설치 시점에 두 가지 내용을 주입할 수 있습니다. 같은 스킬 세트를 유지하면서 회사마다
다른 정책과 환경값을 적용할 수 있으므로, 스킬 본문을 매번 포크할 필요가 없습니다.

- **`.quivo/policy.md`**: 모든 설치된 스킬 뒤에 붙는 회사 정책입니다.
  운영 절차, 권한 규칙, 코드/PR 규칙 등을 넣을 수 있습니다. 이 레포의 템플릿을 참고하세요.
- **`.quivo/config.yml`**: 엔지니어별 환경값입니다. profile, region, ID 같은 값을 런타임에
  스킬이 해석할 수 있게 합니다. [`.quivo/config.example.yml`](./.quivo/config.example.yml)을
  복사해서 시작하면 됩니다.

정책 주입을 건너뛰려면 `quivo init --no-policy`를 사용합니다.

---

## 번들 예제 스킬

이 레포는 스킬 카탈로그가 아니라 템플릿입니다. 그래서 예제 스킬은 의도적으로 작게 유지합니다.

| 스킬 | 목적 | 보여주는 것 |
|------|------|-------------|
| `author-skill` | quivo 표준에 맞는 새 스킬 작성 가이드 | 작성 표준 (`docs/quivo/`) |
| `aws-access` | AWS 인증, identity 확인, AWS CLI 작업의 진입점 | `setup.sh`/`setup.ps1`, env-config 해석, 회사 확장 지점 |
| `ripple` | 테스트가 놓친 변경 영향 탐지 (scan -> clarify -> resolve -> check) | 실행 환경에 독립적인 SDLC 스킬, 구조화된 출력, delta 기준 Iron Law |

작성 표준은 [`docs/quivo/`](./docs/quivo)에 있습니다. 운영 원칙, 스킬 템플릿,
권한 모델, 어댑터 레퍼런스를 포함합니다.

---

## 영감

quivo는 에이전트 스킬을 작성하고 배포하는 여러 오픈소스 프레임워크에서 배웠습니다.
각 프로젝트의 장단점과 quivo가 받아들인 점, 일부러 배제한 점은
**[docs/quivo/reference/inspiration.md](./docs/quivo/reference/inspiration.md)**에 정리되어 있습니다.
더 깊은 비교는 [skill-framework-analysis.md](./docs/quivo/reference/skill-framework-analysis.md)를 참고하세요.

- [**spec-kit**](https://github.com/github/spec-kit): GitHub의 Spec-Driven Development 툴킷.
  spec -> plan -> tasks -> implement 흐름과 30개 이상의 에이전트 타깃
- [**superpowers**](https://github.com/obra/superpowers): Jesse Vincent의 agentic SDLC discipline skills
  (Iron Law, TDD, verification)
- [**oh-my-claudecode**](https://github.com/Yeachan-Heo/oh-my-claudecode): 증거 기반 검증 게이트를 갖춘
  멀티 에이전트 오케스트레이션
- [**gstack**](https://github.com/garrytan/gstack): Garry Tan의 "virtual engineering team" 페르소나
  (anti-sycophancy, hard gates, template generation)
- [**Anthropic Agent Skills**](https://github.com/anthropics/skills): 1st-party `SKILL.md` 표준
  ([engineering blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) ·
  [docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview))
- [**Andrej Karpathy**](https://karpathy.ai/): "모든 토큰은 제 값을 해야 한다"는 미니멀한 스킬 작성 철학
- [**spec-kit-ripple**](https://github.com/chordpli/spec-kit-ripple): 번들 `ripple` 스킬의
  scan -> clarify -> resolve -> check 흐름의 출발점

---

## 요구 사항

- Python 3.10+
- `uv` 권장, 또는 pip
- GitHub Releases 접근을 위한 네트워크, 또는 오프라인/로컬 사용을 위한 `QUIVO_LOCAL_SKILLS`

## 라이선스

[MIT](./LICENSE)

---

<p align="center">
  Built by <a href="https://github.com/chordpli">chordpli</a> · <a href="./LICENSE">MIT</a> · contributions welcome
</p>
