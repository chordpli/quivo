#!/bin/bash
#
# aws-access skill setup (macOS / Linux)
# AWS Profile 을 .quivo/config.yml, env, 또는 대화형 입력으로 설정합니다.
# AWS CLI 자체는 별도로 설치되어 있어야 합니다.
#
# 사용법: bash .claude/skills/aws-access/setup.sh
#

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_project_root() {
    local start="$1"
    local dir="$start"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.quivo/config.yml" || -d "$dir/.git" || -f "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

config_value() {
    local section="$1"
    local key="$2"
    local file="$3"
    [[ -f "$file" ]] || return 0
    awk -v section="$section" -v key="$key" '
        $0 ~ "^" section ":" { in_section=1; next }
        in_section && /^[^[:space:]]/ { in_section=0 }
        in_section {
            split($0, parts, ":")
            k = parts[1]
            gsub(/^[ \t]+|[ \t]+$/, "", k)
            if (k == key) {
                val = substr($0, index($0, ":") + 1)
                sub(/#.*/, "", val)
                gsub(/^[ \t]+|[ \t]+$/, "", val)
                gsub(/^"|"$/, "", val)
                print val
                exit
            }
        }
    ' "$file"
}

REPO_ROOT="$(find_project_root "$PWD" || find_project_root "$SCRIPT_DIR" || pwd)"
CONFIG_FILE="${QUIVO_CONFIG_FILE:-${REPO_ROOT}/.quivo/config.yml}"

CONFIG_PROFILE="$(config_value aws default_profile "$CONFIG_FILE")"
CONFIG_REGION="$(config_value aws default_region "$CONFIG_FILE")"
AWS_PROFILE_NAME="${AWS_PROFILE:-$CONFIG_PROFILE}"
AWS_REGION_NAME="${AWS_REGION:-$CONFIG_REGION}"

if [[ -z "$AWS_PROFILE_NAME" ]]; then
    read -rp "  AWS profile name: " AWS_PROFILE_NAME
fi
if [[ -z "$AWS_REGION_NAME" ]]; then
    read -rp "  AWS region: " AWS_REGION_NAME
fi
if [[ -z "$AWS_PROFILE_NAME" || -z "$AWS_REGION_NAME" ]]; then
    echo "[setup] profile 또는 region 이 비어있습니다. .quivo/config.yml 또는 AWS_PROFILE/AWS_REGION 을 설정하세요."
    exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
    echo "[setup] aws: not found"
    echo "  AWS CLI 를 먼저 설치하세요: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi
echo "[setup] aws: $(aws --version 2>&1)"

if aws configure list-profiles 2>/dev/null | grep -q "^${AWS_PROFILE_NAME}$"; then
    echo "[setup] profile '${AWS_PROFILE_NAME}': already configured"
    echo "  덮어쓰려면: aws configure --profile ${AWS_PROFILE_NAME}"
    exit 0
fi

echo ""
echo "AWS Access Key가 필요합니다. 관리자에게 발급받으세요."
read -p "지금 설정하시겠습니까? (Y/n) " confirm
if [[ "$confirm" =~ ^[Nn] ]]; then
    echo "[setup] 건너뜁니다. 나중에: aws configure --profile ${AWS_PROFILE_NAME}"
    exit 0
fi

read -p "  AWS Access Key ID: " AWS_ACCESS_KEY
read -sp "  AWS Secret Access Key: " AWS_SECRET_KEY
echo ""

if [[ -z "$AWS_ACCESS_KEY" || -z "$AWS_SECRET_KEY" ]]; then
    echo "[setup] 키가 비어있습니다."
    exit 1
fi

if [[ ! "$AWS_ACCESS_KEY" =~ ^AKIA[A-Z0-9]{16}$ ]]; then
    echo "[setup] 경고: Access Key 형식이 일반적이지 않습니다 (AKIA로 시작하는 20자). 그래도 시도합니다."
fi

aws configure set aws_access_key_id "$AWS_ACCESS_KEY" --profile "$AWS_PROFILE_NAME"
aws configure set aws_secret_access_key "$AWS_SECRET_KEY" --profile "$AWS_PROFILE_NAME"
aws configure set region "$AWS_REGION_NAME" --profile "$AWS_PROFILE_NAME"
aws configure set output json --profile "$AWS_PROFILE_NAME"

echo ""
echo "[setup] AWS 연결 확인..."
VERIFY=$(aws sts get-caller-identity --profile "$AWS_PROFILE_NAME" 2>&1)
VERIFY_RC=$?

if [[ $VERIFY_RC -eq 0 ]]; then
    ACCOUNT_ID=$(echo "$VERIFY" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4)
    echo "[setup] profile '${AWS_PROFILE_NAME}': configured (Account: ${ACCOUNT_ID})"
else
    echo "[setup] AWS 인증 실패"
    if echo "$VERIFY" | grep -q "InvalidClientTokenId"; then
        echo "  Access Key ID가 유효하지 않습니다."
    elif echo "$VERIFY" | grep -q "SignatureDoesNotMatch"; then
        echo "  Secret Access Key가 잘못되었습니다 (복사 시 공백 확인)."
    elif echo "$VERIFY" | grep -q "ExpiredToken"; then
        echo "  키가 만료되었습니다."
    else
        echo "  $VERIFY"
    fi
    echo "  재설정: aws configure --profile ${AWS_PROFILE_NAME}"
    exit 1
fi
