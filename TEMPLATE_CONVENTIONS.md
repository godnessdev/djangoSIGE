# Convencoes Para Novos Templates

Atualizado em `2026-04-01`.

## Base

- novos templates autenticados devem herdar de [base.html](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/templates/base/base.html)
- scripts especificos da tela devem ficar no bloco `{% block js %}`
- nao adicionar plugins pesados diretamente no shell global sem necessidade real

## Assets

- usar `{% load static %}` e `{% static %}` em vez de caminhos fixos
- manter versionamento de assets no shell quando houver alteracao crítica de cache
- se a dependencia for de uso localizado, carregar via include especifico da tela

## Interacao

- preferir `HTMX` para trocas parciais simples
- preferir `Alpine.js` para estado local pequeno
- só usar `jQuery` quando o plugin legado ainda exigir
- se um elemento já usa `data-progressive="htmx"`, nao duplicar bind em `admin.js`

## HTML

- manter ids e classes de contrato já usados pelos scripts
- tabs devem seguir `a[href="#pane_id"][data-toggle="tab"]` e `div.tab-pane#pane_id`
- listas administrativas devem manter `#lista-database`
- busca padrão deve manter `#search-bar`

## Acessibilidade minima

- toda ação inline deve ter `aria-label`
- modal deve ter `aria-labelledby` e `aria-describedby`
- inputs de data e hora devem manter placeholder e `autocomplete="off"`

## Estilo

- preferir classes existentes em `theme-overrides.css`
- evitar CSS inline novo quando a regra puder viver na camada de tema
- nao reintroduzir classes de `Materialize`

## Validacao obrigatoria

Depois de alterar templates front:

- `python manage.py check`
- `python manage.py test djangosige.tests.validation`
- `python contrib/validate_smoke.py`
- `python contrib/validate_phase9_quality.py`
