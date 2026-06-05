# Inspiration — 참고 프레임워크 장단점 정리

> quivo 의 설계는 에이전트 "스킬" 저작·배포를 다룬 여러 오픈소스 프레임워크에서 배웠다.
> 이 문서는 각 프레임워크의 **장점 / 단점 / quivo 가 취한 것**을 한눈에 정리한 reference 다.
> 더 깊은 근거 비교(7개 프레임워크 × 21개 패턴 매트릭스, 인용·검증 포함)는
> [`skill-framework-analysis.md`](./skill-framework-analysis.md) 참조.

---

## 한눈에 보기

| 프레임워크 | 한 줄 정체성 | quivo 가 가장 크게 빌린 것 |
|---|---|---|
| [spec-kit](https://github.com/github/spec-kit) | Spec → Plan → Tasks → Implement 파이프라인 + 결정적 스크립트 레이어 | outputs 계약, 30+ 에이전트 배포 모델, `[NEEDS CLARIFICATION]` |
| [superpowers](https://github.com/obra/superpowers) | 자동 트리거되는 SDLC 규율 스킬 (TDD·검증·brainstorm) | Iron Law 블록, 검증-우선, Red Flags STOP |
| [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 메인 세션을 멀티 에이전트 오케스트레이터로 | deliverable(outputs) 패턴, PRD AC, 티어 개념 |
| [gstack](https://github.com/garrytan/gstack) | 에이전트를 "가상 엔지니어링 팀" 역할로 | BAD/GOOD anti-sycophancy, HARD GATE, 템플릿 생성 |
| [Anthropic Agent Skills](https://github.com/anthropics/skills) | 1차 표준: `SKILL.md` + progressive disclosure | description=트리거 계약, 스키마 검증, 3단 점진 공개 |
| [karpathy 철학](https://karpathy.ai/) | "토큰마다 값을 한다" 미니멀 저작 감각 | 4원칙(Think/Simplicity/Surgical/Goal), 군더더기 제거 |

> 멀티 LLM 배포·`AGENTS.md` 어댑터 발상은 spec-kit(30+ 에이전트), 어조/페르소나는 gstack,
> 규율 수사는 superpowers 에서 가장 크게 영향받았다.

---

## spec-kit

GitHub 의 Spec-Driven Development 툴킷. 자연어 → spec → plan → tasks → implement 를
번호 매겨진 아티팩트로 흘리고, 그 아래 결정적(bash/PowerShell) 레이어가 경로·번호·게이트를 처리한다.
이를 **개별 호출 스킬로 포팅한 커뮤니티 변형들**(예: `spec-kit-skills`, `speckit-agent-skills`)도 함께 분석했다.

- **장점**: 결정적 스크립트가 LLM 을 경로/번호/게이트 실패에서 격리 · 요구사항→태스크→커버리지 추적성 · 헌법(constitution) 게이트 · 30+ 에이전트 배포 · fork 없이 확장 가능한 레이어
- **단점**: ~55줄 hook 블록이 9개 커맨드에 복붙되어 drift 위험 · 단일 에이전트 중심(네이티브 병렬·역할 분리 없음) · 스크립트 외 게이트는 honor-system · placeholder 헌법이 게이트를 무력화 · 테스트가 OPTIONAL
- **quivo 적용**: `outputs:` 계약 · `[NEEDS CLARIFICATION]` 마커 · Constitution-as-DNA · 멀티 에이전트 배포 모델. **거부**: 복붙 hook 블록, placeholder 게이트.

## superpowers (obra / Jesse Vincent)

자동 트리거되는 SDLC 규율 스킬 모음. brainstorm→worktree→plan→subagent 실행→2단계 리뷰→TDD 를
하드 게이트로 강제한다. 메타 스킬 `writing-skills` 가 스킬 저작 자체를 TDD 로 본다.

- **장점**: 도메인 무관 일관된 규율 수사 · 실제 트랜스크립트에서 채굴한 규칙(상상 아님) · 컨텍스트 위생(`@`-link 금지) · 검증을 기계적 체크리스트로 · 하네스 간 이식성(툴명 매핑)
- **단점**: 강제가 대부분 **수사(rhetoric)** — 다르게 정렬된 모델은 무시 가능 · 리뷰어 2~3 디스패치/태스크 비용 · brainstorm 의 human-in-the-loop 가 자율 실행과 충돌 · 한 사람의 문화에 묶인 특이 규칙(금지어 등)
- **quivo 적용**: Iron Law 블록 · Red Flags STOP · evidence-over-assertion · verification-before-completion. **거부**: 특정 개인 문화 규칙, 무조건 서브에이전트 위임.

## oh-my-claudecode (Yeachan Heo)

메인 세션을 "지휘자"로 만드는 멀티 에이전트 오케스트레이션 플러그인. 티어드 전문 에이전트에 위임하고,
별도 Architect 가 증거로 검증하기 전엔 완료를 선언하지 않으며, Stop-hook 으로 지속 실행을 강제한다.

- **장점**: Stop-hook 으로 "끝until done" 을 시스템 속성으로 · frontmatter 로 강제되는 역할 분리(검증자는 write 불가) · 비용 규율(티어 모델·티어 검증) · SQLite 원자적 태스크 클레이밍
- **단점**: 중복된 티어 표가 SSOT 에서 drift · "오케스트레이션" 상당수가 모델이 따라야 하는 prose(엔진 아님) · 사소한 편집까지 위임해 지연/비용 · 5000+ 단어 모드 파일이 점진 공개 예산 위반
- **quivo 적용**: deliverable(outputs) 패턴 · PRD AC 형식 · LOW/MED/HIGH 추상 티어. **거부**: 자동 spawn 강제 위임, Stop-hook/영구 상태(quivo 는 git+context 로 충분), Magic-keyword 자동 활성화.

## gstack (Garry Tan)

에이전트를 ~23개 역할 페르소나(CEO/Staff Eng/QA/Release)로 캐스팅해 스프린트 라이프사이클에 배선.
`SKILL.md` 는 `.tmpl` 에서 호스트별로 **생성**되고, 정적 validator 가 CI 를 게이트한다.

- **장점**: anti-sycophancy 어조 잠금 + BAD/GOOD 쌍(값싸고 모델 무관) · 하드 게이트("BLOCKED 로 시끄럽게 실패") · 템플릿 생성 → 호스트 간 drift 없는 author-once · 구조화 완료 상태 enum · 프로젝트별 learnings 코퍼스
- **단점**: validator 가 커맨드만 검사하고 페르소나/게이트 prose 는 구조적으로 강제 못 함 · 창업자 워크플로(CEO/YC)에 특화되어 이식성 약함 · OS 결합 자체 도구 많음 · learnings JSONL 의 스키마/GC 부재
- **quivo 적용**: BAD/GOOD anti-sycophancy 쌍 · HARD GATE/Iron Law 어조 · 어조 잠금. **거부**: 창업자 특화 페르소나, 단일 컨텍스트 페르소나 스위칭(독립 검증엔 분리 에이전트 선호), 검증 안 되는 persona-first-line.

## Anthropic Agent Skills (native)

1차 표준: `SKILL.md`(YAML frontmatter + 본문) + `scripts/`/`references/`/`assets/`.
`skill-creator` 가 초안→평가(with-skill vs baseline)→채점→**description 자동 최적화 루프**까지 제공.
([엔지니어링 블로그](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) · [문서](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview))

- **장점**: 트리거를 경험적으로 측정·최적화(train/test 분할로 overfit 방지) · 3단 점진 공개로 상주 컨텍스트 최소 · 기계 강제 스키마 + 결정적 패키저 · "왜를 설명하라/ALL-CAPS 지양" 철학
- **단점**: eval 도구가 Python+SDK+`claude -p` 에 무겁게 결합(브리틀) · viewer 가 JSON 필드명에 하드 의존 · description 가이드가 내부적으로 불일치(pushy vs 3인칭) · 1024자 캡이 "pushy+나열" 과 충돌
- **quivo 적용**: description=트리거 계약 · frontmatter 스키마 lint · 3단 점진 공개 · scripts/references 사이드카. **거부**: 무거운 Python eval 런타임을 필수로 강제(고가치 스킬 한정 옵션으로).

## karpathy 철학

레포가 아니라 저작 *감각*. 최대 행동변화/토큰을 노린다 — 최소 frontmatter(name + 날카로운 what+when),
prose 보다 체크리스트/표, 여러 개보다 의존성 없는 예시 하나, "모든 토큰이 값을 한다".

- **장점**: 트리거 충실도(WHEN-only 가 본문 스킵 방지) · 낮은 상주 비용 · 스캔 용이성 · 추상 예시 하나로 이식성 · no-narrative 로 부식 방지
- **단점**: 미니멀리즘이 **under-trigger** 위험(공식 표준은 일부러 "pushy") · "모델은 이미 똑똑" 가정이 결정적 태스크에서 컨텍스트 누락 · 정량 피드백 약함 · 버전/owner/패키징 같은 배포 메타데이터엔 침묵
- **quivo 적용**: 4원칙(Think before coding / Simplicity / Surgical / Goal-driven) · 군더더기 제거 · 추상 예시 1개. **보완**: 미니멀 frontmatter 는 유지하되 배포에 필요한 `outputs`/version 은 강제 확장.

---

## quivo 가 명확히 거부한 것 (요약)

- 자동 spawn / Conductor 강제 위임 (헌법 #1 위반)
- SessionStart Hooks / Magic-keyword 자동 활성화 (Parity·사용자 명시 트리거 우선)
- 영구 메모리 런타임(`~/.gstack/`, `.omc/state/`) — `context/<slug>/` + git 으로 충분
- 한 개인 문화에 묶인 금지어·페르소나, 검증 안 된 persona-first-line
- 무거운 Python eval/벤치마크 파이프라인을 모든 스킬에 필수화

## 부속 출처

- **ripple 스킬**의 4단계(scan→clarify→resolve→check) 패턴은 [`chordpli/spec-kit-ripple`](https://github.com/chordpli/spec-kit-ripple) 에서 차용해 quivo 표준으로 정규화했다.
- 전체 비교 매트릭스·인용·adversarial 검증은 [`skill-framework-analysis.md`](./skill-framework-analysis.md).
