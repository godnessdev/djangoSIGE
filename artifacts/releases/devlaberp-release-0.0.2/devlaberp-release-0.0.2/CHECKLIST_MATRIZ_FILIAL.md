# Checklist de Matriz e Filial

Atualizado em `2026-04-02`.

## Objetivo

Transformar o sistema atual, que hoje trata empresas como independentes, em uma estrutura real de:

- `matriz`
- `filial`
- operacao por unidade
- consolidacao gerencial
- controle fiscal e financeiro por empresa

sem perder a capacidade atual de trabalhar com uma unica empresa.

## Estado Atual

Hoje o sistema possui:

- cadastro de empresas
- selecao de empresa ativa por usuario
- operacao dentro de uma empresa por vez

Hoje o sistema **nao possui**:

- hierarquia formal de matriz e filial
- empresa pai
- tipo de empresa na estrutura
- consolidacao entre unidades
- compartilhamento controlado entre unidades

## Principio de Arquitetura

Antes de implementar, a regra central precisa ser esta:

- `empresa juridica` continua sendo a unidade principal de operacao
- `matriz/filial` vira uma relacao hierarquica entre empresas
- cada empresa continua tendo identidade fiscal propria
- consolidacao e compartilhamento devem ser configuraveis

## Decisoes Obrigatorias Antes de Codar

- [ ] decidir se `matriz` tambem pode operar normalmente como unidade de venda/estoque/financeiro
- [ ] decidir se cada `filial` tera estoque proprio
- [ ] decidir se cada `filial` tera caixa proprio
- [ ] decidir se cada `filial` tera numeracao fiscal propria
- [ ] decidir se clientes e produtos serao:
- [ ] `globais do grupo`
- [ ] `por empresa`
- [ ] `mistos`
- [ ] decidir se usuarios podem operar em varias filiais
- [ ] decidir se gestor da matriz pode ver tudo
- [ ] decidir se a filial pode ver apenas os proprios dados

Critério de aceite:

- [ ] regras de negocio da estrutura matriz/filial estao fechadas

## Fase 1 - Modelo de Dados

Objetivo: criar a base estrutural sem quebrar o cadastro atual.

### Campos e relacoes

- [x] adicionar campo `tipo_empresa`
- [ ] tipos:
- [x] `matriz`
- [x] `filial`
- [x] opcional: `independente`
- [x] adicionar relacao `empresa_pai`
- [x] impedir que matriz aponte para outra empresa como pai
- [x] obrigar filial a apontar para uma matriz
- [x] impedir ciclos na hierarquia
- [x] impedir filial apontando para si mesma
- [ ] validar profundidade da estrutura, se necessario

### Regras de integridade

- [x] uma filial nao pode ter outra filial como pai, se essa for a regra adotada
- [x] uma matriz pode ter varias filiais
- [x] empresa independente pode existir sem pai, se permitido
- [x] exclusao de matriz com filiais deve ser bloqueada ou tratada explicitamente

Critério de aceite:

- [x] hierarquia empresarial existe no banco com validacao consistente

## Fase 2 - Cadastro de Empresa

Objetivo: adaptar o cadastro de empresa para suportar a hierarquia.

- [x] incluir campo `tipo_empresa` no formulario
- [x] incluir campo `empresa_pai` quando `tipo_empresa = filial`
- [x] esconder `empresa_pai` quando `tipo_empresa = matriz`
- [x] validar regras no backend, nao so no frontend
- [x] destacar visualmente se a empresa e matriz ou filial
- [x] mostrar nome da matriz na tela de edicao da filial
- [x] listar filiais da matriz na tela da matriz

### Lista de empresas

- [x] exibir coluna `tipo`
- [x] exibir coluna `matriz vinculada`
- [x] permitir filtro por `matriz`, `filial`, `independente`
- [x] permitir filtro por grupo empresarial

Critério de aceite:

- [x] usuario consegue cadastrar e entender a estrutura sem ambiguidade

## Fase 3 - Empresa Ativa e Contexto do Usuario

Objetivo: garantir que o usuario opere na empresa correta.

- [x] adaptar `MinhaEmpresa` para operar bem no modelo matriz/filial
- [x] permitir vinculo do usuario a uma ou mais empresas
- [x] decidir se o usuario tera empresa padrao
- [x] permitir troca de empresa ativa
- [x] mostrar claramente no header qual unidade esta ativa
- [x] impedir vazamento de dados entre empresas

### Perfis

- [x] perfil `gestor da matriz`
- [x] perfil `gestor da filial`
- [x] perfil `operador da filial`
- [x] perfil `auditoria/retaguarda`

Critério de aceite:

- [x] usuario visualiza e opera apenas nas empresas permitidas

## Fase 4 - Clientes, Fornecedores e Transportadoras

Objetivo: definir escopo dos cadastros relacionais.

