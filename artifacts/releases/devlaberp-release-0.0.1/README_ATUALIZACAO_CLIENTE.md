# Atualizacao do Cliente

Atualizado em `2026-04-06`.

## Objetivo

Este guia define o fluxo seguro para atualizar um cliente sem perder:

- banco de dados
- midia e anexos
- configuracao `.env`
- capacidade de rollback

## Regra principal

Nao reinstalar do zero.

Atualizacao correta:

1. gerar nova release
2. copiar a release para o cliente
3. executar `atualizar.ps1`
4. executar `migrar-banco.ps1`
5. executar `verificar-ambiente.ps1`
6. subir novamente a aplicacao

Se houver falha:

7. executar `rollback.ps1`

## Passo 1 - Gerar a nova release

Na sua maquina:

```powershell
powershell -ExecutionPolicy Bypass -File .\gerar-release.ps1 -Version 1.0.1 -Zip
```

## Passo 2 - Copiar a release para o cliente

Copie a nova pasta de release para o servidor do cliente.

## Passo 3 - Parar o sistema antes do update

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\parar-producao.ps1 -DataRoot C:\ProgramData\DevLabERP
```

## Passo 4 - Atualizar o codigo com backup automatico

Na pasta da nova release:

```powershell
powershell -ExecutionPolicy Bypass -File .\devlaberp-release-1.0.1\atualizar.ps1 -SourceRoot .\devlaberp-release-1.0.1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -DatabaseEngine postgresql -DbName devlab_cliente -DbUser devlab_app -DbPassword SUA_SENHA -DbHost 127.0.0.1 -DbPort 5432
```

Esse comando:

- faz backup antes
- preserva `.env`
- preserva midia
- troca o codigo da aplicacao
- atualiza os scripts em `C:\ProgramData\DevLabERP\scripts`

## Passo 5 - Rodar migracoes

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\migrar-banco.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe
```

## Passo 6 - Verificar ambiente e conexao

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\verificar-ambiente.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe
```

## Passo 7 - Subir novamente

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\iniciar-producao.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe -ListenHost 0.0.0.0 -Port 8000
```

## Passo 8 - Validacao pos-update

Validacoes minimas:

- [ ] login abre
- [ ] healthcheck responde
- [ ] matriz abre
- [ ] filial abre
- [ ] produto abre
- [ ] venda simples abre
- [ ] compra simples abre
- [ ] financeiro abre
- [ ] fiscal abre

Healthcheck:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\healthcheck.ps1 -Url http://127.0.0.1:8000/healthz/
```

## Como localizar o backup gerado

O ultimo backup fica referenciado em:

```text
C:\ProgramData\DevLabERP\backups\last-backup.txt
```

## Rollback

Se a atualizacao falhar:

1. parar a aplicacao
2. pegar o caminho do backup
3. rodar rollback
4. validar login e operacao minima

Exemplo:

```powershell
$backup = Get-Content C:\ProgramData\DevLabERP\backups\last-backup.txt -Raw
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\rollback.ps1 -BackupPath $backup.Trim() -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -DbName devlab_cliente -DbUser devlab_app -DbPassword SUA_SENHA -DbHost 127.0.0.1 -DbPort 5432
```

Depois:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\iniciar-producao.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe -ListenHost 0.0.0.0 -Port 8000
```

## Checklist de atualizacao

- [ ] nova release gerada
- [ ] release copiada para o cliente
- [ ] sistema parado
- [ ] `atualizar.ps1` executado
- [ ] backup automatico confirmado
- [ ] `migrar-banco.ps1` executado
- [ ] `verificar-ambiente.ps1` executado
- [ ] sistema iniciado novamente
- [ ] smoke operacional validado

## Checklist de rollback

- [ ] sistema parado
- [ ] caminho do backup identificado
- [ ] `rollback.ps1` executado
- [ ] sistema iniciado novamente
- [ ] smoke minimo validado
