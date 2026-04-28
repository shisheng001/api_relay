$headers = @{
    'Authorization' = 'Bearer wk_LQ7A3Enk_Di2d61C777wLGLyg8s146hC7XZqQeU46m'
    'Content-Type' = 'application/json'
    'Origin' = 'https://railway.app'
    'Referer' = 'https://railway.app'
}

$endpoint = "https://backboard.railway.app/graphql/v1"
$body = '{"query":"{ me { email id } }"}'

Write-Host "Testing Railway GraphQL API with extracted token..."
try {
    $r = Invoke-RestMethod -Uri $endpoint -Headers $headers -Method POST -Body $body -TimeoutSec 15
    if ($r.data.me) {
        Write-Host "[成功] 用户: $($r.data.me.email)"
        Write-Host "[成功] ID: $($r.data.me.id)"
    } else {
        Write-Host "[失败] $($r | ConvertTo-Json)"
    }
} catch {
    Write-Host "[错误] $($_.Exception.Message)"
    Write-Host "状态码: $($_.Exception.Response.StatusCode.value__)"
}
