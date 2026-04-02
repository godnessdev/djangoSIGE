# -*- coding: utf-8 -*-

from djangosige.tests.test_case import BaseTestCase
import json

from django.contrib.auth.models import Group
from djangosige.apps.cadastro.models import Cliente, Empresa, Produto, ProdutoEmpresa
from djangosige.apps.vendas.models import CondicaoPagamento, OrcamentoVenda, PedidoVenda
from djangosige.apps.cadastro.models import MinhaEmpresa, UsuarioEmpresa
from djangosige.apps.estoque.models import LocalEstoque, DEFAULT_LOCAL_ID
from djangosige.apps.fiscal.models import NaturezaOperacao
from django.urls import reverse

from datetime import datetime, timedelta


VENDA_FORMSET_DATA = {
    'produtos_form-0-produto': 1,
    'produtos_form-0-quantidade': 2,
    'produtos_form-0-valor_unit': '100,00',
    'produtos_form-0-tipo_desconto': '0',
    'produtos_form-0-desconto': '20,00',
    'produtos_form-0-valor_rateio_frete': '0,00',
    'produtos_form-0-valor_rateio_despesas': '0,00',
    'produtos_form-0-valor_rateio_seguro': '0,00',
    'produtos_form-0-subtotal': '180,00',
    'produtos_form-1-produto': 2,
    'produtos_form-1-quantidade': 3,
    'produtos_form-1-valor_unit': '100,00',
    'produtos_form-1-tipo_desconto': '0',
    'produtos_form-1-desconto': '20,00',
    'produtos_form-1-valor_rateio_frete': '0,00',
    'produtos_form-1-valor_rateio_despesas': '0,00',
    'produtos_form-1-valor_rateio_seguro': '0,00',
    'produtos_form-1-subtotal': '280,00',
    'produtos_form-TOTAL_FORMS': 2,
    'produtos_form-INITIAL_FORMS': 0,
    'pagamento_form-1-indice_parcela': 1,
    'pagamento_form-1-vencimento': '31/07/2017',
    'pagamento_form-1-valor_parcela': '460,00',
    'pagamento_form-TOTAL_FORMS': 1,
    'pagamento_form-INITIAL_FORMS': 0,
}


def configurar_grupo_empresarial(test_case):
    matriz = Empresa.objects.create(
        nome_razao_social='Matriz Vendas',
        tipo_pessoa='PJ',
        tipo_empresa=Empresa.TIPO_MATRIZ)
    filial = Empresa.objects.create(
        nome_razao_social='Filial Vendas',
        tipo_pessoa='PJ',
        tipo_empresa=Empresa.TIPO_FILIAL,
        empresa_pai=matriz)
    cliente_matriz = Cliente.objects.create(
        nome_razao_social='Cliente Matriz Vendas',
        tipo_pessoa='PJ',
        empresa_relacionada=matriz)
    local_matriz = LocalEstoque.objects.create(
        descricao='Local Matriz Vendas', empresa=matriz)
    local_filial = LocalEstoque.objects.create(
        descricao='Local Filial Vendas', empresa=filial)
    UsuarioEmpresa.objects.get_or_create(
        m_usuario=test_case.usuario, m_empresa=matriz)
    UsuarioEmpresa.objects.get_or_create(
        m_usuario=test_case.usuario, m_empresa=filial)
    MinhaEmpresa.objects.filter(m_usuario=test_case.usuario).update(m_empresa=matriz)
    return matriz, filial, cliente_matriz, local_matriz, local_filial


