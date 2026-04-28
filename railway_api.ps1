# Railway API - 项目部署
$headers = @{
    'Authorization' = 'Bearer a541ddba-dd55-4337-90de-1eb670b39ec0'
    'Content-Type' = 'application/json'
}

# 1. 验证 token
$verifyBody = '{"query":"{ me { email id } }"}'
try {
    $r = Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v1' -Headers $headers -Method POST -Body $verifyBody -TimeoutSec 15
    Write-Output "[TOKEN OK] $($r.data.me.email)"
} catch {
    Write-Output "[TOKEN INVALID] $($_.Exception.Message)"
    exit 1
}

# 2. 获取团队列表
$teamBody = '{"query":"{ me { teams { id name } } }"}'
try {
    $teams = Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v1' -Headers $headers -Method POST -Body $teamBody -TimeoutSec 15
    Write-Output "[TEAMS] $($teams | ConvertTo-Json -Depth 3)"
} catch {
    Write-Output "[TEAMS ERROR] $($_.Exception.Message)"
}
