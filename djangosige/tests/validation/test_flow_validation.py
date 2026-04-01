# -*- coding: utf-8 -*-

import json
import locale
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from djangosige.apps.cadastro.models import (
    Categoria,
    Cliente,
    Empresa,
    Fornecedor,
    Marca,
    Produto,
    Transportadora,
    Unidade,
)
from djangosige.apps.compras.models import ItensCompra, OrcamentoCompra, PedidoCompra
from djangosige.apps.estoque.models import DEFAULT_LOCAL_ID, EntradaEstoque, LocalEstoque, SaidaEstoque, TransferenciaEstoque
from djangosige.apps.financeiro.models import Entrada, PlanoContasGrupo, Saida
from djangosige.apps.fiscal.models import GrupoFiscal, NaturezaOperacao, NotaFiscalEntrada, NotaFiscalSaida
from djangosige.apps.login.models import Usuario
from djangosige.apps.vendas.models import CondicaoPagamento, OrcamentoVenda, PedidoVenda
from djangosige.tests.cadastro.test_views import INLINE_FORMSET_DATA
from djangosige.tests.compras.test_views import COMPRA_FORMSET_DATA
from djangosige.tests.estoque.test_views import MOVIMENTO_ESTOQUE_FORMSET_DATA
from djangosige.tests.fiscal.test_views import AUT_XML_FORMSET_DATA
from djangosige.tests.financeiro.test_views import SUBGRUPO_PLANO_CONTAS_FORMSET_DATA
from djangosige.tests.test_case import (
    BaseTestCase,
    TEST_PASSWORD,
    TEST_USERNAME,
    replace_none_values_in_dictionary,
)
from djangosige.tests.vendas.test_views import VENDA_FORMSET_DATA

try:
    locale.setlocale(locale.LC_ALL, "pt_BR.utf8")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "")


