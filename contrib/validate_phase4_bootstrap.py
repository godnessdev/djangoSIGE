from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "phase4_bootstrap"
REPORT_PATH = ROOT / "PHASE4_BOOTSTRAP5_MIGRATION.md"
BASE_URL = os.environ.get("PHASE4_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE4_USERNAME")
PASSWORD = os.environ.get("PHASE4_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE4_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE4_USERNAME e PHASE4_PASSWORD para validar a Fase 4.")
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


def bootstrap_version(page) -> str:
    return page.evaluate(
        """
        () => {
            if (!window.bootstrap) return '';
            return (
                window.bootstrap.Tooltip?.VERSION ||
                window.bootstrap.Modal?.VERSION ||
                window.bootstrap.Dropdown?.VERSION ||
                ''
            );
        }
        """
    )


def validate_login_grid(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    wait_page(page)
    metrics = page.evaluate(
        """
        () => {
            const row = document.querySelector('.login-page .row');
            const left = row ? row.querySelector('.col-xs-8') : null;
            const right = row ? row.querySelector('.col-xs-4') : null;
            const leftRect = left ? left.getBoundingClientRect() : null;
            const rightRect = right ? right.getBoundingClientRect() : null;
            const hasCompatCss = !!document.querySelector('link[href*="bootstrap-compat.css"]');
            const hasCompatJs = !!window.bootstrapCompat;
            return {
                hasCompatCss,
                hasCompatJs,
                leftWidth: leftRect ? leftRect.width : 0,
                rightWidth: rightRect ? rightRect.width : 0
            };
        }
        """
    )
    ratio = metrics["leftWidth"] / metrics["rightWidth"] if metrics["rightWidth"] else 0
    screenshot = OUTPUT_DIR / "login_grid.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    version = bootstrap_version(page)
    return {
        "label": "Login e grid legado",
        "path": "/login/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("bootstrap_5_loaded", version.startswith("5.3")),
            ("compat_css_loaded", metrics["hasCompatCss"]),
            ("compat_js_loaded", metrics["hasCompatJs"]),
            ("legacy_grid_ratio_ok", 1.7 <= ratio <= 2.3),
        ],
        "meta": {"bootstrap_version": version},
    }


def validate_navbar_and_dropdown(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.set_viewport_size({"width": 640, "height": 960})
    response = page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator(".navbar-toggle").evaluate("el => el.click()")
    page.wait_for_timeout(400)
    navbar_open = "show" in (page.locator("#navbar-collapse").get_attribute("class") or "")

    page.set_viewport_size({"width": 1440, "height": 1080})
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator(".user-helper-dropdown [data-toggle='dropdown']").evaluate("el => el.click()")
    page.wait_for_timeout(400)
    dropdown_visible = page.locator(".user-helper-dropdown .dropdown-menu").is_visible()
    screenshot = OUTPUT_DIR / "navbar_dropdown.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Menus e dropdowns",
        "path": "/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("navbar_collapse_open", navbar_open),
            ("user_dropdown_visible", dropdown_visible),
        ],
    }


def validate_tabs_and_collapse(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    page.set_viewport_size({"width": 1440, "height": 1080})
    response = page.goto(f"{BASE_URL}/financeiro/planodecontas/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("a[href='#tab_saidas']").click()
    page.wait_for_timeout(400)
    tab_selected = page.locator("a[href='#tab_saidas']").get_attribute("aria-selected")
    tab_active = "active" in (page.locator("a[href='#tab_saidas']").get_attribute("class") or "")
    pane_active = "active" in (page.locator("#tab_saidas").get_attribute("class") or "")

    page.evaluate(
        """
        () => {
            const existing = document.getElementById('phase4-legacy-collapse-fixture');
            if (existing) existing.remove();
            const wrapper = document.createElement('div');
            wrapper.id = 'phase4-legacy-collapse-fixture';
            wrapper.innerHTML = `
                <button type="button" id="legacy-collapse-trigger" data-toggle="collapse" data-target=".legacy-collapse-row">
                    Toggle legacy collapse
                </button>
                <table><tbody><tr class="legacy-collapse-row in"><td>Legacy row</td></tr></tbody></table>
            `;
            document.body.appendChild(wrapper);
            if (window.bootstrapCompat) {
                window.bootstrapCompat.syncLegacyDataAttributes(wrapper);
            }
        }
        """
    )

    visible_before = page.locator(".legacy-collapse-row").first.is_visible()
    page.locator("#legacy-collapse-trigger").evaluate("el => el.click()")
    page.wait_for_timeout(300)
    visible_after = page.locator(".legacy-collapse-row").first.is_visible()
    screenshot = OUTPUT_DIR / "tabs_collapse.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Tabs e collapse legado",
        "path": "/financeiro/planodecontas/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("tab_selected", tab_selected == "true"),
            ("tab_active", tab_active),
            ("pane_active", pane_active),
            ("legacy_collapse_toggled", visible_before != visible_after),
        ],
    }


