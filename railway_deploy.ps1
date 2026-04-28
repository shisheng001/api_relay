# Railway 部署脚本
$headers = @{
    'Authorization' = 'Bearer a541ddba-dd55-4337-90de-1eb670b39ec0'
    'Content-Type' = 'application/json'
}

# Railway API endpoints
$baseUrl = "https://backboard.railway.app/graphql/v1"

# 1. 验证 token
Write-Host "验证 Railway Token..."
$query = '{"query":"query { me { email } }"}'
try {
    $r = Invoke-RestMethod -Uri $baseUrl -Headers $headers -Method POST -Body $query -TimeoutSec 10
    if ($r.data.me) {
        Write-Host "[OK] 已登录: $($r.data.me.email)"
    } else {
        Write-Host "[FAIL] Token 无效"
        Write-Host ($r | ConvertTo-Json)
    }
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)"
}