class VendasAdicionarViewsTestCase(BaseTestCase):

    def test_add_orcamento_venda_view_get_request(self):
        url = reverse('vendas:addorcamentovendaview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_pedido_venda_view_get_request(self):
        url = reverse('vendas:addpedidovendaview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_condicao_pagamento_view_get_request(self):
        url = reverse('vendas:addcondicaopagamentoview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_orcamento_venda_view_post_request(self):
        url = reverse('vendas:addorcamentovendaview')
        cli = Cliente.objects.order_by('id').last()
        local_orig = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        data = {
            'data_emissao': '16/07/2017',
            'cliente': cli.pk,
            'status': '0',
            'tipo_desconto': '0',
            'desconto': '40,00',
            'frete': '0,00',
            'seguro': '0,00',
            'despesas': '0,00',
            'mod_frete': '0',
            'impostos': '0,00',
            'valor_total': '460,00',
            'local_orig': local_orig.pk,
        }

        data.update(VENDA_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/orcamento_venda/orcamento_venda_list.html')

        # Assert form invalido
        data['cliente'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['cliente'],
            ['Este campo é obrigatório.'])

    def test_add_pedido_venda_view_post_request(self):
        url = reverse('vendas:addpedidovendaview')
        cli = Cliente.objects.order_by('id').last()
        local_orig = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        data = {
            'data_emissao': '16/07/2017',
            'cliente': cli.pk,
            'status': '0',
            'tipo_desconto': '0',
            'desconto': '40,00',
            'frete': '0,00',
            'seguro': '0,00',
            'despesas': '0,00',
            'mod_frete': '0',
            'impostos': '0,00',
            'valor_total': '460,00',
            'local_orig': local_orig.pk,
        }

        data.update(VENDA_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/pedido_venda/pedido_venda_list.html')

        # Assert form invalido
        data['cliente'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['cliente'],
            ['Este campo é obrigatório.'])

    def test_add_condicao_pagamento_view_post_request(self):
        url = reverse('vendas:addcondicaopagamentoview')

        data = {
            'descricao': 'Condicao Pagamento Teste',
            'forma': '99',
            'n_parcelas': 6,
            'dias_recorrencia': 30,
            'parcela_inicial': 0,
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/pagamento/condicao_pagamento_list.html')

        # Assert form invalido
        data['descricao'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response, 'form', 'descricao', 'Este campo é obrigatório.')


class VendasListarViewsTestCase(BaseTestCase):

    def test_list_orcamento_venda_view_deletar_objeto(self):
        cli = Cliente.objects.order_by('id').last()
        obj = OrcamentoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'vendas:listaorcamentovendaview'), deleted_object=obj)

    def test_list_orcamento_venda_vencido_view_deletar_objeto(self):
        cli = Cliente.objects.order_by('id').last()
        obj = OrcamentoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa,
            data_vencimento=datetime.now().date() - timedelta(days=1))
        self.check_list_view_delete(url=reverse(
            'vendas:listaorcamentovendavencidoview'), deleted_object=obj)

    def test_list_orcamento_venda_vence_hoje_view_deletar_objeto(self):
        cli = Cliente.objects.order_by('id').last()
        obj = OrcamentoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa,
            data_vencimento=datetime.now().date())
        self.check_list_view_delete(url=reverse(
            'vendas:listaorcamentovendahojeview'), deleted_object=obj)

    def test_list_pedido_venda_view_deletar_objeto(self):
        cli = Cliente.objects.order_by('id').last()
        obj = PedidoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'vendas:listapedidovendaview'), deleted_object=obj)

    def test_list_pedido_venda_atrasado_view_deletar_objeto(self):
        cli = Cliente.objects.order_by('id').last()
        obj = PedidoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa,
            data_entrega=datetime.now().date() - timedelta(days=1))
        self.check_list_view_delete(url=reverse(
            'vendas:listapedidovendaatrasadosview'), deleted_object=obj)

    def test_list_pedido_venda_entrega_hoje_view_deletar_objeto(self):
        cli = Cliente.objects.order_by('id').last()
        obj = PedidoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa,
            data_entrega=datetime.now().date())
        self.check_list_view_delete(url=reverse(
            'vendas:listapedidovendahojeview'), deleted_object=obj)

    def test_list_condicao_pagamento_view_deletar_objeto(self):
        obj = CondicaoPagamento.objects.create(n_parcelas=6)
        self.check_list_view_delete(url=reverse(
            'vendas:listacondicaopagamentoview'), deleted_object=obj)

    def test_list_pedido_venda_nao_exibe_outra_empresa(self):
        cli = Cliente.objects.order_by('id').last()
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Vendas', tipo_pessoa='PJ')
        local_outra_empresa = LocalEstoque.objects.create(
            descricao='Local Vendas Outra Empresa', empresa=outra_empresa)
        pedido_outra_empresa = PedidoVenda.objects.create(
            cliente=cli,
            local_orig=local_outra_empresa,
            empresa=outra_empresa)

        response = self.client.get(reverse('vendas:listapedidovendaview'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pedido_outra_empresa in response.context['all_pedidos'])

    def test_list_pedido_venda_modo_grupo_exibe_filial_para_matriz(self):
        matriz, filial, cliente, _local_matriz, local_filial = configurar_grupo_empresarial(self)
        Group.objects.get_or_create(name='gestor_matriz')
        self.user.groups.add(Group.objects.get(name='gestor_matriz'))
        pedido_filial = PedidoVenda.objects.create(
            cliente=cliente,
            local_orig=local_filial,
            empresa=filial)

        response = self.client.get(
            reverse('vendas:listapedidovendaview'),
            {'modo': 'grupo'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['modo_venda'], 'grupo')
        self.assertTrue(pedido_filial in response.context['all_pedidos'])
        self.assertEqual(response.context['empresa_ativa'], matriz)

    def test_list_orcamento_venda_modo_grupo_exibe_filial_para_matriz(self):
        _matriz, filial, cliente, _local_matriz, local_filial = configurar_grupo_empresarial(self)
        Group.objects.get_or_create(name='gestor_matriz')
        self.user.groups.add(Group.objects.get(name='gestor_matriz'))
        orcamento_filial = OrcamentoVenda.objects.create(
            cliente=cliente,
            local_orig=local_filial,
            empresa=filial)

        response = self.client.get(
            reverse('vendas:listaorcamentovendaview'),
            {'modo': 'grupo'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['modo_venda'], 'grupo')
        self.assertTrue(orcamento_filial in response.context['all_orcamentos'])

    def test_list_pedido_venda_paginated(self):
        cli = Cliente.objects.order_by('id').last()
        for _indice in range(105):
            PedidoVenda.objects.create(
                cliente=cli,
                empresa=self.empresa_ativa)

        response = self.client.get(reverse('vendas:listapedidovendaview'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['all_pedidos']), 100)


class VendasEditarViewsTestCase(BaseTestCase):

    def test_edit_orcamento_venda_get_post_request(self):
        # Buscar objeto qualquer
        obj = OrcamentoVenda.objects.order_by('pk').last()
        url = reverse('vendas:editarorcamentovendaview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data.update(VENDA_FORMSET_DATA)
        data.update(response.context['produtos_form'].initial[0])
        data['observacoes'] = 'Orçamento editado.'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/orcamento_venda/orcamento_venda_list.html')

    def test_edit_pedido_venda_get_post_request(self):
        # Buscar objeto qualquer
        obj = PedidoVenda.objects.order_by('pk').last()
        url = reverse('vendas:editarpedidovendaview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data.update(VENDA_FORMSET_DATA)
        data.update(response.context['produtos_form'].initial[0])
        data['observacoes'] = 'Pedido editado.'
        if data['orcamento'] is None:
            data['orcamento'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/pedido_venda/pedido_venda_list.html')

    def test_edit_condicao_pagamento_get_post_request(self):
        # Buscar objeto qualquer
        obj = CondicaoPagamento.objects.order_by('pk').last()
        url = reverse('vendas:editarcondicaopagamentoview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data['descricao'] = 'Condição de pagamento editada'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)


class VendasAjaxRequestViewsTestCase(BaseTestCase):

    def test_info_condicao_pagamento_post_request(self):
        # Buscar objeto qualquer
        obj = CondicaoPagamento.objects.order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('vendas:infocondpagamento')
        data = {'pagamentoId': obj_pk}
        self.check_json_response(
            url, data, obj_pk, model='vendas.condicaopagamento')

    def test_info_venda_post_request(self):
        # Buscar objeto qualquer
        obj = PedidoVenda.objects.order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('vendas:infovenda')
        data = {'vendaId': obj_pk}
        self.check_json_response(url, data, obj_pk, model='vendas.pedidovenda')

    def test_info_venda_nao_retorna_pedido_outra_empresa(self):
        cli = Cliente.objects.order_by('id').last()
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Ajax Vendas', tipo_pessoa='PJ')
        local_outra_empresa = LocalEstoque.objects.create(
            descricao='Local Ajax Vendas', empresa=outra_empresa)
        pedido_outra_empresa = PedidoVenda.objects.create(
            cliente=cli,
            local_orig=local_outra_empresa,
            empresa=outra_empresa)

        response = self.client.post(
            reverse('vendas:infovenda'),
            {'vendaId': pedido_outra_empresa.pk},
            follow=True)
        self.assertEqual(response.status_code, 404)

    def test_info_venda_retorna_cfop_da_empresa_ativa(self):
        cliente = Cliente.objects.filter(
            empresa_relacionada=self.empresa_ativa).order_by('id').last()
        pedido = PedidoVenda.objects.create(
            cliente=cliente,
            local_orig=LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID),
            empresa=self.empresa_ativa)
        produto = Produto.objects.create(
            codigo='VENDA-CFOP-1',
            descricao='Produto Venda CFOP',
            venda='100.00',
        )
        cfop_empresa = NaturezaOperacao.objects.create(
            empresa=self.empresa_ativa, cfop='6108')
        ProdutoEmpresa.objects.create(
            produto=produto,
            empresa=self.empresa_ativa,
            venda='110.00',
            cfop_padrao=cfop_empresa,
        )
        pedido.itens_venda.create(
            produto=produto,
            quantidade='1.00',
            valor_unit='110.00',
            subtotal='110.00',
            desconto='0.00',
            tipo_desconto='0',
        )

        response = self.client.post(reverse('vendas:infovenda'), {
            'vendaId': pedido.pk,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode('utf-8'))
        item_payload = next(item for item in payload if item['model'] == 'vendas.itensvenda')
        self.assertEqual(item_payload['hidden_fields']['cfop'], '6108')


class VendasAcoesUsuarioViewsTestCase(BaseTestCase):

    def test_gerar_pdf_orcamento_venda(self):
        # Buscar objeto qualquer
        obj = OrcamentoVenda.objects.order_by('pk').last()
        url = reverse('vendas:gerarpdforcamentovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')

    def test_gerar_pdf_pedido_venda(self):
        # Buscar objeto qualquer
        obj = PedidoVenda.objects.order_by('pk').last()
        url = reverse('vendas:gerarpdfpedidovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')

    def test_gerar_pedido_venda(self):
        # Criar novo orcamento e gerar pedido
        cli = Cliente.objects.order_by('id').last()
        obj = OrcamentoVenda.objects.create(
            cliente=cli, empresa=self.empresa_ativa)
        url = reverse('vendas:gerarpedidovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/pedido_venda/pedido_venda_edit.html')
        self.assertTrue(isinstance(response.context['object'], PedidoVenda))
        self.assertEqual(response.context['object'].orcamento.pk, obj.pk)

    def test_copiar_pedido_venda(self):
        # Buscar objeto qualquer
        obj = PedidoVenda.objects.order_by('pk').last()
        url = reverse('vendas:copiarpedidovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/pedido_venda/pedido_venda_edit.html')
        self.assertTrue(isinstance(response.context['object'], PedidoVenda))

    def test_copiar_orcamento_venda(self):
        # Buscar objeto qualquer
        obj = OrcamentoVenda.objects.order_by('pk').last()
        url = reverse('vendas:copiarorcamentovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/orcamento_venda/orcamento_venda_edit.html')
        self.assertTrue(isinstance(response.context['object'], OrcamentoVenda))

    def test_cancelar_pedido_venda(self):
        # Buscar objeto qualquer
        obj = PedidoVenda.objects.order_by('pk').last()
        url = reverse('vendas:cancelarpedidovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/pedido_venda/pedido_venda_edit.html')
        self.assertTrue(isinstance(response.context['object'], PedidoVenda))
        self.assertEqual(response.context[
                         'object'].get_status_display(), 'Cancelado')

    def test_cancelar_orcamento_venda(self):
        # Buscar objeto qualquer
        obj = OrcamentoVenda.objects.order_by('pk').last()
        url = reverse('vendas:cancelarorcamentovenda',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'vendas/orcamento_venda/orcamento_venda_edit.html')
        self.assertTrue(isinstance(response.context['object'], OrcamentoVenda))
        self.assertEqual(response.context[
                         'object'].get_status_display(), 'Cancelado')
