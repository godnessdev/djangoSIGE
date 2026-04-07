param(
    [string]$SourceRoot = $PSScriptRoot,
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP')
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$sourceRootPath = Resolve-AbsolutePath $SourceRoot
$installRootPath = Ensure-Directory $InstallRoot
$dataRootPath = Ensure-Directory $DataRoot
$appRoot = Join-Path $installRootPath 'app'
$dataEnvRoot = Ensure-Directory (Join-Path $dataRootPath 'env')
$dataMediaRoot = Ensure-Directory (Get-DefaultMediaPath $dataRootPath)
$dataLogRoot = Ensure-Directory (Join-Path $dataRootPath 'logs')
$dataBackupRoot = Ensure-Directory (Join-Path $dataRootPath 'backups')
$dataScriptsRoot = Ensure-Directory (Join-Path $dataRootPath 'scripts')

Copy-FilteredDirectory -Source $sourceRootPath -Destination $appRoot -ExcludeNames (Get-ReleaseExcludeNames) | Out-Null

$scriptFiles = Get-OperationalScriptFiles

foreach ($scriptName in $scriptFiles) {
    Copy-FileIfExists -Source (Join-Path $PSScriptRoot $scriptName) -Destination (Join-Path $dataScriptsRoot $scriptName) | Out-Null
}

$envExampleSource = Join-Path $PSScriptRoot '.env.example'
$envExampleDestination = Join-Path $dataEnvRoot '.env.example'
Copy-FileIfExists -Source $envExampleSource -Destination $envExampleDestination | Out-Null

$envDestination = Join-Path $dataEnvRoot '.env'
if (-not (Test-Path -LiteralPath $envDestination) -and (Test-Path -LiteralPath $envExampleDestination)) {
    Copy-Item -LiteralPath $envExampleDestination -Destination $envDestination -Force
}

$manifest = [ordered]@{
    installed_at = (Get-Date).ToString('s')
    source_root = $sourceRootPath
    install_root = $installRootPath
    app_root = $appRoot
    data_root = $dataRootPath
    env_root = $dataEnvRoot
    media_root = $dataMediaRoot
    log_root = $dataLogRoot
    backup_root = $dataBackupRoot
    scripts_root = $dataScriptsRoot
}

Write-JsonFile -Path (Join-Path $dataRootPath 'install-manifest.json') -Data $manifest

Write-Output "Instalacao concluida."
Write-Output "App: $appRoot"
Write-Output "Dados: $dataRootPath"
Write-Output "Scripts: $dataScriptsRoot"
