# -*- coding: utf-8 -*-

from djangosige.tests.test_case import BaseTestCase, replace_none_values_in_dictionary
from django.contrib.auth.models import Group
from djangosige.apps.cadastro.models import Empresa, Fornecedor, Produto, MinhaEmpresa, UsuarioEmpresa
from djangosige.apps.compras.models import OrcamentoCompra, PedidoCompra, ItensCompra
from djangosige.apps.estoque.models import LocalEstoque, ProdutoEstocado, DEFAULT_LOCAL_ID
from django.urls import reverse

from datetime import datetime, timedelta

COMPRA_FORMSET_DATA = {
    'produtos_form-0-produto': 1,
    'produtos_form-0-quantidade': 2,
    'produtos_form-0-valor_unit': '100,00',
    'produtos_form-0-tipo_desconto': '0',
    'produtos_form-0-desconto': '20,00',
    'produtos_form-0-subtotal': '180,00',
    'produtos_form-1-produto': 2,
    'produtos_form-1-quantidade': 3,
    'produtos_form-1-valor_unit': '100,00',
    'produtos_form-1-tipo_desconto': '0',
    'produtos_form-1-desconto': '20,00',
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
        nome_razao_social='Matriz Compras',
        tipo_pessoa='PJ',
        tipo_empresa=Empresa.TIPO_MATRIZ)
    filial = Empresa.objects.create(
        nome_razao_social='Filial Compras',
        tipo_pessoa='PJ',
        tipo_empresa=Empresa.TIPO_FILIAL,
        empresa_pai=matriz)
    fornecedor_matriz = Fornecedor.objects.create(
        nome_razao_social='Fornecedor Matriz Compras',
        tipo_pessoa='PJ',
        empresa_relacionada=matriz)
    local_matriz = LocalEstoque.objects.create(
        descricao='Local Matriz Compras', empresa=matriz)
    local_filial = LocalEstoque.objects.create(
        descricao='Local Filial Compras', empresa=filial)
    UsuarioEmpresa.objects.get_or_create(
        m_usuario=test_case.usuario, m_empresa=matriz)
    UsuarioEmpresa.objects.get_or_create(
        m_usuario=test_case.usuario, m_empresa=filial)
    MinhaEmpresa.objects.filter(m_usuario=test_case.usuario).update(m_empresa=matriz)
    return matriz, filial, fornecedor_matriz, local_matriz, local_filial


