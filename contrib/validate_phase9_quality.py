from __future__ import annotations

import os
import sys
import time
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


REPORT_PATH = ROOT / "PHASE9_QUALITY.md"
ARTIFACTS_DIR = ROOT / "artifacts" / "phase9_quality"
BASE_URL = os.environ.get("PHASE9_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE9_USERNAME")
PASSWORD = os.environ.get("PHASE9_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE9_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE9_USERNAME e PHASE9_PASSWORD para validar a Fase 9.")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


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


def finalize_result(page, handlers, label: str, path: str, response, checks: list[tuple[str, bool]], screenshot_name: str):
    screenshot = ARTIFACTS_DIR / screenshot_name
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": label,
        "path": path,
        "status": response.status if response else None,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": checks,
        "screenshot": screenshot,
    }


def validate_dashboard(page):
    path = reverse("base:index")
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    checks = [
        ("app_core_loaded", page.evaluate("() => !!window.AppCore")),
        ("sidebar_present", page.locator("#barralateral").count() == 1),
    ]
    return finalize_result(page, handlers, "Dashboard shell", path, response, checks, "dashboard_shell.png")


def validate_cliente_tabs(page):
    path = reverse("cadastro:addclienteview")
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    page.locator('a[href="#tab_banco"]').click()
    page.wait_for_timeout(400)
    tab_state = page.evaluate(
        """
        () => {
            const activeTabs = document.querySelectorAll('.nav-tabs li.active');
            const activePanes = document.querySelectorAll('.tab-content .tab-pane.active');
            const bancoTab = document.querySelector('a[href="#tab_banco"]');
            const bancoPane = document.querySelector('#tab_banco');
            return {
                activeTabs: activeTabs.length,
                activePanes: activePanes.length,
                bancoTabActive: !!(bancoTab && bancoTab.closest('li.active, .active')),
                bancoPaneActive: !!(bancoPane && bancoPane.classList.contains('active')),
            };
        }
        """
    )
    checks = [
        ("single_active_tab", tab_state["activeTabs"] == 1),
        ("single_active_pane", tab_state["activePanes"] == 1),
        ("dados_bancarios_active", tab_state["bancoTabActive"]),
        ("tab_banco_active", tab_state["bancoPaneActive"]),
    ]
    return finalize_result(page, handlers, "Cadastro tabs", path, response, checks, "cadastro_tabs.png")


def validate_nota_fiscal_tabs(page):
    path = reverse("fiscal:addnotafiscalsaidaview")
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    page.locator('a[href="#tab_inf_ad"]').click()
    page.wait_for_timeout(400)
    tab_state = page.evaluate(
        """
        () => {
            const activeTabs = document.querySelectorAll('.nav-tabs li.active');
            const activePanes = document.querySelectorAll('.tab-content .tab-pane.active');
            const infoTab = document.querySelector('a[href="#tab_inf_ad"]');
            const infoPane = document.querySelector('#tab_inf_ad');
            return {
                activeTabs: activeTabs.length,
                activePanes: activePanes.length,
                infoTabActive: !!(infoTab && infoTab.closest('li.active, .active')),
                infoPaneActive: !!(infoPane && infoPane.classList.contains('active')),
            };
        }
        """
    )
    checks = [
        ("single_active_tab", tab_state["activeTabs"] == 1),
        ("single_active_pane", tab_state["activePanes"] == 1),
        ("informacoes_adicionais_active", tab_state["infoTabActive"]),
        ("tab_inf_ad_active", tab_state["infoPaneActive"]),
    ]
    return finalize_result(page, handlers, "Fiscal tabs", path, response, checks, "fiscal_tabs.png")


def validate_checkbox(page):
    path = reverse("financeiro:addcontapagarview")
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    checkbox = page.locator("#id_movimentar_caixa")
    checkbox.check(force=True)
    page.wait_for_timeout(200)
    checked = checkbox.is_checked()
    checkbox.uncheck(force=True)
    page.wait_for_timeout(200)
    unchecked = not checkbox.is_checked()
    sizing = checkbox.evaluate(
        """
        node => {
            const style = getComputedStyle(node);
            return {
                width: style.width,
                height: style.height,
                appearance: style.appearance || style.webkitAppearance || ''
            };
        }
        """
    )
    checks = [
        ("checkbox_checks", checked),
        ("checkbox_unchecks", unchecked),
        ("checkbox_width_18px", sizing["width"] == "18px"),
        ("checkbox_height_18px", sizing["height"] == "18px"),
    ]
    return finalize_result(page, handlers, "Checkbox financeiro", path, response, checks, "checkbox_financeiro.png")


