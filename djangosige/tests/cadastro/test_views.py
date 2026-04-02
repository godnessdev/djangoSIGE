# -*- coding: utf-8 -*-

import json
from unittest.mock import patch

from djangosige.tests.test_case import BaseTestCase, replace_none_values_in_dictionary
from djangosige.apps.cadastro.models import Produto, ProdutoEmpresa, Unidade, Marca, Categoria, Transportadora, Fornecedor, Cliente, Empresa
from djangosige.apps.estoque.models import LocalEstoque, ProdutoEstocado
from djangosige.apps.fiscal.models import NaturezaOperacao, GrupoFiscal
from django.urls import reverse


CADASTRO_MODELS = (
    Empresa,
    Cliente,
    Fornecedor,
    Transportadora,
    Produto,
    Categoria,
    Unidade,
    Marca,
)

PESSOA_MODELS = (
    Empresa,
    Cliente,
    Fornecedor,
    Transportadora,
)

INLINE_FORMSET_DATA = {
    'endereco_form-0-tipo_endereco': 'UNI',
    'endereco_form-0-logradouro': 'Logradouro Cliente',
    'endereco_form-0-numero': '123',
    'endereco_form-0-bairro': 'Bairro Cliente',
    'endereco_form-0-complemento': '',
    'endereco_form-0-pais': 'Brasil',
    'endereco_form-0-cpais': '1058',
    'endereco_form-0-municipio': 'Municipio',
    'endereco_form-0-cmun': '12345',
    'endereco_form-0-cep': '1234567',
    'endereco_form-0-uf': 'MG',
    'endereco_form-TOTAL_FORMS': 1,
    'endereco_form-INITIAL_FORMS': 0,
    'telefone_form-TOTAL_FORMS': 1,
    'telefone_form-INITIAL_FORMS': 0,
    'email_form-TOTAL_FORMS': 1,
    'email_form-INITIAL_FORMS': 0,
    'site_form-TOTAL_FORMS': 1,
    'site_form-INITIAL_FORMS': 0,
    'banco_form-TOTAL_FORMS': 1,
    'banco_form-INITIAL_FORMS': 0,
    'documento_form-TOTAL_FORMS': 1,
    'documento_form-INITIAL_FORMS': 0,
}


