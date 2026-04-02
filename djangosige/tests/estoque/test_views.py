# -*- coding: utf-8 -*-

from djangosige.tests.test_case import BaseTestCase
from djangosige.apps.cadastro.models import Empresa, Produto, MinhaEmpresa, UsuarioEmpresa
from djangosige.apps.estoque.models import LocalEstoque, DEFAULT_LOCAL_ID, ProdutoEstocado, EntradaEstoque, SaidaEstoque, TransferenciaEstoque
from django.urls import reverse

MOVIMENTO_ESTOQUE_FORMSET_DATA = {
    'itens_form-0-produto': 1,
    'itens_form-0-quantidade': 2,
    'itens_form-0-valor_unit': '100,00',
    'itens_form-0-subtotal': '180,00',
    'itens_form-1-produto': 2,
    'itens_form-1-quantidade': 3,
    'itens_form-1-valor_unit': '100,00',
    'itens_form-1-subtotal': '280,00',
    'itens_form-TOTAL_FORMS': 2,
    'itens_form-INITIAL_FORMS': 0,
}


class EstoqueConsultaViewTestCase(BaseTestCase):
    url = reverse('estoque:consultaestoqueview')

    def test_consulta_estoque_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_consulta_estoque_get_request_local(self):
        # Request com local definido
        local = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)
        data = {
            'local': local.pk,
        }
        response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, 200)

    def test_consulta_estoque_get_request_produto(self):
        # Request com produto definido
        prod = Produto.objects.filter(controlar_estoque=True).first()
        data = {
            'produto': prod.pk,
        }
        response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, 200)

    def test_consulta_estoque_consolidado_grupo(self):
        matriz = Empresa.objects.create(
            nome_razao_social='Matriz Consulta Grupo',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )
        filial = Empresa.objects.create(
            nome_razao_social='Filial Consulta Grupo',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
        )
        MinhaEmpresa.objects.filter(m_usuario=self.usuario).update(m_empresa=matriz)
        UsuarioEmpresa.objects.get_or_create(m_usuario=self.usuario, m_empresa=matriz)
        UsuarioEmpresa.objects.get_or_create(m_usuario=self.usuario, m_empresa=filial)
        produto = Produto.objects.create(
            codigo='CONS-GRUPO-1',
            descricao='Produto Consulta Grupo',
            controlar_estoque=True,
            estoque_minimo='1.00')
        local_matriz = LocalEstoque.objects.create(
            descricao='Local Matriz Consulta', empresa=matriz)
        local_filial = LocalEstoque.objects.create(
            descricao='Local Filial Consulta', empresa=filial)
        ProdutoEstocado.objects.create(
            local=local_matriz, produto=produto, quantidade='2.00')
        ProdutoEstocado.objects.create(
            local=local_filial, produto=produto, quantidade='3.00')

        response = self.client.get(self.url, {'modo': 'grupo'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['pode_consolidar_grupo'])
        resultado = next(item for item in response.context['produtos_filtrados'] if item.pk == produto.pk)
        self.assertEqual(resultado.estoque_exibicao, 5)
        self.assertEqual(len(resultado.saldos_por_empresa_exibicao), 2)

    def test_consulta_estoque_produtos_em_falta_por_filial(self):
        produto = Produto.objects.create(
            codigo='CONS-FALTA-1',
            descricao='Produto Em Falta',
            controlar_estoque=True,
            estoque_minimo='10.00')
        local = LocalEstoque.objects.create(
            descricao='Local Falta', empresa=self.empresa_ativa)
        ProdutoEstocado.objects.create(
            local=local, produto=produto, quantidade='4.00')

        response = self.client.get(self.url, {'modo': 'falta'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(produto, response.context['produtos_filtrados'])


class EstoqueAdicionarViewsTestCase(BaseTestCase):

    def test_add_local_estoque_view_get_request(self):
        url = reverse('estoque:addlocalview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_entrada_estoque_view_get_request(self):
        url = reverse('estoque:addentradaestoqueview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_saida_estoque_view_get_request(self):
        url = reverse('estoque:addsaidaestoqueview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_transferencia_estoque_view_get_request(self):
        url = reverse('estoque:addtransferenciaestoqueview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_local_estoque_view_post_request(self):
        url = reverse('estoque:addlocalview')

        data = {
            'descricao': 'Local Estoque Teste 1',
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert form invalido
        data['descricao'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response, 'form', 'descricao', 'Este campo é obrigatório.')

    def test_add_entrada_estoque_view_post_request(self):
        url = reverse('estoque:addentradaestoqueview')
        local = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        data = {
            'quantidade_itens': 2,
            'valor_total': '460,00',
            'tipo_movimento': '0',
            'local_dest': local.pk,
        }

        data.update(MOVIMENTO_ESTOQUE_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_list.html')

        # Assert form invalido
        data['tipo_movimento'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['tipo_movimento'],
            ['Este campo é obrigatório.'])

    def test_add_saida_estoque_view_post_request(self):
        url = reverse('estoque:addsaidaestoqueview')
        local = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        data = {
            'quantidade_itens': 2,
            'valor_total': '460,00',
            'tipo_movimento': '0',
            'local_orig': local.pk,
        }

        data.update(MOVIMENTO_ESTOQUE_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_list.html')

        # Assert form invalido
        data['tipo_movimento'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['tipo_movimento'],
            ['Este campo é obrigatório.'])

        # Testar retirar produtos de um local sem produtos em estoque
        local = LocalEstoque.objects.create(
            descricao='Novo Local Estoque 1', empresa=self.empresa_ativa)
        data['local_orig'] = local.pk
        data['tipo_movimento'] = '0'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_list.html')

        # Testar retirar produto com estoque atual abaixo do movimentado
        prod1 = Produto.objects.create(
            descricao='Produto com estoque zero', controlar_estoque=True, estoque_atual='0.00')
        ProdutoEstocado(local=local, produto=prod1, quantidade=30).save()
        data['itens_form-2-produto'] = prod1.pk
        data['itens_form-2-quantidade'] = 10
        data['itens_form-2-valor_unit'] = '50,00'
        data['itens_form-2-subtotal'] = '500,00'
        data['itens_form-TOTAL_FORMS'] = 3
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response, 'itens_form', 2, 'quantidade', 'Quantidade retirada do estoque maior que o estoque atual (' + str(prod1.estoque_atual).replace('.', ',') + ') do produto.')

    def test_add_transferencia_estoque_view_post_request(self):
        url = reverse('estoque:addtransferenciaestoqueview')
        local1 = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)
        local2 = LocalEstoque.objects.create(
            descricao='Novo Local Estoque 2', empresa=self.empresa_ativa)

        data = {
            'quantidade_itens': 2,
            'valor_total': '460,00',
            'empresa_destino': self.empresa_ativa.pk,
            'local_estoque_orig': local1.pk,
            'local_estoque_dest': local2.pk,
            'impacto_custo': 'MAN',
        }

        data.update(MOVIMENTO_ESTOQUE_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_list.html')

        # Testar tranferencia de estoque com produto abaixo
        data['quantidade_itens'] = 2
        data['local_estoque_orig'] = local2.pk
        data['local_estoque_dest'] = local1.pk
        data['itens_form-0-quantidade'] = 10
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert form invalido
        data['quantidade_itens'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['quantidade_itens'],
            ['Este campo é obrigatório.'])


    def test_add_transferencia_entre_filiais_mesmo_grupo(self):
        url = reverse('estoque:addtransferenciaestoqueview')
        matriz = Empresa.objects.create(
            nome_razao_social='Matriz Transferencia Grupo',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )
        empresa_origem = Empresa.objects.create(
            nome_razao_social='Filial Origem Transferencia',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
        )
        empresa_destino = Empresa.objects.create(
            nome_razao_social='Filial Destino Transferencia',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
        )
        MinhaEmpresa.objects.filter(m_usuario=self.usuario).update(m_empresa=empresa_origem)
        UsuarioEmpresa.objects.get_or_create(m_usuario=self.usuario, m_empresa=empresa_origem)
        UsuarioEmpresa.objects.get_or_create(m_usuario=self.usuario, m_empresa=empresa_destino)
        local_origem = LocalEstoque.objects.create(
            descricao='Local Origem Grupo', empresa=empresa_origem)
        local_destino = LocalEstoque.objects.create(
            descricao='Local Destino Grupo', empresa=empresa_destino)
        produto = Produto.objects.create(
            codigo='TRANS-GRUPO-1',
            descricao='Produto Transferencia Grupo',
            controlar_estoque=True,
            estoque_atual='8.00')
        ProdutoEstocado.objects.create(
            local=local_origem, produto=produto, quantidade='8.00')

        data = {
            'quantidade_itens': 1,
            'valor_total': '100,00',
            'empresa_destino': empresa_destino.pk,
            'local_estoque_orig': local_origem.pk,
            'local_estoque_dest': local_destino.pk,
            'impacto_custo': 'MAN',
            'itens_form-0-produto': produto.pk,
            'itens_form-0-quantidade': 5,
            'itens_form-0-valor_unit': '20,00',
            'itens_form-0-subtotal': '100,00',
            'itens_form-TOTAL_FORMS': 1,
            'itens_form-INITIAL_FORMS': 0,
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        transferencia = TransferenciaEstoque.objects.order_by('pk').last()
        self.assertEqual(transferencia.empresa_id, empresa_origem.pk)
        self.assertEqual(transferencia.empresa_destino_id, empresa_destino.pk)
        self.assertEqual(transferencia.impacto_custo, 'MAN')
        self.assertEqual(
            ProdutoEstocado.objects.get(local=local_origem, produto=produto).quantidade, 3)
        self.assertEqual(
            ProdutoEstocado.objects.get(local=local_destino, produto=produto).quantidade, 5)

    def test_add_transferencia_rejeita_empresa_destino_fora_do_grupo(self):
        url = reverse('estoque:addtransferenciaestoqueview')
        matriz = Empresa.objects.create(
            nome_razao_social='Matriz Transferencia Restrita',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
        )
        empresa_origem = Empresa.objects.create(
            nome_razao_social='Filial Origem Restrita',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
        )
        empresa_externa = Empresa.objects.create(
            nome_razao_social='Empresa Externa Transferencia',
            tipo_pessoa='PJ')
        MinhaEmpresa.objects.filter(m_usuario=self.usuario).update(m_empresa=empresa_origem)
        UsuarioEmpresa.objects.get_or_create(m_usuario=self.usuario, m_empresa=empresa_origem)
        UsuarioEmpresa.objects.get_or_create(m_usuario=self.usuario, m_empresa=empresa_externa)
        local_origem = LocalEstoque.objects.create(
            descricao='Local Origem Restrita', empresa=empresa_origem)
        local_destino = LocalEstoque.objects.create(
            descricao='Local Destino Externo', empresa=empresa_externa)
        produto = Produto.objects.create(
            codigo='TRANS-REST-1',
            descricao='Produto Transferencia Restrita',
            controlar_estoque=True,
            estoque_atual='8.00')
        ProdutoEstocado.objects.create(
            local=local_origem, produto=produto, quantidade='8.00')

        data = {
            'quantidade_itens': 1,
            'valor_total': '100,00',
            'empresa_destino': empresa_externa.pk,
            'local_estoque_orig': local_origem.pk,
            'local_estoque_dest': local_destino.pk,
            'impacto_custo': 'MAN',
            'itens_form-0-produto': produto.pk,
            'itens_form-0-quantidade': 5,
            'itens_form-0-valor_unit': '20,00',
            'itens_form-0-subtotal': '100,00',
            'itens_form-TOTAL_FORMS': 1,
            'itens_form-INITIAL_FORMS': 0,
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('empresa_destino', response.context_data['form'].errors)


class EstoqueListarViewsTestCase(BaseTestCase):

    def test_list_entrada_estoque_view_deletar_objeto(self):
        obj = EntradaEstoque.objects.create(empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'estoque:listaentradasestoqueview'), deleted_object=obj)

    def test_list_saida_estoque_view_deletar_objeto(self):
        obj = SaidaEstoque.objects.create(empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'estoque:listasaidasestoqueview'), deleted_object=obj)

    def test_list_transferencia_estoque_view_deletar_objeto(self):
        obj = TransferenciaEstoque.objects.create(
            empresa=self.empresa_ativa,
            empresa_destino=self.empresa_ativa,
            local_estoque_orig=LocalEstoque.objects.filter(
                empresa=self.empresa_ativa).order_by('id').first(),
            local_estoque_dest=LocalEstoque.objects.filter(
                empresa=self.empresa_ativa).order_by('id').last())
        self.check_list_view_delete(url=reverse(
            'estoque:listatransferenciasestoqueview'), deleted_object=obj)

    def test_list_todas_movimentacoes_estoque_view_deletar_objetos(self):
        obj = SaidaEstoque.objects.create(empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'estoque:listamovimentoestoqueview'), deleted_object=obj)
        obj = EntradaEstoque.objects.create(empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'estoque:listamovimentoestoqueview'), deleted_object=obj)
        obj = TransferenciaEstoque.objects.create(
            empresa=self.empresa_ativa,
            empresa_destino=self.empresa_ativa,
            local_estoque_orig=LocalEstoque.objects.filter(
                empresa=self.empresa_ativa).order_by('id').first(),
            local_estoque_dest=LocalEstoque.objects.filter(
                empresa=self.empresa_ativa).order_by('id').last())
        self.check_list_view_delete(url=reverse(
            'estoque:listamovimentoestoqueview'), deleted_object=obj)

    def test_list_transferencia_exibe_movimento_destinado_a_empresa_ativa(self):
        empresa_origem = Empresa.objects.create(
            nome_razao_social='Empresa Origem Lista Transferencia',
            tipo_pessoa='PJ')
        local_origem = LocalEstoque.objects.create(
            descricao='Local Origem Lista', empresa=empresa_origem)
        local_destino = LocalEstoque.objects.filter(
            empresa=self.empresa_ativa).order_by('id').first()
        transferencia = TransferenciaEstoque.objects.create(
            empresa=empresa_origem,
            empresa_destino=self.empresa_ativa,
            local_estoque_orig=local_origem,
            local_estoque_dest=local_destino)

        response = self.client.get(reverse('estoque:listatransferenciasestoqueview'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(transferencia, response.context['all_transferencias'])

    def test_list_local_estoque_view_deletar_objeto(self):
        obj = LocalEstoque.objects.create(empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'estoque:listalocalview'), deleted_object=obj)

    def test_list_local_estoque_nao_exibe_outra_empresa(self):
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Estoque', tipo_pessoa='PJ')
        local_outra_empresa = LocalEstoque.objects.create(
            descricao='Local Outra Empresa', empresa=outra_empresa)

        response = self.client.get(reverse('estoque:listalocalview'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(local_outra_empresa in response.context['all_locais'])


class EstoqueEditarViewsTestCase(BaseTestCase):

    def test_detalhar_entrada_estoque_get_request(self):
        # Buscar objeto qualquer
        obj = EntradaEstoque.objects.order_by('pk').last()
        url = reverse('estoque:detalharentradaestoqueview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_detail.html')

    def test_detalhar_saida_estoque_get_request(self):
        # Buscar objeto qualquer
        obj = SaidaEstoque.objects.order_by('pk').last()
        url = reverse('estoque:detalharsaidaestoqueview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_detail.html')

    def test_detalhar_transferencia_estoque_get_request(self):
        # Buscar objeto qualquer
        obj = TransferenciaEstoque.objects.order_by('pk').last()
        url = reverse('estoque:detalhartransferenciaestoqueview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'estoque/movimento/movimento_estoque_detail.html')

    def test_edit_local_estoque_get_post_request(self):
        # Buscar objeto qualquer
        obj = LocalEstoque.objects.order_by('pk').last()
        url = reverse('estoque:editarlocalview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data['descricao'] = 'Local Estoque Editado'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