def validate_modal_and_dropdown(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/financeiro/lancamentos/", wait_until="domcontentloaded")
    wait_page(page)
    page.locator(".header .dropdown-toggle").first.click()
    page.wait_for_timeout(300)
    dropdown_visible = page.locator(".header .dropdown-menu").first.is_visible()
    page.evaluate("$('.modal_selecionar_data').modal('show');")
    page.wait_for_timeout(500)
    modal_open = "show" in (page.locator(".modal_selecionar_data").get_attribute("class") or "")
    body_locked = "modal-open" in (page.locator("body").get_attribute("class") or "")
    page.locator(".modal_selecionar_data [data-dismiss='modal']").first.click()
    page.wait_for_timeout(500)
    modal_closed = not page.locator(".modal_selecionar_data").is_visible()
    screenshot = OUTPUT_DIR / "modal_dropdown.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Modal e dropdown Bootstrap",
        "path": "/financeiro/lancamentos/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("dropdown_visible", dropdown_visible),
            ("modal_open", modal_open),
            ("body_locked", body_locked),
            ("modal_closed", modal_closed),
        ],
    }


def validate_datatables(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}/cadastro/cliente/listaclientes/", wait_until="domcontentloaded")
    wait_page(page)
    metrics = page.evaluate(
        """
        () => {
            const table = window.jQuery && window.jQuery.fn.dataTable
                ? window.jQuery.fn.dataTable.isDataTable('#lista-database')
                : false;
            const wrapper = !!document.querySelector('#lista-database_wrapper');
            const rowsBefore = document.querySelectorAll('#lista-database tbody tr').length;
            return { table, wrapper, rowsBefore };
        }
        """
    )
    page.locator("#search-bar").fill("cliente-inexistente-bootstrap5")
    page.locator("#search-bar").evaluate(
        "el => el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }))"
    )
    page.wait_for_timeout(500)
    filtered_rows = page.evaluate(
        """
        () => {
            if (window.dTable && typeof window.dTable.rows === 'function') {
                return window.dTable.rows({ filter: 'applied' }).count();
            }
            return -1;
        }
        """
    )
    screenshot = OUTPUT_DIR / "datatables.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "DataTables com nova camada visual",
        "path": "/cadastro/cliente/listaclientes/",
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("datatable_initialized", metrics["table"]),
            ("datatable_wrapper_present", metrics["wrapper"]),
            ("datatable_search_applied", filtered_rows == 0 or metrics["rowsBefore"] == 0),
        ],
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    version = next((item.get("meta", {}).get("bootstrap_version") for item in results if item.get("meta")), "")
    lines = [
        "# Phase 4 Bootstrap 5.3 Migration",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        f"- Bootstrap vendorizado atualizado para `Bootstrap {version or '5.3.x'}` nos caminhos existentes",
        "- compatibilidade legada adicionada em `bootstrap-compat.css` e `bootstrap-compat.js`",
        "- classes e atributos legados cobertos: `col-xs-*`, `pull-right`, `navbar-*`, `input-group-addon`, `btn-default`, `caret`, `data-toggle`, `data-target`, `data-dismiss`, jQuery `.modal()` e `.tab()`",
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
            validate_login_grid(unauth_page),
            validate_navbar_and_dropdown(auth_page),
            validate_tabs_and_collapse(auth_page),
            validate_modal_and_dropdown(auth_page),
            validate_datatables(auth_page),
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
