param(
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP'),
    [string]$BackupRoot = '',
    [switch]$IncludeApp,
    [string]$DatabaseEngine = 'auto',
    [string]$DatabasePath = '',
    [string]$MediaRoot = ''
    ,[string]$DbHost = ''
    ,[string]$DbPort = ''
    ,[string]$DbName = ''
    ,[string]$DbUser = ''
    ,[string]$DbPassword = ''
    ,[string]$PgDumpPath = ''
    ,[string]$PgContainerName = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$installRootPath = Resolve-AbsolutePath $InstallRoot
$dataRootPath = Resolve-AbsolutePath $DataRoot
$backupRootPath = if ($BackupRoot) { Ensure-Directory $BackupRoot } else { Ensure-Directory (Join-Path $dataRootPath 'backups') }
$timestamp = Get-TimestampString
$backupPath = Ensure-Directory (Join-Path $backupRootPath $timestamp)
$envPath = Get-DefaultEnvPath $dataRootPath
$envValues = Read-EnvFile $envPath

$resolvedMediaRoot = if ($MediaRoot) { Resolve-AbsolutePath $MediaRoot } elseif ($envValues.ContainsKey('MEDIA_ROOT')) { Resolve-AbsolutePath $envValues['MEDIA_ROOT'] } else { Resolve-AbsolutePath (Get-DefaultMediaPath $dataRootPath) }

$resolvedDatabaseEngine = $DatabaseEngine
if ($resolvedDatabaseEngine -eq 'auto') {
    if ($envValues.ContainsKey('DB_ENGINE')) {
        $resolvedDatabaseEngine = $envValues['DB_ENGINE']
    }
    elseif ($envValues.ContainsKey('DATABASE_URL') -and $envValues['DATABASE_URL'] -like 'sqlite:*') {
        $resolvedDatabaseEngine = 'sqlite'
    }
    elseif ($envValues.ContainsKey('DATABASE_URL') -and $envValues['DATABASE_URL'] -like 'postgres*') {
        $resolvedDatabaseEngine = 'postgresql'
    }
    else {
        $resolvedDatabaseEngine = ''
    }
}

$resolvedDatabasePath = $DatabasePath
if (-not $resolvedDatabasePath -and $resolvedDatabaseEngine -eq 'sqlite') {
    if ($envValues.ContainsKey('DB_NAME')) {
        if ([System.IO.Path]::IsPathRooted($envValues['DB_NAME'])) {
            $resolvedDatabasePath = Resolve-AbsolutePath $envValues['DB_NAME']
        }
        else {
            $resolvedDatabasePath = Resolve-AbsolutePath (Join-Path $dataRootPath $envValues['DB_NAME'])
        }
    }
    elseif ($envValues.ContainsKey('DATABASE_URL') -and $envValues['DATABASE_URL'] -like 'sqlite:///*') {
        $resolvedDatabasePath = $envValues['DATABASE_URL'].Substring('sqlite:///'.Length)
    }
}

$resolvedDbHost = if ($DbHost) { $DbHost } elseif ($envValues['DB_HOST']) { $envValues['DB_HOST'] } else { '127.0.0.1' }
$resolvedDbPort = if ($DbPort) { $DbPort } elseif ($envValues['DB_PORT']) { $envValues['DB_PORT'] } else { '5432' }
$resolvedDbName = if ($DbName) { $DbName } elseif ($envValues['DB_NAME']) { $envValues['DB_NAME'] } else { '' }
$resolvedDbUser = if ($DbUser) { $DbUser } elseif ($envValues['DB_USER']) { $envValues['DB_USER'] } else { '' }
$resolvedDbPassword = if ($DbPassword) { $DbPassword } elseif ($envValues['DB_PASSWORD']) { $envValues['DB_PASSWORD'] } else { '' }

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    install_root = $installRootPath
    data_root = $dataRootPath
    include_app = [bool]$IncludeApp
    env_backup = $false
    media_backup = $false
    database_backup = $false
    database_engine = $resolvedDatabaseEngine
    database_restore_path = $resolvedDatabasePath
    media_restore_path = $resolvedMediaRoot
    database_host = $resolvedDbHost
    database_port = $resolvedDbPort
    database_name = $resolvedDbName
    database_user = $resolvedDbUser
}

