param(
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP'),
    [string]$PythonPath = '',
    [string]$EnvPath = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$installRootPath = Resolve-AbsolutePath $InstallRoot
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
    throw 'Python nao encontrado. Informe -PythonPath.'
}

$dataRootPath = Resolve-AbsolutePath $DataRoot
$resolvedEnvPath = if ($EnvPath) { Resolve-AbsolutePath $EnvPath } else { Resolve-AbsolutePath (Get-DefaultEnvPath $dataRootPath) }

$originalEnvPath = $env:SIGE_ENV_PATH
try {
    $env:SIGE_ENV_PATH = $resolvedEnvPath
    Push-Location $appRoot
    & $pythonExecutable manage.py migrate --noinput
}
finally {
    Pop-Location
    $env:SIGE_ENV_PATH = $originalEnvPath
}
