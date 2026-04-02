$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
    throw "Ambiente virtual nao encontrado em .venv."
}

$python = '.\.venv\Scripts\python.exe'

& $python manage.py test `
    djangosige.tests.login `
    djangosige.tests.cadastro `
    djangosige.tests.estoque `
    djangosige.tests.compras `
    djangosige.tests.vendas `
    djangosige.tests.financeiro `
    djangosige.tests.fiscal `
    djangosige.tests.validation

& $python manage.py bootstrap_matriz_filial_loadtest `
    --prefix LOADTEST `
    --products 10000 `
    --clients 10000 `
    --suppliers 10000 `
    --payables 10000 `
    --receivables 10000 `
    --sales 200 `
    --purchases 200 `
    --transfers 20 `
    --batch-size 1000
