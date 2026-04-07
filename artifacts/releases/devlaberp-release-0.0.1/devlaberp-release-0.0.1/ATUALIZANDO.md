# Atualizando e Distribuindo para Clientes

Atualizado em `2026-04-04`.

## Cenario Alvo

Este guia considera o cenario real do produto:

- `1 matriz`
- `1 ou mais filiais`
- `varios usuarios simultaneos`
- `rede local`
- `banco local no cliente`

## Fases de Execucao

O trabalho deve avancar em ordem. Nenhuma fase segue para a proxima sem os testes da fase atual estarem `100% OK`.

### Status Atual

- [x] Fase 1 - concluida em `2026-04-06`
- [x] Fase 2 - concluida em `2026-04-06`
- [x] Fase 3 - concluida em `2026-04-06`
- [x] Fase 4 - concluida em `2026-04-06`
- [x] Fase 5 - concluida em `2026-04-06`

### Fase 1 - Base de configuracao para producao local

Escopo:

- leitura de `.env` externo
- definicao de `APP_DATA_ROOT`
- externalizacao de `MEDIA_ROOT`, `STATIC_ROOT` e `LOG_ROOT`
- montagem de `DATABASE_URL` por variaveis de ambiente
- suporte oficial a `PostgreSQL`

Testes obrigatorios:

- testes unitarios da resolucao de ambiente e caminhos
- testes unitarios da montagem do banco `sqlite/postgresql`
- smoke de login e validacao basica

Resultado:

- [x] fase concluida
- [x] `49 testes OK`

### Fase 2 - Scripts operacionais

Escopo:

- `gerar-release.ps1`
- `instalar.ps1`
- `backup.ps1`
- `atualizar.ps1`
- `rollback.ps1`

Testes obrigatorios:

- execucao em pasta temporaria
- validacao de backup gerado
- validacao de rollback restaurando versao anterior

Resultado:

- [x] fase concluida
- [x] `11 testes OK`
- [x] smoke manual do `instalar.ps1` executado com sucesso
- [x] geracao de release operacional adicionada

### Fase 3 - Execucao em producao local

Escopo:

- troca de `runserver` por modo de execucao de producao
- servico Windows
- healthcheck basico

Testes obrigatorios:

- aplicacao sobe via comando de producao
- healthcheck responde
- reinicio do servico preserva operacao

Resultado:

- [x] fase concluida
- [x] `19 testes OK`
- [x] modo de producao via `waitress`
- [x] `healthcheck` publico implementado
- [x] scripts de start/stop e registro de servico adicionados

### Fase 4 - Banco e rede local

Escopo:

- padrao oficial com `PostgreSQL`
- checklist de acesso pela rede
- hardening minimo de deploy local

Testes obrigatorios:

- conexao com `PostgreSQL`
- migracoes em base limpa
- acesso HTTP pela rede local validado em ambiente de teste

Resultado:

- [x] fase concluida
- [x] `20 testes OK`
- [x] integracao real com `PostgreSQL` via Docker
- [x] migracao em base limpa validada
- [x] verificacao de ambiente adicionada

### Fase 5 - Atualizacao segura de cliente

Escopo:

- fluxo de backup
- fluxo de upgrade
- fluxo de rollback
- checklist final de implantacao no cliente

Testes obrigatorios:

- upgrade preserva banco e anexos
- rollback restaura banco e codigo
- smoke operacional final

Resultado:

- [x] fase concluida
- [x] `21 testes OK`
- [x] backup/upgrade/rollback validados com `PostgreSQL`
- [x] smoke final apos rollback validado

## Decisao de Arquitetura

Para esse cenario, a recomendacao tecnica deixa de ser `SQLite`.

### Banco de dados

- `Nao usar SQLite` para cliente com varios usuarios na rede
- `Usar PostgreSQL` instalado localmente no servidor da matriz

Motivo:

- `SQLite` nao e a escolha correta para multiusuario em rede local
- concorrencia, bloqueios e risco de corrupcao passam a ser um problema real
- `PostgreSQL` permite operacao simultanea, backup melhor, restauracao e crescimento

### Aplicacao

- a aplicacao roda em `um servidor local` na matriz
- os usuarios acessam pela rede local, via navegador
- as filiais acessam o mesmo servidor, desde que estejam na mesma rede ou VPN