### Decisao estrutural

- [x] definir se `clientes` sao compartilhados entre matriz e filiais
- [x] definir se `fornecedores` sao compartilhados entre matriz e filiais
- [x] definir se `transportadoras` sao compartilhadas entre matriz e filiais

### Se compartilhado

- [ ] criar visao unica por grupo empresarial
- [ ] impedir duplicidade desnecessaria
- [ ] controlar permissao de alteracao centralizada

### Se separado por empresa

- [x] vincular cadastro a empresa
- [x] filtrar listas pela empresa ativa
- [x] bloquear visualizacao cruzada

### Se misto

- [ ] criar flag `global_do_grupo`
- [ ] definir quem pode criar/editar cadastro global

Critério de aceite:

- [x] regra de escopo dos cadastros esta clara e aplicada no sistema

## Fase 5 - Produtos e Catalogo

Objetivo: definir como o produto funciona entre unidades.

### Decisao estrutural

- [x] definir se produto e global do grupo
- [x] definir se preco e por empresa
- [x] definir se estoque e por local/filial
- [x] definir se regra fiscal do produto muda por empresa

### Possivel modelo recomendado

- [x] produto base global
- [x] estoque por empresa/local
- [x] preco por empresa
- [x] configuracao fiscal por empresa quando necessario

Critério de aceite:

- [x] produto atende varias filiais sem duplicacao caotica

## Fase 6 - Estoque por Filial

Objetivo: garantir operacao fisica coerente entre unidades.

- [x] vincular locais de estoque a empresa
- [x] filtrar consulta de estoque pela empresa ativa
- [x] impedir movimento de estoque entre empresas erradas
- [x] criar transferencia entre filiais, se isso fizer parte do projeto
- [x] definir impacto da transferencia no custo
- [x] registrar origem e destino por empresa

### Consultas

- [x] saldo por filial
- [x] saldo consolidado do grupo
- [x] produtos em falta por filial
- [x] comparativo entre unidades

Critério de aceite:

- [x] estoque de cada filial e isolado e auditavel

## Fase 7 - Compras

Objetivo: controlar compras por unidade.

- [x] vincular pedido de compra a empresa
- [x] vincular entrada de estoque a empresa/local
- [x] filtrar listas pela empresa ativa
  - [x] permitir visualizacao consolidada para matriz, se autorizado
  - [x] definir se compra centralizada pela matriz abastece filiais

Critério de aceite:

- [x] compras respeitam a unidade operadora e a consolidacao gerencial

## Fase 8 - Vendas

Objetivo: operar venda por unidade.

- [x] vincular pedido/orcamento/venda a empresa
- [x] usar local de estoque da empresa ativa
- [x] usar configuracao comercial da empresa ativa
- [x] filtrar listas pela empresa ativa
- [x] permitir relatorio consolidado na matriz

Critério de aceite:

- [x] venda nao mistura estoque, cliente e operacao entre filiais sem regra clara

## Fase 9 - Financeiro

Objetivo: separar caixa e contas por empresa.

- [x] vincular contas a pagar a empresa
- [x] vincular contas a receber a empresa
- [x] vincular fluxo de caixa a empresa
- [x] vincular contas e grupos financeiros a empresa ou ao grupo, conforme regra
- [x] filtrar listas pela empresa ativa
- [x] permitir consolidacao por matriz

### Relatorios

- [x] fluxo por filial
- [x] contas por filial
- [x] consolidado do grupo
- [x] comparativo entre unidades

Critério de aceite:

- [x] financeiro da filial nao contamina outra unidade

## Fase 10 - Fiscal

Objetivo: respeitar a realidade juridica de cada empresa.

- [x] cada empresa com seu CNPJ, IE e configuracao fiscal
- [x] certificado por empresa
- [x] serie/numeracao por empresa
- [x] ambiente fiscal por empresa
- [x] natureza e grupo fiscal com escopo definido
- [x] emissao sempre pela empresa ativa correta

### Regras obrigatorias

- [x] nunca emitir nota da filial usando dados da matriz por engano
- [x] nunca misturar numeracao fiscal entre empresas
- [x] validar configuracao antes de emitir

Critério de aceite:

- [x] emissao fiscal por empresa esta segura

## Fase 11 - PDV por Filial

Objetivo: permitir frente de caixa em unidades distintas.

- [ ] vincular caixa do PDV a empresa/filial
- [ ] vincular operador a empresa permitida
- [ ] impedir abertura de caixa em empresa errada
- [ ] usar estoque e financeiro da filial ativa
- [ ] usar fiscal da filial ativa

Critério de aceite:

- [ ] PDV opera corretamente por filial

## Fase 12 - Relatorios e Consolidacao

Objetivo: entregar visao operacional e gerencial.

### Por filial