class ComprasAdicionarViewsTestCase(BaseTestCase):

    def test_add_orcamento_compra_view_get_request(self):
        url = reverse('compras:addorcamentocompraview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_pedido_compra_view_get_request(self):
        url = reverse('compras:addpedidocompraview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_orcamento_compra_view_post_request(self):
        url = reverse('compras:addorcamentocompraview')
        fornecedor = Fornecedor.objects.order_by('id').last()
        local_dest = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        data = {
            'data_emissao': '16/07/2017',
            'fornecedor': fornecedor.pk,
            'status': '0',
            'tipo_desconto': '0',
            'desconto': '40,00',
            'frete': '0,00',
            'seguro': '0,00',
            'despesas': '0,00',
            'mod_frete': '0',
            'total_icms': '0,00',
            'total_ipi': '0,00',
            'valor_total': '460,00',
            'local_dest': local_dest.pk,
        }

        data.update(COMPRA_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/orcamento_compra/orcamento_compra_list.html')

        # Assert form invalido
        data['fornecedor'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['fornecedor'],
            ['Este campo é obrigatório.'])

    def test_add_pedido_compra_view_post_request(self):
        url = reverse('compras:addpedidocompraview')
        fornecedor = Fornecedor.objects.order_by('id').last()
        local_dest = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        data = {
            'data_emissao': '16/07/2017',
            'fornecedor': fornecedor.pk,
            'status': '0',
            'tipo_desconto': '0',
            'desconto': '40,00',
            'frete': '0,00',
            'seguro': '0,00',
            'despesas': '0,00',
            'mod_frete': '0',
            'total_icms': '0,00',
            'total_ipi': '0,00',
            'valor_total': '460,00',
            'local_dest': local_dest.pk,
        }

        data.update(COMPRA_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/pedido_compra/pedido_compra_list.html')

        # Assert form invalido
        data['fornecedor'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(
            response.context_data['form'].errors['fornecedor'],
            ['Este campo é obrigatório.'])


    def test_add_pedido_compra_centralizada_para_filial(self):
        url = reverse('compras:addpedidocompraview')
        matriz, filial, fornecedor, _local_matriz, local_filial = configurar_grupo_empresarial(self)

        data = {
            'data_emissao': '16/07/2017',
            'fornecedor': fornecedor.pk,
            'status': '0',
            'tipo_desconto': '0',
            'desconto': '40,00',
            'frete': '0,00',
            'seguro': '0,00',
            'despesas': '0,00',
            'mod_frete': '0',
            'empresa_destino': filial.pk,
            'total_icms': '0,00',
            'total_ipi': '0,00',
            'valor_total': '460,00',
            'local_dest': local_filial.pk,
        }

        data.update(COMPRA_FORMSET_DATA)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        pedido = PedidoCompra.objects.order_by('pk').last()
        self.assertEqual(pedido.empresa, matriz)
        self.assertEqual(pedido.empresa_destino, filial)
        self.assertEqual(pedido.local_dest, local_filial)


class ComprasListarViewsTestCase(BaseTestCase):

    def test_list_orcamento_compra_view_deletar_objeto(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = OrcamentoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'compras:listaorcamentocompraview'), deleted_object=obj)

    def test_list_orcamento_compra_vencido_view_deletar_objeto(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = OrcamentoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa,
            data_vencimento=datetime.now().date() - timedelta(days=1))
        self.check_list_view_delete(url=reverse(
            'compras:listaorcamentocompravencidosview'), deleted_object=obj)

    def test_list_orcamento_compra_vence_hoje_view_deletar_objeto(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = OrcamentoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa,
            data_vencimento=datetime.now().date())
        self.check_list_view_delete(url=reverse(
            'compras:listaorcamentocomprahojeview'), deleted_object=obj)

    def test_list_pedido_compra_view_deletar_objeto(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = PedidoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa)
        self.check_list_view_delete(url=reverse(
            'compras:listapedidocompraview'), deleted_object=obj)

    def test_list_pedido_compra_atrasado_view_deletar_objeto(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = PedidoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa,
            data_entrega=datetime.now().date() - timedelta(days=1))
        self.check_list_view_delete(url=reverse(
            'compras:listapedidocompraatrasadosview'), deleted_object=obj)

    def test_list_pedido_compra_entrega_hoje_view_deletar_objeto(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = PedidoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa,
            data_entrega=datetime.now().date())
        self.check_list_view_delete(url=reverse(
            'compras:listapedidocomprahojeview'), deleted_object=obj)

    def test_list_pedido_compra_nao_exibe_outra_empresa(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Compras', tipo_pessoa='PJ')
        local_outra_empresa = LocalEstoque.objects.create(
            descricao='Local Compras Outra Empresa', empresa=outra_empresa)
        pedido_outra_empresa = PedidoCompra.objects.create(
            fornecedor=fornecedor,
            local_dest=local_outra_empresa,
            empresa=outra_empresa)

        response = self.client.get(reverse('compras:listapedidocompraview'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pedido_outra_empresa in response.context['all_pedidos'])

    def test_list_pedido_compra_modo_grupo_exibe_filial_para_matriz(self):
        matriz, filial, fornecedor, _local_matriz, local_filial = configurar_grupo_empresarial(self)
        Group.objects.get_or_create(name='gestor_matriz')
        self.user.groups.add(Group.objects.get(name='gestor_matriz'))
        pedido_filial = PedidoCompra.objects.create(
            fornecedor=fornecedor,
            local_dest=local_filial,
            empresa=filial,
            empresa_destino=filial)

        response = self.client.get(
            reverse('compras:listapedidocompraview'),
            {'modo': 'grupo'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['modo_compra'], 'grupo')
        self.assertTrue(pedido_filial in response.context['all_pedidos'])
        self.assertEqual(response.context['empresa_ativa'], matriz)

    def test_list_orcamento_compra_modo_grupo_exibe_filial_para_matriz(self):
        _matriz, filial, fornecedor, _local_matriz, local_filial = configurar_grupo_empresarial(self)
        Group.objects.get_or_create(name='gestor_matriz')
        self.user.groups.add(Group.objects.get(name='gestor_matriz'))
        orcamento_filial = OrcamentoCompra.objects.create(
            fornecedor=fornecedor,
            local_dest=local_filial,
            empresa=filial,
            empresa_destino=filial)

        response = self.client.get(
            reverse('compras:listaorcamentocompraview'),
            {'modo': 'grupo'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['modo_compra'], 'grupo')
        self.assertTrue(orcamento_filial in response.context['all_orcamentos'])


class ComprasEditarViewsTestCase(BaseTestCase):

    def test_edit_orcamento_compra_get_post_request(self):
        # Buscar objeto qualquer
        obj = OrcamentoCompra.objects.order_by('pk').last()
        url = reverse('compras:editarorcamentocompraview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data.update(COMPRA_FORMSET_DATA)
        data.update(response.context['produtos_form'].initial[0])
        data['observacoes'] = 'Orçamento editado.'
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/orcamento_compra/orcamento_compra_list.html')

    def test_edit_pedido_compra_get_post_request(self):
        # Buscar objeto qualquer
        obj = PedidoCompra.objects.order_by('pk').last()
        url = reverse('compras:editarpedidocompraview',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data.update(COMPRA_FORMSET_DATA)
        data.update(response.context['produtos_form'].initial[0])
        replace_none_values_in_dictionary(data)
        data['observacoes'] = 'Pedido editado.'
        if data['orcamento'] is None:
            data['orcamento'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/pedido_compra/pedido_compra_list.html')


class VendasAjaxRequestViewsTestCase(BaseTestCase):

    def test_info_compra_post_request(self):
        # Buscar objeto qualquer
        obj = PedidoCompra.objects.order_by('pk').last()
        obj_pk = obj.pk
        url = reverse('compras:infocompra')
        data = {'compraId': obj_pk}
        self.check_json_response(
            url, data, obj_pk, model='compras.pedidocompra')

    def test_info_compra_nao_retorna_pedido_outra_empresa(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Ajax Compras', tipo_pessoa='PJ')
        local_outra_empresa = LocalEstoque.objects.create(
            descricao='Local Ajax Compras', empresa=outra_empresa)
        pedido_outra_empresa = PedidoCompra.objects.create(
            fornecedor=fornecedor,
            local_dest=local_outra_empresa,
            empresa=outra_empresa)

        response = self.client.post(
            reverse('compras:infocompra'),
            {'compraId': pedido_outra_empresa.pk},
            follow=True)
        self.assertEqual(response.status_code, 404)


class ComprasAcoesUsuarioViewsTestCase(BaseTestCase):

    def test_gerar_pdf_orcamento_compra(self):
        # Buscar objeto qualquer
        obj = OrcamentoCompra.objects.order_by('pk').last()
        url = reverse('compras:gerarpdforcamentocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')

    def test_gerar_pdf_pedido_compra(self):
        # Buscar objeto qualquer
        obj = PedidoCompra.objects.order_by('pk').last()
        url = reverse('compras:gerarpdfpedidocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')

    def test_gerar_pedido_compra(self):
        # Criar novo orcamento e gerar pedido
        fornecedor = Fornecedor.objects.order_by('id').last()
        obj = OrcamentoCompra.objects.create(
            fornecedor=fornecedor, empresa=self.empresa_ativa)
        url = reverse('compras:gerarpedidocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/pedido_compra/pedido_compra_edit.html')
        self.assertTrue(isinstance(response.context['object'], PedidoCompra))
        self.assertEqual(response.context['object'].orcamento.pk, obj.pk)

    def test_copiar_pedido_compra(self):
        # Buscar objeto qualquer
        obj = PedidoCompra.objects.order_by('pk').last()
        url = reverse('compras:copiarpedidocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/pedido_compra/pedido_compra_edit.html')
        self.assertTrue(isinstance(response.context['object'], PedidoCompra))

    def test_copiar_orcamento_compra(self):
        # Buscar objeto qualquer
        obj = OrcamentoCompra.objects.order_by('pk').last()
        url = reverse('compras:copiarorcamentocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/orcamento_compra/orcamento_compra_edit.html')
        self.assertTrue(isinstance(response.context[
                        'object'], OrcamentoCompra))

    def test_cancelar_pedido_compra(self):
        # Buscar objeto qualquer
        obj = PedidoCompra.objects.order_by('pk').last()
        url = reverse('compras:cancelarpedidocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/pedido_compra/pedido_compra_edit.html')
        self.assertTrue(isinstance(response.context['object'], PedidoCompra))
        self.assertEqual(response.context[
                         'object'].get_status_display(), 'Cancelado')

    def test_cancelar_orcamento_compra(self):
        # Buscar objeto qualquer
        obj = OrcamentoCompra.objects.order_by('pk').last()
        url = reverse('compras:cancelarorcamentocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'compras/orcamento_compra/orcamento_compra_edit.html')
        self.assertTrue(isinstance(response.context[
                        'object'], OrcamentoCompra))
        self.assertEqual(response.context[
                         'object'].get_status_display(), 'Cancelado')

    def test_receber_pedido_compra(self):
        fornecedor = Fornecedor.objects.order_by('id').last()
        local_dest = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)

        # Criar novo pedido de compra
        obj = PedidoCompra(movimentar_estoque=True, fornecedor=fornecedor,
                           local_dest=local_dest, empresa=self.empresa_ativa,
                           data_entrega=datetime.now().date(), status='0')
        obj.save()
        prod1 = Produto(codigo='000000000000111', descricao='Produto Teste Recebimento Pedido Compra 1',
                        controlar_estoque=True, estoque_atual='0.00')
        prod1.save()
        prod2 = Produto(codigo='000000000000222', descricao='Produto Teste Recebimento Pedido Compra 2',
                        controlar_estoque=True, estoque_atual='0.00')
        prod2.save()
        item1 = ItensCompra(produto=prod1, quantidade=3,
                            valor_unit='10.00', subtotal='30.00')
        item1.compra_id = obj
        item1.save()
        item2 = ItensCompra(produto=prod2, quantidade=2,
                            valor_unit='20.00', subtotal='40.00')
        item2.compra_id = obj
        item2.save()
        url = reverse('compras:receberpedidocompra',
                      kwargs={'pk': obj.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Assert que estoque foi movimentado corretamente
        obj.refresh_from_db()
        self.assertEqual(obj.get_status_display(), 'Recebido')
        self.assertEqual(len(obj.entrada_estoque_pedido.all()), 1)
        mvmt_entrada = obj.entrada_estoque_pedido.all()[0]
        for item in mvmt_entrada.itens_movimento.all():
            self.assertTrue(item.produto.pk in [prod1.pk, prod2.pk])
            if item.produto.pk == prod1.pk:
                prod1.refresh_from_db()
                self.assertEqual(item.quantidade, prod1.estoque_atual)
            elif item.produto.pk == prod2.pk:
                prod2.refresh_from_db()
                self.assertEqual(item.quantidade, prod2.estoque_atual)

    def test_receber_pedido_compra_centralizada_movimenta_filial_destino(self):
        matriz, filial, fornecedor, _local_matriz, local_filial = configurar_grupo_empresarial(self)

        obj = PedidoCompra(
            movimentar_estoque=True,
            fornecedor=fornecedor,
            local_dest=local_filial,
            empresa=matriz,
            empresa_destino=filial,
            data_entrega=datetime.now().date(),
            status='0')
        obj.save()
        prod = Produto(
            codigo='000000000000333',
            descricao='Produto Teste Recebimento Centralizado',
            controlar_estoque=True,
            estoque_atual='0.00')
        prod.save()
        item = ItensCompra(
            produto=prod,
            quantidade=4,
            valor_unit='15.00',
            subtotal='60.00')
        item.compra_id = obj
        item.save()

        response = self.client.get(
            reverse('compras:receberpedidocompra', kwargs={'pk': obj.pk}),
            follow=True)
        self.assertEqual(response.status_code, 200)

        obj.refresh_from_db()
        mvmt_entrada = obj.entrada_estoque_pedido.get()
        prod_estocado = ProdutoEstocado.objects.get(local=local_filial, produto=prod)
        self.assertEqual(mvmt_entrada.empresa, filial)
        self.assertEqual(prod_estocado.quantidade, item.quantidade)
