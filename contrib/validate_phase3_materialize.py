from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "phase3_materialize"
REPORT_PATH = ROOT / "PHASE3_MATERIALIZE_REMOVAL.md"
BASE_URL = os.environ.get("PHASE3_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE3_USERNAME")
PASSWORD = os.environ.get("PHASE3_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE3_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE3_USERNAME e PHASE3_PASSWORD para validar a Fase 3.")
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


def no_materialize(page) -> bool:
    hrefs = page.locator("link[rel='stylesheet']").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('href') || '')"
    )
    return all("materialize.css" not in href for href in hrefs)


def validate_login(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    wait_page(page)
    checkbox = page.locator("#remember_me")
    checkbox.click()
    checked = checkbox.is_checked()
    checkbox_visible = checkbox.is_visible()
    screenshot = OUTPUT_DIR / "login_checkbox.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Login com checkbox",
        "path": "/login/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("materialize_not_loaded", no_materialize(page)),
            ("checkbox_visible", checkbox_visible),
            ("checkbox_checked", checked),
        ],
    }


def validate_radio_and_focus(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/cadastro/cliente/adicionar/", wait_until="domcontentloaded")
    wait_page(page)
    radios = page.locator("input[type='radio']")
    radio_count = radios.count()
    radios.nth(1).click()
    radio_checked = radios.nth(1).is_checked()
    text_input = page.locator("input[type='text']").first
    initial_border = text_input.evaluate("el => getComputedStyle(el).borderColor")
    text_input.focus()
    page.wait_for_timeout(200)
    focus_shadow = text_input.evaluate("el => getComputedStyle(el).boxShadow")
    focus_border = text_input.evaluate("el => getComputedStyle(el).borderColor")
    focus_active = text_input.evaluate("el => document.activeElement === el")
    screenshot = OUTPUT_DIR / "cliente_radio_focus.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Formulario com radio e foco",
        "path": "/cadastro/cliente/adicionar/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("materialize_not_loaded", no_materialize(page)),
            ("radio_count_gt_zero", radio_count > 0),
            ("radio_checked", radio_checked),
            ("focus_active", focus_active),
            ("focus_border_changed", focus_border != initial_border),
        ],
    }


def validate_form_errors(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/cadastro/cliente/adicionar/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("form").evaluate("form => form.submit()")
    wait_page(page)
    error_count = page.locator("label.error, .error-msg, .alert-danger").count()
    screenshot = OUTPUT_DIR / "cliente_errors.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Formulario com validacao visual",
        "path": "/cadastro/cliente/adicionar/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("materialize_not_loaded", no_materialize(page)),
            ("error_feedback_present", error_count > 0),
        ],
    }


def validate_modal_dropdown(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/financeiro/lancamentos/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator(".header .dropdown-toggle").first.click()
    page.wait_for_timeout(300)
    dropdown_visible = page.locator(".header .dropdown-menu").first.is_visible()
    page.evaluate("$('.modal_selecionar_data').modal('show');")
    page.wait_for_timeout(500)
    modal_open = "modal-open" in (page.locator("body").get_attribute("class") or "")
    screenshot = OUTPUT_DIR / "financeiro_modal_dropdown.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Modal e dropdown",
        "path": "/financeiro/lancamentos/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("materialize_not_loaded", no_materialize(page)),
            ("dropdown_visible", dropdown_visible),
            ("modal_open", modal_open),
        ],
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    lines = [
        "# Phase 3 Materialize Removal",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        "- `materialize.css` removido do carregamento de `base.html`, `404.html` e `500.html`",
        "- classes legadas `filled-in`, `chk-col-light-blue`, `waves-effect` e `waves-block` deixaram de ser usadas",
        "- checkbox do login, radios de formulario, foco de inputs, modais e dropdowns seguem funcionando sem a biblioteca",
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
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE_PATH))
        unauth_context = browser.new_context(viewport={"width": 1440, "height": 1080})
        auth_context = browser.new_context(viewport={"width": 1440, "height": 1080})
        unauth_page = unauth_context.new_page()
        auth_page = auth_context.new_page()
        login(auth_page)

        results = [
            validate_login(unauth_page),
            validate_radio_and_focus(auth_page),
            validate_form_errors(auth_page),
            validate_modal_dropdown(auth_page),
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