if ($IncludeApp -and (Test-Path -LiteralPath (Join-Path $installRootPath 'app'))) {
    Copy-FilteredDirectory -Source (Join-Path $installRootPath 'app') -Destination (Join-Path $backupPath 'app') | Out-Null
}

$backupEnvRoot = Ensure-Directory (Join-Path $backupPath 'env')
$envCopied = Copy-FileIfExists -Source $envPath -Destination (Join-Path $backupEnvRoot '.env')
if (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $envPath) '.env.example')) {
    Copy-FileIfExists -Source (Join-Path (Split-Path -Parent $envPath) '.env.example') -Destination (Join-Path $backupEnvRoot '.env.example') | Out-Null
}
$manifest.env_backup = [bool]$envCopied

$mediaCopied = Copy-DirectoryIfExists -Source $resolvedMediaRoot -Destination (Join-Path $backupPath 'media')
$manifest.media_backup = [bool]$mediaCopied

if ($resolvedDatabaseEngine -eq 'sqlite' -and $resolvedDatabasePath) {
    $databaseDir = Ensure-Directory (Join-Path $backupPath 'database')
    if (Copy-FileIfExists -Source $resolvedDatabasePath -Destination (Join-Path $databaseDir (Split-Path -Leaf $resolvedDatabasePath))) {
        $manifest.database_backup = $true
    }
}
elseif ($resolvedDatabaseEngine -in @('postgres', 'postgresql', 'pgsql')) {
    if (-not $resolvedDbName -or -not $resolvedDbUser) {
        throw 'Configuracao PostgreSQL incompleta para backup.'
    }

    $databaseDir = Ensure-Directory (Join-Path $backupPath 'database')
    $dumpFile = Join-Path $databaseDir 'postgres.sql'

    if ($PgContainerName) {
        $originalPassword = $env:PGPASSWORD
        try {
            $env:PGPASSWORD = $resolvedDbPassword
            & docker exec -e "PGPASSWORD=$resolvedDbPassword" $PgContainerName pg_dump -U $resolvedDbUser -d $resolvedDbName --clean --if-exists --no-owner --no-privileges |
                Out-File -FilePath $dumpFile -Encoding utf8
            $manifest.database_backup = $true
        }
        finally {
            $env:PGPASSWORD = $originalPassword
        }
    }
    else {
        $pgDumpExecutable = if ($PgDumpPath) { Resolve-AbsolutePath $PgDumpPath } else {
            $pgDumpCommand = Get-Command 'pg_dump' -ErrorAction SilentlyContinue
            if ($pgDumpCommand) { $pgDumpCommand.Source } else { '' }
        }

        if (-not $pgDumpExecutable) {
            throw 'pg_dump nao encontrado para backup PostgreSQL.'
        }

        $originalPassword = $env:PGPASSWORD
        try {
            $env:PGPASSWORD = $resolvedDbPassword
            & $pgDumpExecutable -h $resolvedDbHost -p $resolvedDbPort -U $resolvedDbUser -d $resolvedDbName --clean --if-exists --no-owner --no-privileges -f $dumpFile
            $manifest.database_backup = $true
        }
        finally {
            $env:PGPASSWORD = $originalPassword
        }
    }
}

Write-JsonFile -Path (Join-Path $backupPath 'backup-manifest.json') -Data $manifest
[System.IO.File]::WriteAllText((Join-Path $backupRootPath 'last-backup.txt'), $backupPath, [System.Text.UTF8Encoding]::new($false))

Write-Output $backupPath