def validate_list_page(page):
    path = reverse("cadastro:listaclientesview")
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("#search-bar").fill("cliente-inexistente-phase9")
    page.wait_for_timeout(500)
    checks_state = page.evaluate(
        """
        () => {
            const resources = performance.getEntriesByType('resource').map(entry => entry.name);
            const removeButton = document.querySelector('.btn-remove');
            return {
                dataTablesLoaded: resources.some(name => name.includes('jquery.dataTables.min.js')),
                footerPresent: !!document.querySelector('.app-datatable-footer'),
                removeDisabled: !!(removeButton && removeButton.disabled),
                searchValue: document.querySelector('#search-bar')?.value || ''
            };
        }
        """
    )
    checks = [
        ("datatables_loaded", checks_state["dataTablesLoaded"]),
        ("datatable_footer_present", checks_state["footerPresent"]),
        ("remove_button_disabled", checks_state["removeDisabled"]),
        ("search_input_interacted", checks_state["searchValue"] == "cliente-inexistente-phase9"),
    ]
    return finalize_result(page, handlers, "Lista com DataTables", path, response, checks, "lista_datatables.png")


def validate_global_modal(page):
    path = reverse("base:index")
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    page.evaluate("() => window.AppCore.messages.success('Validacao Fase 9')")
    page.wait_for_timeout(400)
    state = page.evaluate(
        """
        () => {
            const modal = document.getElementById('modal-msg');
            return {
                visible: !!(modal && modal.classList.contains('show')),
                okVisible: !!document.querySelector('#btn-ok'),
                title: document.querySelector('#modal-msg-title')?.textContent || '',
            };
        }
        """
    )
    checks = [
        ("modal_visible", state["visible"]),
        ("modal_ok_present", state["okVisible"]),
        ("modal_title_success", state["title"].strip() == "Sucesso"),
    ]
    return finalize_result(page, handlers, "Modal global", path, response, checks, "modal_global.png")


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_request_failures = sum(len(item["request_failures"]) for item in results)

    lines = [
        "# Phase 9 Qualidade, Testes e Observabilidade",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        "- contratos principais de frontend foram revalidados em browser real",
        "- tabs de cadastro e fiscal permanecem trocando corretamente",
        "- checkbox financeiro permanece funcional e com tamanho visual esperado",
        "- modal global e lista com DataTables seguem operacionais",
        f"- fluxos validados: `{len(results)}`",
        f"- console warnings/errors: `{total_console}`",
        f"- page errors: `{total_page_errors}`",
        f"- requests com falha: `{total_request_failures}`",
        "",
        "## Evidencias",
        "",
    ]

    for item in results:
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- URL: `{item['path']}`",
                f"- status HTTP: `{item['status']}`",
                f"- screenshot: [{item['screenshot'].name}]({item['screenshot'].as_posix()})",
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
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE_PATH))
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        context.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        page = context.new_page()

        login(page)

        results = [
            validate_dashboard(page),
            validate_cliente_tabs(page),
            validate_nota_fiscal_tabs(page),
            validate_checkbox(page),
            validate_list_page(page),
            validate_global_modal(page),
        ]

        context.close()
        browser.close()

    for item in results:
        if item["console_messages"] or item["page_errors"] or item["request_failures"]:
            raise SystemExit(f"Falha visual detectada em {item['label']}")
        if item["status"] != 200:
            raise SystemExit(f"Status invalido em {item['label']}: {item['status']}")
        for check, value in item["checks"]:
            if not value:
                raise SystemExit(f"Check invalido em {item['label']}: {check}={value}")

    write_report(results)
    print(f"Relatorio gerado em: {REPORT_PATH}")
    print(f"Evidencias salvas em: {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
