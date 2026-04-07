param(
    [string]$SourceRoot = $PSScriptRoot,
    [string]$OutputRoot = (Join-Path $PSScriptRoot 'artifacts\releases'),
    [string]$Version = '',
    [switch]$Zip
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$sourceRootPath = Resolve-AbsolutePath $SourceRoot
$outputRootPath = Ensure-Directory $OutputRoot

if (-not $Version) {
    $initFile = Join-Path $sourceRootPath 'djangosige\__init__.py'
    if (Test-Path -LiteralPath $initFile) {
        $match = Select-String -Path $initFile -Pattern "__version__\s*=\s*'([^']+)'" | Select-Object -First 1
        if ($match) {
            $Version = $match.Matches[0].Groups[1].Value
        }
    }
}

if (-not $Version) {
    $Version = Get-TimestampString
}

$packageName = "devlaberp-release-$Version"
$releaseRoot = Join-Path $outputRootPath $packageName
$packageRoot = Join-Path $releaseRoot $packageName

Reset-Directory $releaseRoot | Out-Null
Copy-FilteredDirectory -Source $sourceRootPath -Destination $packageRoot -ExcludeNames (Get-ReleaseExcludeNames) | Out-Null

$docsToCopy = @(
    '.env.example',
    'README.md',
    'ATUALIZANDO.md',
    'README_INSTALACAO_CLIENTE.md',
    'README_ATUALIZACAO_CLIENTE.md'
)

foreach ($docName in $docsToCopy) {
    Copy-FileIfExists -Source (Join-Path $sourceRootPath $docName) -Destination (Join-Path $releaseRoot $docName) | Out-Null
}

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    version = $Version
    package_name = $packageName
    source_root = $sourceRootPath
    release_root = $releaseRoot
    app_root = $packageRoot
    scripts = Get-OperationalScriptFiles
}

Write-JsonFile -Path (Join-Path $releaseRoot 'release-manifest.json') -Data $manifest

if ($Zip) {
    $zipPath = Join-Path $outputRootPath "$packageName.zip"
    if (Test-Path -LiteralPath $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $releaseRoot '*') -DestinationPath $zipPath -Force
    Write-Output "Release gerada: $releaseRoot"
    Write-Output "ZIP: $zipPath"
}
else {
    Write-Output "Release gerada: $releaseRoot"
}
