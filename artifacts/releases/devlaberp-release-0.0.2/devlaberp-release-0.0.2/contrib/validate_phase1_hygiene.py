from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "phase1_hygiene"
REPORT_PATH = ROOT / "PHASE1_STACK_HYGIENE.md"
BASE_URL = os.environ.get("PHASE1_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE1_USERNAME")
PASSWORD = os.environ.get("PHASE1_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE1_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE1_USERNAME e PHASE1_PASSWORD para validar telas autenticadas.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def wait_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        page.wait_for_load_state("load", timeout=5000)
    page.wait_for_timeout(600)


def login(page) -> None:
    page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("input[name='username']").fill(USERNAME)
    page.locator("input[name='password']").fill(PASSWORD)
    page.locator("form#login button[type='submit']").click()
    wait_page(page)

    if "selecionarempresa" in page.url:
        select = page.locator("select[name='m_empresa']")
        options = select.locator("option").evaluate_all(
            "nodes => nodes.map(node => node.value).filter(Boolean)"
        )
        if options:
            select.select_option(options[0])
            page.locator("button[type='submit']").click()
            wait_page(page)

    if "login" in page.url and page.locator("form#login").count():
        raise RuntimeError("Falha ao autenticar na validacao da Fase 1.")


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


def validate_login(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    wait_page(page)
    screenshot = OUTPUT_DIR / "login.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    stylesheets = page.evaluate("document.styleSheets.length")
    return {
        "name": "Login sem autenticacao",
        "path": "/login/",
        "screenshot": screenshot,
        "checks": [
            ("stylesheets_loaded", stylesheets > 0),
            ("scripts_loaded", page.evaluate("document.scripts.length") > 0),
            ("datatable_absent", page.locator("#lista-database_wrapper").count() == 0),
        ],
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
    }


def validate_dashboard(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    wait_page(page)
    first_toggle = page.locator(".sidebar .menu > .list > li > a.menu-toggle").first
    first_toggle.click()
    page.wait_for_timeout(400)
    submenu_visible = first_toggle.evaluate(
        "node => !!node.nextElementSibling && getComputedStyle(node.nextElementSibling).display !== 'none'"
    )
    screenshot = OUTPUT_DIR / "dashboard_menu.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "name": "Dashboard com menu lateral",
        "path": "/",
        "screenshot": screenshot,
        "checks": [
            ("submenu_visible", submenu_visible),
            ("body_class_present", bool(page.locator("body").get_attribute("class"))),
        ],
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
    }


def validate_client_list(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.goto(f"{BASE_URL}/cadastro/cliente/listaclientes/", wait_until="domcontentloaded")
    wait_page(page)
    screenshot = OUTPUT_DIR / "clientes_lista.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    datatable_available = page.evaluate("typeof $.fn.DataTable === 'function'")
    datatable_wrapper = page.locator("#lista-database_wrapper").count()
    return {
        "name": "Lista com DataTables",
        "path": "/cadastro/cliente/listaclientes/",
        "screenshot": screenshot,
        "checks": [
            ("datatable_available", datatable_available),
            ("datatable_wrapper_present", datatable_wrapper > 0),
        ],
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
    }


def validate_client_form(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.goto(f"{BASE_URL}/cadastro/cliente/adicionar/", wait_until="domcontentloaded")
    wait_page(page)
    screenshot = OUTPUT_DIR / "cliente_form.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "name": "Formulario com mask e jQuery UI",
        "path": "/cadastro/cliente/adicionar/",
        "screenshot": screenshot,
        "checks": [
            ("mask_available", page.evaluate("typeof $.fn.mask === 'function'")),
            ("jquery_ui_available", page.evaluate("typeof $.ui !== 'undefined'")),
        ],
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
    }


def validate_financeiro(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.goto(f"{BASE_URL}/financeiro/lancamentos/", wait_until="domcontentloaded")
    wait_page(page)
    dropdown_toggle = page.locator(".header .dropdown-toggle").first
    dropdown_toggle.click()
    page.wait_for_timeout(400)
    dropdown_visible = page.locator(".header .dropdown-menu").first.is_visible()
    page.evaluate("$('.modal_selecionar_data').modal('show');")
    page.wait_for_timeout(500)
    modal_open = "modal-open" in (page.locator("body").get_attribute("class") or "")
    screenshot = OUTPUT_DIR / "financeiro_higiene.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "name": "Lista financeira com dropdown e modal",
        "path": "/financeiro/lancamentos/",
        "screenshot": screenshot,
        "checks": [
            ("dropdown_visible", dropdown_visible),
            ("modal_open", modal_open),
            ("mask_available", page.evaluate("typeof $.fn.mask === 'function'")),
            ("jquery_ui_available", page.evaluate("typeof $.ui !== 'undefined'")),
        ],
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)

    lines = [
        "# Phase 1 Stack Hygiene",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Ajustes Aplicados",
        "",
        "- ordem de assets normalizada em `base.html`: vendor CSS, app CSS, overrides e core JS",
        "- `Materialize` saiu do `@import` de `style.css` e passou a ser carregado explicitamente",
        "- overrides visuais de 2026 isolados em `djangosige/static/css/theme-overrides.css`",
        "- loaders repetidos padronizados em `load_jquery_mask.html`, `load_jqueryui.html` e `load_datetimepicker.html`",
        "- duplicidade do modal base removida das telas de login e lista de usuarios",
        "",
        "## Resultado da Validacao",
        "",
        f"- telas verificadas: `{len(results)}`",
        f"- console warnings/errors: `{total_console}`",
        f"- page errors: `{total_page_errors}`",
        f"- requests com falha: `{total_failures}`",
        "- comparacao com a baseline visual da Fase 0: mantido em `0` erros de console e `0` requests falhos",
        "",
        "## Evidencias",
        "",
    ]

    for result in results:
        screenshot = result["screenshot"].as_posix()
        lines.append(f"### {result['name']}")
        lines.append("")
        lines.append(f"- URL: `{result['path']}`")
        lines.append(f"- screenshot: [{result['screenshot'].name}]({screenshot})")
        for key, value in result["checks"]:
            lines.append(f"- {key}: `{value}`")
        lines.append(f"- console warnings/errors: `{len(result['console_messages'])}`")
        lines.append(f"- page errors: `{len(result['page_errors'])}`")
        lines.append(f"- requests com falha: `{len(result['request_failures'])}`")
        lines.append("")

    lines.extend(
        [
            "## Dependencias Mantidas de Forma Intencional",
            "",
            "- `jQuery`, `Bootstrap 3`, `DataTables`, `jQuery UI`, `jquery.mask`, `jquery.datetimepicker` e `jquery.multi-select` continuam ativos",
            "- nenhuma biblioteca funcional foi removida nesta fase; o foco foi reduzir acoplamento e padronizar a carga",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_prerequisites()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=str(EDGE_PATH),
        )
        unauth_context = browser.new_context(viewport={"width": 1440, "height": 1080})
        unauth_page = unauth_context.new_page()
        auth_context = browser.new_context(viewport={"width": 1440, "height": 1080})
        auth_page = auth_context.new_page()

        login(auth_page)

        results = [
            validate_login(unauth_page),
            validate_dashboard(auth_page),
            validate_client_list(auth_page),
            validate_client_form(auth_page),
            validate_financeiro(auth_page),
        ]

        unauth_context.close()
        auth_context.close()
        browser.close()

    for result in results:
        if result["console_messages"] or result["page_errors"] or result["request_failures"]:
            raise SystemExit(f"Falha na validacao visual da Fase 1 em: {result['name']}")
        for key, value in result["checks"]:
            if value in (False, 0, "", None):
                raise SystemExit(f"Check invalido em {result['name']}: {key}={value}")

    write_report(results)
    print(f"Relatorio gerado em: {REPORT_PATH}")
    print(f"Evidencias salvas em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
