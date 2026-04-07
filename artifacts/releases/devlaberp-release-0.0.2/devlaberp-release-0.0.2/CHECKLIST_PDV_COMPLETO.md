# Checklist de PDV Completo

Atualizado em `2026-04-02`.

## Objetivo

Construir um `PDV / Frente de Caixa` completo, integrado ao ERP atual, com foco em:

- velocidade de operacao
- seguranca por perfil
- usabilidade para vendedor e caixa
- integracao com estoque, financeiro e fiscal
- operacao por cliente com implantacao padrao

## Visao do Produto

O PDV deve ser um modulo proprio, separado da retaguarda administrativa.

### Regra de produto

- `ERP`: cadastro, estoque, financeiro, fiscal, relatorios, configuracoes
- `PDV`: venda rapida, caixa, pagamento, impressao, consulta basica e operacao do atendente

### Regra de UX

O PDV nao deve parecer tela administrativa.

- [ ] layout full-screen
- [ ] foco em teclado e leitor de codigo de barras
- [ ] botoes grandes e claros
- [ ] fluxo com poucos cliques
- [ ] operacao rapida em toque e mouse

## Fase 0 - Escopo e Regras de Negocio

Objetivo: definir exatamente o que o PDV vai fazer.

- [ ] definir tipos de venda atendidos no PDV
- [ ] definir se o PDV vende com ou sem identificacao do cliente
- [ ] definir se havera venda como consumidor final padrao
- [ ] definir regras de desconto
- [ ] definir regras de cancelamento
- [ ] definir regras de sangria e suprimento
- [ ] definir limite de permissao por operador
- [ ] definir se emite `NFC-e`, `SAT`, `cupom nao fiscal` ou comprovante interno
- [ ] definir operacao online, offline ou hibrida

Critério de aceite:

- [ ] regras de negocio do PDV estao fechadas
- [ ] existe documento do que entra e do que nao entra no MVP

## Fase 1 - Estrutura do Modulo PDV

Objetivo: criar a base tecnica do modulo.

- [ ] criar app/rotas proprias do `pdv`
- [ ] separar templates do PDV dos templates administrativos
- [ ] criar layout proprio do PDV
- [ ] criar menu/entrada especifica para usuarios com permissao de caixa
- [ ] definir contexto de empresa, operador e caixa ativo

Critério de aceite:

- [ ] existe rota principal do PDV
- [ ] o PDV abre sem depender da navegacao do ERP administrativo

## Fase 2 - Acesso, Perfis e Permissoes

Objetivo: controlar quem pode fazer o que no caixa.

- [ ] criar perfis:
- [ ] `operador`
- [ ] `supervisor`
- [ ] `gerente`
- [ ] criar permissoes especificas do PDV
- [ ] limitar acesso do operador ao modulo PDV
- [ ] bloquear telas administrativas para operador simples
- [ ] exigir autorizacao superior para operacoes sensiveis

### Permissoes minimas

- [ ] abrir caixa
- [ ] fechar caixa
- [ ] vender no PDV
- [ ] aplicar desconto
- [ ] cancelar item
- [ ] cancelar venda
- [ ] reimprimir comprovante
- [ ] fazer sangria
- [ ] fazer suprimento
- [ ] visualizar movimento do caixa

Critério de aceite:

- [ ] cada perfil enxerga apenas o necessario

## Fase 3 - Abertura e Fechamento de Caixa

Objetivo: controlar o ciclo operacional do caixa.

- [ ] abrir caixa com operador, data/hora e valor inicial
- [ ] impedir venda sem caixa aberto
- [ ] registrar sangria
- [ ] registrar suprimento
- [ ] fechar caixa com resumo do turno
- [ ] registrar divergencia entre valor esperado e contado
- [ ] bloquear reabertura irregular do mesmo caixa

Critério de aceite:

- [ ] toda venda fica vinculada a um caixa aberto
- [ ] fechamento gera resumo auditavel

## Fase 4 - Tela Principal de Venda

Objetivo: criar a experiencia central do PDV.

- [ ] campo com foco automatico para codigo de barras
- [ ] busca rapida por nome, codigo e codigo de barras
- [ ] adicionar item por scanner
- [ ] adicionar item por busca manual
- [ ] alterar quantidade rapido
- [ ] remover item do carrinho
- [ ] mostrar subtotal, desconto, total e troco
- [ ] destacar produto adicionado mais recente
- [ ] atalho para limpar venda
- [ ] atalho para finalizar venda

