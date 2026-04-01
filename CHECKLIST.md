# Checklist de Modernizacao

Atualizado em `2026-04-01`.

## Objetivo

Modernizar a stack e o visual do sistema sem alterar a estrutura funcional do projeto, preservando:

- Django server-rendered com templates
- rotas atuais
- fluxo de negocio atual
- performance local e de producao
- compatibilidade incremental durante a migracao

## Principios

- nao reescrever o sistema inteiro
- evitar mudancas de arquitetura de alto risco
- migrar por camadas
- manter cada fase validavel de forma independente
- sempre ter rollback claro por arquivo ou modulo

## Estado Atual

- backend: `Django 4.2`
- frontend base: `HTML + Django templates`
- css/js legado: `Bootstrap 3`, `jQuery`, `Materialize`, plugins antigos
- estaticos: `WhiteNoise` e `collectstatic` ja preparados
- validacao operacional atual: `8/8` passando em `djangosige.tests.validation`

## Fase 0 - Baseline e Protecao

Objetivo: congelar o estado atual e garantir que qualquer melhoria futura tenha comparacao objetiva.

- [x] registrar baseline visual das telas principais
- [x] registrar baseline tecnico das dependencias front atuais
- [x] mapear todos os plugins JS em uso real
- [x] mapear quais telas usam DataTables, jQuery UI, mask, datetimepicker e multi-select
- [x] mapear quais componentes dependem de Materialize
- [x] registrar tempo de carregamento aproximado das telas principais
- [x] registrar tamanho atual dos assets estaticos

Artefatos da fase:

- [PHASE0_BASELINE.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE0_BASELINE.md)
- [PHASE0_VISUAL_VALIDATION.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE0_VISUAL_VALIDATION.md)
- [collect_phase0_baseline.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/collect_phase0_baseline.py)
- [validate_phase0_visual.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase0_visual.py)

Testes da fase:

- [x] `python manage.py check`
- [x] `python manage.py test djangosige.tests.validation`
- [x] `python contrib/validate_smoke.py`
- [x] validacao manual de `login`, `dashboard`, listas, formularios e modais

Critério de aceite:

- baseline documentado e comparavel antes da migracao

## Fase 1 - Higiene da Stack Front

Objetivo: limpar o terreno sem mudar HTML estrutural nem fluxo.

- [x] inventariar imports de CSS e JS em [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)
- [x] remover duplicidades e dependencias nao usadas
- [x] padronizar ordem de carregamento de assets
- [x] revisar assets vendorizados antigos e substituir por versoes estaveis da mesma linha quando necessario
- [x] isolar CSS proprio do projeto do CSS de bibliotecas
- [x] separar overrides visuais do legado em uma camada previsivel
- [x] revisar se ha plugins front obsoletos que podem sair sem impacto

Artefatos da fase:

- [PHASE1_STACK_HYGIENE.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE1_STACK_HYGIENE.md)
- [validate_phase1_hygiene.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase1_hygiene.py)
- [theme-overrides.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/theme-overrides.css)
- [load_jquery_mask.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/load_jquery_mask.html)
- [load_datetimepicker.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/load_datetimepicker.html)

Testes da fase:

- [x] smoke das paginas com e sem DataTables
- [x] validacao manual dos menus laterais e dropdowns
- [x] validacao manual de modais e mascaras
- [x] comparar console do navegador antes/depois para erros JS

Critério de aceite:

- mesma funcionalidade, menos acoplamento entre bibliotecas

## Fase 2 - Design System Leve

Objetivo: criar uma base visual moderna por cima do HTML atual.

- [x] definir tokens de design em CSS: cores, tipografia, espacamento, radius, sombras
- [x] consolidar variaveis visuais em um bloco central
- [x] padronizar topbar, sidebar, cards, tabelas, inputs, botoes e alertas
- [x] padronizar estilos de estados: hover, foco, erro, sucesso, desabilitado
- [x] melhorar legibilidade de tabelas densas
- [x] revisar responsividade real em mobile e notebook
- [x] padronizar tipografia para todo o sistema
- [x] revisar contraste e acessibilidade basica

Artefatos da fase:

- [PHASE2_DESIGN_SYSTEM.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE2_DESIGN_SYSTEM.md)
- [validate_phase2_design.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase2_design.py)
- [theme-overrides.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/theme-overrides.css)
- [404.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/404.html)
- [500.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/500.html)

Testes da fase:

