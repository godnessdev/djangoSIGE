# Phase 8 Performance Front e Entrega

Atualizado em `2026-04-01 21:29:42`.

## Resultado

- shell JS global do app caiu de `527.8 KB` para `446.6 KB`
- reducao do caminho critico sem lista: `-81.3 KB` por pagina
- paginas de erro deixaram de carregar `164.3 KB` de JavaScript legado
- `DataTables` saiu do carregamento global e agora sobe apenas nas telas com `#lista-database`
- listas continuam com busca, paginacao, footer reorganizado e remocao em massa

## Comparativo de Tempo de Resposta

| Tela | Baseline Fase 0 | Atual | Delta | Status | HTML |
| --- | --- | --- | --- | --- | --- |
| Login | `11.2 ms` | `12.8 ms` | `+1.6 ms` | `200` | `5.8 KB` |
| Dashboard | `17.6 ms` | `18.1 ms` | `+0.5 ms` | `200` | `29.4 KB` |
| Cadastro Clientes | `6.4 ms` | `7.0 ms` | `+0.6 ms` | `200` | `23.2 KB` |
| Vendas Pedidos | `5.2 ms` | `4.9 ms` | `-0.3 ms` | `200` | `23.0 KB` |
| Compras Pedidos | `5.0 ms` | `5.3 ms` | `+0.3 ms` | `200` | `23.0 KB` |
| Financeiro Lancamentos | `5.6 ms` | `6.5 ms` | `+0.9 ms` | `200` | `26.3 KB` |
| Estoque Consulta | `5.9 ms` | `6.8 ms` | `+0.9 ms` | `200` | `25.2 KB` |
| Fiscal NFs | `5.1 ms` | `4.5 ms` | `-0.6 ms` | `200` | `26.0 KB` |

## Medicao Browser

| Tela | Status | Carga total | Assets estaticos | DataTables | Evidencia |
| --- | --- | --- | --- | --- | --- |
| Login | `200` | `1720.8 ms` | `786.6 KB` | `False` | [page_1.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase8_performance/page_1.png) |
| Dashboard | `200` | `1407.8 ms` | `801.3 KB` | `False` | [page_2.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase8_performance/page_2.png) |
| Cadastro Lista | `200` | `1445.0 ms` | `882.6 KB` | `True` | [page_3.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase8_performance/page_3.png) |
| Cadastro Formulario | `200` | `1520.5 ms` | `913.6 KB` | `False` | [page_4.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase8_performance/page_4.png) |
| Erro 404 | `404` | `1385.7 ms` | `0.0 B` | `False` | [page_5.png](C:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/artifacts/phase8_performance/page_5.png) |

## Rede Local Mais Lenta

Latencia simulada de `75 ms` por request estatico para verificar regressao perceptivel no shell atual.

| Tela | Status | Carga total |
| --- | --- | --- |
| Dashboard lento | `200` | `2222.4 ms` |
| Cadastro lista lento | `200` | `2327.1 ms` |
| Cadastro formulario lento | `200` | `2558.5 ms` |

## Checks

### Login

- URL: `/login/`
- recursos estaticos unicos: `13`
- datatables_not_loaded: `True`

### Dashboard

- URL: `/`
- recursos estaticos unicos: `14`
- datatables_not_loaded: `True`

### Cadastro Lista

- URL: `/cadastro/cliente/listaclientes/`
- recursos estaticos unicos: `15`
- datatables_loaded: `True`
- datatable_footer_present: `True`
- remove_button_disabled_initially: `True`

### Cadastro Formulario

- URL: `/cadastro/cliente/adicionar/`
- recursos estaticos unicos: `17`
- datatables_not_loaded: `True`

### Erro 404

- URL: `/pagina-inexistente-phase8/`
- recursos estaticos unicos: `0`
- datatables_not_loaded: `True`
- error_page_has_no_js_runtime: `True`
