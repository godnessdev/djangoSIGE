# Validation Checklist

Atualizado em `2026-04-01`.

## Inventario de rotas nomeadas

- `admin`: 20
- `base`: 1
- `login`: 12
- `cadastro`: 30
- `vendas`: 22
- `compras`: 19
- `financeiro`: 24
- `estoque`: 14
- `fiscal`: 28

## Evidencia automatica atual

- `manage.py check`: `OK`
- Smoke test autenticado de rotas sem parametros: `OK`
- Suite operacional de fluxos: `8/8` testes passando
- Suite completa atual: `164/175` testes passando

Comando de smoke:

```powershell
.\.venv\Scripts\python contrib\validate_smoke.py
```

Comando da suite operacional:

```powershell
.\.venv\Scripts\python manage.py test djangosige.tests.validation --verbosity 2
```

## Status por modulo

- `Base`: `OK`
  Fluxo inicial e dashboard respondendo `200`.
- `Login`: `OK`
  Login, cadastro de usuario, perfil, selecao de empresa, detalhe e exclusao de usuario validados.
- `Cadastro`: `OK`
  Adicao, edicao com `pk` e endpoints AJAX principais validados.
- `Vendas`: `OK`
  Adicao, edicao, AJAX, PDFs e acoes de gerar/copiar/cancelar validados.
- `Compras`: `OK`
  Adicao, edicao, AJAX, PDFs, gerar/copiar/cancelar e recebimento de pedido validados.
- `Financeiro`: `OK`
  Fluxo de caixa, adicao, edicao, geracao de lancamento e faturamento de pedidos validados.
- `Estoque`: `OK`
  Consulta, adicao de movimentos, detalhes com `pk` e edicao de local validados.
- `Fiscal`: `PARCIAL`
  Adicao, edicao, geracao de NF por pedido e configuracao validadas; emissao/consulta real SEFAZ depende de certificado, empresa e ambiente externo.

## Correcoes feitas neste ciclo

- Prioridade do `.env` sobre variaveis globais do Windows para evitar `DEBUG=False` indevido.
- Servico de estaticos restaurado no ambiente local.
- Tags antigas de template (`ifequal`) migradas para sintaxe suportada.
- Compatibilidade `Python 3.12` adicionada para `locale.format` e `collections.Callable`.
- Compatibilidade de PDFs com `Geraldo` restabelecida.
- Permissoes customizadas de `financeiro` e `fiscal` adicionadas via migracoes.
- Dependencias opcionais de PDF/NF-e instaladas e registradas.
- Suite operacional nova criada em `djangosige/tests/validation/test_flow_validation.py`.

## Pendencias reais

- Validar fluxos SEFAZ ponta a ponta apenas com certificado, empresa configurada e ambiente externo.
- Cobrir em automacao as telas fiscais externas (`emitir`, `cancelar`, `consultar`, `baixar`, `manifestacao`) com mocks ou homologacao.
- Validar fluxos SEFAZ apenas com certificado e ambiente de homologacao.

## Observacao sobre os 11 testes restantes

Os `11` testes que ainda falham continuam concentrados em asserts antigos de formulario (`assertFormError`) escritos para uma API de teste anterior do Django. O padrao da falha indica incompatibilidade da suite legada com Django 4, nao erro novo de runtime na aplicacao.
