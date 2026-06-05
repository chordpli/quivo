#Requires -Version 5.1
<#
.SYNOPSIS
  aws-access skill setup (Windows)
.DESCRIPTION
  AWS Profile 을 환경변수(AWS_PROFILE / AWS_REGION) 또는 대화형 입력으로 설정합니다.
  AWS CLI 자체는 별도로 설치되어 있어야 합니다.
.NOTES
  사용법:
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
    .\.claude\skills\aws-access\setup.ps1
#>

$ErrorActionPreference = "Continue"

# Profile/region resolve: env > prompt. (.quivo/config.yml 는 setup.sh 가 읽으며,
# Windows 에서는 AWS_PROFILE/AWS_REGION env 또는 아래 프롬프트로 설정합니다.)
$AWS_PROFILE_NAME = $env:AWS_PROFILE
$AWS_REGION = $env:AWS_REGION
if ([string]::IsNullOrEmpty($AWS_PROFILE_NAME)) {
    $AWS_PROFILE_NAME = Read-Host "  AWS profile name"
}
if ([string]::IsNullOrEmpty($AWS_REGION)) {
    $AWS_REGION = Read-Host "  AWS region"
}
if ([string]::IsNullOrEmpty($AWS_PROFILE_NAME) -or [string]::IsNullOrEmpty($AWS_REGION)) {
    Write-Host "[setup] profile 또는 region 이 비어있습니다. AWS_PROFILE/AWS_REGION 을 설정하세요."
    exit 1
}

function Test-Command($cmd) {
    try { Get-Command $cmd -ErrorAction Stop | Out-Null; return $true }
    catch { return $false }
}

if (-not (Test-Command "aws")) {
    Write-Host "[setup] aws: not found"
    Write-Host "  AWS CLI 를 먼저 설치하세요: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
}
Write-Host "[setup] aws: $(aws --version 2>&1)"

$profiles = aws configure list-profiles 2>$null
if ($profiles -contains $AWS_PROFILE_NAME) {
    Write-Host "[setup] profile '$AWS_PROFILE_NAME': already configured"
    Write-Host "  덮어쓰려면: aws configure --profile $AWS_PROFILE_NAME"
    exit 0
}

Write-Host ""
Write-Host "AWS Access Key가 필요합니다. 관리자에게 발급받으세요."
$confirm = Read-Host "지금 설정하시겠습니까? (Y/n)"
if ($confirm -eq 'n' -or $confirm -eq 'N') {
    Write-Host "[setup] 건너뜁니다. 나중에: aws configure --profile $AWS_PROFILE_NAME"
    exit 0
}

$accessKey = Read-Host "  AWS Access Key ID"
$secretKey = Read-Host "  AWS Secret Access Key" -AsSecureString
$secretKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretKey)
)

if ([string]::IsNullOrEmpty($accessKey) -or [string]::IsNullOrEmpty($secretKeyPlain)) {
    Write-Host "[setup] 키가 비어있습니다."
    exit 1
}

if ($accessKey -notmatch "^AKIA[A-Z0-9]{16}$") {
    Write-Host "[setup] 경고: Access Key 형식이 일반적이지 않습니다 (AKIA로 시작하는 20자). 그래도 시도합니다."
}

aws configure set aws_access_key_id $accessKey --profile $AWS_PROFILE_NAME
aws configure set aws_secret_access_key $secretKeyPlain --profile $AWS_PROFILE_NAME
aws configure set region $AWS_REGION --profile $AWS_PROFILE_NAME
aws configure set output json --profile $AWS_PROFILE_NAME

Write-Host ""
Write-Host "[setup] AWS 연결 확인..."
$verifyOutput = aws sts get-caller-identity --profile $AWS_PROFILE_NAME 2>&1 | Out-String

if ($LASTEXITCODE -eq 0) {
    try {
        $identity = $verifyOutput | ConvertFrom-Json
        Write-Host "[setup] profile '$AWS_PROFILE_NAME': configured (Account: $($identity.Account))"
    } catch {
        Write-Host "[setup] profile '$AWS_PROFILE_NAME': configured"
    }
} else {
    Write-Host "[setup] AWS 인증 실패"
    if ($verifyOutput -match "InvalidClientTokenId") {
        Write-Host "  Access Key ID가 유효하지 않습니다."
    } elseif ($verifyOutput -match "SignatureDoesNotMatch") {
        Write-Host "  Secret Access Key가 잘못되었습니다 (복사 시 공백 확인)."
    } elseif ($verifyOutput -match "ExpiredToken") {
        Write-Host "  키가 만료되었습니다."
    } else {
        Write-Host "  $($verifyOutput.Trim())"
    }
    Write-Host "  재설정: aws configure --profile $AWS_PROFILE_NAME"
    exit 1
}
