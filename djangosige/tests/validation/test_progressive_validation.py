# -*- coding: utf-8 -*-

from django.db.models import Q
from django.urls import reverse

from djangosige.apps.cadastro.models import Cliente, Empresa, Fornecedor, Transportadora
from djangosige.apps.financeiro.models import Entrada
from djangosige.tests.test_case import BaseTestCase


class ProgressiveEnhancementValidationTestCase(BaseTestCase):

    def test_htmx_info_endpoints_render_html_partials(self):
        client = Cliente.objects.order_by("pk").last()
        fornecedor = Fornecedor.objects.order_by("pk").last()
        empresa = Empresa.objects.order_by("pk").last()
        transportadora = Transportadora.objects.order_by("pk").last()

        specs = (
            (
                "cadastro:infocliente",
                {"pessoaId": client.pk, "panel": "cliente"},
                'id="cliente-info-panel"',
            ),
            (
                "cadastro:infocliente",
                {"pessoaId": client.pk, "panel": "dest"},
                'id="dest-info-panel"',
            ),
            (
                "cadastro:infofornecedor",
                {"pessoaId": fornecedor.pk, "panel": "fornecedor"},
                'id="fornecedor-info-panel"',
            ),
            (
                "cadastro:infofornecedor",
                {"pessoaId": fornecedor.pk, "panel": "emit"},
                'id="emit-info-panel"',
            ),
            (
                "cadastro:infoempresa",
                {"pessoaId": empresa.pk, "panel": "emit"},
                'id="emit-info-panel"',
            ),
            (
                "cadastro:infoempresa",
                {"pessoaId": empresa.pk, "panel": "dest"},
                'id="dest-info-panel"',
            ),
            (
                "cadastro:infotransportadora",
                {"transportadoraId": transportadora.pk},
                'id="veiculo-wrapper"',
            ),
        )

        for url_name, payload, marker in specs:
            with self.subTest(flow=url_name, marker=marker):
                response = self.client.post(
                    reverse(url_name),
                    payload,
                    HTTP_HX_REQUEST="true",
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(marker, response.content.decode("utf-8"))

    def test_htmx_gerar_lancamento_returns_redirect_header(self):
        conta_receber = (
            Entrada.objects.filter(status="1")
            .exclude(Q(data_pagamento__isnull=True) & Q(data_vencimento__isnull=True))
            .order_by("pk")
            .last()
        )
        self.assertIsNotNone(conta_receber)
        data_pagamento = conta_receber.data_pagamento or conta_receber.data_vencimento

        response = self.client.post(
            reverse("financeiro:gerarlancamento"),
            {
                "contaId": conta_receber.pk,
                "tipoConta": "0",
                "dataPagamento": data_pagamento.strftime("%d/%m/%Y"),
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            response["HX-Redirect"],
            reverse("financeiro:editarrecebimentoview", kwargs={"pk": conta_receber.pk}),
        )
