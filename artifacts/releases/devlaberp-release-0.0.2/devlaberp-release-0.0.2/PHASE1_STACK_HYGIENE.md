# Phase 1 Stack Hygiene

Atualizado em `2026-04-01 16:42:36`.

## Ajustes Aplicados

- ordem de assets normalizada em `base.html`: vendor CSS, app CSS, overrides e core JS
- `Materialize` saiu do `@import` de `style.css` e passou a ser carregado explicitamente
- overrides visuais de 2026 isolados em `djangosige/static/css/theme-overrides.css`
- loaders repetidos padronizados em `load_jquery_mask.html`, `load_jqueryui.html` e `load_datetimepicker.html`
- duplicidade do modal base removida das telas de login e lista de usuarios

## Resultado da Validacao

- telas verificadas: `5`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- comparacao com a baseline visual da Fase 0: mantido em `0` erros de console e `0` requests falhos

## Evidencias

### Login sem autenticacao

- URL: `/login/`
- screenshot: [login.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase1_hygiene/login.png)
- stylesheets_loaded: `True`
- scripts_loaded: `True`
- datatable_absent: `True`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

### Dashboard com menu lateral

- URL: `/`
- screenshot: [dashboard_menu.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase1_hygiene/dashboard_menu.png)
- submenu_visible: `True`
- body_class_present: `True`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

### Lista com DataTables

- URL: `/cadastro/cliente/listaclientes/`
- screenshot: [clientes_lista.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase1_hygiene/clientes_lista.png)
- datatable_available: `True`
- datatable_wrapper_present: `True`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

### Formulario com mask e jQuery UI

- URL: `/cadastro/cliente/adicionar/`
- screenshot: [cliente_form.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase1_hygiene/cliente_form.png)
- mask_available: `True`
- jquery_ui_available: `True`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

### Lista financeira com dropdown e modal

- URL: `/financeiro/lancamentos/`
- screenshot: [financeiro_higiene.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase1_hygiene/financeiro_higiene.png)
- dropdown_visible: `True`
- modal_open: `True`
- mask_available: `True`
- jquery_ui_available: `True`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

## Dependencias Mantidas de Forma Intencional

- `jQuery`, `Bootstrap 3`, `DataTables`, `jQuery UI`, `jquery.mask`, `jquery.datetimepicker` e `jquery.multi-select` continuam ativos
- nenhuma biblioteca funcional foi removida nesta fase; o foco foi reduzir acoplamento e padronizar a carga