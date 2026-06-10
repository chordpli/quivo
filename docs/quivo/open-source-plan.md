# quivo 오픈소스화 설계 문서

> 이 문서는 사내 비공개 도구 **vills**(VMS unified skills CLI)를 오픈소스 포크형 프레임워크 **quivo**
> 로 전환한 설계 결정·구조·로드맵을 기록한다. 구현은 이 레포에 이미 반영되어 있다.

---

## 1. 목표와 모델

**목표.** 기업마다 레포를 포크/클론해 자기 회사 전용 스킬을 구성하게 한다. 한 레포로:
- 스킬이 한 곳에서 버전 관리·히스토리 추적됨
- 모든 엔지니어가 같은 버전의 스킬을 봄
- Claude 뿐 아니라 다양한 LLM 하네스에서 동작

**선택한 모델: 모노레포 템플릿 포크.**
레포 자체가 제품(starter template)이다. 사용자는 포크/클론해서 그대로 쓰기 시작하고, 회사 스킬로
채워넣는다. CLI + 스킬 스캐폴딩이 한 몸. (`create-next-app` 같은 보일러플레이트 모델.)

검토했으나 **채택하지 않은** 대안:
- *CLI 분리(업스트림 패키지) + 스킬 레포만 포크* — 업글이 깨끗하지만 사용자 멘탈모델("포크해서 가져간다")과 어긋남.
- *spec-kit 식 override→preset→extension→core 레이어* — "core 안 건드리고 업스트림 업데이트 당기기"용인데, 포크해서 소유하는 모델에선 불필요. 그냥 파일을 직접 고친다. 회사 *내부* 커스텀은 설치 시점 주입(`policy.md`+`config.yml`)이 담당.

---

## 2. vills → quivo 전환 내역

| 영역 | 변경 |
|------|------|
| 브랜드 | `vills`/`vskills` → `quivo`, `VILLS_*` → `QUIVO_*`, `.vills/` → `.quivo/`, `~/.vills/` → `~/.quivo/` |
| 레포 결합 제거 | `DEFAULT_REPO = "VMS-Holdings/vms-skills"` → `chordpli/quivo` + `quivo.yml` 기반 해석 |
| VMS 전용 스킬 제거 | `db-access`, `ecs-access`, `seed-community`, `test-accounts` 삭제 |
| 남긴 예시 스킬 | `author-skill`(작성 가이드) + `aws-access`(AWS 인증·식별 진입점으로 일반화, setup 스크립트 + env-config 패턴 예시, 베스천 SG/IP 등록은 "회사 확장" 섹션으로만) + `ripple`(구현 후 사이드이펙트 탐지, 범용 SDLC 스킬, 제거된 스킬 참조는 일반화) |
| 정책 일반화 | `.quivo/policy.md` 를 VMS 전용 188줄 → 회사가 채우는 범용 템플릿으로 재작성 |
| 문서 | `docs/vskills/` → `docs/quivo/`, VMS/oceanlife 예시값 제거, `scope` enum `vms` → `company` |
| 라이선스 | `Private :: Do Not Upload` → **MIT** + PyPI 업로드 가능 classifier |
| 신규 문서 | `fork-guide.md`, 본 문서 |

---

## 3. 아키텍처

### 3.1 CLI ↔ 스킬 분리 (두 트랙)

- `quivo update` — **CLI 자체** 업그레이드 (`cli-v*` 태그)
- `quivo sync` — **스킬 콘텐츠** 새로고침 (`skills-v*` 태그)

업스트림 CLI 개선과 회사별 스킬 커스텀이 독립적으로 굴러간다.

### 3.2 레포 해석 (`src/quivo/release.py`)

```
QUIVO_REPO 환경변수  >  레포 루트 quivo.yml 의 repo:  >  내장 기본값(chordpli/quivo)
```

포크한 회사는 `quivo.yml` 한 줄만 바꾸면 엔지니어 전원이 자동으로 자기 레포를 본다.