- [x] revisao visual em `login`
- [x] revisao visual em `dashboard`
- [x] revisao visual em telas de lista
- [x] revisao visual em telas de formulario
- [x] revisao visual em modais
- [x] revisao visual em paginas de erro `404` e `500`

Critério de aceite:

- interface mais atual, consistente e legivel sem reestruturar templates

## Fase 3 - Remocao Gradual de Materialize

Objetivo: eliminar uma fonte de peso e conflito visual.

- [x] identificar componentes realmente dependentes de `materialize.css`
- [x] substituir estilos herdados de Materialize por CSS proprio ou Bootstrap moderno
- [x] remover classes que existem apenas por causa do Materialize
- [x] validar checkboxes, radios, inputs e efeitos de foco apos a retirada
- [x] remover import de Materialize quando a cobertura estiver completa

Artefatos da fase:

- [PHASE3_MATERIALIZE_REMOVAL.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE3_MATERIALIZE_REMOVAL.md)
- [validate_phase3_materialize.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase3_materialize.py)
- [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)
- [login.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/login/login.html)
- [admin.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/admin.js)
- [theme-overrides.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/theme-overrides.css)

Testes da fase:

- [x] formularios com checkbox e radio
- [x] formularios com validacao visual
- [x] modais e dropdowns
- [x] tela de login

Critério de aceite:

- sistema visualmente estavel sem depender de Materialize

## Fase 4 - Migracao Bootstrap 3 para Bootstrap 5.3

Objetivo: atualizar a base visual para uma stack atual sem trocar a arquitetura do app.

- [x] mapear classes Bootstrap 3 usadas no projeto
- [x] migrar grid legado (`col-xs-*`, etc.) para grid atual
- [x] migrar componentes de navbar, dropdown, modal e tabs
- [x] revisar utilitarios removidos ou renomeados
- [x] revisar dependencias de JS especificas do Bootstrap 3
- [x] remover necessidade de `jQuery` nas partes que dependiam apenas do Bootstrap
- [x] validar compatibilidade de DataTables com a nova camada visual

Artefatos da fase:

- [PHASE4_BOOTSTRAP5_MIGRATION.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE4_BOOTSTRAP5_MIGRATION.md)
- [validate_phase4_bootstrap.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase4_bootstrap.py)
- [bootstrap-compat.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/bootstrap-compat.css)
- [bootstrap-compat.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/bootstrap/bootstrap-compat.js)
- [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)

Testes da fase:

- [x] menus e dropdowns
- [x] tabs
- [x] modais
- [x] formularios e grids
- [x] telas de lista e dashboard

Critério de aceite:

- Bootstrap 5 funcionando sem regressao visual relevante

## Fase 5 - Interacoes Modernas com HTMX e Alpine.js

Objetivo: modernizar interacoes sem SPA e sem reescrever o backend.

- [ ] adicionar `HTMX` como camada de interacao progressiva
- [ ] adicionar `Alpine.js` apenas para estados pequenos de interface
- [ ] substituir AJAX simples em jQuery por `HTMX` onde fizer sentido
- [ ] substituir toggles e comportamentos pequenos por `Alpine.js`
- [ ] manter renderizacao principal no servidor
- [ ] preservar URLs, permissoes e respostas do Django

Prioridades para migracao:

- [ ] modais simples
- [ ] consultas AJAX de cliente/fornecedor/produto
- [ ] partes de filtros e acoes de lista
- [ ] telas com submit parcial de formulario quando fizer sentido

Testes da fase:

- [ ] endpoints AJAX atuais continuam respondendo
- [ ] comportamentos de modal e carregamento parcial funcionando
- [ ] sem erros JS no console
- [ ] sem regressao nas permissoes e CSRF

Critério de aceite:

- menos jQuery no projeto e interacoes mais simples de manter

## Fase 6 - Reducao Gradual de jQuery

Objetivo: tirar jQuery do caminho critico e deixar apenas onde ainda for inevitavel.

- [ ] mapear uso de jQuery por arquivo
- [ ] separar uso estrutural de uso incidental
- [ ] trocar eventos simples por JS nativo ou Alpine.js
- [ ] trocar requests simples por HTMX
- [ ] remover plugins que prendem o projeto em jQuery sem necessidade
- [ ] manter jQuery apenas nos pontos ainda nao migrados
- [ ] definir criterio para remocao final

Testes da fase:

- [ ] formularios com mascara
- [ ] tabelas com comportamento dinamico
- [ ] menus laterais
- [ ] modais

Critério de aceite:

- jQuery deixa de ser dependencia central do frontend

