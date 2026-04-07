# Checklist de Modernizacao

Atualizado em `2026-04-01 21:40`.

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
- validacao operacional atual: `15/15` passando em `djangosige.tests.validation`

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

- [x] adicionar `HTMX` como camada de interacao progressiva
- [x] adicionar `Alpine.js` apenas para estados pequenos de interface
- [x] substituir AJAX simples em jQuery por `HTMX` onde fizer sentido
- [x] substituir toggles e comportamentos pequenos por `Alpine.js`
- [x] manter renderizacao principal no servidor
- [x] preservar URLs, permissoes e respostas do Django

Artefatos da fase:

- [PHASE5_HTMX_ALPINE.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE5_HTMX_ALPINE.md)
- [validate_phase5_progressive.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase5_progressive.py)
- [test_progressive_validation.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/tests/validation/test_progressive_validation.py)
- [progressive-enhancement.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/progressive-enhancement.js)

Prioridades para migracao:

- [x] modais simples
- [x] consultas AJAX de cliente, fornecedor, emitente, destinatario e transportadora
- [x] telas com submit parcial de formulario quando fizer sentido
- [ ] consultas AJAX de produto com impacto em formset e calculo fiscal
- [ ] partes de filtros e acoes de lista

Decisao de escopo da fase:

- `produto/formset` ficou fora desta fase por depender de logica tributaria e de itens mais acoplados
- filtros e acoes mais densas de lista ficam para a Fase 6 e Fase 7

Testes da fase:

- [x] endpoints AJAX atuais continuam respondendo
- [x] comportamentos de modal e carregamento parcial funcionando
- [x] sem erros JS no console
- [x] sem regressao nas permissoes e CSRF

Critério de aceite:

- menos jQuery no projeto e interacoes mais simples de manter

## Fase 6 - Reducao Gradual de jQuery

Objetivo: tirar jQuery do caminho critico e deixar apenas onde ainda for inevitavel.

- [x] mapear uso de jQuery por arquivo
- [x] separar uso estrutural de uso incidental
- [x] trocar eventos simples por JS nativo ou Alpine.js
- [x] trocar requests simples por HTMX
- [x] remover do caminho critico o shell principal que ainda dependia de jQuery
- [x] manter jQuery apenas nos pontos ainda nao migrados
- [x] definir criterio para remocao final

Artefatos da fase:

- [PHASE6_JQUERY_REDUCTION.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE6_JQUERY_REDUCTION.md)
- [validate_phase6_jquery_reduction.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase6_jquery_reduction.py)
- [app-core.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/app-core.js)
- [admin.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/admin.js)
- [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)

Escopo concluido da fase:

- shell principal migrado para JS nativo com `AppCore`
- modal global de mensagens desacoplado de chamadas diretas em `jQuery`
- destaque de menu ativo e navegacao lateral sem init estrutural legado
- exemplo real de evento inline simples migrado para JS nativo

Pontos que permanecem deliberadamente fora desta fase:

- `DataTables`, mascaras, datepickers e formsets ainda dependentes de plugins legados
- listas e componentes mais densos ficam concentrados na Fase 7
- remocao final de `jQuery` fica condicionada ao fechamento dos plugins restantes

Testes da fase:

- [x] `python manage.py check`
- [x] `python manage.py test djangosige.tests.validation`
- [x] `python manage.py collectstatic --noinput`
- [x] `python contrib/validate_smoke.py`
- [x] `python contrib/validate_phase6_jquery_reduction.py`
- [x] menus laterais
- [x] modais
- [x] destaque de menu ativo
- [x] fluxo inline simples migrado

Critério de aceite:

- jQuery deixa de ser dependencia central do frontend

## Fase 7 - Tabelas, Formularios e Componentes Pesados

Objetivo: atacar os pontos mais usados e com maior custo de manutencao.

### Tabelas

- [x] revisar uso de DataTables
- [x] definir permanencia com modernizacao incremental da camada visual
- [x] padronizar cabecalho, filtros, paginacao e selecao em massa
- [x] melhorar densidade visual para ERP

### Formularios

- [x] padronizar layout horizontal e vertical
- [x] padronizar mensagens de erro
- [x] padronizar mascaras e datepickers
- [x] melhorar consistencia entre create/edit/detail

### Modais

- [x] padronizar estrutura visual
- [x] revisar acessibilidade basica
- [x] revisar foco e fechamento

Artefatos da fase:

