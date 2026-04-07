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

from djangosige.apps.cadastro.models import Cliente, Empresa, PessoaFisica, PessoaJuridica
from django.urls import reverse


OUTPUT_DIR = ROOT / "artifacts" / "phase5_progressive"
REPORT_PATH = ROOT / "PHASE5_HTMX_ALPINE.md"
BASE_URL = os.environ.get("PHASE5_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE5_USERNAME")
PASSWORD = os.environ.get("PHASE5_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE5_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE5_USERNAME e PHASE5_PASSWORD para validar a Fase 5.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def wait_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        page.wait_for_load_state("load", timeout=5000)
    page.wait_for_timeout(700)


def login(page) -> None:
    page.goto(f"{BASE_URL}{reverse('login:loginview')}", wait_until="domcontentloaded")
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


def first_non_empty_option(page, selector: str) -> str | None:
    values = page.locator(selector + " option").evaluate_all(
        "nodes => nodes.map(node => node.value).filter(Boolean)"
    )
    return values[0] if values else None


def prepare_fiscal_validation_context() -> dict[str, object]:
    empresa = Empresa.objects.create(
        nome_razao_social="Empresa Temporaria Fase 5",
        tipo_pessoa="PJ",
    )
    PessoaJuridica.objects.create(
        pessoa_id=empresa,
        cnpj="12.345.678/0001-90",
        inscricao_estadual="123456789",
        responsavel="Validacao Fase 5",
    )

    cliente = Cliente.objects.create(
        nome_razao_social="Cliente Temporario Fase 5",
        tipo_pessoa="PF",
    )
    PessoaFisica.objects.create(
        pessoa_id=cliente,
        cpf="123.456.789-00",
        rg="12.345.678-9",
    )

    return {
        "path": reverse("fiscal:addnotafiscalsaidaview"),
        "emit_url": reverse("cadastro:infoempresa"),
        "dest_url": reverse("cadastro:infocliente"),
        "empresa_pk": str(empresa.pk),
        "cliente_pk": str(cliente.pk),
        "cleanup": {
            "empresa_pk": empresa.pk,
            "cliente_pk": cliente.pk,
        },
    }


def cleanup_fiscal_validation_context(context: dict[str, object]) -> None:
    cleanup = context.get("cleanup", {})
    empresa_pk = cleanup.get("empresa_pk")
    cliente_pk = cleanup.get("cliente_pk")
    if empresa_pk:
        Empresa.objects.filter(pk=empresa_pk).delete()
    if cliente_pk:
        Cliente.objects.filter(pk=cliente_pk).delete()


def validate_vendor_stack(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{reverse('vendas:addpedidovendaview')}", wait_until="domcontentloaded")
    wait_page(page)
    checks = page.evaluate(
        """
        () => ({
            hasHtmx: !!window.htmx,
            hasAlpine: !!window.Alpine,
            hasProgressiveApi: !!window.ProgressiveEnhancement,
            clienteProgressive: document.getElementById('id_cliente')?.dataset.progressive === 'htmx',
            transportadoraProgressive: document.getElementById('id_transportadora')?.dataset.progressive === 'htmx'
        })
        """
    )
    screenshot = OUTPUT_DIR / "vendor_stack.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "HTMX e Alpine carregados",
        "path": reverse("vendas:addpedidovendaview"),
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("htmx_loaded", checks["hasHtmx"]),
            ("alpine_loaded", checks["hasAlpine"]),
            ("progressive_api_loaded", checks["hasProgressiveApi"]),
            ("cliente_marked_progressive", checks["clienteProgressive"]),
            ("transportadora_marked_progressive", checks["transportadoraProgressive"]),
        ],
    }


def validate_venda_cliente(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{reverse('vendas:addpedidovendaview')}", wait_until="domcontentloaded")
    wait_page(page)
    cliente_value = first_non_empty_option(page, "#id_cliente")
    if not cliente_value:
        raise SystemExit("Nenhum cliente disponivel para validar o fluxo progressivo de vendas.")
    page.locator("a[href='#tab_cliente']").click()
    page.locator("#id_cliente").select_option(cliente_value)
    page.wait_for_function(
        """() => !document.querySelector('#cliente-info-panel .progressive-info-empty')""",
        timeout=10000,
    )
    panel_checks = page.evaluate(
        """
        () => ({
            hasEmptyState: !!document.querySelector('#cliente-info-panel .progressive-info-empty'),
            limite: document.getElementById('limite_credito_cliente')?.textContent.trim() || '',
            indicador: document.getElementById('ind_ie_cliente')?.textContent.trim() || ''
        })
        """
    )
    screenshot = OUTPUT_DIR / "venda_cliente.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Venda com painel progressivo de cliente",
        "path": reverse("vendas:addpedidovendaview"),
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("empty_state_removed", not panel_checks["hasEmptyState"]),
            ("limite_or_indicator_populated", bool(panel_checks["limite"] or panel_checks["indicador"])),
        ],
    }


def validate_compra_fornecedor(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    response = page.goto(f"{BASE_URL}{reverse('compras:addpedidocompraview')}", wait_until="domcontentloaded")
    wait_page(page)
    fornecedor_value = first_non_empty_option(page, "#id_fornecedor")
    if not fornecedor_value:
        raise SystemExit("Nenhum fornecedor disponivel para validar o fluxo progressivo de compras.")
    page.locator("a[href='#tab_fornecedor']").click()
    page.locator("#id_fornecedor").select_option(fornecedor_value)
    page.wait_for_function(
        """() => !document.querySelector('#fornecedor-info-panel .progressive-info-empty')""",
        timeout=10000,
    )
    panel_checks = page.evaluate(
        """
        () => ({
            hasEmptyState: !!document.querySelector('#fornecedor-info-panel .progressive-info-empty'),
            totalFields: document.querySelectorAll('#fornecedor-info-panel .display-fornecedor-field').length
        })
        """
    )
    screenshot = OUTPUT_DIR / "compra_fornecedor.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Compra com painel progressivo de fornecedor",
        "path": reverse("compras:addpedidocompraview"),
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("empty_state_removed", not panel_checks["hasEmptyState"]),
            ("fornecedor_fields_present", panel_checks["totalFields"] >= 6),
        ],
    }