Critério de aceite:

- [ ] operador consegue vender sem navegar por varias telas

## Fase 5 - Produtos e Regras Comerciais

Objetivo: fazer a venda refletir o cadastro real.

- [ ] usar preco de venda do produto
- [ ] validar estoque disponivel quando controlar estoque
- [ ] permitir venda de item sem estoque apenas se configurado
- [ ] tratar unidade, fracionado e quantidade decimal quando aplicavel
- [ ] permitir observacao por item ou venda
- [ ] permitir desconto por item
- [ ] permitir desconto no total
- [ ] registrar motivo do desconto quando necessario

Critério de aceite:

- [ ] precos e estoque respeitam as regras do ERP

## Fase 6 - Cliente e Identificacao da Venda

Objetivo: vincular cliente quando fizer sentido.

- [ ] venda sem cliente identificado
- [ ] venda com cliente selecionado
- [ ] busca rapida de cliente
- [ ] cadastro rapido de cliente no PDV ou atalho para cadastro
- [ ] CPF/CNPJ no fechamento quando exigido
- [ ] consumidor final padrao configuravel

Critério de aceite:

- [ ] o operador nao trava se o cliente nao quiser identificar

## Fase 7 - Pagamento

Objetivo: fechar a venda com flexibilidade real.

- [ ] pagamento em dinheiro
- [ ] pagamento em cartao
- [ ] pagamento em pix
- [ ] pagamento misto
- [ ] calculo de troco
- [ ] bloqueio de valor pago inferior ao total
- [ ] permitir parcelamento se fizer sentido para o negocio
- [ ] registrar bandeira/observacao quando necessario

Critério de aceite:

- [ ] fechamento suporta os meios de pagamento do cliente final

## Fase 8 - Integracao com Financeiro

Objetivo: transformar venda de PDV em movimento financeiro confiavel.

- [ ] gerar lancamento financeiro da venda
- [ ] separar por meio de pagamento
- [ ] vincular ao caixa aberto
- [ ] refletir em fluxo de caixa
- [ ] suportar cancelamento/estorno
- [ ] tratar vendas a prazo, se o PDV suportar

Critério de aceite:

- [ ] venda do PDV aparece corretamente no financeiro

## Fase 9 - Integracao com Estoque

Objetivo: baixar estoque com rastreabilidade.

- [ ] baixar estoque na confirmacao da venda
- [ ] reverter estoque em cancelamento
- [ ] respeitar local de estoque do caixa/loja
- [ ] impedir inconsistencia de saldo
- [ ] registrar movimentacao de estoque originada pelo PDV

Critério de aceite:

- [ ] estoque do PDV e estoque da retaguarda permanecem coerentes

## Fase 10 - Fiscal

Objetivo: preparar a emissao fiscal correta.

- [ ] definir modelo fiscal do PDV por cliente
- [ ] integrar com `NFC-e` quando aplicavel
- [ ] emitir comprovante simples quando o cliente nao usar fiscal eletronico
- [ ] registrar numero, serie e status da emissao
- [ ] tratar rejeicao fiscal sem perder a venda
- [ ] permitir reprocessamento quando necessario

Critério de aceite:

- [ ] o PDV fecha venda de forma compativel com a exigencia fiscal do cliente

## Fase 11 - Comprovante e Impressao

Objetivo: entregar saida pratica para o caixa.

- [ ] impressao de comprovante
- [ ] layout de cupom simples
- [ ] reimpressao de ultima venda
- [ ] reimpressao de venda do dia
- [ ] compatibilidade com impressora termica
- [ ] teste de impressao local

Critério de aceite:

- [ ] operador consegue imprimir sem sair do fluxo de caixa

## Fase 12 - Hardware e Perifericos

Objetivo: garantir operacao de frente de loja.

- [ ] leitor de codigo de barras
- [ ] impressora termica
- [ ] gaveta de dinheiro, se aplicavel
- [ ] balanca, se aplicavel
- [ ] segundo monitor, se aplicavel

Critério de aceite:

- [ ] perifericos criticos do cliente foram homologados

## Fase 13 - Atalhos e Produtividade

