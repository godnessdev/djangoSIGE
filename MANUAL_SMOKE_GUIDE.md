# Smoke Manual Guiado

Atualizado em `2026-04-01`.

## Objetivo

Checklist curto para validar a stack front depois de mexer em visual, assets ou JS.

## Preparacao

- subir o sistema em `http://127.0.0.1:8000/login/`
- entrar com um usuario administrativo
- usar `Ctrl+F5` antes de validar telas alteradas

## Fluxos principais

### 1. Login

- abrir `/login/`
- confirmar carregamento de CSS, sem tela crua
- validar submit de login

### 2. Dashboard

- abrir `/`
- confirmar menu lateral, topbar e cards sem erro visual
- abrir e fechar a sidebar

### 3. Lista administrativa

- abrir `/cadastro/cliente/listaclientes/`
- usar a busca
- confirmar paginação e footer do DataTables
- marcar um item e verificar habilitação do botão remover

### 4. Cadastro com tabs

- abrir `/cadastro/cliente/adicionar/`
- clicar em `DADOS BANCARIOS`
- confirmar somente uma aba e um pane ativos

### 5. Financeiro com checkbox

- abrir `/financeiro/contapagar/adicionar/`
- marcar e desmarcar `movimentar_caixa`
- confirmar que o checkbox continua clicável e com visual correto

### 6. Modal global

- em qualquer tela autenticada, disparar uma mensagem do sistema ou uma remoção
- confirmar abertura do modal com botões corretos

### 7. Fiscal com tabs

- abrir `/fiscal/notafiscal/saida/adicionar/`
- clicar em `INFORMACOES ADICIONAIS`
- confirmar troca correta da aba

### 8. Paginas de erro

- abrir uma URL inexistente, por exemplo `/pagina-inexistente-smoke/`
- confirmar tela `404` estilizada e sem runtime JS desnecessário

## Sinais de regressao

- erro ou warning no console
- request de asset falhando
- duas abas ativas ao mesmo tempo
- checkbox/radio com tamanho de input de texto
- lista sem paginação ou busca
- modal sem foco ou sem botão esperado
