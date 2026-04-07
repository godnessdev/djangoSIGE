from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "phase0_visual"
REPORT_PATH = ROOT / "PHASE0_VISUAL_VALIDATION.md"
BASE_URL = os.environ.get("PHASE0_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE0_USERNAME")
PASSWORD = os.environ.get("PHASE0_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE0_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


@dataclass(frozen=True)
class PageSpec:
    slug: str
    title: str
    path: str
    requires_auth: bool = True
    modal_script: str | None = None


PAGES = (
    PageSpec("login", "Login", "/login/", requires_auth=False),
    PageSpec(
        "login_modal",
        "Modal base no login",
        "/login/",
        requires_auth=False,
        modal_script="""
            $('#modal-msg .modal-title').text('Validacao visual');
            $('#modal-msg .modal-body').text('Modal base carregado corretamente.');
            $('#btn-ok, #btn-sim, #btn-nao').show();
            $('#modal-msg').modal('show');
        """,
    ),
    PageSpec("dashboard", "Dashboard", "/"),
    PageSpec("clientes_lista", "Lista de clientes", "/cadastro/cliente/listaclientes/"),
    PageSpec("cliente_form", "Formulario de cliente", "/cadastro/cliente/adicionar/"),
    PageSpec("financeiro_lista", "Lancamentos financeiros", "/financeiro/lancamentos/"),
    PageSpec(
        "financeiro_modal",
        "Modal financeiro",
        "/financeiro/lancamentos/",
        modal_script="""
            $('.modal_selecionar_data').modal('show');
        """,
    ),
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE0_USERNAME e PHASE0_PASSWORD para validar telas autenticadas.")
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
    if page.locator("form#login").count():
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
        raise RuntimeError("Falha ao autenticar no fluxo visual da Fase 0.")


def collect_page_metrics(page) -> dict[str, object]:
    return {
        "final_url": page.url,
        "document_title": page.title(),
        "stylesheets": page.evaluate("document.styleSheets.length"),
        "scripts": page.evaluate("document.scripts.length"),
        "body_class": page.locator("body").get_attribute("class") or "",
        "html_bytes": len(page.content().encode("utf-8")),
    }


def capture_page(page, spec: PageSpec) -> dict[str, object]:
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

    page.goto(f"{BASE_URL}{spec.path}", wait_until="domcontentloaded")
    wait_page(page)

    if spec.modal_script:
        page.evaluate(spec.modal_script)
        page.wait_for_timeout(500)

    screenshot_path = OUTPUT_DIR / f"{spec.slug}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    metrics = collect_page_metrics(page)

    page.remove_listener("console", on_console)
    page.remove_listener("pageerror", on_page_error)
    page.remove_listener("requestfailed", on_request_failed)

    return {
        "slug": spec.slug,
        "label": spec.title,
        "path": spec.path,
        "screenshot": screenshot_path,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        **metrics,
    }


def validate_pages() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=str(EDGE_PATH),
        )

        unauth_context = browser.new_context(
            viewport={"width": 1440, "height": 1080},
            ignore_https_errors=True,
        )
        unauth_page = unauth_context.new_page()
        for spec in [item for item in PAGES if not item.requires_auth]:
            results.append(capture_page(unauth_page, spec))
        unauth_context.close()

        auth_context = browser.new_context(
            viewport={"width": 1440, "height": 1080},
            ignore_https_errors=True,
        )
        auth_page = auth_context.new_page()
        if any(spec.requires_auth for spec in PAGES):
            login(auth_page)
        for spec in [item for item in PAGES if item.requires_auth]:
            results.append(capture_page(auth_page, spec))
        auth_context.close()

        browser.close()
    return results


def write_report(results: list[dict[str, object]]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Phase 0 Visual Validation",
        "",
        f"Atualizado em `{timestamp}`.",
        "",
        "## Escopo",
        "",
        "- validacao visual com navegador real headless usando Microsoft Edge",
        "- telas exigidas pela Fase 0: login, dashboard, lista, formulario e modais",
        "- evidencias salvas em `artifacts/phase0_visual`",
        "",
        "## Resultado Geral",
        "",
    ]

    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    lines.extend(
        [
            f"- telas validadas: `{len(results)}`",
            f"- avisos/erros de console capturados: `{total_console}`",
            f"- erros de pagina capturados: `{total_page_errors}`",
            f"- requests com falha capturados: `{total_failures}`",
            "",
            "## Evidencias por Tela",
            "",
        ]
    )

    for item in results:
        screenshot_path = item["screenshot"].as_posix()
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- URL: `{item['path']}`",
                f"- URL final: `{item['final_url']}`",
                f"- titulo do documento: `{item['document_title']}`",
                f"- classes do body: `{item['body_class']}`",
                f"- stylesheets ativos: `{item['stylesheets']}`",
                f"- scripts no documento: `{item['scripts']}`",
                f"- tamanho do HTML renderizado: `{item['html_bytes']} bytes`",
                f"- screenshot: [{item['slug']}.png]({screenshot_path})",
            ]
        )
        if item["console_messages"]:
            lines.append(f"- console: `{len(item['console_messages'])}` evento(s)")
            lines.extend([f"  - `{message}`" for message in item["console_messages"][:10]])
        else:
            lines.append("- console: `0` eventos de warning/error")
        if item["page_errors"]:
            lines.append(f"- page errors: `{len(item['page_errors'])}`")
            lines.extend([f"  - `{message}`" for message in item["page_errors"][:10]])
        else:
            lines.append("- page errors: `0`")
        if item["request_failures"]:
            lines.append(f"- requests com falha: `{len(item['request_failures'])}`")
            lines.extend([f"  - `{message}`" for message in item["request_failures"][:10]])
        else:
            lines.append("- requests com falha: `0`")
        lines.append("")

    lines.extend(
        [
            "## Conclusao",
            "",
            "- a Fase 0 possui baseline tecnico e visual documentado",
            "- qualquer regressao de stack ou layout agora pode ser comparada contra os artefatos desta fase",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_prerequisites()
    results = validate_pages()
    write_report(results)
    print(f"Relatorio gerado em: {REPORT_PATH}")
    print(f"Evidencias salvas em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
