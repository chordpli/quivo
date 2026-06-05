# Skill Triggering Tests

LLM 호출 기반 트리거링 검증. 자연어 사용자 메시지가 SKILL.md `description` 매칭으로 의도한 스킬을 자동 발화시키는지 확인.

`quivo 설계 (F-D)` 의 구현. 출처 패턴: `obra/superpowers` 의 `tests/skill-triggering/`.

## 구조

```
tests/skill-triggering/
  run-test.sh           # 단일 스킬 테스트 실행
  run-all.sh            # 모든 prompts/*.txt 순회
  prompts/
    <skill-name>.txt    # 해당 스킬을 트리거해야 하는 자연어 입력
```

## 새 스킬 트리거 테스트 추가

1. `prompts/<skill-name>.txt` 작성. 사용자가 평소 그 스킬을 부를 때 쓸 법한 자연어 메시지.
2. 로컬에서 1회 검증: `./run-test.sh <skill-name> prompts/<skill-name>.txt 3`
3. PASS 확인 후 commit.

## 비용·한계

- 각 시도가 `claude -p` 라이브 호출. 실 토큰 소모.
- **자동 실행 X**. PR 마다 돌리지 않는다. 릴리스 전 수동 또는 `workflow_dispatch` 로만.
- 트리거 감지는 *느슨한* 매칭 (출력에 스킬명/경로 등장). 정확도 더 필요하면 transcript JSON 파싱으로 강화.
- 환경: `claude` CLI 가 PATH 에 있어야 함. CI 에서는 secret 으로 인증 토큰 제공.

## 실행

```bash
# 단일 스킬
./run-test.sh author-skill prompts/author-skill.txt

# 전체
./run-all.sh

# 재시도 횟수 변경
RETRIES=5 ./run-all.sh
```

종료 코드: PASS 면 0, 하나라도 실패면 1.
