param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP'),
    [string]$MediaRoot = '',
    [string]$DbHost = '',
    [string]$DbPort = '',
    [string]$DbName = '',
    [string]$DbUser = '',
    [string]$DbPassword = '',
    [string]$PsqlPath = '',
    [string]$PgContainerName = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$backupPathResolved = Resolve-AbsolutePath $BackupPath
if (-not (Test-Path -LiteralPath $backupPathResolved)) {
    throw "Backup nao encontrado: $BackupPath"
}

$installRootPath = Ensure-Directory $InstallRoot
$dataRootPath = Ensure-Directory $DataRoot
$manifestPath = Join-Path $backupPathResolved 'backup-manifest.json'
$manifest = $null

if (Test-Path -LiteralPath $manifestPath) {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
}

$resolvedMediaRoot = if ($MediaRoot) {
    Resolve-AbsolutePath $MediaRoot
}
elseif ($manifest -and $manifest.PSObject.Properties.Name -contains 'media_restore_path' -and $manifest.media_restore_path) {
    Resolve-AbsolutePath $manifest.media_restore_path
}
else {
    Resolve-AbsolutePath (Get-DefaultMediaPath $dataRootPath)
}

if (Test-Path -LiteralPath (Join-Path $backupPathResolved 'app')) {
    Copy-FilteredDirectory -Source (Join-Path $backupPathResolved 'app') -Destination (Join-Path $installRootPath 'app') | Out-Null
}

$backupEnvPath = Join-Path (Join-Path $backupPathResolved 'env') '.env'
if (Test-Path -LiteralPath $backupEnvPath) {
    Copy-FileIfExists -Source $backupEnvPath -Destination (Join-Path (Join-Path $dataRootPath 'env') '.env') | Out-Null
}

$backupEnvExamplePath = Join-Path (Join-Path $backupPathResolved 'env') '.env.example'
if (Test-Path -LiteralPath $backupEnvExamplePath) {
    Copy-FileIfExists -Source $backupEnvExamplePath -Destination (Join-Path (Join-Path $dataRootPath 'env') '.env.example') | Out-Null
}

if (Test-Path -LiteralPath (Join-Path $backupPathResolved 'media')) {
    Copy-FilteredDirectory -Source (Join-Path $backupPathResolved 'media') -Destination $resolvedMediaRoot | Out-Null
}

if ($manifest -and $manifest.database_backup -and $manifest.database_engine -eq 'sqlite' -and $manifest.database_restore_path) {
    $databaseBackupDir = Join-Path $backupPathResolved 'database'
    $databaseBackupFile = Get-ChildItem -LiteralPath $databaseBackupDir -File | Select-Object -First 1
    if ($databaseBackupFile) {
        Copy-FileIfExists -Source $databaseBackupFile.FullName -Destination $manifest.database_restore_path | Out-Null
    }
}
elseif ($manifest -and $manifest.database_backup -and $manifest.database_engine -in @('postgres', 'postgresql', 'pgsql')) {
    $databaseDump = Join-Path (Join-Path $backupPathResolved 'database') 'postgres.sql'
    if (Test-Path -LiteralPath $databaseDump) {
        $resolvedDbHost = if ($DbHost) { $DbHost } elseif ($manifest.database_host) { $manifest.database_host } else { '127.0.0.1' }
        $resolvedDbPort = if ($DbPort) { $DbPort } elseif ($manifest.database_port) { $manifest.database_port } else { '5432' }
        $resolvedDbName = if ($DbName) { $DbName } elseif ($manifest.database_name) { $manifest.database_name } else { '' }
        $resolvedDbUser = if ($DbUser) { $DbUser } elseif ($manifest.database_user) { $manifest.database_user } else { '' }
        $resolvedDbPassword = $DbPassword

        if (-not $resolvedDbPassword) {
            $envPath = Get-DefaultEnvPath $dataRootPath
            $envValues = Read-EnvFile $envPath
            if ($envValues['DB_PASSWORD']) {
                $resolvedDbPassword = $envValues['DB_PASSWORD']
            }
        }

        if ($PgContainerName) {
            Get-Content -LiteralPath $databaseDump -Raw |
                & docker exec -i -e "PGPASSWORD=$resolvedDbPassword" $PgContainerName psql -U $resolvedDbUser -d $resolvedDbName
        }
        else {
            $psqlExecutable = if ($PsqlPath) { Resolve-AbsolutePath $PsqlPath } else {
                $psqlCommand = Get-Command 'psql' -ErrorAction SilentlyContinue
                if ($psqlCommand) { $psqlCommand.Source } else { '' }
            }

            if (-not $psqlExecutable) {
                throw 'psql nao encontrado para rollback PostgreSQL.'
            }

            $originalPassword = $env:PGPASSWORD
            try {
                $env:PGPASSWORD = $resolvedDbPassword
                Get-Content -LiteralPath $databaseDump -Raw | & $psqlExecutable -h $resolvedDbHost -p $resolvedDbPort -U $resolvedDbUser -d $resolvedDbName
            }
            finally {
                $env:PGPASSWORD = $originalPassword
            }
        }
    }
}

Write-Output "Rollback concluido: $backupPathResolved"