Objetivo: deixar o PDV realmente rapido.

- [ ] atalhos de teclado
- [ ] foco automatico no campo principal
- [ ] confirmacoes curtas e objetivas
- [ ] feedback claro ao adicionar item
- [ ] feedback sonoro opcional
- [ ] estados de erro sem travar o caixa

Critério de aceite:

- [ ] operador treinado consegue usar quase tudo sem mouse

## Fase 14 - Historico, Consulta e Auditoria

Objetivo: permitir rastreio e suporte.

- [ ] historico das vendas do dia
- [ ] consulta por numero, cliente ou horario
- [ ] detalhamento da venda
- [ ] log de cancelamento
- [ ] log de desconto
- [ ] log de abertura/fechamento de caixa
- [ ] log de sangria/suprimento

Critério de aceite:

- [ ] qualquer operacao sensivel fica rastreavel

## Fase 15 - Offline e Resiliencia

Objetivo: decidir como o PDV se comporta sem internet.

- [ ] definir se o PDV exige conexao constante
- [ ] se offline:
- [ ] fila local de vendas
- [ ] fila de emissao fiscal
- [ ] reconciliacao posterior
- [ ] tratamento de duplicidade

Critério de aceite:

- [ ] comportamento em queda de internet esta definido e testado

## Fase 16 - Testes do PDV

Objetivo: nao subir caixa sem confianca operacional.

### Testes funcionais

- [ ] abrir caixa
- [ ] vender 1 item
- [ ] vender varios itens
- [ ] desconto por item
- [ ] desconto total
- [ ] venda com cliente
- [ ] venda sem cliente
- [ ] dinheiro com troco
- [ ] cartao
- [ ] pix
- [ ] pagamento misto
- [ ] cancelamento de item
- [ ] cancelamento de venda
- [ ] reimpressao
- [ ] fechamento de caixa

### Testes de integracao

- [ ] baixa de estoque
- [ ] lancamento financeiro
- [ ] emissao fiscal
- [ ] restauracao de fluxo apos erro

### Testes de permissao

- [ ] operador sem permissao de desconto
- [ ] operador sem permissao de cancelamento
- [ ] autorizacao de supervisor

Critério de aceite:

- [ ] cenario de caixa real roda ponta a ponta sem quebra

## Fase 17 - Implantacao por Cliente

Objetivo: distribuir o PDV como produto instalavel.

- [ ] definir modo de instalacao por cliente
- [ ] configurar branding por cliente
- [ ] configurar impressora por cliente
- [ ] configurar fiscal por cliente
- [ ] configurar meios de pagamento por cliente
- [ ] gerar pacote de entrega
- [ ] manual de instalacao do PDV
- [ ] manual de operacao do caixa

Critério de aceite:

- [ ] novo cliente pode receber PDV sem customizacao manual extensa

## Fase 18 - MVP do PDV

Objetivo: definir o minimo necessario para vender.

### MVP recomendado

- [ ] login do operador
- [ ] abertura de caixa
- [ ] tela de venda rapida
- [ ] busca por produto/codigo de barras
- [ ] carrinho
- [ ] pagamento em dinheiro/cartao/pix
- [ ] troco
- [ ] baixa de estoque
- [ ] lancamento financeiro
- [ ] impressao simples
- [ ] fechamento de caixa
- [ ] historico do dia
- [ ] cancelamento com permissao

### Pode ficar para segunda fase

- [ ] offline
- [ ] balanca
- [ ] multi-caixa sofisticado
- [ ] promocao complexa
- [ ] fidelidade
- [ ] comissao
- [ ] segunda tela cliente
- [ ] integracao TEF avancada

## Ordem Recomendada

1. `escopo e regras`
2. `estrutura do modulo`
3. `permissoes`
4. `abertura/fechamento de caixa`
5. `tela principal de venda`
6. `pagamento`
7. `estoque`
8. `financeiro`
9. `impressao`
10. `fiscal`
11. `historico e auditoria`
12. `implantacao por cliente`

## Proximo Passo Pratico

Se for comecar agora, a ordem mais pragmatica e:

1. fechar o `MVP do PDV`
2. criar `rotas e layout proprio`
3. implementar `caixa + venda + pagamento`
4. integrar `estoque e financeiro`
5. homologar `impressao`
6. fechar `fiscal` por cliente
