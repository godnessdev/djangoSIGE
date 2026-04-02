from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "phase6_jquery_reduction"
REPORT_PATH = ROOT / "PHASE6_JQUERY_REDUCTION.md"
BASE_URL = os.environ.get("PHASE6_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE6_USERNAME")
PASSWORD = os.environ.get("PHASE6_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE6_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE6_USERNAME e PHASE6_PASSWORD para validar a Fase 6.")
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


def validate_login_modal(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    wait_page(page)
    page.evaluate("AppCore.messages.success('Validacao Fase 6');")
    page.wait_for_timeout(500)
    checks = page.evaluate(
        """
        () => ({
            appCoreLoaded: !!window.AppCore,
            modalVisible: document.querySelector('#modal-msg.show') !== null,
            title: document.querySelector('#modal-msg .modal-title')?.textContent.trim() || '',
            body: document.querySelector('#modal-msg .modal-body p')?.textContent.trim() || ''
        })
        """
    )
    screenshot = OUTPUT_DIR / "login_modal.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "AppCore e modal global sem jQuery",
        "path": "/login/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("app_core_loaded", checks["appCoreLoaded"]),
            ("modal_visible", checks["modalVisible"]),
            ("modal_title_ok", checks["title"] == "Sucesso"),
            ("modal_body_ok", checks["body"] == "Validacao Fase 6"),
        ],
    }


def validate_shell_navigation(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.set_viewport_size({"width": 1024, "height": 960})
    response = page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    wait_page(page)
    page.evaluate("document.querySelector('.bars').click()")
    page.wait_for_timeout(300)
    checks = page.evaluate(
        """
        () => ({
            overlayOpen: document.body.classList.contains('overlay-open'),
            overlayVisible: getComputedStyle(document.querySelector('.overlay')).display !== 'none'
        })
        """
    )
    page.evaluate(
        """
        () => {
            document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
        """
    )
    page.wait_for_timeout(300)
    after_close = page.evaluate(
        """
        () => ({
            overlayOpen: document.body.classList.contains('overlay-open'),
            cadastroMenuVisible: getComputedStyle(document.querySelector('.menu .list > li:nth-child(2) .ml-menu')).display !== 'none'
        })
        """
    )
    page.evaluate("document.querySelector('.menu .list > li:nth-child(2) > a.menu-toggle').click()")
    page.wait_for_timeout(300)
    menu_open = page.evaluate(
        """
        () => ({
            cadastroMenuVisible: getComputedStyle(document.querySelector('.menu .list > li:nth-child(2) .ml-menu')).display !== 'none',
            cadastroToggleToggled: document.querySelector('.menu .list > li:nth-child(2) > a.menu-toggle').classList.contains('toggled')
        })
        """
    )
    screenshot = OUTPUT_DIR / "shell_navigation.png"
    page.screenshot(path=str(screenshot), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1080})
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Sidebar, overlay e menu nativos",
        "path": "/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("overlay_opens", checks["overlayOpen"] and checks["overlayVisible"]),
            ("overlay_closes", not after_close["overlayOpen"]),
            ("menu_opens", menu_open["cadastroMenuVisible"]),
            ("menu_toggle_marked", menu_open["cadastroToggleToggled"]),
        ],
    }


def validate_active_menu(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/cadastro/cliente/listaclientes/", wait_until="domcontentloaded")
    wait_page(page)
    checks = page.evaluate(
        """
        () => {
            const activeLink = Array.from(document.querySelectorAll('.menu .list a')).find(
                (link) => link.href === window.location.href
            );
            return {
                activeLinkText: activeLink ? activeLink.textContent.trim() : '',
                activeParent: !!(activeLink && activeLink.closest('li.active')),
                parentMenuOpen: !!(activeLink && activeLink.closest('.ml-menu') && getComputedStyle(activeLink.closest('.ml-menu')).display !== 'none')
            };
        }
        """
    )
    screenshot = OUTPUT_DIR / "active_menu.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Menu ativo sem dinamicMenu em jQuery",
        "path": "/cadastro/cliente/listaclientes/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("active_link_found", checks["activeLinkText"] == "Clientes"),
            ("active_parent_marked", checks["activeParent"]),
            ("parent_menu_open", checks["parentMenuOpen"]),
        ],
    }


def validate_fiscal_import_inline(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/fiscal/notafiscal/saida/listanotafiscal/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("#importar_nota").click()
    page.wait_for_timeout(300)
    checks = page.evaluate(
        """
        () => {
            const form = document.getElementById('form_importar_nota');
            const modalVisible = document.querySelector('.importar_nota_modal.show') !== null;
            if (form) {
                form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            }
            return {
                modalVisible,
                loaderVisible: getComputedStyle(document.querySelector('.page-loader-wrapper')).display !== 'none',
                loaderMessage: document.querySelector('.loader .loader-message')?.textContent.trim() || ''
            };
        }
        """
    )
    screenshot = OUTPUT_DIR / "fiscal_import_inline.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Evento inline simples migrado para nativo",
        "path": "/fiscal/notafiscal/saida/listanotafiscal/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("import_modal_visible", checks["modalVisible"]),
            ("loader_visible", checks["loaderVisible"]),
            ("loader_message_set", checks["loaderMessage"] == "Importando nota fiscal, aguarde..."),
        ],
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    lines = [
        "# Phase 6 Reducao Gradual de jQuery",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        "- shell principal validado com `AppCore` em JS nativo",
        "- modal global de mensagens validado sem dependencia direta de `jQuery`",
        "- destaque de menu ativo validado sem `dinamicMenu` no init legado",
        "- exemplo real de evento inline simples validado sem `jQuery`",
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
        unauth_context.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        auth_context.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        unauth_page = unauth_context.new_page()
        auth_page = auth_context.new_page()
        login(auth_page)

        results = [
            validate_login_modal(unauth_page),
            validate_shell_navigation(auth_page),
            validate_active_menu(auth_page),
            validate_fiscal_import_inline(auth_page),
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
