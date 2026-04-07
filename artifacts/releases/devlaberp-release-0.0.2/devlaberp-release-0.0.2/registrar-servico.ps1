param(
    [string]$InstallRoot = (Join-Path $env:ProgramFiles 'DevLabERP'),
    [string]$DataRoot = (Join-Path $env:ProgramData 'DevLabERP'),
    [string]$ServiceName = 'DevLabERP',
    [string]$PythonPath = '',
    [string]$ListenHost = '0.0.0.0',
    [int]$Port = 8000,
    [switch]$EmitOnly
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'deploy-common.ps1')

$dataRootPath = Ensure-Directory $DataRoot
$scriptsRoot = Ensure-Directory (Join-Path $dataRootPath 'scripts')
$starterScript = Join-Path $scriptsRoot 'iniciar-producao.ps1'
$nssm = Get-Command 'nssm.exe' -ErrorAction SilentlyContinue

$pythonArgument = if ($PythonPath) { "-PythonPath `"$PythonPath`"" } else { '' }
$serviceCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$starterScript`" -InstallRoot `"$InstallRoot`" -DataRoot `"$DataRoot`" -ListenHost `"$ListenHost`" -Port $Port $pythonArgument"

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    service_name = $ServiceName
    install_root = (Resolve-AbsolutePath $InstallRoot)
    data_root = $dataRootPath
    start_command = $serviceCommand
    provider = if ($nssm) { 'nssm' } else { 'manual' }
}

Write-JsonFile -Path (Join-Path $dataRootPath 'service-manifest.json') -Data $manifest

if ($EmitOnly -or -not $nssm) {
    Write-Output $serviceCommand
    if (-not $nssm) {
        Write-Output 'NSSM nao encontrado. Manifesto do servico gerado para configuracao manual.'
    }
    exit 0
}

& $nssm.Source install $ServiceName "powershell.exe" "-NoProfile -ExecutionPolicy Bypass -File `"$starterScript`" -InstallRoot `"$InstallRoot`" -DataRoot `"$DataRoot`" -ListenHost `"$ListenHost`" -Port $Port $pythonArgument"
Write-Output "Servico registrado: $ServiceName"
