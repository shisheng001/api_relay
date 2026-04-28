$headers = @{
    'Authorization' = 'Bearer a541ddba-dd55-4337-90de-1eb670b39ec0'
    'Content-Type' = 'application/json'
}
$body = '{"query":"{ me { email } }"}'
try {
    $response = Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v1' -Headers $headers -Method POST -Body $body
    Write-Output $response
} catch {
    Write-Output "Error: $_"
    Write-Output "Status: $($_.Exception.Response.StatusCode)"
}
