param(
    [string]$AdminHost = '127.0.0.1',
    [string]$AdminPort = '5432',
    [string]$AdminDatabase = 'postgres',
    [string]$AdminUser = 'postgres',
    [string]$AdminPassword = '',
    [string]$AppDatabase = 'devlab_cliente',
    [string]$AppUser = 'devlab_app',
    [string]$AppPassword = '',
    [string]$PsqlPath = '',
    [string]$PgContainerName = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

if (-not $AppPassword) {
    throw 'Informe -AppPassword para provisionar o usuario da aplicacao.'
}

$adminHostLiteral = Escape-SqlLiteral $AdminHost
$adminPortLiteral = Escape-SqlLiteral $AdminPort
$adminDbLiteral = Escape-SqlLiteral $AdminDatabase
$adminUserLiteral = Escape-SqlLiteral $AdminUser
$appDbLiteral = Escape-SqlLiteral $AppDatabase
$appUserLiteral = Escape-SqlLiteral $AppUser
$appPasswordLiteral = Escape-SqlLiteral $AppPassword
$appDbIdent = Escape-SqlIdentifier $AppDatabase
$appUserIdent = Escape-SqlIdentifier $AppUser

$sql = @"
DO `$do`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$appUserLiteral') THEN
        EXECUTE 'CREATE ROLE "$appUserIdent" LOGIN PASSWORD ''$appPasswordLiteral''';
    ELSE
        EXECUTE 'ALTER ROLE "$appUserIdent" WITH LOGIN PASSWORD ''$appPasswordLiteral''';
    END IF;
END
`$do`$;

SELECT 'CREATE DATABASE "$appDbIdent" OWNER "$appUserIdent"'
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = '$appDbLiteral'
)\gexec

ALTER DATABASE "$appDbIdent" OWNER TO "$appUserIdent";
GRANT ALL PRIVILEGES ON DATABASE "$appDbIdent" TO "$appUserIdent";
"@

if ($PgContainerName) {
    $sql | & docker exec -i -e "PGPASSWORD=$AdminPassword" $PgContainerName psql -v ON_ERROR_STOP=1 -U $AdminUser -d $AdminDatabase
    if ($LASTEXITCODE -ne 0) {
        throw 'Falha ao provisionar PostgreSQL via container.'
    }
}
else {
    $psqlExecutable = if ($PsqlPath) {
        Resolve-AbsolutePath $PsqlPath
    }
    else {
        $psqlCommand = Get-Command 'psql' -ErrorAction SilentlyContinue
        if ($psqlCommand) { $psqlCommand.Source } else { '' }
    }

    if (-not $psqlExecutable) {
        throw 'psql nao encontrado. Informe -PsqlPath ou garanta psql no PATH.'
    }

    $originalPassword = $env:PGPASSWORD
    try {
        $env:PGPASSWORD = $AdminPassword
        $sql | & $psqlExecutable -v ON_ERROR_STOP=1 -h $AdminHost -p $AdminPort -U $AdminUser -d $AdminDatabase
        if ($LASTEXITCODE -ne 0) {
            throw 'Falha ao provisionar PostgreSQL.'
        }
    }
    finally {
        $env:PGPASSWORD = $originalPassword
    }
}

Write-Output "Provisionamento concluido."
Write-Output "Banco: $AppDatabase"
Write-Output "Usuario: $AppUser"
