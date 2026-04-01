# Phase 0 Visual Validation

Atualizado em `2026-04-01 16:32:25`.

## Escopo

- validacao visual com navegador real headless usando Microsoft Edge
- telas exigidas pela Fase 0: login, dashboard, lista, formulario e modais
- evidencias salvas em `artifacts/phase0_visual`

## Resultado Geral

- telas validadas: `7`
- avisos/erros de console capturados: `0`
- erros de pagina capturados: `0`
- requests com falha capturados: `0`

## Evidencias por Tela

### Login

- URL: `/login/`
- URL final: `http://127.0.0.1:8000/login/`
- titulo do documento: `DjangoSIGE | Login`
- classes do body: `login-page ls-closed`
- stylesheets ativos: `3`
- scripts no documento: `4`
- tamanho do HTML renderizado: `5831 bytes`
- screenshot: [login.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/login.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

### Modal base no login

- URL: `/login/`
- URL final: `http://127.0.0.1:8000/login/`
- titulo do documento: `DjangoSIGE | Login`
- classes do body: `login-page ls-closed modal-open`
- stylesheets ativos: `3`
- scripts no documento: `4`
- tamanho do HTML renderizado: `6013 bytes`
- screenshot: [login_modal.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/login_modal.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

### Dashboard

- URL: `/`
- URL final: `http://127.0.0.1:8000/`
- titulo do documento: `DjangoSIGE | Página Inicial`
- classes do body: `theme`
- stylesheets ativos: `3`
- scripts no documento: `4`
- tamanho do HTML renderizado: `28842 bytes`
- screenshot: [dashboard.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/dashboard.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

### Lista de clientes

- URL: `/cadastro/cliente/listaclientes/`
- URL final: `http://127.0.0.1:8000/cadastro/cliente/listaclientes/`
- titulo do documento: `DjangoSIGE | Clientes Cadastrados`
- classes do body: `theme`
- stylesheets ativos: `3`
- scripts no documento: `4`
- tamanho do HTML renderizado: `24701 bytes`
- screenshot: [clientes_lista.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/clientes_lista.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

### Formulario de cliente

- URL: `/cadastro/cliente/adicionar/`
- URL final: `http://127.0.0.1:8000/cadastro/cliente/adicionar/`
- titulo do documento: `DjangoSIGE | Cadastrar Cliente`
- classes do body: `theme`
- stylesheets ativos: `4`
- scripts no documento: `10`
- tamanho do HTML renderizado: `52786 bytes`
- screenshot: [cliente_form.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/cliente_form.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

### Lancamentos financeiros

- URL: `/financeiro/lancamentos/`
- URL final: `http://127.0.0.1:8000/financeiro/lancamentos/`
- titulo do documento: `DjangoSIGE | Todos Os Lançamentos`
- classes do body: `theme`
- stylesheets ativos: `4`
- scripts no documento: `9`
- tamanho do HTML renderizado: `24748 bytes`
- screenshot: [financeiro_lista.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/financeiro_lista.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

### Modal financeiro

- URL: `/financeiro/lancamentos/`
- URL final: `http://127.0.0.1:8000/financeiro/lancamentos/`
- titulo do documento: `DjangoSIGE | Todos Os Lançamentos`
- classes do body: `theme modal-open`
- stylesheets ativos: `4`
- scripts no documento: `9`
- tamanho do HTML renderizado: `24828 bytes`
- screenshot: [financeiro_modal.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase0_visual/financeiro_modal.png)
- console: `0` eventos de warning/error
- page errors: `0`
- requests com falha: `0`

## Conclusao

- a Fase 0 possui baseline tecnico e visual documentado
- qualquer regressao de stack ou layout agora pode ser comparada contra os artefatos desta fase