# Phase 0 Baseline

Atualizado em `2026-04-01`.

## Resumo

- baseline tecnico consolidado antes da modernizacao estrutural do frontend
- foco em stack atual, plugins ativos, peso dos assets e tempos aproximados das telas principais
- baseline visual manual deve partir das telas-alvo listadas neste arquivo

## Stack Atual

- renderizacao: `Django templates`
- framework CSS principal: `Bootstrap 3.4.1`
- CSS legado adicional: `Materialize 0.97.7` importado por [style.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/style.css)
- JavaScript principal: `jQuery 3.7.1` e [admin.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/admin.js)
- estaticos: `WhiteNoise` + `collectstatic`

## Imports Base

- `favicon.ico`
- `css/bootstrap.min.css`
- `css/style.css`
- `js/jquery/jquery-3.0.0.min.js`
- `js/bootstrap/bootstrap.min.js`
- `js/jquery.dataTables.min.js`
- `js/admin.js`

## Assets Estaticos

- total de arquivos em `djangosige/static`: `71`
- tamanho total em `djangosige/static`: `2.7 MB`
- arquivos de runtime UI: `36`
- tamanho de runtime UI: `1.6 MB`
- arquivos de dados auxiliares (`csv`): `32`
- tamanho de dados auxiliares: `1.0 MB`

### Top 15 Assets de Runtime

- `djangosige/static/css/iconfont/MaterialIcons-Regular.svg`: `277.4 KB`
- `djangosige/static/js/admin.js`: `148.4 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.eot`: `139.9 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.ttf`: `125.2 KB`
- `djangosige/static/css/bootstrap.min.css`: `118.6 KB`
- `djangosige/static/fonts/glyphicons-halflings-regular.svg`: `106.5 KB`
- `djangosige/static/js/jquery/jquery-3.0.0.min.js`: `85.5 KB`
- `djangosige/static/js/jquery.dataTables.min.js`: `81.3 KB`
- `djangosige/static/js/jquery-ui.min.js`: `72.5 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.woff`: `56.3 KB`
- `djangosige/static/js/jquery.datetimepicker.full.min.js`: `55.2 KB`
- `djangosige/static/css/style.css`: `50.1 KB`
- `djangosige/static/fonts/glyphicons-halflings-regular.ttf`: `44.3 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.woff2`: `43.3 KB`
- `djangosige/static/js/bootstrap/bootstrap.min.js`: `38.8 KB`

### Top 15 Assets Gerais

- `djangosige/static/tabelas/ncm/ncm171a.csv`: `620.9 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.svg`: `277.4 KB`
- `djangosige/static/tabelas/municipios/codigos_municipios.csv`: `153.0 KB`
- `djangosige/static/js/admin.js`: `148.4 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.eot`: `139.9 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.ttf`: `125.2 KB`
- `djangosige/static/css/bootstrap.min.css`: `118.6 KB`
- `djangosige/static/fonts/glyphicons-halflings-regular.svg`: `106.5 KB`
- `djangosige/static/js/jquery/jquery-3.0.0.min.js`: `85.5 KB`
- `djangosige/static/tabelas/cest/cest.csv`: `81.8 KB`
- `djangosige/static/js/jquery.dataTables.min.js`: `81.3 KB`
- `djangosige/static/js/jquery-ui.min.js`: `72.5 KB`
- `djangosige/static/css/iconfont/MaterialIcons-Regular.woff`: `56.3 KB`
- `djangosige/static/js/jquery.datetimepicker.full.min.js`: `55.2 KB`
- `djangosige/static/css/style.css`: `50.1 KB`

## Plugins e Bibliotecas Encontradas

### Bootstrap 3

- `djangosige/templates/404.html:18`
  Trecho: `<link href="{% static 'css/bootstrap.min.css' %}" rel="stylesheet">`
- `djangosige/templates/500.html:18`
  Trecho: `<link href="{% static 'css/bootstrap.min.css' %}" rel="stylesheet">`
- `djangosige/templates/base/base.html:20`
  Trecho: `<link href="{% static 'css/bootstrap.min.css' %}" rel="stylesheet">`
- `djangosige/templates/cadastro/pessoa_tab_list.html:2`
  Trecho: `<li role="presentation" class="active"><a href="#tab_inf_gerais" data-toggle="tab">INFORMAÇÕES GERAIS</a></li>`
