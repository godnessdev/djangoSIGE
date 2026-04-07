# Atualizacao do Cliente

Atualizado em `2026-04-07`.

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

## Regra de banco

Alteracao de banco nunca e feita manualmente no cliente.

Quando a versao nova muda estrutura:

- a estrutura ja vem versionada em `migrations`
- o cliente recebe isso via release
- a aplicacao do banco acontece com `migrar-banco.ps1`

Ou seja:

- `nao` criar coluna no `pgAdmin` para "ajudar"
- `nao` editar tabela direto no `PostgreSQL`
- `nao` rodar SQL avulso sem estar documentado

## Regra de dependencia

Se a release mudou `requirements.txt`, rode tambem:

```powershell
C:\DevLabERP\venv\Scripts\python.exe -m pip install -r C:\DevLabERP\app\requirements.txt
```

A `venv` so precisa ser recriada se:

- o Python do servidor estiver errado
- a `venv` estiver corrompida
- a instalacao anterior tiver sido perdida

Em atualizacao normal, a `venv` e reaproveitada.

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

## Passo 5 - Instalar dependencias, se houver mudanca

Se a release alterou `requirements.txt`:

```powershell
C:\DevLabERP\venv\Scripts\python.exe -m pip install -r C:\DevLabERP\app\requirements.txt
```

Se nao alterou, siga para o proximo passo.

## Passo 6 - Rodar migracoes e gerar estaticos

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\migrar-banco.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe
```

Esse script faz:

- `manage.py migrate --noinput`
- `manage.py collectstatic --noinput`

Logo, ele e obrigatorio mesmo em releases que mudam template, CSS ou JS.

## Passo 7 - Verificar ambiente e conexao

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\verificar-ambiente.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe
```

## Passo 8 - Subir novamente

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\iniciar-producao.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe -ListenHost 0.0.0.0 -Port 8000
```

## Passo 9 - Validacao pos-update

Validacoes minimas:

- [ ] `http://127.0.0.1:8000/healthz/`
- [ ] `http://127.0.0.1:8000/login/`
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

## Sequencia oficial sem atalhos

Toda atualizacao correta segue exatamente esta ordem:

1. parar
2. backup
3. atualizar codigo
4. instalar dependencia nova, se houver
5. migrar banco e gerar estaticos
6. verificar ambiente
7. subir novamente
8. validar login e fluxo minimo

Nao inverter:

- `migrate` antes de trocar codigo
- `iniciar-producao` antes de `migrar-banco`
- smoke funcional antes de `healthcheck`

## Checklist de atualizacao

- [ ] nova release gerada
- [ ] release copiada para o cliente
- [ ] sistema parado
- [ ] `atualizar.ps1` executado
- [ ] backup automatico confirmado
- [ ] dependencias atualizadas, se necessario
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
