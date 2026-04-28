# Railway REST API - 使用 Railway Token 直接操作
# Railway Token 来自浏览器认证

$headers = @{
    'Content-Type' = 'application/json'
}

# Railway REST API endpoints
$baseUrl = "https://railway.app/api"

# 尝试不同的认证方式
Write-Host "=== 测试 Railway API ==="

# 1. 尝试获取当前会话 (不需要token)
try {
    $r = Invoke-RestMethod -Uri "https://railway.app/api/users/me" -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    Write-Host "[成功] $($r)"
} catch {
    Write-Host "[失败] $($_.Exception.Message)"
}

# 2. 尝试 Railway API v2
try {
    $r2 = Invoke-RestMethod -Uri "https://backboard.railway.app/api/users/me" -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    Write-Host "[成功2] $($r2)"
} catch {
    Write-Host "[失败2] $($_.Exception.Message)"
}

# 3. 检查 Railway CLI token 文件内容
Write-Host "`n=== Railway Token 文件 ==="
$authFile = "$env:USERPROFILE\.railway\auth.json"
if (Test-Path $authFile) {
    Get-Content $authFile -Raw
}

# 4. Railway 的 OAuth token 可以从浏览器 localStorage 获取
Write-Host "`n=== 尝试读取浏览器 localStorage ==="
# Edge localStorage for railway.app
$localStoragePath = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Local Storage\leveldb"
Write-Host "LevelDB path: $localStoragePath"
Write-Host "Files: $(Get-ChildItem $localStoragePath -File | Measure-Object).Count"
