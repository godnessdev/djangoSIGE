# -*- coding: utf-8 -*-

from decimal import Decimal

from djangosige.tests.test_case import BaseTestCase
from django.utils import timezone
from django.urls import resolve, reverse
from djangosige.apps.base.views import IndexView
from djangosige.apps.cadastro.models import Empresa
from djangosige.apps.financeiro.models import MovimentoCaixa
from djangosige.configs import DEBUG


class BaseViewsTestCase(BaseTestCase):

    def test_home_page_resolves(self):
        view = resolve('/')
        self.assertEqual(view.func.__name__,
                         IndexView.as_view().__name__)

    def test_home_page_get_request(self):
        url = reverse('base:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_home_page_ignora_movimento_de_outra_empresa_e_agrega_mesma_data(self):
        hoje = timezone.now().date()
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Outra Empresa Dashboard',
            tipo_pessoa='PJ',
        )
        MovimentoCaixa.objects.create(
            empresa=self.empresa_ativa,
            data_movimento=hoje,
            saldo_inicial=Decimal('100.00'),
            saldo_final=Decimal('150.00'),
            entradas=Decimal('50.00'),
            saidas=Decimal('0.00'),
        )
        MovimentoCaixa.objects.create(
            empresa=self.empresa_ativa,
            data_movimento=hoje,
            saldo_inicial=Decimal('150.00'),
            saldo_final=Decimal('130.00'),
            entradas=Decimal('0.00'),
            saidas=Decimal('20.00'),
        )
        MovimentoCaixa.objects.create(
            empresa=outra_empresa,
            data_movimento=hoje,
            saldo_inicial=Decimal('999.00'),
            saldo_final=Decimal('999.00'),
            entradas=Decimal('999.00'),
            saidas=Decimal('0.00'),
        )

        response = self.client.get(reverse('base:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['movimento_dia'].entradas, Decimal('50.00'))
        self.assertEqual(response.context['movimento_dia'].saidas, Decimal('20.00'))
        self.assertEqual(response.context['movimento_dia'].saldo_final, Decimal('130.00'))

    def test_404_page(self):
        response = self.client.get("/404/")
        self.assertTemplateUsed(response, '404.html')
        self.assertEqual(response.status_code, 404)

    def test_500_page(self):
        response = self.client.get("/500/")
        # Se DEBUG=True temos views personalizadas,
        # caso contrário /500/ retornar 404
        if DEBUG:
            self.assertTemplateUsed(response, '500.html')
            self.assertEqual(response.status_code, 500)
        else:
            self.assertTemplateUsed(response, '404.html')
            self.assertEqual(response.status_code, 404)
