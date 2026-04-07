# -*- coding: utf-8 -*-

import re
from pathlib import Path

from django.test import SimpleTestCase
from django.urls import reverse

from djangosige.tests.test_case import BaseTestCase


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = ROOT / "djangosige" / "templates"


class FrontendTemplateContractTestCase(SimpleTestCase):

    def test_base_template_declares_frontend_shell_contract(self):
        template = (TEMPLATE_ROOT / "base" / "base.html").read_text(encoding="utf-8", errors="ignore")

        self.assertIn("js/vendor/htmx.min.js", template)
        self.assertIn("js/vendor/alpine.min.js", template)
        self.assertIn("js/app-core.js", template)
        self.assertIn("js/admin.js", template)
        self.assertIn("js/progressive-enhancement.js", template)
        self.assertIn("window.SIGE_ASSETS.dataTables", template)
        self.assertIn('id="global-nav-search"', template)
        self.assertIn('id="topbar-quick-create"', template)
        self.assertIn('id="topbar-price-lookup"', template)
        self.assertIn('id="topbar-notifications"', template)
        self.assertIn('id="topbar-user-menu"', template)
        self.assertNotRegex(template, r"<script[^>]+src=\"[^\"]*jquery\.dataTables\.min\.js")

    def test_error_templates_do_not_ship_runtime_javascript(self):
        for template_name in ("404.html", "500.html"):
            with self.subTest(template=template_name):
                template = (TEMPLATE_ROOT / template_name).read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("js/jquery/jquery-3.0.0.min.js", template)
                self.assertNotIn("js/bootstrap/bootstrap.min.js", template)

    def test_search_partial_declares_list_toolbar_contract(self):
        template = (TEMPLATE_ROOT / "base" / "search.html").read_text(encoding="utf-8", errors="ignore")
        self.assertIn('id="search-bar"', template)
        self.assertIn('id="list-toolbar-filters"', template)
        self.assertIn('id="list-status-filter"', template)
        self.assertIn('id="list-summary"', template)


class FrontendRenderContractValidationTestCase(BaseTestCase):

    def test_dashboard_renders_decision_driven_sections(self):
        response = self.client.get(reverse("base:index"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn('id="dashboard-overview"', html)
        self.assertIn('id="dashboard-financial-grid"', html)
        self.assertIn('id="dashboard-chart"', html)
        self.assertIn('id="global-nav-search"', html)
        self.assertIn('id="topbar-price-lookup"', html)
        self.assertIn('id="topbar-notifications"', html)
        self.assertIn("Dashboard operacional", html)
        self.assertIn("Alertas prioritarios", html)

    def test_form_pages_render_shell_without_eager_datatables_script(self):
        form_pages = (
            reverse("cadastro:addclienteview"),
            reverse("financeiro:addcontapagarview"),
            reverse("fiscal:addnotafiscalsaidaview"),
        )

        for path in form_pages:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode("utf-8")
                self.assertIn("js/vendor/htmx.min.js", html)
                self.assertIn("js/vendor/alpine.min.js", html)
                self.assertIn("window.SIGE_ASSETS.dataTables", html)
                self.assertNotRegex(html, r"<script[^>]+src=\"[^\"]*jquery\.dataTables\.min\.js")

    def test_list_pages_keep_table_contract_markers(self):
        list_pages = (
            reverse("cadastro:listaclientesview"),
            reverse("vendas:listapedidovendaview"),
            reverse("financeiro:listalancamentoview"),
        )

        for path in list_pages:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode("utf-8")
                self.assertIn('id="lista-database"', html)
                self.assertIn('id="search-bar"', html)
                self.assertIn('id="list-toolbar-filters"', html)
                self.assertIn('id="list-summary"', html)
                self.assertIn("window.SIGE_ASSETS.dataTables", html)

    def test_tabs_and_modal_contract_markers_are_present(self):
        pessoa_response = self.client.get(reverse("cadastro:addclienteview"))
        self.assertEqual(pessoa_response.status_code, 200)
        pessoa_html = pessoa_response.content.decode("utf-8")
        self.assertIn('href="#tab_banco"', pessoa_html)
        self.assertIn('id="tab_banco"', pessoa_html)
        self.assertIn('class="input-group-addon js-cnpj-lookup"', pessoa_html)
        self.assertIn(reverse("cadastro:consultacnpj"), pessoa_html)

        fiscal_response = self.client.get(reverse("fiscal:addnotafiscalsaidaview"))
        self.assertEqual(fiscal_response.status_code, 200)
        fiscal_html = fiscal_response.content.decode("utf-8")
        self.assertIn('href="#tab_inf_ad"', fiscal_html)
        self.assertIn('id="tab_inf_ad"', fiscal_html)

        financeiro_response = self.client.get(reverse("financeiro:listalancamentoview"))
        self.assertEqual(financeiro_response.status_code, 200)
        financeiro_html = financeiro_response.content.decode("utf-8")
        self.assertIn('id="modal-msg"', financeiro_html)
        self.assertIn('id="btn-ok"', financeiro_html)
        self.assertIn('id="btn-sim"', financeiro_html)
