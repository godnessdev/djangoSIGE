param(
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP'),
    [string]$PythonPath = '',
    [string]$ListenHost = '0.0.0.0',
    [int]$Port = 8000,
    [string]$EnvPath = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$installRootPath = Resolve-AbsolutePath $InstallRoot
$dataRootPath = Ensure-Directory $DataRoot
$appRoot = Join-Path $installRootPath 'app'
if (-not (Test-Path -LiteralPath $appRoot)) {
    throw "Aplicacao nao encontrada em $appRoot"
}

$pythonExecutable = if ($PythonPath) {
    Resolve-AbsolutePath $PythonPath
}
elseif (Test-Path -LiteralPath (Join-Path $installRootPath 'venv\Scripts\python.exe')) {
    Resolve-AbsolutePath (Join-Path $installRootPath 'venv\Scripts\python.exe')
}
else {
    throw 'Python de producao nao encontrado. Informe -PythonPath.'
}

$resolvedEnvPath = if ($EnvPath) { Resolve-AbsolutePath $EnvPath } else { Resolve-AbsolutePath (Get-DefaultEnvPath $dataRootPath) }
$logRoot = Ensure-Directory (Join-Path $dataRootPath 'logs')
$pidFile = Join-Path $logRoot 'devlab-prod.pid'
$stdoutLog = Join-Path $logRoot 'devlab-prod.stdout.log'
$stderrLog = Join-Path $logRoot 'devlab-prod.stderr.log'

if (Test-Path -LiteralPath $pidFile) {
    $existingPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    if ($existingPid) {
        $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($existingProcess) {
            Write-Output "Servico de producao ja esta em execucao. PID: $existingPid"
            exit 0
        }
    }
    Remove-Item -LiteralPath $pidFile -Force
}

$runnerScriptPath = Join-Path $logRoot 'devlab-prod-runner.py'
$runnerScript = @"
import os
import sys
from waitress import serve

os.environ.setdefault("SIGE_ENV_PATH", r"$resolvedEnvPath")
sys.path.insert(0, r"$appRoot")

from djangosige.wsgi import application

serve(application, host="$ListenHost", port=$Port)
"@
[System.IO.File]::WriteAllText($runnerScriptPath, $runnerScript, [System.Text.UTF8Encoding]::new($false))

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = $pythonExecutable
$processInfo.WorkingDirectory = $appRoot
$processInfo.Arguments = "`"$runnerScriptPath`""
$processInfo.UseShellExecute = $true
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null

[System.IO.File]::WriteAllText($pidFile, [string]$process.Id, [System.Text.UTF8Encoding]::new($false))

Write-Output "Servico de producao iniciado."
Write-Output "PID: $($process.Id)"
Write-Output "URL: http://$ListenHost`:$Port/healthz/"
