# Instalacao no Cliente

Atualizado em `2026-04-06`.

## Objetivo

Este guia e para instalar o DevLab ERP em um cliente com:

- `servidor local na matriz`
- `PostgreSQL local`
- `usuarios acessando pela rede local`

## O que voce leva para o cliente

Leve a `release` gerada por [gerar-release.ps1](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/gerar-release.ps1).

Estrutura esperada da entrega:

```text
devlaberp-release-X.Y.Z\
  devlaberp-release-X.Y.Z\   -> codigo da aplicacao
  .env.example
  README_INSTALACAO_CLIENTE.md
  README_ATUALIZACAO_CLIENTE.md
  ATUALIZANDO.md
  release-manifest.json
```

## Pre-requisitos na maquina do cliente

Antes de instalar, garanta:

- Windows com acesso administrativo
- Python instalado, ou `venv` ja preparado
- `PostgreSQL` instalado localmente
- `psql` disponivel no servidor
- firewall liberado para a porta da aplicacao
- IP fixo ou reserva DHCP no servidor

## Estrutura final da instalacao

Destino recomendado:

```text
C:\DevLabERP\app
C:\ProgramData\DevLabERP\env\.env
C:\ProgramData\DevLabERP\data\media
C:\ProgramData\DevLabERP\logs
C:\ProgramData\DevLabERP\backups
C:\ProgramData\DevLabERP\scripts
```

## Passo 1 - Gerar a release na sua maquina

No projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\gerar-release.ps1 -Version 1.0.0 -Zip
```

Isso gera a pasta em `artifacts\releases` e, se usado `-Zip`, tambem um `.zip`.

## Passo 2 - Copiar a release para o servidor do cliente

Copie a pasta ou o zip para a maquina servidora do cliente.

Se usar zip:

1. extraia o arquivo
2. entre na pasta da release

## Passo 3 - Instalar a aplicacao

Na pasta da release:

```powershell
powershell -ExecutionPolicy Bypass -File .\devlaberp-release-1.0.0\instalar.ps1 -SourceRoot .\devlaberp-release-1.0.0 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP
```

Resultado esperado:

- aplicacao copiada para `C:\DevLabERP\app`
- scripts operacionais copiados para `C:\ProgramData\DevLabERP\scripts`
- `.env` criado em `C:\ProgramData\DevLabERP\env\.env`

## Passo 4 - Ajustar o .env do cliente

Editar:

```text
C:\ProgramData\DevLabERP\env\.env
```

Modelo minimo:

```env
DEBUG=False
SECRET_KEY=trocar-em-cada-cliente
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.0.10

APP_DATA_ROOT=C:/ProgramData/DevLabERP
MEDIA_ROOT=C:/ProgramData/DevLabERP/data/media
STATIC_ROOT=C:/ProgramData/DevLabERP/data/staticfiles
LOG_ROOT=C:/ProgramData/DevLabERP/logs

DB_ENGINE=postgresql
DB_NAME=devlab_cliente
DB_USER=devlab_app
DB_PASSWORD=senha_forte
DB_HOST=127.0.0.1
DB_PORT=5432
```

## Passo 5 - Provisionar usuario e banco do PostgreSQL

Se o PostgreSQL ja estiver instalado no servidor, voce pode criar o usuario e o banco automaticamente:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\provisionar-postgres.ps1 -AdminHost 127.0.0.1 -AdminPort 5432 -AdminDatabase postgres -AdminUser postgres -AdminPassword SENHA_DO_POSTGRES -AppDatabase devlab_cliente -AppUser devlab_app -AppPassword SENHA_DA_APLICACAO
```

Esse comando:

- cria o usuario `devlab_app` se nao existir
- atualiza a senha do usuario
- cria o banco `devlab_cliente` se nao existir
- define o dono do banco

Se voce preferir fazer manualmente, o equivalente no `psql` e:

```sql
CREATE USER devlab_app WITH PASSWORD 'SENHA_DA_APLICACAO';
CREATE DATABASE devlab_cliente OWNER devlab_app;
GRANT ALL PRIVILEGES ON DATABASE devlab_cliente TO devlab_app;
```

## Passo 6 - Preparar o Python de producao

Use `Python 3.12 x64`.

Se o cliente ainda nao tiver a `venv`:

```powershell
cd C:\DevLabERP
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r .\app\requirements.txt
```

## Passo 7 - Rodar migracoes

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\migrar-banco.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe
```

## Passo 8 - Verificar o ambiente

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\verificar-ambiente.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe
```

O comando precisa terminar sem erro.

## Passo 9 - Subir a aplicacao em modo producao

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\iniciar-producao.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -PythonPath C:\DevLabERP\venv\Scripts\python.exe -ListenHost 0.0.0.0 -Port 8000
```

## Passo 10 - Testar o healthcheck

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\healthcheck.ps1 -Url http://127.0.0.1:8000/healthz/
```

Esperado:

```json
{"status": "ok", "service": "devlab-erp"}
```

## Passo 11 - Registrar como servico

Se tiver `nssm` instalado:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ProgramData\DevLabERP\scripts\registrar-servico.ps1 -InstallRoot C:\DevLabERP -DataRoot C:\ProgramData\DevLabERP -ServiceName DevLabERP
```

Se nao tiver `nssm`, o script gera o comando e o manifesto para configuracao manual.

## Passo 12 - Validar acesso na rede

De outra maquina da rede:

```text
http://IP-DO-SERVIDOR:8000/login/
```

Validacoes minimas:

- login abre
- onboarding abre em base vazia
- healthcheck responde
- 2 ou mais maquinas acessam ao mesmo tempo

## Checklist final de instalacao

- [ ] release gerada e copiada
- [ ] app instalado em `C:\DevLabERP`
- [ ] `.env` do cliente ajustado
- [ ] usuario e banco PostgreSQL provisionados
- [ ] `venv` preparada
- [ ] dependencias instaladas
- [ ] migracoes executadas
- [ ] ambiente validado
- [ ] aplicacao iniciada em modo producao
- [ ] acesso pela rede validado
- [ ] servico registrado