### Servico web

Nao usar `manage.py runserver` em cliente final.

Usar:

- `waitress` para servir o Django no Windows
- `nssm` ou `Agendador de Tarefas` para manter o servico de pe
- opcionalmente `Caddy` ou `IIS` como proxy reverso

## Estrutura Recomendada no Cliente

Servidor da matriz:

```text
C:\DevLabERP\
  app\                 -> codigo da aplicacao
  venv\                -> ambiente Python
  releases\            -> pacotes/versionamento

C:\ProgramData\DevLabERP\
  env\.env             -> configuracao do cliente
  data\                -> anexos, media, arquivos locais
  backups\             -> backups do banco e media
  logs\                -> logs da aplicacao
  scripts\             -> scripts de instalar/atualizar/rollback
```

Banco:

- `PostgreSQL` instalado na maquina servidora
- base por cliente, por exemplo: `devlab_cliente_x`

## Checklist de Distribuicao Inicial

### Fase 1 - Preparar a Arquitetura Correta

- [x] trocar o ambiente padrao de cliente de `SQLite` para `PostgreSQL`
- [x] configurar leitura de banco por variaveis de ambiente
- [x] mover `MEDIA_ROOT`, logs e configuracoes para fora da pasta do codigo
- [x] garantir que o sistema funcione sem depender da pasta do desenvolvedor
- [x] garantir que o sistema suba sem `DEBUG`

Criterio de aceite:

- [x] o sistema funciona em uma pasta limpa, fora do repositorio

### Fase 2 - Empacotamento para Cliente

- [x] definir estrutura padrao de pastas do cliente
- [x] gerar pacote de release da aplicacao
- [x] incluir arquivo `.env.example`
- [x] incluir guias de instalacao e atualizacao
- [x] incluir script `instalar.ps1`
- [x] incluir script `atualizar.ps1`
- [x] incluir script `backup.ps1`
- [x] incluir script `rollback.ps1`

Criterio de aceite:

- [x] uma maquina nova consegue instalar o sistema so com o pacote entregue

### Fase 3 - Banco de Dados

- [ ] instalar `PostgreSQL` no servidor do cliente
- [ ] criar usuario do banco para a aplicacao
- [ ] criar base de dados do cliente
- [ ] configurar backup automatico do banco
- [ ] validar restauracao de teste

Criterio de aceite:

- [ ] banco roda localmente e suporta varios usuarios simultaneos

### Fase 4 - Aplicacao em Producao Local

- [ ] criar `venv` do cliente
- [ ] instalar dependencias
- [ ] configurar `.env`
- [ ] rodar `migrate`
- [ ] rodar `collectstatic`, se necessario
- [ ] subir a aplicacao via `waitress`
- [ ] registrar servico Windows
- [ ] configurar porta padrao da aplicacao

Criterio de aceite:

- [ ] sistema sobe automaticamente apos reiniciar a maquina

### Fase 5 - Rede Local

- [ ] definir IP fixo ou reserva DHCP para o servidor
- [ ] liberar a porta da aplicacao no firewall
- [ ] validar acesso pela rede local
- [ ] testar acesso simultaneo de pelo menos 3 usuarios
- [ ] validar impressao, se houver
- [ ] validar fiscal, se houver certificado

Criterio de aceite:

- [ ] usuarios acessam pelo navegador a partir de outras maquinas da rede

### Fase 6 - Dados Iniciais do Cliente

- [ ] instalar a versao correta
- [ ] fazer o primeiro acesso
- [ ] cadastrar a matriz
- [ ] cadastrar a filial
- [ ] criar usuario administrador do cliente
- [ ] criar usuarios operacionais
- [ ] vincular usuarios as empresas corretas
- [ ] validar empresa ativa
- [ ] validar acessos por perfil

Criterio de aceite:

- [ ] matriz e filial operam no mesmo ambiente com usuarios reais

## Checklist de Atualizacao Sem Perder Dados

### Antes de atualizar

- [ ] confirmar versao atual instalada
- [ ] confirmar versao alvo
- [ ] avisar o cliente da janela de manutencao
- [ ] pedir encerramento do uso do sistema
- [ ] fazer backup do banco
- [ ] fazer backup da pasta `media` ou equivalente
- [ ] validar que o backup foi gerado