### 3.3 멀티 LLM 어댑터 (`src/quivo/adapters/`)

`BaseAdapter` 추상 클래스 + 하네스별 구현:
- `ClaudeAdapter` → `.claude/skills/q-<name>/SKILL.md` (frontmatter 보존, `name:` 은 `q-` prefix)
- `CodexAdapter` → `.agents/skills/q-<name>/SKILL.md` (frontmatter 보존 — Codex 가 open agent skills 표준에 따라 `.agents/skills/` 를 네이티브 스캔)
- 공통: `CLAUDE.md`/`AGENTS.md` 관리 블록 유지, 레거시 레이아웃 자동 정리 (spec-kit 차용)

새 하네스 = 어댑터 1개 추가. 변환 규칙은 [`reference/agent-adapters.md`](./reference/agent-adapters.md).

### 3.4 회사 커스텀 주입 (설치 시점)

- **`.quivo/policy.md`** — 모든 설치 스킬 본문 끝에 append (`_append_policy`). 포크 안 하고도 회사 규칙 주입.
- **`.quivo/config.yml`** — 엔지니어별 환경값(profile/region/ID). 스킬이 런타임에 4단(인자>env>config>prompt) 해석.

### 3.5 버전/무결성

- `manifest.json` — 스킬별 sha256 (skill.yaml+SKILL.md+setup scripts)
- `skills/VERSION` — 번들 버전
- GitHub Release `skills-v*` — 불변 태그 번들

→ "모두 같은 버전 + 히스토리 추적" 요구를 릴리스 태그 + git 으로 충족.

---

## 4. 배포 모드

| 모드 | 동작 | private | 구현 상태 |
|------|------|---------|-----------|
| **A. Releases** | 포크가 `skills-v*` 번들 발행 → CLI 다운로드+캐시 | read 토큰 1회 (asset API + Bearer) | 구현됨 |
| **B. Local/clone** | `QUIVO_LOCAL_SKILLS` 경로에서 직접 설치 | git 인증 그대로 | 구현됨 |
| **C. Git fetch** | CLI 가 태그 기준 shallow clone/fetch | 기존 gh/SSH 인증 재사용, 토큰 불필요 | **미구현 (제안)** — private 포크 마찰 최소화용 향후 항목 |

---

## 5. 네이밍

`quivo` — quiver(화살통)에서. 스킬 = 화살, 에이전트에 장착. 포크해서 자기 화살통을 채운다는 그림과 맞음.
PyPI/GitHub 점유 없음 확인 후 확정. CLI·경로·env·패키지명 일괄 적용.

---

## 6. 로드맵

### 단기
- **배포 모드 C** (git fetch) — private 포크에서 토큰 셋업 제거
- 어댑터 추가: Cursor(`.cursor/rules`), Gemini CLI, GitHub Copilot(`.github/copilot-instructions.md`), 범용 `AGENTS.md`
- `quivo doctor` 를 범용 도구 체크로 정리 (aws/mysql 가정 제거)

### 중기 (vills 시절 deferred 유지)
- `EXAMPLES.md` 사이드카 분리 (어댑터 확장)
- frontmatter `permissions:` → `.claude/settings.json` 자동 생성
- 스킬 description 트리거 최적화 (native-anthropic train/test 패턴, 고트래픽 스킬 한정 옵션 CI)

### 설계 근거
- 프레임워크별 장단점 + quivo 가 취한/버린 것: [`reference/inspiration.md`](./reference/inspiration.md) (출처 링크 포함)
- 깊은 비교(7개 프레임워크 × 21개 패턴 매트릭스, 인용·adversarial 검증): [`reference/skill-framework-analysis.md`](./reference/skill-framework-analysis.md)
  (spec-kit / superpowers / oh-my-claudecode / karpathy / native-anthropic / gstack)

---

## 7. 라이선스

[MIT](../../LICENSE). 누구나 포크/수정/재배포 가능.
