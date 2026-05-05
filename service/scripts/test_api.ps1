$loginBody = '{"username":"admin","password":"admin123"}'
$loginResp = Invoke-RestMethod -Uri 'http://localhost:8000/api/system/login' -Method Post -Body $loginBody -ContentType 'application/json'
$token = $loginResp.data.accessToken
Write-Host "LOGIN_OK TOKEN=$token"
