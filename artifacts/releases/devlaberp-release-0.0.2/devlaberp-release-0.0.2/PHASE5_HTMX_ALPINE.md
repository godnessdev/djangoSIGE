# Phase 5 HTMX e Alpine.js

Atualizado em `2026-04-01 20:25:47`.

## Resultado

- `HTMX` adicionado como camada progressiva para consultas simples e submit de modal
- `Alpine.js` adicionado apenas para estados locais de carregamento/envio
- endpoints legados em JSON preservados e suporte HTMX negociado por `HX-Request`
- submit HX do modal financeiro coberto por teste Django dedicado em `djangosige.tests.validation.test_progressive_validation`
- `produto/formset` pesado permanece para a Fase 6/Fase 7
- telas validadas: `5`
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`

## Evidencias

### HTMX e Alpine carregados

- URL: `/vendas/pedidovenda/adicionar/`
- status HTTP: `200`
- screenshot: [vendor_stack.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase5_progressive/vendor_stack.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- htmx_loaded: `True`
- alpine_loaded: `True`
- progressive_api_loaded: `True`
- cliente_marked_progressive: `True`
- transportadora_marked_progressive: `True`

### Venda com painel progressivo de cliente

- URL: `/vendas/pedidovenda/adicionar/`
- status HTTP: `200`
- screenshot: [venda_cliente.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase5_progressive/venda_cliente.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- empty_state_removed: `True`
- limite_or_indicator_populated: `True`

### Compra com painel progressivo de fornecedor

- URL: `/compras/pedidocompra/adicionar/`
- status HTTP: `200`
- screenshot: [compra_fornecedor.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase5_progressive/compra_fornecedor.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- empty_state_removed: `True`
- fornecedor_fields_present: `True`

### NF-e com paineis progressivos de emitente e destinatario

- URL: `/fiscal/notafiscal/saida/adicionar/`
- status HTTP: `200`
- screenshot: [fiscal_emit_dest.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase5_progressive/fiscal_emit_dest.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- emit_empty_state_removed: `True`
- dest_empty_state_removed: `True`
- emit_fields_present: `True`
- dest_fields_present: `True`

### Modal progressivo de gerar lancamento

- URL: `/financeiro/lancamentos/`
- status HTTP: `200`
- screenshot: [lancamento_modal.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase5_progressive/lancamento_modal.png)
- console warnings/errors: `0`
- page errors: `0`
- requests com falha: `0`
- button_marked_progressive: `True`
- modal_visible_during_flow: `True`
- alpine_bound_to_modal: `True`
