from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangosige.configs.settings")

import django
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


django.setup()

from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from djangosige.apps.financeiro.models import PlanoContasGrupo, Saida  # noqa: E402


OUTPUT_DIR = ROOT / "artifacts" / "phase7_components"
REPORT_PATH = ROOT / "PHASE7_TABLES_FORMS_MODALS.md"
BASE_URL = os.environ.get("PHASE7_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE7_USERNAME")
PASSWORD = os.environ.get("PHASE7_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE7_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


LIST_PAGES = [
    ("Cadastro lista", reverse("cadastro:listaclientesview")),
    ("Vendas lista", reverse("vendas:listapedidovendaview")),
    ("Compras lista", reverse("compras:listapedidocompraview")),
    ("Financeiro lista", reverse("financeiro:listalancamentoview")),
    ("Fiscal lista", reverse("fiscal:listanotafiscalsaidaview")),
]

FORM_PAGES = [
    ("Cadastro formulario", reverse("cadastro:addprodutoview"), ".field-action", None),
    ("Vendas formulario", reverse("vendas:addpedidovendaview"), ".field-action", "input.datepicker"),
    ("Compras formulario", reverse("compras:addpedidocompraview"), ".field-action", "input.datepicker"),
    ("Financeiro formulario", reverse("financeiro:addcontapagarview"), ".is-choice-group", "input.datepicker"),
    ("Fiscal formulario", reverse("fiscal:addnotafiscalsaidaview"), ".field-action", "input.datetimepicker"),
]


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE7_USERNAME e PHASE7_PASSWORD para validar a Fase 7.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_seed_data() -> None:
    grupo, _ = PlanoContasGrupo.objects.get_or_create(
        codigo="990001",
        defaults={"tipo_grupo": "1", "descricao": "Grupo Validacao Fase 7"},
    )
    if not Saida.objects.exists():
        Saida.objects.create(
            descricao="Conta a pagar Fase 7",
            grupo_plano=grupo,
            status="1",
            data_vencimento=timezone.now().date(),
            valor_total="100.00",
            valor_liquido="100.00",
        )


def wait_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        page.wait_for_load_state("load", timeout=5000)
    page.wait_for_timeout(700)


def login(page) -> None:
    page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("input[name='username']").fill(USERNAME)
    page.locator("input[name='password']").fill(PASSWORD)
    page.locator("form#login button[type='submit']").click()
    wait_page(page)
    if "selecionarempresa" in page.url:
        select = page.locator("select[name='m_empresa']")
        values = select.locator("option").evaluate_all(
            "nodes => nodes.map(node => node.value).filter(Boolean)"
        )
        if values:
            select.select_option(values[0])
            page.locator("button[type='submit']").click()
            wait_page(page)


def attach_collectors(page):
    console_messages: list[str] = []
    page_errors: list[str] = []
    request_failures: list[str] = []

    def on_console(msg):
        if msg.type in {"error", "warning"}:
            console_messages.append(f"{msg.type}: {msg.text}")

    def on_page_error(exc):
        page_errors.append(str(exc))

    def on_request_failed(request):
        failure = request.failure
        request_failures.append(
            f"{request.method} {request.url} :: {failure.error_text if failure else 'unknown'}"
        )

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("requestfailed", on_request_failed)
    return console_messages, page_errors, request_failures, on_console, on_page_error, on_request_failed


def detach_collectors(page, handlers):
    console_messages, page_errors, request_failures, on_console, on_page_error, on_request_failed = handlers
    page.remove_listener("console", on_console)
    page.remove_listener("pageerror", on_page_error)
    page.remove_listener("requestfailed", on_request_failed)
    return console_messages, page_errors, request_failures


def validate_list_page(page, label: str, path: str, screenshot_name: str) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    checks = page.evaluate(
        """
        () => {
            const search = document.querySelector('#search-bar');
            const footer = document.querySelector('.app-datatable-footer');
            const removeButton = document.querySelector('.btn-remove');
            const dataTable = document.querySelector('#lista-database');
            return {
                searchType: search ? search.getAttribute('type') : '',
                footerExists: !!footer,
                footerSections: document.querySelectorAll('.app-datatable-footer > div').length,
                removeDisabled: !!(removeButton && removeButton.disabled),
                tableExists: !!dataTable,
                infoExists: !!document.querySelector('.dataTables_info'),
                paginateExists: !!document.querySelector('.dataTables_paginate')
            };
        }
        """
    )
    screenshot = OUTPUT_DIR / screenshot_name
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": label,
        "path": path,
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("table_exists", checks["tableExists"]),
            ("search_type_search", checks["searchType"] == "search"),
            ("datatable_footer_exists", checks["footerExists"]),
            ("datatable_footer_sections", checks["footerSections"] >= 3),
            ("remove_button_disabled_initially", checks["removeDisabled"]),
            ("datatable_info_exists", checks["infoExists"]),
            ("datatable_paginate_exists", checks["paginateExists"]),
        ],
    }


