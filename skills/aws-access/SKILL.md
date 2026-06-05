---
name: aws-access
description: AWS 자격증명을 설정·검증하고 AWS CLI 작업의 깨끗한 진입점을 제공한다. AWS 작업을 시작하거나, 인증이 안 된 상태에서 AWS 명령을 실행해야 하거나, 어떤 프로파일/리전/계정으로 접근 중인지 확인해야 할 때 사용.
version: 0.1.0
scope: general
agents: [claude, codex]
risk: medium
policy_injection: required
outputs: []
---

# AWS Access

> **The Iron Law**: AWS access key / secret / session token 을 파일·로그·산출물에 절대 기록하지 않는다. 자격증명은 환경변수로만 전달한다.

You are operating as quivo aws-access worker. Before running any AWS command, you MUST resolve an explicit profile and region and verify the caller identity. Never fall back to an implicit default profile silently.

## When to use

AWS 리소스를 다루는 작업을 시작할 때의 진입점. 인증을 설정(또는 검증)하고, "지금 어떤 계정/프로파일/리전으로 접근 중인지"를 확정한 뒤, 이후 AWS CLI 작업이 안전하게 이어지도록 한다. 단독 호출 가능 (P6) — 다른 스킬 산출물이 없어도 동작한다. AWS 를 쓰는 다른 스킬이 이 스킬을 선행 단계로 호출할 수도 있다.

## Inputs

- **Config**: `.quivo/config.yml` 의 `aws.default_profile`, `aws.default_region`, `aws.account_id` (선택)
- **Env**: `AWS_PROFILE`, `AWS_REGION` (config 보다 우선)
- **CLI 인자**: `--profile`, `--region` (env 보다 우선)
- **인증 방식**: 액세스 키 (`aws configure`) 또는 AWS SSO (`aws configure sso` / `aws sso login`) 둘 다 지원
- **Bash**: `aws sts get-caller-identity`, `aws configure list-profiles`, `aws configure export-credentials`, `aws sso login`, `aws --version`
- **Setup 스크립트** (선택): `setup.sh` (macOS/Linux), `setup.ps1` (Windows) — 프로파일을 대화형으로 구성

## Process

1. **프로파일·리전 해결** (해결 순서: CLI 인자 > env > config > prompt):
   - `PROFILE` = `--profile` 인자 ?? `$AWS_PROFILE` ?? `aws.default_profile` ?? prompt
   - `REGION`  = `--region` 인자 ?? `$AWS_REGION` ?? `aws.default_region` ?? prompt
   - 둘 중 하나라도 비어 있고 prompt 도 실패하면 **중단** 하고 사용자에게 보고. 추정 진행 금지.

2. **AWS CLI 확인**:
   ```bash
   aws --version || { echo "AWS CLI 미설치 — https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"; exit 1; }
   ```

3. **프로파일 존재 확인**:
   ```bash
   aws configure list-profiles | grep -qx "$PROFILE" || echo "프로파일 '$PROFILE' 미구성"
   ```
   미구성이면 인증 설정으로 분기 (Step 4). 이미 있으면 검증으로 (Step 5).

4. **인증 설정** (미구성이거나 만료 시 — 사용자에게 방식 확인):
   - **액세스 키 방식**: `setup.sh`/`setup.ps1` 실행, 또는 `aws configure --profile "$PROFILE"`.
   - **SSO 방식**: `aws configure sso --profile "$PROFILE"` 후 `aws sso login --profile "$PROFILE"`.
   - 자격증명을 *직접 입력받아 파일에 쓰지 않는다* — AWS CLI 의 설정 도구에 위임한다.

5. **자격증명 검증** (필수 — 추정 금지):
   ```bash
   aws sts get-caller-identity --profile "$PROFILE" --region "$REGION"
   ```
   성공 시 Account / Arn / UserId 를 사용자에게 보고. 실패 시 Failure modes 의 해당 분기로.

6. **세션 준비** (이후 AWS 작업으로 자격증명을 넘길 때만):
   ```bash
   eval "$(aws configure export-credentials --profile "$PROFILE" --format env)"
   export AWS_REGION="$REGION"
   ```
   이후 AWS 명령은 해결된 `PROFILE`/`REGION` 을 항상 명시한다.

7. **결과 보고**: 해결된 PROFILE / REGION / Account, 인증 상태(설정함 / 이미 유효 / 갱신함)를 보고하고, 사용자가 요청한 후속 AWS 작업이 있으면 그 진입점으로 넘긴다.

