param(
    [string]$SourceRoot = $PSScriptRoot,
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP'),
    [string]$DatabaseEngine = 'auto',
    [string]$DatabasePath = '',
    [string]$MediaRoot = '',
    [string]$DbHost = '',
    [string]$DbPort = '',
    [string]$DbName = '',
    [string]$DbUser = '',
    [string]$DbPassword = '',
    [string]$PgDumpPath = '',
    [string]$PgContainerName = '',
    [switch]$SkipBackup
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$sourceRootPath = Resolve-AbsolutePath $SourceRoot
$installRootPath = Ensure-Directory $InstallRoot
$dataRootPath = Ensure-Directory $DataRoot
$scriptsRoot = Ensure-Directory (Join-Path $dataRootPath 'scripts')

$backupPath = ''
if (-not $SkipBackup) {
    $backupScript = Join-Path $scriptsRoot 'backup.ps1'
    if (-not (Test-Path -LiteralPath $backupScript)) {
        $backupScript = Join-Path $PSScriptRoot 'backup.ps1'
    }

    $backupPath = & $backupScript `
        -InstallRoot $installRootPath `
        -DataRoot $dataRootPath `
        -IncludeApp `
        -DatabaseEngine $DatabaseEngine `
        -DatabasePath $DatabasePath `
        -MediaRoot $MediaRoot `
        -DbHost $DbHost `
        -DbPort $DbPort `
        -DbName $DbName `
        -DbUser $DbUser `
        -DbPassword $DbPassword `
        -PgDumpPath $PgDumpPath `
        -PgContainerName $PgContainerName
}

$appRoot = Join-Path $installRootPath 'app'
Copy-FilteredDirectory -Source $sourceRootPath -Destination $appRoot -ExcludeNames (Get-ReleaseExcludeNames) | Out-Null

$scriptFiles = Get-OperationalScriptFiles

foreach ($scriptName in $scriptFiles) {
    Copy-FileIfExists -Source (Join-Path $sourceRootPath $scriptName) -Destination (Join-Path $scriptsRoot $scriptName) | Out-Null
}

$envRoot = Ensure-Directory (Join-Path $dataRootPath 'env')
Copy-FileIfExists -Source (Join-Path $sourceRootPath '.env.example') -Destination (Join-Path $envRoot '.env.example') | Out-Null

$manifest = [ordered]@{
    updated_at = (Get-Date).ToString('s')
    source_root = $sourceRootPath
    install_root = $installRootPath
    data_root = $dataRootPath
    backup_path = $backupPath
}

Write-JsonFile -Path (Join-Path $dataRootPath 'update-manifest.json') -Data $manifest

if ($backupPath) {
    Write-Output "Atualizacao concluida. Backup: $backupPath"
}
else {
    Write-Output 'Atualizacao concluida.'
}
