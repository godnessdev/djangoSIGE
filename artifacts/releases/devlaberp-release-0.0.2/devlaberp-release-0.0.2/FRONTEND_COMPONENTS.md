# Componentes Front Reutilizaveis

Atualizado em `2026-04-01`.

## Shell

- `base/base.html`
  Contrato: carrega shell global, menu lateral, topbar, modal global e bloco `js`.
- `base/modal.html`
  Contrato: modal global de mensagens usado por `AppCore.messages`.
- `base/search.html`
  Contrato: busca padrão de listas com `#search-bar`.

## Listas

- `#lista-database`
  Contrato: tabela padrão para DataTables.
- `.app-datatable-footer`
  Contrato: rodapé reorganizado por `admin.js`/`progressive-enhancement.js`.
- `.btn-remove`
  Contrato: ação em massa; deve iniciar desabilitada após init.

## Formularios

- `.form-group` + `.form-line`
  Contrato: unidade base de campo legado.
- `.field-action`
  Contrato: ação inline ao lado do campo; deve ter `aria-label`.
- `.is-choice-group`
  Contrato: grupo com checkbox/radio; evita herança indevida de `form-control`.
- `input.datepicker`
  Contrato: placeholder `dd/mm/aaaa`, `inputmode="numeric"`, `autocomplete="off"`.
- `input.datetimepicker`
  Contrato: placeholder `dd/mm/aaaa hh:mm`, `inputmode="numeric"`, `autocomplete="off"`.

## Tabs

- `.nav-tabs a[data-toggle="tab"]`
  Contrato: compatibilidade legada com Bootstrap 5 via `bootstrap-compat.js`.
- `.tab-content .tab-pane`
  Contrato: somente uma aba e um pane ativos por vez.

## Formsets

- `.formset-box`
  Contrato: container legado de formsets.
- `.app-formset-box`
  Contrato: shell visual padronizado para formsets mais pesados.
- `.add-formset` / `.remove-formset`
  Contrato: ações controladas por `admin.js`.

## Componentes progressivos

- `data-progressive="htmx"`
  Contrato: o elemento já foi migrado para fluxo HTMX e nao deve duplicar bind jQuery legado.
- painéis em `templates/progressive/*.html`
  Contrato: resposta HTML parcial para requests HTMX.

## Componentes que exigem cuidado

- listas com `DataTables`
- tabs de cadastro e fiscal
- modais financeiros
- formulários com máscaras, datepicker ou formset

Antes de alterar qualquer um deles, rodar a validacao da fase correspondente e a [Fase 9](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE9_QUALITY.md).
