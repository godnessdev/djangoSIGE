param(
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP')
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$dataRootPath = Resolve-AbsolutePath $DataRoot
$pidFile = Join-Path (Join-Path $dataRootPath 'logs') 'devlab-prod.pid'

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Output 'Nenhum processo de producao registrado.'
    exit 0
}

$processIdValue = (Get-Content -LiteralPath $pidFile -Raw).Trim()
if (-not $processIdValue) {
    Remove-Item -LiteralPath $pidFile -Force
    Write-Output 'Arquivo PID vazio removido.'
    exit 0
}

$process = Get-Process -Id $processIdValue -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item -LiteralPath $pidFile -Force
    Write-Output "PID $processIdValue nao estava ativo."
    exit 0
}

Stop-Process -Id $processIdValue -Force
Remove-Item -LiteralPath $pidFile -Force
Write-Output "Processo de producao finalizado: $processIdValue"
