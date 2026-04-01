from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "phase2_design"
REPORT_PATH = ROOT / "PHASE2_DESIGN_SYSTEM.md"
BASE_URL = os.environ.get("PHASE2_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE2_USERNAME")
PASSWORD = os.environ.get("PHASE2_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE2_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE2_USERNAME e PHASE2_PASSWORD para validar telas autenticadas.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
        options = select.locator("option").evaluate_all(
            "nodes => nodes.map(node => node.value).filter(Boolean)"
        )
        if options:
            select.select_option(options[0])
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


def capture(page, path: str, screenshot_name: str, action=None) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    if action:
        action(page)
        page.wait_for_timeout(500)
    screenshot = OUTPUT_DIR / screenshot_name
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    if path in {"/404/", "/500/"}:
        allowed_messages = {
            "error: Failed to load resource: the server responded with a status of 404 (Not Found)",
            "error: Failed to load resource: the server responded with a status of 500 (Internal Server Error)",
        }
        console_messages = [message for message in console_messages if message not in allowed_messages]
    return {
        "path": path,
        "screenshot": screenshot,
        "status": response.status if response else None,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "stylesheets": page.evaluate("document.styleSheets.length"),
        "scripts": page.evaluate("document.scripts.length"),
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    lines = [
        "# Phase 2 Design System",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        "- design tokens e estados visuais centralizados em `djangosige/static/css/theme-overrides.css`",
        "- `404` e `500` alinhadas ao mesmo sistema visual da aplicacao",
        f"- telas validadas: `{len(results)}`",
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
                f"- stylesheets: `{item['stylesheets']}`",
                f"- scripts: `{item['scripts']}`",
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
        unauth_context = browser.new_context(viewport={"width": 1440, "height": 1080})
        auth_context = browser.new_context(viewport={"width": 1440, "height": 1080})
        unauth_page = unauth_context.new_page()
        auth_page = auth_context.new_page()
        login(auth_page)

        login_result = capture(unauth_page, "/login/", "login.png")
        login_result["label"] = "Login"
        login_result["checks"] = [
            ("stylesheets_loaded", login_result["stylesheets"] > 0),
            ("body_login_page", "login-page" in (unauth_page.locator("body").get_attribute("class") or "")),
        ]

        dashboard_result = capture(auth_page, "/", "dashboard.png", lambda page: page.locator(".sidebar .menu > .list > li > a.menu-toggle").first.click())
        dashboard_result["label"] = "Dashboard"
        dashboard_result["checks"] = [
            (
                "submenu_visible",
                auth_page.locator(".sidebar .menu > .list > li > a.menu-toggle").first.evaluate(
                    "node => !!node.nextElementSibling && getComputedStyle(node.nextElementSibling).display !== 'none'"
                ),
            ),
        ]

        list_result = capture(auth_page, "/cadastro/cliente/listaclientes/", "lista.png")
        list_result["label"] = "Lista administrativa"
        list_result["checks"] = [
            ("datatable_wrapper_present", auth_page.locator("#lista-database_wrapper").count() > 0),
            ("table_headers_present", auth_page.locator("table thead th").count() > 3),
        ]

        form_result = capture(auth_page, "/cadastro/empresa/adicionar/", "form_tabs.png")
        form_result["label"] = "Formulario com tabs"
        form_result["checks"] = [
            ("tabs_present", auth_page.locator(".nav-tabs li").count() > 1),
            ("form_controls_present", auth_page.locator(".form-control").count() > 5),
        ]

        modal_result = capture(auth_page, "/financeiro/lancamentos/", "modal.png", lambda page: page.evaluate("$('.modal_selecionar_data').modal('show');"))
        modal_result["label"] = "Modal"
        modal_result["checks"] = [
            ("modal_open", "modal-open" in (auth_page.locator("body").get_attribute("class") or "")),
            ("dropdown_button_present", auth_page.locator(".header .dropdown-toggle").count() > 0),
        ]

        error_404_result = capture(auth_page, "/404/", "404.png")
        error_404_result["label"] = "Pagina 404"
        error_404_result["checks"] = [
            ("status_404", error_404_result["status"] == 404),
            ("error_code_visible", auth_page.locator(".error-code").first.inner_text() == "404"),
        ]

        error_500_result = capture(auth_page, "/500/", "500.png")
        error_500_result["label"] = "Pagina 500"
        error_500_result["checks"] = [
            ("status_500", error_500_result["status"] == 500),
            ("error_code_visible", auth_page.locator(".error-code").first.inner_text() == "500"),
        ]

        results = [
            login_result,
            dashboard_result,
            list_result,
            form_result,
            modal_result,
            error_404_result,
            error_500_result,
        ]

        unauth_context.close()
        auth_context.close()
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
