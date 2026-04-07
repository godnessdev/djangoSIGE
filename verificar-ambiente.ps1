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
$envValues = Read-EnvFile $resolvedEnvPath

if ($envValues['DEBUG'] -eq 'True') {
    throw 'Ambiente invalido: DEBUG=True'
}

if (-not $envValues['SECRET_KEY'] -or $envValues['SECRET_KEY'] -eq 'trocar-em-cada-cliente') {
    throw 'Ambiente invalido: SECRET_KEY nao definida corretamente'
}

if (-not $envValues['ALLOWED_HOSTS']) {
    throw 'Ambiente invalido: ALLOWED_HOSTS vazio'
}

$originalEnvPath = $env:SIGE_ENV_PATH
$originalDjangoSettingsModule = $env:DJANGO_SETTINGS_MODULE
try {
    $env:SIGE_ENV_PATH = $resolvedEnvPath
    $env:DJANGO_SETTINGS_MODULE = 'djangosige.configs'
    Push-Location $appRoot
    & $pythonExecutable manage.py check
    & $pythonExecutable -c "import os; os.environ.setdefault('SIGE_ENV_PATH', r'$resolvedEnvPath'); import django; django.setup(); from django.db import connection; connection.ensure_connection(); cursor = connection.cursor(); cursor.execute('SELECT 1'); print('DB_OK')"
}
finally {
    Pop-Location
    $env:SIGE_ENV_PATH = $originalEnvPath
    $env:DJANGO_SETTINGS_MODULE = $originalDjangoSettingsModule
}
