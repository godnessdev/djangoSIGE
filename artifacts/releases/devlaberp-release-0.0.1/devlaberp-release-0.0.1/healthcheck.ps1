param(
    [string]$Url = 'http://127.0.0.1:8000/healthz/'
)

$ErrorActionPreference = 'Stop'

$response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
if ($response.StatusCode -ne 200) {
    throw "Healthcheck falhou com status $($response.StatusCode)"
}

Write-Output $response.Content