def validate_form_page(page, label: str, path: str, required_selector: str, date_selector: str | None, screenshot_name: str) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    checks = page.evaluate(
        """
        ({ requiredSelector, dateSelector }) => {
            const requiredNodes = document.querySelectorAll(requiredSelector);
            const dateField = dateSelector ? document.querySelector(dateSelector) : null;
            const formsetBox = document.querySelector('.app-formset-box');
            const firstFieldAction = document.querySelector('.field-action');
            return {
                requiredCount: requiredNodes.length,
                datePlaceholder: dateField ? (dateField.getAttribute('placeholder') || '') : null,
                dateInputmode: dateField ? (dateField.getAttribute('inputmode') || '') : null,
                dateAutocomplete: dateField ? (dateField.getAttribute('autocomplete') || '') : null,
                formsetExists: !!formsetBox,
                fieldActionAria: firstFieldAction ? !!firstFieldAction.getAttribute('aria-label') : null
            };
        }
        """,
        {"requiredSelector": required_selector, "dateSelector": date_selector},
    )
    screenshot = OUTPUT_DIR / screenshot_name
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    check_items = [
        ("required_selector_present", checks["requiredCount"] > 0),
    ]
    if date_selector:
        check_items.extend(
            [
                ("date_placeholder_present", checks["datePlaceholder"] not in ("", None)),
                ("date_inputmode_numeric", checks["dateInputmode"] == "numeric"),
                ("date_autocomplete_off", checks["dateAutocomplete"] == "off"),
            ]
        )
    if checks["fieldActionAria"] is not None:
        check_items.append(("field_action_has_aria_label", checks["fieldActionAria"]))
    if "Vendas" in label or "Compras" in label:
        check_items.append(("formset_box_present", checks["formsetExists"]))
    return {
        "label": label,
        "path": path,
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": check_items,
    }


def validate_finance_modal(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    path = reverse("financeiro:listalancamentoview")
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    page.evaluate(
        """
        () => {
            const modal = document.querySelector('.modal_selecionar_data');
            window.bootstrap.Modal.getOrCreateInstance(modal).show();
        }
        """
    )
    page.wait_for_timeout(400)
    checks = page.evaluate(
        """
        () => {
            const modal = document.querySelector('.modal_selecionar_data');
            const confirmButton = document.getElementById('baixar_conta_confirma');
            const dateInput = document.getElementById('id_data_pagamento');
            return {
                visible: !!document.querySelector('.modal_selecionar_data.show'),
                footerFlex: getComputedStyle(modal.querySelector('.modal-footer')).display === 'flex',
                confirmVisible: !!confirmButton,
                datePlaceholder: dateInput ? (dateInput.getAttribute('placeholder') || '') : '',
                dateInputmode: dateInput ? (dateInput.getAttribute('inputmode') || '') : ''
            };
        }
        """
    )
    screenshot = OUTPUT_DIR / "financeiro_modal.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Financeiro modal",
        "path": path,
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("modal_visible", checks["visible"]),
            ("modal_footer_flex", checks["footerFlex"]),
            ("confirm_button_present", checks["confirmVisible"]),
            ("date_placeholder_present", checks["datePlaceholder"] != ""),
            ("date_inputmode_numeric", checks["dateInputmode"] == "numeric"),
        ],
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    lines = [
        "# Phase 7 Tabelas, Formularios e Modais",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        "- listas padronizadas com busca, DataTables e estado inicial de remocao validados",
        "- formularios pesados validados com acoes inline, placeholders de data e formsets padronizados",
        "- modal financeiro validado com estrutura e footer consistentes",
        f"- telas/fluxos validados: `{len(results)}`",
        f"- console warnings/errors: `{total_console}`",
        f"- page errors: `{total_page_errors}`",
        f"- requests com falha: `{total_failures}`",
        "",
        "## Evidencias",
        "",
    ]
    for item in results:
        screenshot = item["screenshot"].as_posix()
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- URL: `{item['path']}`",
                f"- status HTTP: `{item['status']}`",
                f"- screenshot: [{item['screenshot'].name}]({screenshot})",
                f"- console warnings/errors: `{len(item['console_messages'])}`",
                f"- page errors: `{len(item['page_errors'])}`",
                f"- requests com falha: `{len(item['request_failures'])}`",
            ]
        )
        for check, value in item["checks"]:
            lines.append(f"- {check}: `{value}`")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_prerequisites()
    ensure_seed_data()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE_PATH))
        context = browser.new_context(viewport={"width": 1440, "height": 1080})
        context.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        page = context.new_page()
        login(page)

        results = []
        for index, (label, path) in enumerate(LIST_PAGES, start=1):
            results.append(validate_list_page(page, label, path, f"list_{index}.png"))
        for index, (label, path, selector, date_selector) in enumerate(FORM_PAGES, start=1):
            results.append(validate_form_page(page, label, path, selector, date_selector, f"form_{index}.png"))
        results.append(validate_finance_modal(page))

        context.close()
        browser.close()

    for item in results:
        if item["console_messages"] or item["page_errors"] or item["request_failures"]:
            raise SystemExit(f"Falha visual detectada em {item['label']}")
        for check, value in item["checks"]:
            if value in (False, 0, "", None):
                raise SystemExit(f"Check invalido em {item['label']}: {check}={value}")

    write_report(results)
    print(f"Relatorio gerado em: {REPORT_PATH}")
    print(f"Evidencias salvas em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