class LoginOperationalValidationTestCase(BaseTestCase):

    def test_login_profile_and_user_management_flows(self):
        login_url = reverse("login:loginview")
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 302)

        self.client.logout()
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login/login.html")

        response = self.client.post(
            login_url,
            {"username": TEST_USERNAME, "password": TEST_PASSWORD},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/index.html")

        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        register_url = reverse("login:registrarview")
        response = self.client.post(
            register_url,
            {
                "username": "validation-user",
                "password": "validation-pass-123",
                "confirm": "validation-pass-123",
                "email": "validation-user@email.com",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="validation-user").exists())

        profile_edit_url = reverse("login:editarperfilview")
        empresa = Empresa.objects.create()
        usuario = Usuario.objects.get(user=self.user)
        response = self.client.get(profile_edit_url)
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        data["username"] = response.context["user"].username
        data["first_name"] = response.context["user"].first_name
        data["last_name"] = response.context["user"].last_name
        data["email"] = response.context["user"].email
        data["m_empresa_form-m_empresa"] = empresa.pk
        response = self.client.post(profile_edit_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login/perfil.html")
        self.assertEqual(usuario.empresa_usuario.all()[0].m_empresa.pk, empresa.pk)

        select_company_url = reverse("login:selecionarempresaview")
        outra_empresa = Empresa.objects.filter(~Q(id=empresa.pk)).first() or Empresa.objects.create()
        response = self.client.post(
            select_company_url,
            {"m_empresa": outra_empresa.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario.empresa_usuario.all()[0].m_empresa.pk, outra_empresa.pk)

        users_url = reverse("login:usuariosview")
        new_user = User.objects.create(username="delete-validation-user")
        response = self.client.get(users_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login/lista_users.html")
        self.assertTrue(new_user in response.context["object_list"])

        detail_url = reverse("login:usuariodetailview", kwargs={"pk": self.user.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login/detalhe_users.html")

        delete_url = reverse("login:deletarusuarioview", kwargs={"pk": new_user.pk})
        response = self.client.post(delete_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=new_user.pk).exists())


class CadastroOperationalValidationTestCase(BaseTestCase):

    def test_cadastro_add_and_ajax_flows(self):
        pessoa_specs = (
            ("empresa", Empresa, {"empresa_form-nome_razao_social": "Empresa Validacao", "empresa_form-tipo_pessoa": "PJ", "empresa_form-inscricao_municipal": "", "empresa_form-informacoes_adicionais": ""}),
            ("cliente", Cliente, {"cliente_form-nome_razao_social": "Cliente Validacao", "cliente_form-tipo_pessoa": "PJ", "cliente_form-inscricao_municipal": "", "cliente_form-informacoes_adicionais": "", "cliente_form-limite_de_credito": "0.00", "cliente_form-indicador_ie": "1", "cliente_form-id_estrangeiro": ""}),
            ("fornecedor", Fornecedor, {"fornecedor_form-nome_razao_social": "Fornecedor Validacao", "fornecedor_form-tipo_pessoa": "PJ", "fornecedor_form-inscricao_municipal": "", "fornecedor_form-informacoes_adicionais": ""}),
            ("transportadora", Transportadora, {"transportadora_form-nome_razao_social": "Transportadora Validacao", "transportadora_form-tipo_pessoa": "PJ", "transportadora_form-inscricao_municipal": "", "transportadora_form-informacoes_adicionais": "", "veiculo_form-TOTAL_FORMS": 1, "veiculo_form-INITIAL_FORMS": 0, "veiculo_form-0-descricao": "Veiculo Validacao", "veiculo_form-0-placa": "ZZZ0000", "veiculo_form-0-uf": "SP"}),
        )

        for model_name, model, data in pessoa_specs:
            with self.subTest(flow=f"add_{model_name}"):
                payload = {}
                payload.update(INLINE_FORMSET_DATA)
                payload.update(data)
                response = self.client.post(reverse(f"cadastro:add{model_name}view"), payload, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(model.objects.filter(nome_razao_social__icontains="Validacao").exists())

        response = self.client.post(
            reverse("cadastro:addprodutoview"),
            {
                "codigo": "000000000009999",
                "descricao": "Produto Validacao",
                "origem": "0",
                "venda": "100,00",
                "custo": "50,00",
                "estoque_minimo": "10,00",
                "estoque_atual": "50,00",
                "ncm": "02109100[EX:01]",
                "fornecedor": Fornecedor.objects.order_by("id").last().pk,
                "local_dest": LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID).pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cadastro/produto/produto_list.html")

        ajax_specs = (
            ("cadastro:infoempresa", {"pessoaId": Empresa.objects.order_by("pk").last().pk}),
            ("cadastro:infocliente", {"pessoaId": Cliente.objects.order_by("pk").last().pk}),
            ("cadastro:infofornecedor", {"pessoaId": Fornecedor.objects.order_by("pk").last().pk}),
            ("cadastro:infotransportadora", {"transportadoraId": Transportadora.objects.order_by("pk").last().pk}),
            ("cadastro:infoproduto", {"produtoId": Produto.objects.order_by("pk").last().pk}),
        )
        for url_name, payload in ajax_specs:
            with self.subTest(flow=url_name):
                response = self.client.post(reverse(url_name), payload, follow=True)
                self.assertEqual(response.status_code, 200)
                content = json.loads(response.content.decode("utf-8"))
                self.assertTrue(len(content) >= 1)

    def test_cadastro_edit_flows_with_pk(self):
        person_models = (Empresa, Cliente, Fornecedor, Transportadora)
        for model in person_models:
            obj = model.objects.order_by("pk").last()
            model_name = model.__name__.lower()
            with self.subTest(flow=f"edit_{model_name}"):
                url = reverse(f"cadastro:editar{model_name}view", kwargs={"pk": obj.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                data = response.context["form"].initial
                if model_name == "cliente":
                    data[f"{response.context['form'].prefix}-limite_de_credito"] = data["limite_de_credito"]
                    del data["limite_de_credito"]
                elif model_name == "transportadora":
                    data["veiculo_form-TOTAL_FORMS"] = 1
                    data["veiculo_form-INITIAL_FORMS"] = 0
                    data["veiculo_form-0-descricao"] = "Veiculo Editado"
                    data["veiculo_form-0-placa"] = "YYY0000"
                    data["veiculo_form-0-uf"] = "SP"
                data["informacoes_adicionais"] = "Editado na validacao."
                data.update(INLINE_FORMSET_DATA)
                response = self.client.post(url, data, follow=True)
                self.assertEqual(response.status_code, 200)

        simple_specs = (
            (Produto.objects.order_by("pk").last(), "cadastro:editarprodutoview", {"inf_adicionais": "Produto validado"}),
            (Categoria.objects.order_by("pk").last(), "cadastro:editarcategoriaview", {"categoria_desc": "Categoria Validada"}),
            (Marca.objects.order_by("pk").last(), "cadastro:editarmarcaview", {"marca_desc": "Marca Validada"}),
            (Unidade.objects.order_by("pk").last(), "cadastro:editarunidadeview", {"unidade_desc": "Unidade Validada"}),
        )
        for obj, url_name, updates in simple_specs:
            with self.subTest(flow=url_name):
                url = reverse(url_name, kwargs={"pk": obj.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                data = response.context["form"].initial
                replace_none_values_in_dictionary(data)
                data.update(updates)
                response = self.client.post(url, data, follow=True)
                self.assertEqual(response.status_code, 200)


class VendasOperationalValidationTestCase(BaseTestCase):

    def test_vendas_add_edit_ajax_and_action_flows(self):
        cli = Cliente.objects.order_by("id").last()
        local_orig = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)
        venda_payload = {
            "data_emissao": "16/07/2017",
            "cliente": cli.pk,
            "status": "0",
            "tipo_desconto": "0",
            "desconto": "40,00",
            "frete": "0,00",
            "seguro": "0,00",
            "despesas": "0,00",
            "mod_frete": "0",
            "impostos": "0,00",
            "valor_total": "460,00",
            "local_orig": local_orig.pk,
        }

        for url_name, template_name in (
            ("vendas:addorcamentovendaview", "vendas/orcamento_venda/orcamento_venda_list.html"),
            ("vendas:addpedidovendaview", "vendas/pedido_venda/pedido_venda_list.html"),
        ):
            with self.subTest(flow=url_name):
                payload = dict(venda_payload)
                payload.update(VENDA_FORMSET_DATA)
                response = self.client.post(reverse(url_name), payload, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template_name)

        response = self.client.post(
            reverse("vendas:addcondicaopagamentoview"),
            {
                "descricao": "Condicao Validacao",
                "forma": "99",
                "n_parcelas": 6,
                "dias_recorrencia": 30,
                "parcela_inicial": 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "vendas/pagamento/condicao_pagamento_list.html")

        edit_specs = (
            ("vendas:editarorcamentovendaview", OrcamentoVenda.objects.order_by("pk").last(), "vendas/orcamento_venda/orcamento_venda_list.html"),
            ("vendas:editarpedidovendaview", PedidoVenda.objects.order_by("pk").last(), "vendas/pedido_venda/pedido_venda_list.html"),
        )
        for url_name, obj, template_name in edit_specs:
            with self.subTest(flow=url_name):
                url = reverse(url_name, kwargs={"pk": obj.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                data = response.context["form"].initial
                replace_none_values_in_dictionary(data)
                data.update(VENDA_FORMSET_DATA)
                data.update(response.context["produtos_form"].initial[0])
                data["observacoes"] = "Fluxo de validacao"
                if "orcamento" in data and data["orcamento"] is None:
                    data["orcamento"] = ""
                response = self.client.post(url, data, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template_name)

        condicao = CondicaoPagamento.objects.order_by("pk").last()
        response = self.client.get(reverse("vendas:editarcondicaopagamentoview", kwargs={"pk": condicao.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        data["descricao"] = "Condicao Validacao Editada"
        response = self.client.post(reverse("vendas:editarcondicaopagamentoview", kwargs={"pk": condicao.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        for url_name, payload in (
            ("vendas:infocondpagamento", {"pagamentoId": condicao.pk}),
            ("vendas:infovenda", {"vendaId": PedidoVenda.objects.order_by("pk").last().pk}),
        ):
            with self.subTest(flow=url_name):
                response = self.client.post(reverse(url_name), payload, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(len(json.loads(response.content.decode("utf-8"))) >= 1)

        for url_name, obj in (
            ("vendas:gerarpdforcamentovenda", OrcamentoVenda.objects.order_by("pk").last()),
            ("vendas:gerarpdfpedidovenda", PedidoVenda.objects.order_by("pk").last()),
        ):
            with self.subTest(flow=url_name):
                response = self.client.get(reverse(url_name, kwargs={"pk": obj.pk}))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get("Content-Type"), "application/pdf")

        action_specs = (
            ("vendas:gerarpedidovenda", OrcamentoVenda.objects.create(cliente=cli), "vendas/pedido_venda/pedido_venda_edit.html"),
            ("vendas:copiarpedidovenda", PedidoVenda.objects.order_by("pk").last(), "vendas/pedido_venda/pedido_venda_edit.html"),
            ("vendas:copiarorcamentovenda", OrcamentoVenda.objects.order_by("pk").last(), "vendas/orcamento_venda/orcamento_venda_edit.html"),
            ("vendas:cancelarpedidovenda", PedidoVenda.objects.order_by("pk").last(), "vendas/pedido_venda/pedido_venda_edit.html"),
            ("vendas:cancelarorcamentovenda", OrcamentoVenda.objects.order_by("pk").last(), "vendas/orcamento_venda/orcamento_venda_edit.html"),
        )
        for url_name, obj, template_name in action_specs:
            with self.subTest(flow=url_name):
                response = self.client.get(reverse(url_name, kwargs={"pk": obj.pk}), follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template_name)


class ComprasOperationalValidationTestCase(BaseTestCase):

    def test_compras_add_edit_ajax_and_action_flows(self):
        fornecedor = Fornecedor.objects.order_by("id").last()
        local_dest = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)
        compra_payload = {
            "data_emissao": "16/07/2017",
            "fornecedor": fornecedor.pk,
            "status": "0",
            "tipo_desconto": "0",
            "desconto": "40,00",
            "frete": "0,00",
            "seguro": "0,00",
            "despesas": "0,00",
            "mod_frete": "0",
            "total_icms": "0,00",
            "total_ipi": "0,00",
            "valor_total": "460,00",
            "local_dest": local_dest.pk,
        }

        for url_name, template_name in (
            ("compras:addorcamentocompraview", "compras/orcamento_compra/orcamento_compra_list.html"),
            ("compras:addpedidocompraview", "compras/pedido_compra/pedido_compra_list.html"),
        ):
            with self.subTest(flow=url_name):
                payload = dict(compra_payload)
                payload.update(COMPRA_FORMSET_DATA)
                response = self.client.post(reverse(url_name), payload, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template_name)

        edit_specs = (
            ("compras:editarorcamentocompraview", OrcamentoCompra.objects.order_by("pk").last(), "compras/orcamento_compra/orcamento_compra_list.html"),
            ("compras:editarpedidocompraview", PedidoCompra.objects.order_by("pk").last(), "compras/pedido_compra/pedido_compra_list.html"),
        )
        for url_name, obj, template_name in edit_specs:
            with self.subTest(flow=url_name):
                url = reverse(url_name, kwargs={"pk": obj.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                data = response.context["form"].initial
                data.update(COMPRA_FORMSET_DATA)
                data.update(response.context["produtos_form"].initial[0])
                replace_none_values_in_dictionary(data)
                data["observacoes"] = "Fluxo de validacao"
                if "orcamento" in data and data["orcamento"] is None:
                    data["orcamento"] = ""
                response = self.client.post(url, data, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template_name)

        response = self.client.post(
            reverse("compras:infocompra"),
            {"compraId": PedidoCompra.objects.order_by("pk").last().pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(json.loads(response.content.decode("utf-8"))) >= 1)

        for url_name, obj in (
            ("compras:gerarpdforcamentocompra", OrcamentoCompra.objects.order_by("pk").last()),
            ("compras:gerarpdfpedidocompra", PedidoCompra.objects.order_by("pk").last()),
        ):
            with self.subTest(flow=url_name):
                response = self.client.get(reverse(url_name, kwargs={"pk": obj.pk}))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get("Content-Type"), "application/pdf")

        action_specs = (
            ("compras:gerarpedidocompra", OrcamentoCompra.objects.create(fornecedor=fornecedor), "compras/pedido_compra/pedido_compra_edit.html"),
            ("compras:copiarpedidocompra", PedidoCompra.objects.order_by("pk").last(), "compras/pedido_compra/pedido_compra_edit.html"),
            ("compras:copiarorcamentocompra", OrcamentoCompra.objects.order_by("pk").last(), "compras/orcamento_compra/orcamento_compra_edit.html"),
            ("compras:cancelarpedidocompra", PedidoCompra.objects.order_by("pk").last(), "compras/pedido_compra/pedido_compra_edit.html"),
            ("compras:cancelarorcamentocompra", OrcamentoCompra.objects.order_by("pk").last(), "compras/orcamento_compra/orcamento_compra_edit.html"),
        )
        for url_name, obj, template_name in action_specs:
            with self.subTest(flow=url_name):
                response = self.client.get(reverse(url_name, kwargs={"pk": obj.pk}), follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template_name)

        pedido = PedidoCompra.objects.create(
            movimentar_estoque=True,
            fornecedor=fornecedor,
            local_dest=local_dest,
            data_entrega=datetime.now().date(),
            status="0",
        )
        prod1 = Produto.objects.create(codigo="000000000000311", descricao="Produto Validacao Compra 1", controlar_estoque=True, estoque_atual="0.00")
        prod2 = Produto.objects.create(codigo="000000000000322", descricao="Produto Validacao Compra 2", controlar_estoque=True, estoque_atual="0.00")
        item1 = ItensCompra(produto=prod1, quantidade=3, valor_unit="10.00", subtotal="30.00")
        item1.compra_id = pedido
        item1.save()
        item2 = ItensCompra(produto=prod2, quantidade=2, valor_unit="20.00", subtotal="40.00")
        item2.compra_id = pedido
        item2.save()
        response = self.client.get(reverse("compras:receberpedidocompra", kwargs={"pk": pedido.pk}), follow=True)
        self.assertEqual(response.status_code, 200)
        pedido.refresh_from_db()
        self.assertEqual(pedido.get_status_display(), "Recebido")


class FinanceiroOperationalValidationTestCase(BaseTestCase):

    def test_financeiro_flow_validation(self):
        fluxo_url = reverse("financeiro:fluxodecaixaview")
        response = self.client.get(fluxo_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(fluxo_url, {"from": datetime.today().strftime("%d/%m/%Y")})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("financeiro:addgrupoview"),
            {
                "grupo_form-tipo_grupo": "0",
                "grupo_form-descricao": "Grupo Validacao",
                **SUBGRUPO_PLANO_CONTAS_FORMSET_DATA,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "financeiro/plano/plano.html")

        add_specs = (
            ("financeiro:addcontapagarview", {"status": "1", "descricao": "Conta a pagar Validacao", "valor_total": "100,00", "abatimento": "0,00", "juros": "0,00", "valor_liquido": "100,00", "data_vencimento": (datetime.today() + timedelta(days=30)).strftime("%d/%m/%Y"), "movimentar_caixa": True}),
            ("financeiro:addcontareceberview", {"status": "1", "descricao": "Conta a receber Validacao", "valor_total": "100,00", "abatimento": "0,00", "juros": "0,00", "valor_liquido": "100,00", "data_vencimento": (datetime.today() + timedelta(days=31)).strftime("%d/%m/%Y"), "movimentar_caixa": True}),
            ("financeiro:addrecebimentoview", {"status": "0", "descricao": "Recebimento Validacao", "valor_total": "100,00", "abatimento": "0,00", "juros": "0,00", "valor_liquido": "100,00", "data_pagamento": datetime.today().strftime("%d/%m/%Y"), "movimentar_caixa": True}),
            ("financeiro:addpagamentoview", {"status": "0", "descricao": "Pagamento Validacao", "valor_total": "100,00", "abatimento": "0,00", "juros": "0,00", "valor_liquido": "100,00", "data_pagamento": datetime.today().strftime("%d/%m/%Y"), "movimentar_caixa": True}),
        )
        for url_name, payload in add_specs:
            with self.subTest(flow=url_name):
                response = self.client.post(reverse(url_name), payload, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "financeiro/lancamento/lancamento_list.html")

        grupo = PlanoContasGrupo.objects.order_by("pk").last()
        response = self.client.get(reverse("financeiro:editargrupoview", kwargs={"pk": grupo.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        data.update(SUBGRUPO_PLANO_CONTAS_FORMSET_DATA)
        data["descricao"] = "Grupo Validacao Editado"
        response = self.client.post(reverse("financeiro:editargrupoview", kwargs={"pk": grupo.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        conta_pagar = Saida.objects.filter(status="1").order_by("pk").last()
        response = self.client.get(reverse("financeiro:editarcontapagarview", kwargs={"pk": conta_pagar.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        replace_none_values_in_dictionary(data)
        data["descricao"] = "Conta Pagar Validada"
        response = self.client.post(reverse("financeiro:editarcontapagarview", kwargs={"pk": conta_pagar.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        conta_receber = Entrada.objects.filter(status="1").order_by("pk").last()
        response = self.client.get(reverse("financeiro:editarcontareceberview", kwargs={"pk": conta_receber.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        replace_none_values_in_dictionary(data)
        data["descricao"] = "Conta Receber Validada"
        response = self.client.post(reverse("financeiro:editarcontareceberview", kwargs={"pk": conta_receber.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        recebimento = Entrada.objects.filter(status="0", movimentar_caixa=True).exclude(Q(movimento_caixa__isnull=True) | Q(data_pagamento__isnull=True)).order_by("pk").last()
        response = self.client.get(reverse("financeiro:editarrecebimentoview", kwargs={"pk": recebimento.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        replace_none_values_in_dictionary(data)
        data["descricao"] = "Recebimento Validado"
        data["valor_total"] = locale.format_string("%.2f", Decimal(data["valor_total"]) + Decimal("20.00"), 1)
        data["valor_liquido"] = locale.format_string("%.2f", Decimal(data["valor_liquido"]) + Decimal("20.00"), 1)
        response = self.client.post(reverse("financeiro:editarrecebimentoview", kwargs={"pk": recebimento.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        pagamento = Saida.objects.filter(status="0", movimentar_caixa=True).exclude(Q(movimento_caixa__isnull=True) | Q(data_pagamento__isnull=True)).order_by("pk").last()
        response = self.client.get(reverse("financeiro:editarpagamentoview", kwargs={"pk": pagamento.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        replace_none_values_in_dictionary(data)
        data["descricao"] = "Pagamento Validado"
        data["valor_total"] = locale.format_string("%.2f", Decimal(data["valor_total"]) + Decimal("20.00"), 1)
        data["valor_liquido"] = locale.format_string("%.2f", Decimal(data["valor_liquido"]) + Decimal("20.00"), 1)
        response = self.client.post(reverse("financeiro:editarpagamentoview", kwargs={"pk": pagamento.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        conta_receber = Entrada.objects.filter(status="1", movimentar_caixa=True).exclude(Q(movimento_caixa__isnull=True) | (Q(data_pagamento__isnull=True) & Q(data_vencimento__isnull=True))).order_by("pk").last()
        data_pagamento = conta_receber.data_pagamento or conta_receber.data_vencimento
        response = self.client.post(reverse("financeiro:gerarlancamento"), {"contaId": conta_receber.pk, "tipoConta": "0", "dataPagamento": data_pagamento.strftime("%d/%m/%Y")}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode("utf-8"))["url"], reverse("financeiro:editarrecebimentoview", kwargs={"pk": conta_receber.id}))

        conta_pagar = Saida.objects.filter(status="1", movimentar_caixa=True).exclude(Q(movimento_caixa__isnull=True) | (Q(data_pagamento__isnull=True) & Q(data_vencimento__isnull=True))).order_by("pk").last()
        data_pagamento = conta_pagar.data_pagamento or conta_pagar.data_vencimento
        response = self.client.post(reverse("financeiro:gerarlancamento"), {"contaId": conta_pagar.pk, "tipoConta": "1", "dataPagamento": data_pagamento.strftime("%d/%m/%Y")}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode("utf-8"))["url"], reverse("financeiro:editarpagamentoview", kwargs={"pk": conta_pagar.id}))

        for pk in (4, 5, 6):
            response = self.client.get(reverse("financeiro:faturarpedidovenda", kwargs={"pk": pk}), follow=True, HTTP_REFERER=reverse("financeiro:listalancamentoview"))
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("financeiro:faturarpedidocompra", kwargs={"pk": 5}), follow=True, HTTP_REFERER=reverse("financeiro:listalancamentoview"))
        self.assertEqual(response.status_code, 200)


class EstoqueOperationalValidationTestCase(BaseTestCase):

    def test_estoque_consulta_add_detail_and_edit_flows(self):
        consulta_url = reverse("estoque:consultaestoqueview")
        response = self.client.get(consulta_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(consulta_url, {"local": LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID).pk})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(consulta_url, {"produto": Produto.objects.filter(controlar_estoque=True).first().pk})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("estoque:addlocalview"), {"descricao": "Local Validacao"}, follow=True)
        self.assertEqual(response.status_code, 200)

        entrada_payload = {"quantidade_itens": 2, "valor_total": "460,00", "tipo_movimento": "0", "local_dest": LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID).pk}
        entrada_payload.update(MOVIMENTO_ESTOQUE_FORMSET_DATA)
        response = self.client.post(reverse("estoque:addentradaestoqueview"), entrada_payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "estoque/movimento/movimento_estoque_list.html")

        saida_payload = {"quantidade_itens": 2, "valor_total": "460,00", "tipo_movimento": "0", "local_orig": LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID).pk}
        saida_payload.update(MOVIMENTO_ESTOQUE_FORMSET_DATA)
        response = self.client.post(reverse("estoque:addsaidaestoqueview"), saida_payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "estoque/movimento/movimento_estoque_list.html")

        local_1 = LocalEstoque.objects.get(pk=DEFAULT_LOCAL_ID)
        local_2 = LocalEstoque.objects.create(descricao="Local Transferencia Validacao")
        transferencia_payload = {"quantidade_itens": 2, "valor_total": "460,00", "tipo_movimento": "0", "local_estoque_orig": local_1.pk, "local_estoque_dest": local_2.pk}
        transferencia_payload.update(MOVIMENTO_ESTOQUE_FORMSET_DATA)
        response = self.client.post(reverse("estoque:addtransferenciaestoqueview"), transferencia_payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "estoque/movimento/movimento_estoque_list.html")

        for url_name, obj in (
            ("estoque:detalharentradaestoqueview", EntradaEstoque.objects.order_by("pk").last()),
            ("estoque:detalharsaidaestoqueview", SaidaEstoque.objects.order_by("pk").last()),
            ("estoque:detalhartransferenciaestoqueview", TransferenciaEstoque.objects.order_by("pk").last()),
        ):
            with self.subTest(flow=url_name):
                response = self.client.get(reverse(url_name, kwargs={"pk": obj.pk}))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "estoque/movimento/movimento_estoque_detail.html")

        local = LocalEstoque.objects.order_by("pk").last()
        response = self.client.get(reverse("estoque:editarlocalview", kwargs={"pk": local.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        data["descricao"] = "Local Validacao Editado"
        response = self.client.post(reverse("estoque:editarlocalview", kwargs={"pk": local.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)


class FiscalOperationalValidationTestCase(BaseTestCase):

    def test_fiscal_add_edit_and_generation_flows(self):
        response = self.client.post(reverse("fiscal:addnaturezaoperacaoview"), {"cfop": "1116", "descricao": "Natureza Validacao", "tp_operacao": "0", "id_dest": "1"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "fiscal/natureza_operacao/natureza_operacao_list.html")

        response = self.client.post(reverse("fiscal:addgrupofiscalview"), {"descricao": "Grupo Fiscal Validacao", "regime_trib": "1", "icmssn_form-csosn": "102", "icmssn_form-mod_bcst": "4", "icmssn_form-mod_bc": "3", "ipi_form-cst": "02", "ipi_form-tipo_ipi": "0", "pis_form-cst": "07", "cofins_form-cst": "07", "icms_dest_form-p_fcp_dest": "2", "icms_dest_form-p_icms_dest": "18", "icms_dest_form-p_icms_inter": "7.00", "icms_dest_form-p_icms_inter_part": "60.00"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "fiscal/grupo_fiscal/grupo_fiscal_list.html")

        dh_atual = timezone.now().strftime("%d/%m/%Y %H:%M")
        response = self.client.post(reverse("fiscal:addnotafiscalsaidaview"), {"versao": "3.10", "natop": "Natureza Validacao", "indpag": "0", "mod": "55", "serie": "101", "dhemi": dh_atual, "dhsaient": dh_atual, "iddest": "1", "tp_imp": "1", "tp_emis": "1", "tp_amb": "2", "fin_nfe": "1", "ind_final": "0", "ind_pres": "0", "status_nfe": "3", "tpnf": "1", "n_nf_saida": "777777777", **AUT_XML_FORMSET_DATA}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "fiscal/nota_fiscal/nota_fiscal_list.html")

        natureza = NaturezaOperacao.objects.order_by("pk").last()
        response = self.client.get(reverse("fiscal:editarnaturezaoperacaoview", kwargs={"pk": natureza.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        replace_none_values_in_dictionary(data)
        data["descricao"] = "Natureza Validacao Editada"
        response = self.client.post(reverse("fiscal:editarnaturezaoperacaoview", kwargs={"pk": natureza.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        grupo = GrupoFiscal.objects.order_by("pk").last()
        response = self.client.get(reverse("fiscal:editargrupofiscalview", kwargs={"pk": grupo.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        if response.context["icms_form"].initial:
            data["icms_form-mod_bc"] = response.context["icms_form"].initial["mod_bc"]
            data["icms_form-mod_bcst"] = response.context["icms_form"].initial["mod_bcst"]
        elif response.context["icmssn_form"].initial:
            data["icmssn_form-mod_bc"] = response.context["icmssn_form"].initial["mod_bc"]
            data["icmssn_form-mod_bcst"] = response.context["icmssn_form"].initial["mod_bcst"]
        data["ipi_form-tipo_ipi"] = response.context["ipi_form"].initial["tipo_ipi"]
        data["descricao"] = "Grupo Fiscal Validacao Editado"
        response = self.client.post(reverse("fiscal:editargrupofiscalview", kwargs={"pk": grupo.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        nota_saida = NotaFiscalSaida.objects.order_by("pk").last()
        response = self.client.get(reverse("fiscal:editarnotafiscalsaidaview", kwargs={"pk": nota_saida.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        data.update(AUT_XML_FORMSET_DATA)
        data["dhemi"] = timezone.now().strftime("%d/%m/%Y %H:%M")
        data["natop"] = f"{data['natop']} (Validacao)"
        replace_none_values_in_dictionary(data)
        response = self.client.post(reverse("fiscal:editarnotafiscalsaidaview", kwargs={"pk": nota_saida.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        nota_entrada = NotaFiscalEntrada.objects.order_by("pk").last()
        response = self.client.get(reverse("fiscal:editarnotafiscalentradaview", kwargs={"pk": nota_entrada.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.context["form"].initial
        data["dhemi"] = timezone.now().strftime("%d/%m/%Y %H:%M")
        data["natop"] = f"{data['natop']} (Validacao)"
        replace_none_values_in_dictionary(data)
        response = self.client.post(reverse("fiscal:editarnotafiscalentradaview", kwargs={"pk": nota_entrada.pk}), data, follow=True)
        self.assertEqual(response.status_code, 200)

        pedido = PedidoVenda.objects.order_by("pk").last()
        response = self.client.get(reverse("fiscal:gerarnotafiscalsaida", kwargs={"pk": pedido.pk}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.context["object"], NotaFiscalSaida))

        response = self.client.get(reverse("fiscal:configuracaonotafiscal"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "fiscal/nota_fiscal/nota_fiscal_config.html")