def validate_fiscal_emit_dest(page, context: dict[str, object]) -> dict[str, object]:
    handlers = attach_collectors(page)
    target_path = context["path"]
    response = page.goto(f"{BASE_URL}{target_path}", wait_until="domcontentloaded")
    wait_page(page)
    page.locator("a[href='#tab_emit_dest']").click()
    page.evaluate(
        """
        ({ emitUrl, emitValue, destUrl, destValue }) => {
            window.htmx.ajax('POST', emitUrl, {
                target: '#emit-info-panel',
                swap: 'outerHTML',
                values: { pessoaId: emitValue, panel: 'emit' }
            });
            window.htmx.ajax('POST', destUrl, {
                target: '#dest-info-panel',
                swap: 'outerHTML',
                values: { pessoaId: destValue, panel: 'dest' }
            });
        }
        """,
        {
            "emitUrl": context["emit_url"],
            "emitValue": context["empresa_pk"],
            "destUrl": context["dest_url"],
            "destValue": context["cliente_pk"],
        },
    )
    page.wait_for_function(
        """() => !document.querySelector('#emit-info-panel .progressive-info-empty')""",
        timeout=10000,
    )
    page.wait_for_function(
        """() => !document.querySelector('#dest-info-panel .progressive-info-empty')""",
        timeout=10000,
    )
    panel_checks = page.evaluate(
        """
        () => ({
            emitEmptyState: !!document.querySelector('#emit-info-panel .progressive-info-empty'),
            destEmptyState: !!document.querySelector('#dest-info-panel .progressive-info-empty'),
            emitFields: document.querySelectorAll('#emit-info-panel .display-emit-field').length,
            destFields: document.querySelectorAll('#dest-info-panel .display-dest-field').length
        })
        """
    )
    screenshot = OUTPUT_DIR / "fiscal_emit_dest.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "NF-e com paineis progressivos de emitente e destinatario",
        "path": target_path,
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("emit_empty_state_removed", not panel_checks["emitEmptyState"]),
            ("dest_empty_state_removed", not panel_checks["destEmptyState"]),
            ("emit_fields_present", panel_checks["emitFields"] >= 8),
            ("dest_fields_present", panel_checks["destFields"] >= 8),
        ],
    }


def validate_lancamento_modal(page) -> dict[str, object]:
    handlers = attach_collectors(page)
    target_url = reverse("financeiro:listalancamentoview")
    response = page.goto(f"{BASE_URL}{target_url}", wait_until="domcontentloaded")
    wait_page(page)
    page.evaluate(
        """
        () => {
            document.getElementById('id_tipo_conta').value = '0';
            document.getElementById('id_conta_id').value = '1';
        }
        """
    )
    page.evaluate("$('.modal_selecionar_data').modal('show');")
    page.wait_for_timeout(300)
    button_checks = page.evaluate(
        """
        () => ({
            progressiveAttr: document.getElementById('baixar_conta_confirma')?.dataset.progressive === 'htmx',
            modalVisible: document.querySelector('.modal_selecionar_data.show') !== null,
            alpineBound: !!document.querySelector('.modal_selecionar_data[x-data]')
        })
        """
    )
    screenshot = OUTPUT_DIR / "lancamento_modal.png"
    page.screenshot(path=str(screenshot), full_page=True)
    console_messages, page_errors, request_failures = detach_collectors(page, handlers)
    return {
        "label": "Modal progressivo de gerar lancamento",
        "path": target_url,
        "status": response.status if response else None,
        "screenshot": screenshot,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "checks": [
            ("button_marked_progressive", button_checks["progressiveAttr"]),
            ("modal_visible_during_flow", button_checks["modalVisible"]),
            ("alpine_bound_to_modal", button_checks["alpineBound"]),
        ],
    }


def write_report(results: list[dict[str, object]]) -> None:
    total_console = sum(len(item["console_messages"]) for item in results)
    total_page_errors = sum(len(item["page_errors"]) for item in results)
    total_failures = sum(len(item["request_failures"]) for item in results)
    lines = [
        "# Phase 5 HTMX e Alpine.js",
        "",
        f"Atualizado em `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        "- `HTMX` adicionado como camada progressiva para consultas simples e submit de modal",
        "- `Alpine.js` adicionado apenas para estados locais de carregamento/envio",
        "- endpoints legados em JSON preservados e suporte HTMX negociado por `HX-Request`",
        "- telas validadas: `{}`".format(len(results)),
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
    fiscal_context = prepare_fiscal_validation_context()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE_PATH))
            context = browser.new_context(viewport={"width": 1440, "height": 1080})
            context.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
            page = context.new_page()
            login(page)

            results = [
                validate_vendor_stack(page),
                validate_venda_cliente(page),
                validate_compra_fornecedor(page),
                validate_fiscal_emit_dest(page, fiscal_context),
                validate_lancamento_modal(page),
            ]

            context.close()
            browser.close()
    finally:
        cleanup_fiscal_validation_context(fiscal_context)

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