- [PHASE7_TABLES_FORMS_MODALS.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE7_TABLES_FORMS_MODALS.md)
- [validate_phase7_components.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase7_components.py)
- [search.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/search.html)
- [modal.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/modal.html)
- [formset_table.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/formset/formset_table.html)
- [theme-overrides.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/theme-overrides.css)
- [app-core.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/app-core.js)
- [progressive-enhancement.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/progressive-enhancement.js)

Escopo concluido da fase:

- busca padrao das listas modernizada e acessivel
- DataTables reorganizado com rodape consistente, pagina de 25 itens e estado inicial de remocao desabilitado
- acoes inline de campo padronizadas com `aria-label`
- placeholders e atributos consistentes para `datepicker` e `datetimepicker`
- formsets de venda e compra encapsulados em shell visual previsivel
- modal global e modal financeiro revisados para estrutura e foco mais consistentes

Testes da fase:

- [x] `python manage.py check`
- [x] `python manage.py test djangosige.tests.validation`
- [x] `python manage.py collectstatic --noinput`
- [x] `python contrib/validate_smoke.py`
- [x] `python contrib/validate_phase7_components.py`
- [x] listas de cadastro
- [x] listas de vendas
- [x] listas de compras
- [x] telas de financeiro
- [x] telas de fiscal

Critério de aceite:

- componentes mais usados com visual e comportamento consistentes

## Fase 8 - Performance Front e Entrega

Objetivo: melhorar carregamento sem trocar o modelo de renderizacao.

- [x] minificar e revisar assets que ainda nao estao otimizados
- [x] remover CSS morto quando possivel
- [x] remover JS morto quando possivel
- [x] revisar ordem de carregamento de scripts
- [x] usar `defer` quando seguro
- [x] revisar imagens e icones
- [x] medir novamente o tamanho dos assets finais
- [x] medir novamente tempo de carregamento das telas principais

Artefatos da fase:

- [PHASE8_FRONT_PERFORMANCE.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE8_FRONT_PERFORMANCE.md)
- [validate_phase8_performance.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase8_performance.py)
- [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)
- [admin.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/admin.js)
- [404.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/404.html)
- [500.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/500.html)

Testes da fase:

- [x] `python manage.py check`
- [x] `python manage.py test djangosige.tests.validation`
- [x] `python manage.py collectstatic --noinput`
- [x] `python contrib/validate_smoke.py`
- [x] comparativo antes/depois do peso dos estaticos
- [x] comparativo antes/depois do tempo de carregamento
- [x] validacao manual em rede local mais lenta

Critério de aceite:

- frontend mais leve que o baseline ou no minimo sem regressao perceptivel

## Fase 9 - Qualidade, Testes e Observabilidade

Objetivo: deixar a modernizacao sustentavel.

- [x] expandir `djangosige.tests.validation` para cobrir mais fluxos visuais/JS
- [x] criar smoke manual guiado por telas principais
- [x] revisar erros no console do navegador
- [x] documentar dependencias front oficiais do projeto
- [x] documentar padrao de componentes e classes reutilizaveis
- [x] documentar convencoes para novos templates

Artefatos da fase:

- [PHASE9_QUALITY.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/PHASE9_QUALITY.md)
- [validate_phase9_quality.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/contrib/validate_phase9_quality.py)
- [test_frontend_contracts_validation.py](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/tests/validation/test_frontend_contracts_validation.py)
- [FRONTEND_DEPENDENCIES.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/FRONTEND_DEPENDENCIES.md)
- [FRONTEND_COMPONENTS.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/FRONTEND_COMPONENTS.md)
- [TEMPLATE_CONVENTIONS.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/TEMPLATE_CONVENTIONS.md)
- [MANUAL_SMOKE_GUIDE.md](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/MANUAL_SMOKE_GUIDE.md)

Testes fixos por entrega:

- [x] `python manage.py check`
- [x] `python manage.py collectstatic --noinput`
- [x] `python manage.py test djangosige.tests.validation`
- [x] `python contrib/validate_smoke.py`
- [x] validacao manual das telas alteradas

Critério de aceite:

- qualquer nova alteracao visual ou de stack pode ser validada rapidamente

## Ordem Recomendada de Execucao

- [x] Fase 0
- [x] Fase 1
- [x] Fase 2
- [x] Fase 3
- [x] Fase 4
- [x] Fase 5
- [x] Fase 6
- [x] Fase 7
- [x] Fase 8
- [x] Fase 9

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
- [x] iniciar Fase 5

## Escopo da Terceira Onda

Reducao do legado e consolidacao:

- [x] concluir Fase 5
- [x] concluir Fase 6
- [x] concluir Fase 7
- [x] concluir Fase 8
- [x] concluir Fase 9

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
