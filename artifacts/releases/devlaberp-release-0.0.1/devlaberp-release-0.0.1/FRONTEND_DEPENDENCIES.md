# Dependencias Front Oficiais

Atualizado em `2026-04-01`.

## Shell principal

- `Bootstrap 5.3.3`
  Arquivos: `djangosige/static/css/bootstrap.min.css`, `djangosige/static/js/bootstrap/bootstrap.min.js`
  Papel: grid, modal, tabs, dropdowns e utilitarios base.
- `bootstrap-compat.css` e `bootstrap-compat.js`
  Arquivos: `djangosige/static/css/bootstrap-compat.css`, `djangosige/static/js/bootstrap/bootstrap-compat.js`
  Papel: compatibilidade incremental com markup legado de Bootstrap 3.
- `jQuery 3.7.1`
  Arquivo: `djangosige/static/js/jquery/jquery-3.0.0.min.js`
  Papel: suporte aos plugins legados ainda ativos.
- `AppCore`
  Arquivo: `djangosige/static/js/app-core.js`
  Papel: shell principal, sidebar, overlay, modal global, loader e anotações de acessibilidade.
- `admin.js`
  Arquivo: `djangosige/static/js/admin.js`
  Papel: automações legadas, formsets, datepickers, masks, requests AJAX e DataTables.
- `progressive-enhancement.js`
  Arquivo: `djangosige/static/js/progressive-enhancement.js`
  Papel: camada progressiva para HTMX, DataTables e formulários modernizados.

## Interacao progressiva

- `HTMX 2.0.8`
  Arquivo: `djangosige/static/js/vendor/htmx.min.js`
  Papel: carregamento parcial, trocas HTML e submit progressivo.
- `Alpine.js`
  Arquivo: `djangosige/static/js/vendor/alpine.min.js`
  Papel: estados pequenos de interface e comportamento local.

## Plugins legados ainda oficiais

- `DataTables 1.10.13`
  Arquivo: `djangosige/static/js/jquery.dataTables.min.js`
  Papel: listas administrativas com busca, paginação e ordenação.
  Regra: nao carregar diretamente no `base.html`; usar o lazy-load do `window.SIGE_ASSETS.dataTables`.
- `jQuery UI 1.12.1`
  Arquivo: `djangosige/static/js/jquery-ui.min.js`
  Papel: `datepicker`, `autocomplete` e `tooltip` legado.
- `jquery.datetimepicker`
  Arquivo: `djangosige/static/js/jquery.datetimepicker.full.min.js`
  Papel: campos de data e hora.
- `jquery.mask 1.14.8`
  Arquivo: `djangosige/static/js/jquery.mask.js`
  Papel: máscaras de telefone, CPF/CNPJ, valores e campos numéricos.
- `MultiSelect 0.9.12`
  Arquivo: `djangosige/static/js/jquery.multi-select.js`
  Papel: seleção múltipla na edição de permissões.

## CSS do projeto

- `style.css`
  Papel: legado estrutural do projeto.
- `theme-overrides.css`
  Papel: design system, componentes padronizados e overrides modernos.

## Regras de carga

- scripts globais ficam concentrados em [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)
- plugins pesados ou específicos devem entrar só via include da tela ou lazy-load
- `404.html` e `500.html` nao devem carregar runtime JS
- qualquer nova dependencia front deve ser documentada neste arquivo antes de entrar no shell
