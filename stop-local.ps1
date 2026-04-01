$ErrorActionPreference = 'Stop'

$processes = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*manage.py runserver*8000*' -and $_.CommandLine -like '*devlab-system*' }

if (-not $processes) {
    Write-Output 'Nenhum servidor local do devlab-system esta em execucao na porta 8000.'
    exit 0
}

$processes | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
    Write-Output "Processo finalizado: $($_.ProcessId)"
}