class CadastroAdicionarViewsTestCase(BaseTestCase):

    def test_add_views_get_request(self):
        for model in CADASTRO_MODELS:
            model_name = model.__name__.lower()
            url = reverse('cadastro:add{}view'.format(model_name))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            # Testar permissao
            permission_codename = 'add_' + str(model_name)
            self.check_user_get_permission(
                url, permission_codename=permission_codename)

    def test_add_pessoa_post_request(self):
        for model in PESSOA_MODELS:
            model_name = model.__name__.lower()
            url = reverse('cadastro:add{}view'.format(model_name))
            pessoa_data = {
                '{}_form-nome_razao_social'.format(model_name): 'Razao Social Qualquer',
                '{}_form-tipo_pessoa'.format(model_name): 'PJ',
                '{}_form-inscricao_municipal'.format(model_name): '',
                '{}_form-informacoes_adicionais'.format(model_name): '',
            }

            if model_name == 'cliente':
                pessoa_data['cliente_form-limite_de_credito'] = '0.00'
                pessoa_data['cliente_form-indicador_ie'] = '1'
                pessoa_data['cliente_form-id_estrangeiro'] = ''
            elif model_name == 'transportadora':
                pessoa_data['veiculo_form-TOTAL_FORMS'] = 1
                pessoa_data['veiculo_form-INITIAL_FORMS'] = 0
                pessoa_data['veiculo_form-0-descricao'] = 'Veiculo1'
                pessoa_data['veiculo_form-0-placa'] = 'XXXXXXXX'
                pessoa_data['veiculo_form-0-uf'] = 'SP'

            pessoa_data.update(INLINE_FORMSET_DATA)

            response = self.client.post(url, pessoa_data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'cadastro/pessoa_list.html')
            created_obj = model.objects.order_by('pk').last()
            if model is not Empresa:
                self.assertEqual(created_obj.empresa_relacionada_id, self.empresa_ativa.pk)

            # Assert form invalido
            pessoa_data['{}_form-nome_razao_social'.format(model_name)] = ''
            response = self.client.post(url, pessoa_data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('nome_razao_social', response.context_data['form'].errors)
            self.assertIn('Este campo é obrigatório.',
                          response.context_data['form'].errors['nome_razao_social'])

    def test_add_produto_post_request(self):
        url = reverse('cadastro:addprodutoview')
        produto_data = {
            'codigo': '000000000000010',
            'descricao': 'Produto Teste',
            'origem': '0',
            'venda': '100,00',
            'custo': '50,00',
            'estoque_minimo': '100,00',
            'estoque_atual': '500,00',
            'ncm': '02109100[EX:01]',
            'fornecedor': '2',  # Id Fornecedor1
            'local_dest': '1',  # Id Estoque Padrao
        }

        response = self.client.post(url, produto_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastro/produto/produto_list.html')
        produto = Produto.objects.get(codigo='000000000000010')
        configuracao = ProdutoEmpresa.objects.get(
            produto=produto, empresa=self.empresa_ativa)
        self.assertEqual(str(configuracao.venda), '100.00')
        self.assertEqual(str(configuracao.custo), '50.00')

        # Assert form invalido
        produto_data['codigo'] = ''
        response = self.client.post(url, produto_data, follow=True)
        self.assertFormError(response, 'form', 'codigo',
                             'Este campo é obrigatório.')

    def test_add_categoria_post_request(self):
        url = reverse('cadastro:addcategoriaview')
        data = {
            'categoria_desc': 'Categoria Teste',
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert form invalido
        data['categoria_desc'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response, 'form', 'categoria_desc', 'Este campo é obrigatório.')

    def test_add_marca_post_request(self):
        url = reverse('cadastro:addmarcaview')
        data = {
            'marca_desc': 'Marca Teste',
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert form invalido
        data['marca_desc'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertFormError(response, 'form', 'marca_desc',
                             'Este campo é obrigatório.')

    def test_add_unidade_post_request(self):
        url = reverse('cadastro:addunidadeview')
        data = {
            'sigla_unidade': 'UNT',
            'unidade_desc': 'Unidade Teste',
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert form invalido
        data['sigla_unidade'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response, 'form', 'sigla_unidade', 'Este campo é obrigatório.')


class CadastroListarViewsTestCase(BaseTestCase):

    def test_list_views_deletar_objeto(self):
        for model in CADASTRO_MODELS:
            model_name = model.__name__.lower()
            if model_name == 'fornecedor':
                url = reverse('cadastro:listafornecedoresview')
            else:
                url = reverse('cadastro:lista{}sview'.format(model_name))

            create_kwargs = {}
            if model in (Cliente, Fornecedor, Transportadora):
                create_kwargs['empresa_relacionada'] = self.empresa_ativa
            obj = model.objects.create(**create_kwargs)
            self.check_list_view_delete(url=url, deleted_object=obj)

        url = reverse('cadastro:listaprodutosbaixoestoqueview')
        obj = Produto.objects.create()
        self.check_list_view_delete(url=url, deleted_object=obj)

    def test_list_clientes_paginated(self):
        for indice in range(105):
            Cliente.objects.create(
                nome_razao_social='Cliente Paginado {:03d}'.format(indice),
                tipo_pessoa='PJ',
                empresa_relacionada=self.empresa_ativa)

        response = self.client.get(reverse('cadastro:listaclientesview'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['all_clientes']), 100)

    def test_list_produtos_paginated(self):
        for indice in range(105):
            Produto.objects.create(
                codigo='PROD-PAG-{:03d}'.format(indice),
                descricao='Produto Paginado {:03d}'.format(indice))

        response = self.client.get(reverse('cadastro:listaprodutosview'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['all_produtos']), 100)


class CadastroEditarViewsTestCase(BaseTestCase):

    def test_edit_pessoa_get_post_request(self):
        for model in PESSOA_MODELS:
            # Buscar objeto qualquer
            model_name = model.__name__.lower()
            obj = model.objects.order_by('pk').last()
            url = reverse('cadastro:editar{}view'.format(model_name),
                          kwargs={'pk': obj.pk})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = response.context['form'].initial
            replace_none_values_in_dictionary(data)
            if model_name == 'cliente':
                data['{}-limite_de_credito'.format(response.context['form'].prefix)] = data[
                    'limite_de_credito']
                del data['limite_de_credito']
            elif model_name == 'transportadora':
                data['veiculo_form-TOTAL_FORMS'] = 1
                data['veiculo_form-INITIAL_FORMS'] = 0
                data['veiculo_form-0-descricao'] = 'Veiculo1'
                data['veiculo_form-0-placa'] = 'XXXXXXXX'
                data['veiculo_form-0-uf'] = 'SP'

            # Inserir informacoes adicionais
            data['informacoes_adicionais'] = 'Objeto editado.'
            data.update(INLINE_FORMSET_DATA)
            response = self.client.post(url, data, follow=True)
            self.assertEqual(response.status_code, 200)

            # Assert form invalido
            data[
                '{}_form-nome_razao_social'.format(response.context['form'].prefix)] = ''
            response = self.client.post(url, data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('nome_razao_social', response.context_data['form'].errors)
            self.assertIn('Este campo é obrigatório.',
                          response.context_data['form'].errors['nome_razao_social'])

    def test_edit_produto_get_post_request(self):
        obj = Produto.objects.create(
            codigo='PROD-EDIT-01',
            descricao='Produto Editavel',
            venda='80.00',
            custo='40.00',
        )
        NaturezaOperacao.objects.create(
            empresa=self.empresa_ativa, cfop='5102')
        grupo_global = GrupoFiscal.objects.create(
            empresa=self.empresa_ativa, descricao='Grupo Global Editavel', regime_trib='0')
        grupo_empresa = GrupoFiscal.objects.create(
            empresa=self.empresa_ativa, descricao='Grupo Empresa Editavel', regime_trib='1')
        obj.grupo_fiscal = grupo_global
        obj.save()
        ProdutoEmpresa.objects.create(
            produto=obj,
            empresa=self.empresa_ativa,
            venda='95.00',
            custo='52.00',
            grupo_fiscal=grupo_empresa,
        )
        url = reverse('cadastro:editarprodutoview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        replace_none_values_in_dictionary(data)
        data['inf_adicionais'] = 'Produto editado.'
        data['venda'] = '120,00'
        data['custo'] = '75,00'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastro/produto/produto_list.html')
        obj.refresh_from_db()
        configuracao = ProdutoEmpresa.objects.get(
            produto=obj, empresa=self.empresa_ativa)
        self.assertEqual(str(configuracao.venda), '120.00')
        self.assertEqual(str(configuracao.custo), '75.00')
        self.assertEqual(str(obj.venda), '80.00')
        self.assertEqual(str(obj.custo), '40.00')

    def test_produto_form_nao_exibe_fiscal_de_outra_empresa(self):
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Fiscal Externa',
            tipo_pessoa='PJ')
        NaturezaOperacao.objects.create(
            empresa=outra_empresa, cfop='6101')
        GrupoFiscal.objects.create(
            empresa=outra_empresa,
            descricao='Grupo Fiscal Externo',
            regime_trib='0')

        response = self.client.get(reverse('cadastro:addprodutoview'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context['form'].fields['cfop_padrao'].queryset.filter(
                empresa=outra_empresa).exists())
        self.assertFalse(
            response.context['form'].fields['grupo_fiscal'].queryset.filter(
                empresa=outra_empresa).exists())

    def test_edit_categoria_get_post_request(self):
        # Buscar objeto qualquer
        obj = Categoria.objects.order_by('pk').last()
        url = reverse('cadastro:editarcategoriaview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data['categoria_desc'] = 'Categoria Editada'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert form invalido
        data['categoria_desc'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response, 'form', 'categoria_desc', 'Este campo é obrigatório.')

    def test_edit_marca_get_post_request(self):
        # Buscar objeto qualquer
        obj = Marca.objects.order_by('pk').last()
        url = reverse('cadastro:editarmarcaview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data['marca_desc'] = 'Marca Editada'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_edit_unidade_get_post_request(self):
        # Buscar objeto qualquer
        obj = Unidade.objects.order_by('pk').last()
        url = reverse('cadastro:editarunidadeview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data['unidade_desc'] = 'Unidade Editada'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)


class CadastroAjaxRequestViewsTestCase(BaseTestCase):

    class _MockHTTPResponse(object):
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return json.dumps(self.payload).encode('utf-8')

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def test_info_cliente_post_request(self):
        # Buscar objeto qualquer
        obj = Cliente.objects.filter(empresa_relacionada=self.empresa_ativa).order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('cadastro:infocliente')
        data = {'pessoaId': obj_pk}
        self.check_json_response(url, data, obj_pk, model='cadastro.cliente')

    def test_info_transportadora_post_request(self):
        # Buscar objeto qualquer
        obj = Transportadora.objects.filter(empresa_relacionada=self.empresa_ativa).order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('cadastro:infotransportadora')
        data = {'transportadoraId': obj_pk}
        self.check_json_response(
            url, data, obj_pk, model='cadastro.transportadora')

    def test_info_fornecedor_post_request(self):
        # Buscar objeto qualquer
        obj = Fornecedor.objects.filter(empresa_relacionada=self.empresa_ativa).order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('cadastro:infofornecedor')
        data = {'pessoaId': obj_pk}
        self.check_json_response(
            url, data, obj_pk, model='cadastro.fornecedor')

    def test_info_produto_post_request(self):
        # Buscar objeto qualquer
        obj = Produto.objects.order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('cadastro:infoproduto')
        data = {'produtoId': obj_pk}
        self.check_json_response(url, data, obj_pk, model='cadastro.produto')

    @patch('djangosige.apps.cadastro.views.ajax_views.urllib_request.urlopen')
    def test_consulta_cnpj_get_request(self, mocked_urlopen):
        mocked_urlopen.return_value = self._MockHTTPResponse({
            'cnpj': '27865757000102',
            'razao_social': 'EMPRESA VALIDACAO LTDA',
            'nome_fantasia': 'EMPRESA VALIDACAO',
            'logradouro': 'Rua Exemplo',
            'numero': '100',
            'complemento': 'Sala 2',
            'bairro': 'Centro',
            'municipio': 'Belo Horizonte',
            'uf': 'MG',
            'cep': '30110000',
            'ddd_telefone_1': '31',
            'telefone_1': '33334444',
            'email': 'contato@example.com',
            'qsa': [{'nome_socio': 'SOCIO TESTE'}],
        })

        response = self.client.get(reverse('cadastro:consultacnpj'), {'cnpj': '27.865.757/0001-02'})
        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.content.decode('utf-8'))
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['nome_razao_social'], 'EMPRESA VALIDACAO LTDA')
        self.assertEqual(payload['data']['cnpj'], '27.865.757/0001-02')
        self.assertEqual(payload['data']['telefone'], '(31) 3333-4444')

    def test_consulta_preco_produto_get_request(self):
        produto = Produto.objects.create(
            codigo='PRECO001',
            descricao='Produto Preco Teste',
            venda='1250.90',
            custo='900.00',
            estoque_minimo='1.00',
            estoque_atual='5.00',
        )
        ProdutoEmpresa.objects.create(
            produto=produto,
            empresa=self.empresa_ativa,
            venda='777.70',
            custo='500.00',
        )
        local = LocalEstoque.objects.create(
            descricao='Local Consulta Preco', empresa=self.empresa_ativa)
        ProdutoEstocado.objects.create(
            produto=produto, local=local, quantidade='3.00')

        response = self.client.get(reverse('cadastro:consultaprecoproduto'), {'term': 'Prod'})
        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.content.decode('utf-8'))
        self.assertTrue(payload['success'])
        self.assertGreaterEqual(len(payload['results']), 1)
        result = next(item for item in payload['results'] if item['id'] == produto.pk)
        self.assertEqual(result['descricao'], 'Produto Preco Teste')
        self.assertEqual(result['preco'], 'R$ 777,70')
        self.assertEqual(result['estoque'], '3,00')

    def test_info_produto_retorna_preco_da_empresa_ativa(self):
        produto = Produto.objects.create(
            codigo='INFO001',
            descricao='Produto Info Empresa',
            venda='90.00',
            custo='40.00',
            estoque_atual='2.00',
        )
        ProdutoEmpresa.objects.create(
            produto=produto,
            empresa=self.empresa_ativa,
            venda='145.00',
            custo='70.00',
        )

        response = self.client.post(reverse('cadastro:infoproduto'), {
            'produtoId': produto.pk,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode('utf-8'))
        produto_payload = next(item for item in payload if item['model'] == 'cadastro.produto')
        self.assertEqual(produto_payload['fields']['venda'], '145.00')


class EmpresaHierarquiaViewsTestCase(BaseTestCase):

    def test_add_filial_with_matriz(self):
        matriz = Empresa.objects.create(
            nome_razao_social='Matriz Base',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )
        url = reverse('cadastro:addempresaview')
        data = {
            'empresa_form-nome_razao_social': 'Filial Nova',
            'empresa_form-tipo_pessoa': 'PJ',
            'empresa_form-tipo_empresa': Empresa.TIPO_FILIAL,
            'empresa_form-empresa_pai': matriz.pk,
            'empresa_form-inscricao_municipal': '',
            'empresa_form-cnae': '',
            'empresa_form-iest': '',
            'empresa_form-informacoes_adicionais': '',
        }
        data.update(INLINE_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastro/pessoa_list.html')

        filial = Empresa.objects.get(nome_razao_social='Filial Nova')
        self.assertEqual(filial.tipo_empresa, Empresa.TIPO_FILIAL)
        self.assertEqual(filial.empresa_pai_id, matriz.pk)

    def test_add_filial_without_matriz_is_invalid(self):
        url = reverse('cadastro:addempresaview')
        data = {
            'empresa_form-nome_razao_social': 'Filial Sem Matriz',
            'empresa_form-tipo_pessoa': 'PJ',
            'empresa_form-tipo_empresa': Empresa.TIPO_FILIAL,
            'empresa_form-inscricao_municipal': '',
            'empresa_form-cnae': '',
            'empresa_form-iest': '',
            'empresa_form-informacoes_adicionais': '',
        }
        data.update(INLINE_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('empresa_pai', response.context_data['form'].errors)
        self.assertIn('Selecione a matriz desta filial.',
                      response.context_data['form'].errors['empresa_pai'])

    def test_empresa_list_displays_tipo_e_matriz(self):
        matriz = Empresa.objects.create(
            nome_razao_social='Matriz Lista',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )
        Empresa.objects.create(
            nome_razao_social='Filial Lista',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
        )

        response = self.client.get(reverse('cadastro:listaempresasview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matriz')
        self.assertContains(response, 'Filial')
        self.assertContains(response, 'Matriz Lista')

    def test_empresa_list_filter_by_tipo(self):
        Empresa.objects.create(
            nome_razao_social='Empresa Independente Filtro',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_INDEPENDENTE,
        )
        Empresa.objects.create(
            nome_razao_social='Empresa Matriz Filtro',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )

        response = self.client.get(reverse('cadastro:listaempresasview'), {
            'tipo_empresa': Empresa.TIPO_MATRIZ,
        })
        self.assertEqual(response.status_code, 200)
        for empresa in response.context['all_empresas']:
            self.assertEqual(empresa.tipo_empresa, Empresa.TIPO_MATRIZ)

    def test_empresa_list_filter_by_grupo_empresarial(self):
        matriz = Empresa.objects.create(
            nome_razao_social='Matriz Grupo Filtro',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )
        filial = Empresa.objects.create(
            nome_razao_social='Filial Grupo Filtro',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
        )
        independente = Empresa.objects.create(
            nome_razao_social='Independente Fora Grupo',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_INDEPENDENTE,
        )

        response = self.client.get(reverse('cadastro:listaempresasview'), {
            'grupo_empresa': matriz.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(matriz, response.context['all_empresas'])
        self.assertIn(filial, response.context['all_empresas'])
        self.assertNotIn(independente, response.context['all_empresas'])


class CadastroEmpresaRelacionadaPorEmpresaTestCase(BaseTestCase):

    def test_lista_clientes_nao_exibe_outra_empresa(self):
        empresa_secundaria = Empresa.objects.create(
            nome_razao_social='Empresa Cliente Externo', tipo_pessoa='PJ')
        cliente_externo = Cliente.objects.create(
            nome_razao_social='Cliente Externo', tipo_pessoa='PJ', empresa_relacionada=empresa_secundaria)

        response = self.client.get(reverse('cadastro:listaclientesview'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(cliente_externo, response.context['all_clientes'])
