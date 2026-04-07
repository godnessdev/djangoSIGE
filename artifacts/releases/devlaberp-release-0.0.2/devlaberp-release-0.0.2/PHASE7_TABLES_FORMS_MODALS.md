# Phase 7 Tabelas, Formularios e Modais

Atualizado em `2026-04-01 20:59:53`.

## Resultado

- listas padronizadas com busca, DataTables e estado inicial de remocao validados
- formularios pesados validados com acoes inline, placeholders de data e formsets padronizados
- modal financeiro validado com estrutura e footer consistentes
- telas/fluxos validados: `11`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

## Evidencias

### Cadastro lista

- URL: `/cadastro/cliente/listaclientes/`
- status HTTP: `200`
- screenshot: [list_1.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/list_1.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- table_exists: `True`
- search_type_search: `True`
- datatable_footer_exists: `True`
- datatable_footer_sections: `True`
- remove_button_disabled_initially: `True`
- datatable_info_exists: `True`
- datatable_paginate_exists: `True`

### Vendas lista

- URL: `/vendas/pedidovenda/listapedidovenda/`
- status HTTP: `200`
- screenshot: [list_2.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/list_2.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- table_exists: `True`
- search_type_search: `True`
- datatable_footer_exists: `True`
- datatable_footer_sections: `True`
- remove_button_disabled_initially: `True`
- datatable_info_exists: `True`
- datatable_paginate_exists: `True`

### Compras lista

- URL: `/compras/pedidocompra/listapedidocompra/`
- status HTTP: `200`
- screenshot: [list_3.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/list_3.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- table_exists: `True`
- search_type_search: `True`
- datatable_footer_exists: `True`
- datatable_footer_sections: `True`
- remove_button_disabled_initially: `True`
- datatable_info_exists: `True`
- datatable_paginate_exists: `True`

### Financeiro lista

- URL: `/financeiro/lancamentos/`
- status HTTP: `200`
- screenshot: [list_4.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/list_4.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- table_exists: `True`
- search_type_search: `True`
- datatable_footer_exists: `True`
- datatable_footer_sections: `True`
- remove_button_disabled_initially: `True`
- datatable_info_exists: `True`
- datatable_paginate_exists: `True`

### Fiscal lista

- URL: `/fiscal/notafiscal/saida/listanotafiscal/`
- status HTTP: `200`
- screenshot: [list_5.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/list_5.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- table_exists: `True`
- search_type_search: `True`
- datatable_footer_exists: `True`
- datatable_footer_sections: `True`
- remove_button_disabled_initially: `True`
- datatable_info_exists: `True`
- datatable_paginate_exists: `True`

### Cadastro formulario

- URL: `/cadastro/produto/adicionar/`
- status HTTP: `200`
- screenshot: [form_1.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/form_1.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- required_selector_present: `True`
- field_action_has_aria_label: `True`

### Vendas formulario

- URL: `/vendas/pedidovenda/adicionar/`
- status HTTP: `200`
- screenshot: [form_2.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/form_2.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- required_selector_present: `True`
- date_placeholder_present: `True`
- date_inputmode_numeric: `True`
- date_autocomplete_off: `True`
- field_action_has_aria_label: `True`
- formset_box_present: `True`

### Compras formulario

- URL: `/compras/pedidocompra/adicionar/`
- status HTTP: `200`
- screenshot: [form_3.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/form_3.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- required_selector_present: `True`
- date_placeholder_present: `True`
- date_inputmode_numeric: `True`
- date_autocomplete_off: `True`
- field_action_has_aria_label: `True`
- formset_box_present: `True`

### Financeiro formulario

- URL: `/financeiro/contapagar/adicionar/`
- status HTTP: `200`
- screenshot: [form_4.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/form_4.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- required_selector_present: `True`
- date_placeholder_present: `True`
- date_inputmode_numeric: `True`
- date_autocomplete_off: `True`
- field_action_has_aria_label: `True`

### Fiscal formulario

- URL: `/fiscal/notafiscal/saida/adicionar/`
- status HTTP: `200`
- screenshot: [form_5.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/form_5.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- required_selector_present: `True`
- date_placeholder_present: `True`
- date_inputmode_numeric: `True`
- date_autocomplete_off: `True`
- field_action_has_aria_label: `True`

### Financeiro modal

- URL: `/financeiro/lancamentos/`
- status HTTP: `200`
- screenshot: [financeiro_modal.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase7_components/financeiro_modal.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- modal_visible: `True`
- modal_footer_flex: `True`
- confirm_button_present: `True`
- date_placeholder_present: `True`
- date_inputmode_numeric: `True`