## Fase 7 - Tabelas, Formularios e Componentes Pesados

Objetivo: atacar os pontos mais usados e com maior custo de manutencao.

### Tabelas

- [ ] revisar uso de DataTables
- [ ] definir se permanece, moderniza ou reduz escopo
- [ ] padronizar cabecalho, filtros, paginacao e selecao em massa
- [ ] melhorar densidade visual para ERP

### Formularios

- [ ] padronizar layout horizontal e vertical
- [ ] padronizar mensagens de erro
- [ ] padronizar mascaras e datepickers
- [ ] melhorar consistencia entre create/edit/detail

### Modais

- [ ] padronizar estrutura visual
- [ ] revisar acessibilidade basica
- [ ] revisar foco e fechamento

Testes da fase:

- [ ] listas de cadastro
- [ ] listas de vendas
- [ ] listas de compras
- [ ] telas de financeiro
- [ ] telas de fiscal

Critério de aceite:

- componentes mais usados com visual e comportamento consistentes

## Fase 8 - Performance Front e Entrega

Objetivo: melhorar carregamento sem trocar o modelo de renderizacao.

- [ ] minificar e revisar assets que ainda nao estao otimizados
- [ ] remover CSS morto quando possivel
- [ ] remover JS morto quando possivel
- [ ] revisar ordem de carregamento de scripts
- [ ] usar `defer` quando seguro
- [ ] revisar imagens e icones
- [ ] medir novamente o tamanho dos assets finais
- [ ] medir novamente tempo de carregamento das telas principais

Testes da fase:

- [ ] comparativo antes/depois do peso dos estaticos
- [ ] comparativo antes/depois do tempo de carregamento
- [ ] validacao manual em rede local mais lenta

Critério de aceite:

- frontend mais leve que o baseline ou no minimo sem regressao perceptivel

## Fase 9 - Qualidade, Testes e Observabilidade

Objetivo: deixar a modernizacao sustentavel.

- [ ] expandir `djangosige.tests.validation` para cobrir mais fluxos visuais/JS
- [ ] criar smoke manual guiado por telas principais
- [ ] revisar erros no console do navegador
- [ ] documentar dependencias front oficiais do projeto
- [ ] documentar padrao de componentes e classes reutilizaveis
- [ ] documentar convencoes para novos templates

Testes fixos por entrega:

- [ ] `python manage.py check`
- [ ] `python manage.py collectstatic --noinput`
- [ ] `python manage.py test djangosige.tests.validation`
- [ ] `python contrib/validate_smoke.py`
- [ ] validacao manual das telas alteradas

Critério de aceite:

- qualquer nova alteracao visual ou de stack pode ser validada rapidamente

## Ordem Recomendada de Execucao

- [x] Fase 0
- [x] Fase 1
- [x] Fase 2
- [x] Fase 3
- [x] Fase 4
- [ ] Fase 5
- [ ] Fase 6
- [ ] Fase 7
- [ ] Fase 8
- [ ] Fase 9

## Escopo da Primeira Onda

Melhor relacao risco/retorno:

- [x] concluir Fase 0
- [x] concluir Fase 1
- [x] concluir Fase 2
- [x] iniciar Fase 3

## Escopo da Segunda Onda

Modernizacao estrutural do frontend sem mudar arquitetura backend:

- [x] concluir Fase 3
- [x] concluir Fase 4
- [ ] iniciar Fase 5

## Escopo da Terceira Onda

Reducao do legado e consolidacao:

- [ ] concluir Fase 5
- [ ] concluir Fase 6
- [ ] concluir Fase 7
- [ ] concluir Fase 8
- [ ] concluir Fase 9

## Riscos Conhecidos

- Bootstrap 5 pode quebrar markup legado se a migracao for ampla demais de uma vez
- DataTables e plugins antigos podem depender de jQuery de forma forte
- formularios com mascaras e datepickers exigem migracao cuidadosa
- fiscal e telas com fluxo complexo devem ser migradas por modulo, nao em lote

## Decisao Tecnica Recomendada

Stack-alvo recomendada:

- backend: `Django templates`
- interacao: `HTMX`
- microcomportamentos: `Alpine.js`
- base visual: `Bootstrap 5.3` ou CSS proprio leve
- entrega de estaticos: `WhiteNoise`

Nao recomendado para este projeto neste momento:

- reescrever em `React`, `Next.js`, `Vue` ou SPA completa
- alterar a estrutura de rotas e views do Django sem necessidade