- [ ] vendas por filial
- [ ] compras por filial
- [ ] estoque por filial
- [ ] financeiro por filial
- [ ] fiscal por filial

### Consolidado

- [ ] vendas consolidadas da matriz
- [ ] financeiro consolidado
- [ ] estoque consolidado
- [ ] ranking entre filiais
- [ ] comparativo de desempenho

Critério de aceite:

- [ ] gestor da matriz consegue ver consolidado sem quebrar o isolamento operacional

## Fase 13 - Permissoes e Seguranca

Objetivo: impedir vazamento e operacao cruzada indevida.

- [x] usuario comum so ve empresas autorizadas
- [ ] matriz pode ter permissao ampliada
- [x] filial nao ve outra filial sem autorizacao
- [x] APIs e AJAX tambem respeitam empresa ativa
- [ ] relatorios, PDFs e exportacoes respeitam escopo de empresa

Critério de aceite:

- [ ] nao existe acesso cruzado indevido entre empresas

## Fase 14 - Onboarding Inicial

Objetivo: preparar o sistema desde a primeira instalacao.

- [ ] definir se o primeiro cadastro sera matriz
- [ ] permitir criar filiais depois
- [ ] incluir matriz/filial no checklist de primeira instalacao
- [ ] criar fluxo de onboarding de grupo empresarial, se necessario

Critério de aceite:

- [ ] novo cliente consegue começar com matriz unica e evoluir para filiais

## Fase 15 - Migracao do Banco Atual

Objetivo: transformar a base atual sem perder operacao.

- [x] criar migracao de schema para novos campos
- [x] definir valor padrao para empresas existentes
- [ ] marcar empresas atuais como `independente` ou `matriz`
- [ ] revisar dados existentes que precisam de saneamento
- [ ] testar migracao em copia real do banco

Critério de aceite:

- [ ] sistema atual migra sem perda de dados

## Fase 16 - UI e Navegacao

Objetivo: deixar claro em que unidade o usuario esta.

- [x] mostrar empresa ativa no topo
- [x] destacar se e matriz ou filial
- [x] permitir troca de empresa quando usuario tiver acesso a varias
- [ ] mostrar filtros de unidade em relatorios consolidados
- [x] mostrar vinculo matriz/filial no cadastro de empresa

Critério de aceite:

- [ ] usuario sempre sabe em qual empresa esta operando

## Fase 17 - Testes

Objetivo: nao implantar estrutura multiempresa sem cobertura real.

### Testes de modelo

- [x] criar matriz
- [x] criar filial
- [x] impedir ciclo
- [x] impedir pai invalido

### Testes de permissao

- [x] usuario da filial nao acessa outra filial
- [x] gestor da matriz acessa consolidado
- [ ] operador da filial so opera na propria unidade

### Testes funcionais

- [ ] venda na matriz
- [ ] venda na filial
- [ ] compra na filial
- [ ] estoque na filial
- [ ] financeiro na filial
- [ ] fiscal na filial

### Testes de relatorio

- [ ] relatorio por filial
- [ ] consolidado da matriz

Critério de aceite:

- [ ] estrutura matriz/filial esta coberta nos fluxos criticos

## Fase 18 - Implantacao por Cliente

Objetivo: transformar isso em recurso comercial utilizavel.

- [ ] permitir cliente com empresa unica
- [ ] permitir cliente com matriz e 1 filial
- [ ] permitir cliente com varias filiais
- [ ] documentar configuracao por cliente
- [ ] documentar limites do recurso na versao inicial

Critério de aceite:

- [ ] funcionalidade pode ser ativada por cliente sem fork do sistema

## MVP Recomendado de Matriz/Filial

Se for fazer o minimo bem feito primeiro:

- [x] hierarquia `matriz` / `filial`
- [x] empresa ativa por usuario
- [x] isolamento por empresa em vendas, compras, estoque, financeiro e fiscal
- [ ] relatorios por empresa
- [ ] consolidado simples para matriz
- [x] UI com empresa ativa clara

## Segunda Onda Recomendada

- [ ] cadastro global do grupo
- [ ] transferencia entre filiais
- [ ] precificacao por filial
- [ ] consolidacao avancada
- [ ] dashboard multicompanhia
- [ ] permissao avancada por grupo empresarial

## Ordem Recomendada de Execucao

1. `regras de negocio`
2. `modelo de dados`
3. `cadastro de empresa`
4. `empresa ativa e permissao`
5. `isolamento por modulo`
6. `relatorios e consolidacao`
7. `migracao de base atual`
8. `implantacao por cliente`

## Proximo Passo Pratico

Se quisermos começar certo, a ordem mais pragmatica e:

1. fechar a regra de `empresa_pai` + `tipo_empresa`
2. decidir escopo de `cadastros compartilhados ou nao`
3. aplicar `empresa ativa` em todos os modulos
4. fechar `relatorio consolidado da matriz`