## Iron Laws

- MUST: 모르는 부분은 추측하지 않는다. 잘 모르는 영역은 사용자에게 명시적으로 묻는다 (P1 Sync, 헌법 #4 Evidence Over Assertion).
- MUST: 모든 AWS CLI 호출에 해결된 `PROFILE` 과 `REGION` 을 명시한다. 암묵적 기본 프로파일/리전 fallback 금지.
- MUST: 자격증명 검증(`sts get-caller-identity`) 통과 전에는 "인증 완료"를 주장하지 않는다 (헌법 #4 Evidence).
- MUST NOT: access key / secret / session token 을 파일·로그·산출물·커밋에 기록하지 않는다. 환경변수로만 전달.
- MUST NOT: 본 스킬 본문에 특정 profile 이름·계정 ID·리소스 ID 를 하드코딩하지 않는다 (config/env 로만).
- MUST NOT: 리소스를 *변경* 하는 명령(생성/삭제/수정)을 사용자 명시 동의 없이 실행하지 않는다. 본 스킬의 기본 범위는 인증 + 식별까지다.

### BAD / GOOD

- BAD: `$AWS_PROFILE` 이 비어 있는데 "기본 프로파일로 진행"하며 `aws s3 ls` 를 실행.
- GOOD: profile/region 을 config>env>prompt 로 해결하고, 비면 사용자에게 묻고, 끝까지 비면 중단.

- BAD: `aws configure list-profiles` 에 프로파일이 보이니 검증 없이 "인증됨" 보고.
- GOOD: `sts get-caller-identity` 로 실제 호출이 성공하는지 확인한 뒤에만 인증 완료 보고.

- BAD: 사용자가 준 access key 를 `~/.aws/credentials` 가 아닌 임시 파일이나 로그에 남김.
- GOOD: AWS CLI 의 `aws configure`/SSO 도구에 위임하고, 키는 어디에도 별도 기록하지 않음.

### Red Flags — STOP

다음 신호가 출력에 나타나려 하면 *즉시 stop* 하고 사용자에게 보고:

- config / env / prompt 모두 부재인데 "기본값으로" 진행
- "예전엔 이 프로파일이었으니까" — 기억·관습 기반 profile/region/account 추정
- 검증 없이 "아마 인증돼 있을 것" — `sts get-caller-identity` 생략
- access key/secret 을 화면·로그·파일에 그대로 출력하려는 시도
- 사용자 동의 없이 리소스를 변경(create/delete/modify)하려는 시도

## Failure modes

- **Config 누락 + env 미설정 + prompt 실패** → "프로파일/리전을 알 수 없음" 보고, `.quivo/config.example.yml` 복사 안내 후 중단.
- **`aws` CLI 미설치 / PATH 에 없음** → 설치 안내(공식 문서 링크) 후 중단. 추정 진행 금지.
- **`Unable to locate credentials` (Profile 미설정)** → Step 4 (액세스 키 또는 SSO) 안내 후 설정. 임의 진행 금지.
- **자격증명 만료 (`ExpiredToken`)** → SSO 재로그인(`aws sso login`) 또는 키 갱신 안내 후 재검증.
- **`InvalidClientTokenId` / `SignatureDoesNotMatch`** → 키가 잘못됨. 재설정 안내 후 중단.
- **`sts get-caller-identity` 가 예상과 다른 계정 반환** → 사용자에게 보고하고 의도한 계정인지 확인받기 전 후속 작업 중단.

## Extending — 회사 커스터마이즈 예시

> 본 스킬의 기본 범위는 "인증 + 식별"이다. 회사 인프라에 맞춰 *진입 후 단계* 를 덧붙일 수 있다.
> 아래는 흔한 확장 예시이며, 채택 시 `Inputs`/`Process`/`Iron Laws` 에 해당 동작과 안전장치를 추가하고
> 필요한 값은 `.quivo/config.yml` 로 분리한다 (본문 하드코딩 금지).

- **Bastion Security Group IP 등록**: 사내 DB/서비스가 bastion SG allow-list 뒤에 있는 경우, 인증 후 현재 머신 IP 를 지정된 SG 에 upsert. 안전장치: *지정된 SG 하나만* 조작, 규칙 Description 에 `whoami` 기입, 본인 규칙만 교체/삭제.
- **AWS SSO 자동 로그인**: 만료 감지 시 `aws sso login` 자동 트리거.
- **MFA 세션 토큰 발급**: `aws sts get-session-token` 으로 임시 자격증명 발급 후 export.
