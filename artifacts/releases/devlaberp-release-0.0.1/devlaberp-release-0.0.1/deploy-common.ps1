$ErrorActionPreference = 'Stop'

function Resolve-AbsolutePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Assert-SafeDirectoryTarget {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $resolved = Resolve-AbsolutePath $Path
    $root = [System.IO.Path]::GetPathRoot($resolved)

    if ([string]::IsNullOrWhiteSpace($resolved) -or $resolved -eq $root) {
        throw "Caminho inseguro para operacao destrutiva: $Path"
    }

    return $resolved
}

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $resolved = Resolve-AbsolutePath $Path
    if (-not (Test-Path -LiteralPath $resolved)) {
        New-Item -ItemType Directory -Path $resolved -Force | Out-Null
    }
    return $resolved
}

function Reset-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $resolved = Assert-SafeDirectoryTarget $Path
    if (Test-Path -LiteralPath $resolved) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    New-Item -ItemType Directory -Path $resolved -Force | Out-Null
    return $resolved
}

function Get-ReleaseExcludeNames {
    return @(
        '.git',
        '.github',
        '.idea',
        '.venv',
        '.pytest_cache',
        '__pycache__',
        'artifacts',
        'build',
        'dist',
        'env',
        'media',
        'staticfiles',
        'logs',
        '.env',
        'db.sqlite3',
        'runserver.stdout.log',
        'runserver.stderr.log'
    )
}

function Get-OperationalScriptFiles {
    return @(
        'deploy-common.ps1',
        'instalar.ps1',
        'backup.ps1',
        'atualizar.ps1',
        'rollback.ps1',
        'iniciar-producao.ps1',
        'parar-producao.ps1',
        'healthcheck.ps1',
        'registrar-servico.ps1',
        'migrar-banco.ps1',
        'verificar-ambiente.ps1'
    )
}

function Copy-FilteredDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination,
        [string[]]$ExcludeNames = @()
    )

    $sourcePath = Resolve-AbsolutePath $Source
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Origem nao encontrada: $Source"
    }

    $destinationPath = Reset-Directory $Destination

    Get-ChildItem -LiteralPath $sourcePath -Force | ForEach-Object {
        if ($ExcludeNames -contains $_.Name) {
            return
        }

        $target = Join-Path $destinationPath $_.Name
        if ($_.PSIsContainer) {
            Copy-FilteredDirectory -Source $_.FullName -Destination $target -ExcludeNames $ExcludeNames
        }
        else {
            Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        }
    }

    return $destinationPath
}

function Copy-DirectoryIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    $sourcePath = Resolve-AbsolutePath $Source
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        return $false
    }

    Copy-FilteredDirectory -Source $sourcePath -Destination $Destination | Out-Null
    return $true
}

function Copy-FileIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    $sourcePath = Resolve-AbsolutePath $Source
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        return $false
    }

    $destinationPath = Resolve-AbsolutePath $Destination
    $destinationDir = Split-Path -Parent $destinationPath
    Ensure-Directory $destinationDir | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    return $true
}

function Read-EnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $values = @{}
    $resolved = Resolve-AbsolutePath $Path
    if (-not (Test-Path -LiteralPath $resolved)) {
        return $values
    }

    Get-Content -LiteralPath $resolved | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) {
            return
        }

        $parts = $line.Split('=', 2)
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }

    return $values
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        $Data
    )

    $destination = Resolve-AbsolutePath $Path
    $dir = Split-Path -Parent $destination
    Ensure-Directory $dir | Out-Null
    $json = $Data | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($destination, $json, [System.Text.UTF8Encoding]::new($false))
}

function Get-TimestampString {
    return (Get-Date).ToString('yyyyMMdd-HHmmss')
}

function Get-DefaultEnvPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DataRoot
    )

    return Join-Path (Join-Path $DataRoot 'env') '.env'
}

function Get-DefaultMediaPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DataRoot
    )

    return Join-Path (Join-Path $DataRoot 'data') 'media'
}
