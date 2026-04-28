# Railway GraphQL API 测试
param(
    [string]$Token = "a541ddba-dd55-4337-90de-1eb670b39ec0"
)

$headers = @{
    'Authorization' = "Bearer $Token"
    'Content-Type' = 'application/json'
}

$endpoint = "https://backboard.railway.app/graphql/v1"

Write-Host "测试 Railway GraphQL API..."
Write-Host "Token: $($Token.Substring(0,8))..."

# 测试查询
$body = @{
    query = "{ me { email } }"
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri $endpoint -Headers $headers -Method POST -Body $body -TimeoutSec 15 -ErrorAction Stop
    Write-Host "[成功] 用户: $($r.data.me.email)"
} catch {
    Write-Host "[失败] $($_.Exception.Message)"
    Write-Host "状态码: $($_.Exception.Response.StatusCode.value__)"
}

# 尝试 railway.app REST API
Write-Host "`n测试 railway.app API..."
$restHeaders = @{
    'Authorization' = "Bearer $Token"
}
try {
    $r2 = Invoke-RestMethod -Uri "https://railway.app/api/projects" -Headers $restHeaders -Method GET -TimeoutSec 15 -ErrorAction Stop
    Write-Host "[成功] $($r2)"
} catch {
    Write-Host "[失败] $($_.Exception.Message)"
}
