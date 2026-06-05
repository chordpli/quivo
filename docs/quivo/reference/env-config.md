# Reference — 환경 설정 (`.quivo/config.yml`) 과 디스커버리 패턴

> 인프라값(프로파일, 리전, 클러스터, SG ID 등)을 스킬 본문에 하드코딩하지 않기 위한 규약. 사람·환경마다 다른 값을 깔끔하게 분리한다.
>
> 헌법 #5 (Surgical Scope) + #2 (Self-Contained) 운영을 위한 도구.

---

## 1. 왜 필요한가

스킬 본문에 다음 같은 값을 직접 적어두면 깨진다:

- AWS Profile 이름: 사람마다 다름 (`alice-admin` vs `bob-admin`)
- 리전·계정: 환경마다 다름
- ECS 클러스터/서비스 목록: 자주 변함 (새 마이크로서비스 추가 = 모든 SKILL.md PR)
- Bastion SG ID: 환경마다 다름

따라서 quivo 는 **3계층 해결**을 강제한다:

1. **CLI/인자**: 사용자가 명시적으로 넘긴 값 (예: `--profile`)
2. **환경변수**: `AWS_PROFILE`, `AWS_REGION`, `<APP>_ECS_CLUSTER`, ...
3. **`.quivo/config.yml`**: 프로젝트/팀 기본값
4. **대화형 prompt**: 모두 누락이면 사용자에게 묻기 (skill 의 default 제안 가능)

빈 문자열·미설정은 *"다음 resolver 로 넘긴다"*. 4단계까지 모두 실패하면 스킬이 명확한 에러로 중단한다 (헌법 #4 Evidence — 추정 진행 금지).

---

## 2. `.quivo/config.yml` 스키마

전체 예시는 `.quivo/config.example.yml` (git tracked). 실제 파일 `.quivo/config.yml` 은 **gitignored**.

| 섹션 | 키 | 타입 | 설명 |
|---|---|---|---|
| `aws` | `default_profile` | string | AWS CLI profile 이름 |
| `aws` | `default_region` | string | 리전 (e.g. `ap-southeast-1`) |
| `aws` | `account_id` | string | 계정 ID (검증·로그 경로용) |
| `bastion` | `members_sg_id` | string | IP upsert 대상 SG (다른 SG 절대 금지) |
| `bastion` | `dev_port` / `prod_port` | int | MySQL 게이트웨이 포트 |
| `ecs` | `default_cluster` | string | ECS 클러스터명 |
| `ecs` | `aliases` | map | 서비스 별칭 (선택) |
| `db` | `dev_secret_id` / `prod_secret_id` | string | Secrets Manager secret ID |
| `cache` | `ttl_seconds` | int | 디스커버리 캐시 TTL |
| `cache` | `dir` | string | 캐시 디렉토리 (기본 `.quivo/cache`) |

값이 누락된 키는 *"이 환경에선 사용 안 함"* 으로 해석되며 호출하는 스킬이 prompt 로 대체한다.

---

## 3. 스킬 작성 규약

### 3.1 본문 Inputs 섹션에 의존 명시

```markdown
## Inputs

- **Config**: `.quivo/config.yml` 의 `aws.default_profile`, `aws.default_region`
- **Env**: `AWS_PROFILE` (config 미설정 시 fallback), `AWS_REGION`
- **CLI**: `--profile`, `--region` (env 보다 우선)
```

### 3.2 Process Step 0 — 환경 해결

모든 인프라 의존 스킬은 Process 첫 단계에서 값을 해결:

```markdown
1. **환경 해결**:
   - profile: `--profile` 인자 > `$AWS_PROFILE` > config `aws.default_profile` > 사용자 prompt
   - region: 같은 순서로 `AWS_REGION` / `aws.default_region`
   - 셋 다 누락 시 *"profile 을 알려주세요"* prompt 후 중단 가능
   - 해결된 값을 이후 단계에서 변수로 사용
```

### 3.3 디스커버리 + 캐시 (목록 데이터)

ECS 서비스 목록 같은 *가변 리스트* 는 캐시 패턴:

```markdown
2. **서비스 목록 확보** (`.quivo/cache/ecs-services-${CLUSTER}.json`):
   - 캐시 파일 존재 + `mtime < ttl_seconds` → 사용
   - 없거나 만료 → `aws ecs list-services --cluster $CLUSTER` 호출 후 캐시 갱신
   - `aws ecs describe-services` 로 상태 보강 (선택)
```

### 3.4 본문에 두면 안 되는 것

| 금지 | 대안 |
|---|---|
| 특정 AWS Profile 이름 | config / env / prompt |
| 특정 SG ID, Bastion IP, Account ID | config |
| ECS 서비스명 표 (고정 표) | 디스커버리 + 캐시. 본문엔 *패턴* 만. |
| MySQL 호스트명 | Secrets Manager secret ID 만 적고 실제 호스트는 런타임 조회 |

---

## 4. 캐시 디렉토리 구조

```
.quivo/cache/
  ecs-services-myapp-prod.json         # aws ecs list-services 결과 + mtime
  ecs-task-defs-<service>.json         # 선택, describe-task-definition 결과
  rds-endpoints.json                   # 선택, RDS 디스커버리 결과
```

캐시는 항상 `.gitignore` 됨 (`.quivo/cache/`).
캐시 무효화는 사용자가 직접 (`rm -rf .quivo/cache/`) 또는 스킬의 `refresh` 서브명령.

---

## 5. Failure modes 표준

환경 해결 실패는 항상 다음 4가지 케이스로 분기:

| 케이스 | 동작 |
|---|---|
| Config 파일 없음 | 사용자에게 `.quivo/config.example.yml` 복사 안내 |
| 키 누락 (예: `aws.default_profile` 빈 값) | 사용자에게 값을 묻고 *세션 한정 사용* (config 자동 수정 금지) |
| Env var 도 없음 | 동상 |
| AWS API 호출 거부 (`AccessDenied` 등) | `.quivo/policy.md` §2 에 명시된 권한 미부여로 추정. 사용자에게 보고하고 중단 |

---

## 6. 헌법 연결

| 헌법 원칙 | 본 규약과의 관계 |
|---|---|
| #2 Self-Contained | 스킬이 외부 환경 가정을 명시 → 어디서든 동작 |
| #3 Parity | 본문에 두므로 Codex 변환 시에도 동일 동작 |
| #4 Evidence | 값 누락 시 추정 금지, 명시적 prompt 또는 중단 |
| #5 Surgical | 해결된 값 *외* 다른 환경 값에 손대지 않음 |
| #7 Policy SSOT | 권한 부여는 policy.md, 인프라 값은 config.yml — 책임 분리 |
