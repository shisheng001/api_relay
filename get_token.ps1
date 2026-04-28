# Extract Railway session
$leveldbPath = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Local Storage\leveldb"
$railwayToken = "IndrX0xRN0EzRW5rX0RpMmQ2MUM3Nzd3TEdMeWc4czE0NmhDN1hacVFlVTQ2bV9jbGllbnRTZXNzaW9u"
try {
    $decoded = [System.Convert]::FromBase64String($railwayToken)
    Write-Host "Token decoded: $([System.Text.Encoding]::UTF8.GetString($decoded))"
} catch {
    Write-Host "Failed: $_"
}