- `djangosige/templates/compras/compra_form.html:6`
  Trecho: `<li role="presentation" class="active"><a href="#tab_informacoes" data-toggle="tab">INFORMAÇÕES</a></li>`
- `djangosige/templates/vendas/venda_form.html:6`
  Trecho: `<li role="presentation" class="active"><a href="#tab_informacoes" data-toggle="tab">INFORMAÇÕES</a></li>`
- `djangosige/templates/cadastro/produto/produto_tab_list.html:2`
  Trecho: `<li role="presentation" class="active"><a href="#tab_dados_gerais" data-toggle="tab">DADOS GERAIS</a></li>`
- `djangosige/templates/estoque/consulta/consulta_estoque.html:83`
  Trecho: `<tr colspan="6" style="font-weight: bolder;background-color: #d2dee0;" class="prevent-click-row" data-toggle="collapse" data-target=".accord`
- `djangosige/templates/estoque/movimento/movimento_estoque_detail.html:31`
  Trecho: `<li role="presentation" class="active"><a href="#tab_dados_gerais" data-toggle="tab">DADOS GERAIS</a></li>`
- `djangosige/templates/estoque/movimento/movimento_estoque_form.html:5`
  Trecho: `<li role="presentation" class="active"><a href="#tab_dados_gerais" data-toggle="tab">DADOS GERAIS</a></li>`
- `djangosige/templates/estoque/movimento/movimento_estoque_list.html:25`
  Trecho: `<button class="btn btn-success dropdown-toggle" type="button" data-toggle="dropdown">Adicionar`
- `djangosige/templates/financeiro/lancamento/lancamento_list.html:25`
  Trecho: `<button class="btn btn-success dropdown-toggle" type="button" data-toggle="dropdown">Adicionar`

### jQuery

- `djangosige/templates/404.html:36`
  Trecho: `<script src="{% static 'js/jquery/jquery-3.0.0.min.js' %}"></script>`
- `djangosige/templates/500.html:36`
  Trecho: `<script src="{% static 'js/jquery/jquery-3.0.0.min.js' %}"></script>`
- `djangosige/templates/base/base.html:26`
  Trecho: `<script src="{% static 'js/jquery/jquery-3.0.0.min.js' %}"></script>`
- `djangosige/templates/base/datepicker_js.html:2`
  Trecho: `$.Admin.datepicker.init();`
- `djangosige/templates/base/datetimepicker_js.html:2`
  Trecho: `$.Admin.datetimepicker.init();`
- `djangosige/templates/base/popup_form.html:37`
  Trecho: `$.Admin.popupwindow.init();`
- `djangosige/templates/cadastro/pessoa_blockjs.html:12`
  Trecho: `$.Admin.pessoaForm.init(cmun_path, mun_inicial);`
- `djangosige/templates/compras/compra_jsblock.html:16`
  Trecho: `$.Admin.compraForm.init(req_urls);`
- `djangosige/templates/login/login.html:71`
  Trecho: `$.Admin.messages.msgSucesso("{{message}}");`
- `djangosige/templates/login/selecionar_minha_empresa.html:38`
  Trecho: `$.Admin.popupwindow.init();`
- `djangosige/templates/vendas/venda_jsblock.html:17`
  Trecho: `$.Admin.vendaForm.init(req_urls);`
- `djangosige/templates/cadastro/cliente/cliente_blockjs.html:14`
  Trecho: `$.Admin.maskInput.maskPessoa();`

### DataTables

- `djangosige/templates/base/base.html:456`
  Trecho: `<script src="{% static 'js/jquery.dataTables.min.js' %}"></script>`
- `djangosige/static/js/admin.js:193`
  Trecho: `dTable = $('#lista-database').DataTable({`
- `djangosige/static/js/jquery.dataTables.min.js:84`
  Trecho: `break}else{K(p,0,"Cannot reinitialise DataTable",3);return}}if(p.sTableId==this.id){r.splice(j,1);break}}if(null===e||""===e)this.id=e="Data`

### jQuery UI

- `djangosige/templates/base/load_jqueryui.html:3`
  Trecho: `<link href="{% static 'css/jquery-ui/jquery-ui.min.css' %}" rel="stylesheet">`
- `djangosige/templates/cadastro/produto/produto_jsblock.html:6`
  Trecho: `<link href="{% static 'css/jquery-ui/jquery-ui.min.css' %}" rel="stylesheet">`
