$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
    throw "Ambiente virtual nao encontrado em .venv. Execute a configuracao inicial antes de iniciar o sistema."
}

$existing = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*manage.py runserver 0.0.0.0:8000*' -and $_.CommandLine -like '*devlab-system*' }

if ($existing) {
    Write-Output "Sistema ja esta online na porta 8000."
    $existing | Select-Object ProcessId, CommandLine
    exit 0
}

$process = Start-Process -FilePath '.\.venv\Scripts\python.exe' `
    -ArgumentList 'manage.py', 'runserver', '0.0.0.0:8000', '--noreload' `
    -WorkingDirectory $root `
    -PassThru

Write-Output "Sistema iniciado."
Write-Output "PID: $($process.Id)"
Write-Output "URL: http://127.0.0.1:8000/login/"