### Durante a atualizacao

- [ ] parar o servico da aplicacao
- [ ] preservar `.env`
- [ ] preservar dados e anexos
- [ ] substituir apenas a pasta do codigo
- [ ] instalar dependencias novas, se houver
- [ ] rodar `migrate`
- [ ] rodar rotinas de saneamento de dados, se houver
- [ ] subir novamente o servico

### Depois da atualizacao

- [ ] validar login
- [ ] validar empresa ativa
- [ ] validar matriz
- [ ] validar filial
- [ ] validar cadastro de produto
- [ ] validar venda simples
- [ ] validar compra simples
- [ ] validar financeiro
- [ ] validar fiscal

Criterio de aceite:

- [ ] cliente atualiza sem perda de banco, anexos ou configuracoes

## Checklist de Rollback

Executar rollback quando:

- migracao falhar
- sistema nao subir
- fluxo critico quebrar apos a atualizacao

Passos:

- [ ] parar o servico
- [ ] restaurar backup do banco
- [ ] restaurar pasta anterior da aplicacao
- [ ] restaurar anexos, se necessario
- [ ] subir a versao anterior
- [ ] validar login e operacao basica

Criterio de aceite:

- [ ] cliente volta para a versao anterior com os dados preservados

## Checklist de Backup

### Banco

- [ ] backup diario completo
- [ ] retencao minima de 7 backups
- [ ] ao menos 1 copia externa

### Arquivos

- [ ] backup diario da pasta de `media`
- [ ] backup de certificados, se houver
- [ ] backup do `.env`

### Teste de restauracao

- [ ] restaurar banco em ambiente de teste
- [ ] validar que o sistema sobe com o backup restaurado

Criterio de aceite:

- [ ] backup nao e so arquivo gerado, e backup restauravel

## Estrutura de Ambiente Recomendada

Exemplo de `.env` para cliente:

```env
DEBUG=False
SECRET_KEY=trocar-em-cada-cliente
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.0.10

DB_ENGINE=postgresql
DB_NAME=devlab_cliente
DB_USER=devlab_app
DB_PASSWORD=senha_forte
DB_HOST=127.0.0.1
DB_PORT=5432

MEDIA_ROOT=C:/ProgramData/DevLabERP/data/media
LOG_ROOT=C:/ProgramData/DevLabERP/logs
```

## Mudancas Estruturais Recomendadas no Produto

Estas mudancas valem a pena antes de distribuir para cliente:

### Obrigatorias

- [x] remover dependencia pratica de `SQLite` para deploy real
- [x] adicionar suporte oficial a `PostgreSQL` nas configuracoes
- [x] externalizar `MEDIA_ROOT`, logs e `.env`
- [x] criar scripts de `instalar`, `atualizar`, `backup` e `rollback`
- [x] criar modo de execucao de producao sem `runserver`

### Muito recomendadas

- [x] criar comando de verificacao de ambiente
- [x] criar healthcheck do sistema
- [ ] registrar logs de atualizacao
- [ ] documentar porta, firewall e acesso pela rede

## Sequencia Recomendada de Entrega

### Etapa 1 - Estrutura de deploy

- [x] preparar configuracao para `PostgreSQL`
- [x] mover caminhos locais para fora do projeto
- [x] fechar `.env` de producao

### Etapa 2 - Scripts

- [x] criar `gerar-release.ps1`
- [x] criar `instalar.ps1`
- [x] criar `atualizar.ps1`
- [x] criar `backup.ps1`
- [x] criar `rollback.ps1`

### Etapa 3 - Operacao

- [x] subir servico local de producao
- [ ] testar acesso de varias maquinas na rede
- [ ] testar primeiro cliente real

## Decisao Final

Para o seu cenario, a estrategia correta e:

- `servidor local na matriz`
- `PostgreSQL local`
- `usuarios acessando pela rede`
- `codigo separado dos dados`
- `atualizacao por pacote + migrate + backup + rollback`

## Proximo Passo Pratico

Ordem recomendada agora:

1. fechar a configuracao do projeto para `PostgreSQL`
2. externalizar banco, media, logs e `.env`
3. criar scripts de instalacao e atualizacao
4. testar numa maquina limpa simulando cliente real