- `djangosige/templates/estoque/local/local_add.html:64`
  Trecho: `<link href="{% static 'css/jquery-ui/jquery-ui.min.css' %}" rel="stylesheet">`
- `djangosige/templates/fiscal/natureza_operacao/natureza_operacao_add.html:64`
  Trecho: `<link href="{% static 'css/jquery-ui/jquery-ui.min.css' %}" rel="stylesheet">`
- `djangosige/templates/fiscal/natureza_operacao/natureza_operacao_edit.html:64`
  Trecho: `<link href="{% static 'css/jquery-ui/jquery-ui.min.css' %}" rel="stylesheet">`
- `djangosige/static/js/admin.js:426`
  Trecho: `$(this).datepicker('destroy').removeAttr('id').removeProp('id');`

### Datetimepicker

- `djangosige/templates/fiscal/nota_fiscal/nota_fiscal_jsblock.html:10`
  Trecho: `<link href="{% static 'css/jquery.datetimepicker.css' %}" rel="stylesheet">`
- `djangosige/static/js/admin.js:3183`
  Trecho: `$('.datetimepicker').datetimepicker({`

### jQuery Mask

- `djangosige/templates/compras/compra_jsblock.html:3`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/vendas/venda_jsblock.html:3`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/cadastro/cliente/cliente_blockjs.html:5`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/cadastro/empresa/empresa_blockjs.html:5`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/cadastro/fornecedor/fornecedor_blockjs.html:5`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/cadastro/produto/produto_jsblock.html:3`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/cadastro/transportadora/transportadora_blockjs.html:5`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/estoque/movimento/movimento_estoque_jsblock.html:3`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/estoque/movimento/movimento_estoque_list.html:72`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/financeiro/lancamento/lancamento_jsblock.html:3`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/financeiro/lancamento/lancamento_list.html:75`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`
- `djangosige/templates/fiscal/grupo_fiscal/grupo_fiscal_jsblock.html:3`
  Trecho: `<script src="{% static 'js/jquery.mask.js' %}"></script>`

### Multi Select

- `djangosige/templates/login/editar_permissoes_user.html:66`
  Trecho: `<script src="{% static 'js/jquery.multi-select.js' %}"></script>`
- `djangosige/static/js/jquery.multi-select.js:346`
  Trecho: `this.$element.multiSelect(this.options);`

### Materialize

- `djangosige/templates/login/login.html:38`
  Trecho: `<input type="checkbox" name="remember_me" id="remember_me" class="filled-in chk-col-light-blue">`
- `djangosige/static/css/materialize.css:159`
  Trecho: `[type="checkbox"]:not(.filled-in) + label:after {`
- `djangosige/static/css/style.css:1`
  Trecho: `@import url(materialize.css);`

### Material Icons

- `djangosige/templates/base/base.html:63`
  Trecho: `<span style="padding-left:25px;"><i class="material-icons">&#xE8DF;</i></span>`
- `djangosige/templates/base/index.html:15`
  Trecho: `<h2><i class="material-icons">&#xE85D;</i>CADASTRO</h2>`
- `djangosige/templates/base/modal.html:8`
  Trecho: `<i class="material-icons"></i>`
- `djangosige/templates/base/popup_form.html:27`
  Trecho: `<button class="btn btn-success foot-btn" type="submit"><i class="material-icons">&#xE148;</i><span> SALVAR</span></button>`
- `djangosige/templates/base/search.html:3`
  Trecho: `<i class="material-icons">&#xE8B6;</i>`
- `djangosige/templates/cadastro/pessoa_add.html:18`
  Trecho: `<a href="{{return_url}}"><i class="material-icons">&#xE5C4;</i></a>{{title_complete}}`
- `djangosige/templates/cadastro/pessoa_edit.html:19`
  Trecho: `<a href="{{return_url}}"><i class="material-icons">&#xE5C4;</i></a>{{object.nome_razao_social}}`
- `djangosige/templates/cadastro/pessoa_list.html:21`
  Trecho: `<a href="{{add_url}}" class="btn btn-success"><i class="material-icons">&#xE148;</i><span> ADICIONAR</span></a>`
- `djangosige/templates/compras/compra_form.html:113`
  Trecho: `<a class="input-group-addon newwindow" style="color: green;" title="Adicionar fornecedor" href="{% url 'cadastro:addfornecedorview' %}"><i c`
- `djangosige/templates/compras/modal_calculo_imposto.html:24`
  Trecho: `<i class="material-icons" style="font-size: 18px;margin-left: 10px;" title="Desmarcar esta opção caso o cálculo automático dos impostos este`
- `djangosige/templates/formset/formset.html:7`
  Trecho: `<h4 class="formset-title">{{title}}<span class="formset-padrao"> (padrão)<i class="material-icons" title="As entradas padrão serão utilizada`
- `djangosige/templates/formset/formset_fields.html:10`
  Trecho: `<label>{% if field.label %}{{field.label}}<span class="formset-padrao"> (padrão)<i class="material-icons" title="As entradas padrão serão ut`

## Telas-Alvo para Baseline Visual

- `Login`: Tela de autenticacao e estado de erro
  Template base: `djangosige/templates/login/login.html`
- `Dashboard`: Cards, tabelas e hierarquia visual da home
  Template base: `djangosige/templates/base/index.html`
- `Lista padrao`: Tabela, busca, botoes e acao em massa
  Template base: `djangosige/templates/cadastro/pessoa_list.html`
- `Formulario padrao`: Inputs, tabs e botoes de salvar
  Template base: `djangosige/templates/cadastro/pessoa_edit.html`
- `Modal padrao`: Confirmacoes e acoes de usuario
  Template base: `djangosige/templates/base/modal.html`
- `Fluxo financeiro`: Tabela densa e filtros operacionais
  Template base: `djangosige/templates/financeiro/lancamento/lancamento_list.html`
- `Nota fiscal`: Tabs, campos densos e modais detalhados
  Template base: `djangosige/templates/fiscal/nota_fiscal/nota_fiscal_edit.html`

## Tempos Aproximados de Resposta

Medicao feita com `Django test client`, 3 requisicoes por pagina, usando usuario autenticado nas telas protegidas.

| Tela | URL | Status | Media | Pico | Tamanho HTML |
| --- | --- | --- | --- | --- | --- |
| Login | `/login/` | `200` | `11.2 ms` | `30.8 ms` | `5.9 KB` |
| Dashboard | `/` | `200` | `17.6 ms` | `31.0 ms` | `28.4 KB` |
| Cadastro Clientes | `/cadastro/cliente/listaclientes/` | `200` | `6.4 ms` | `7.2 ms` | `21.8 KB` |
| Vendas Pedidos | `/vendas/pedidovenda/listapedidovenda/` | `200` | `5.2 ms` | `5.4 ms` | `22.0 KB` |
| Compras Pedidos | `/compras/pedidocompra/listapedidocompra/` | `200` | `5.0 ms` | `6.1 ms` | `22.0 KB` |
| Financeiro Lancamentos | `/financeiro/lancamentos/` | `200` | `5.6 ms` | `7.0 ms` | `24.0 KB` |
| Estoque Consulta | `/estoque/consultaestoque/` | `200` | `5.9 ms` | `7.7 ms` | `23.3 KB` |
| Fiscal NFs | `/fiscal/notafiscal/saida/listanotafiscal/` | `200` | `5.1 ms` | `6.1 ms` | `24.6 KB` |

## Componentes Legados com Maior Impacto

- `Materialize`: ainda entra via `@import` em `style.css` e influencia checkboxes, radios e estilos de form
- `Bootstrap 3`: base de layout, navbar, modal, tabs e dropdowns
- `jQuery + admin.js`: controla menu lateral, modal de mensagens, DataTables, formsets, datepickers, masks e automacoes de formulario
- `DataTables`: padrao de listas administrativas
- `jQuery UI`: datepicker e autocomplete
- `jquery.datetimepicker`: campos de data e hora
- `jquery.mask`: mascaras de moeda e campos numericos
- `jquery.multi-select`: selecao multipla em pontos especificos

## Baseline de Validacao

- `python manage.py check`: executar a cada fase
- `python manage.py test djangosige.tests.validation`: baseline funcional principal
- `python contrib/validate_smoke.py`: smoke de rotas sem parametros

## Observacoes

- o maior peso absoluto em `static/` nao esta no runtime, e sim nas tabelas CSV auxiliares do dominio
- os maiores pesos de runtime concentram-se em `admin.js`, `bootstrap.min.css`, `jquery`, `DataTables`, `jQuery UI`, `datetimepicker` e fontes de icones
- a migracao mais sensivel sera a retirada de `Materialize` e a troca de `Bootstrap 3` por `Bootstrap 5`, porque essas camadas afetam praticamente todo o markup
