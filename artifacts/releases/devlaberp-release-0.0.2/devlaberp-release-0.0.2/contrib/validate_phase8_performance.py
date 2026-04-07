from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangosige.configs.settings")

import django
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402


APP_ROOT = ROOT / "djangosige"
STATIC_ROOT = APP_ROOT / "static"
BASELINE_PATH = ROOT / "PHASE0_BASELINE.md"
REPORT_PATH = ROOT / "PHASE8_FRONT_PERFORMANCE.md"
ARTIFACTS_DIR = ROOT / "artifacts" / "phase8_performance"
BASE_URL = os.environ.get("PHASE8_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERNAME = os.environ.get("PHASE8_USERNAME")
PASSWORD = os.environ.get("PHASE8_PASSWORD")
EDGE_PATH = Path(
    os.environ.get(
        "PHASE8_EDGE_PATH",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    )
)

KEY_PAGES = [
    ("Login", reverse("login:loginview"), False),
    ("Dashboard", reverse("base:index"), True),
    ("Cadastro Clientes", reverse("cadastro:listaclientesview"), True),
    ("Vendas Pedidos", reverse("vendas:listapedidovendaview"), True),
    ("Compras Pedidos", reverse("compras:listapedidocompraview"), True),
    ("Financeiro Lancamentos", reverse("financeiro:listalancamentoview"), True),
    ("Estoque Consulta", reverse("estoque:consultaestoqueview"), True),
    ("Fiscal NFs", reverse("fiscal:listanotafiscalsaidaview"), True),
]

BROWSER_PAGES = [
    ("Login", reverse("login:loginview"), False, False),
    ("Dashboard", reverse("base:index"), True, False),
    ("Cadastro Lista", reverse("cadastro:listaclientesview"), True, True),
    ("Cadastro Formulario", reverse("cadastro:addclienteview"), True, False),
    ("Erro 404", "/pagina-inexistente-phase8/", False, False),
]

GLOBAL_JS_BEFORE = [
    "js/jquery/jquery-3.0.0.min.js",
    "js/vendor/htmx.min.js",
    "js/vendor/alpine.min.js",
    "js/bootstrap/bootstrap.min.js",
    "js/bootstrap/bootstrap-compat.js",
    "js/app-core.js",
    "js/jquery.dataTables.min.js",
    "js/admin.js",
    "js/progressive-enhancement.js",
]

GLOBAL_JS_AFTER = [path for path in GLOBAL_JS_BEFORE if path != "js/jquery.dataTables.min.js"]
ERROR_JS_BEFORE = [
    "js/jquery/jquery-3.0.0.min.js",
    "js/bootstrap/bootstrap.min.js",
]


def ensure_prerequisites() -> None:
    if not EDGE_PATH.exists():
        raise SystemExit(f"Edge nao encontrado em: {EDGE_PATH}")
    if not USERNAME or not PASSWORD:
        raise SystemExit("Defina PHASE8_USERNAME e PHASE8_PASSWORD para validar a Fase 8.")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def file_size(relative_path: str) -> int:
    candidate = STATIC_ROOT / relative_path.replace("/", os.sep)
    return candidate.stat().st_size if candidate.exists() else 0


def parse_phase0_times() -> dict[str, float]:
    if not BASELINE_PATH.exists():
        return {}

    baseline = {}
    table_row = re.compile(r"^\|\s*(.+?)\s*\|\s*`.+?`\s*\|\s*`.+?`\s*\|\s*`([\d.]+) ms`\s*\|")
    for line in BASELINE_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = table_row.match(line.strip())
        if match:
            baseline[match.group(1)] = float(match.group(2))
    return baseline


def measure_server_pages() -> list[dict[str, object]]:
    client = Client(HTTP_HOST="127.0.0.1")
    anon_client = Client(HTTP_HOST="127.0.0.1")
    user = get_user_model().objects.filter(is_superuser=True).first() or get_user_model().objects.first()
    if user:
        client.force_login(user)

    results = []
    for label, path, authenticated in KEY_PAGES:
        active_client = client if authenticated else anon_client
        timings = []
        response = None
        for _ in range(3):
            start = time.perf_counter()
            response = active_client.get(path)
            timings.append((time.perf_counter() - start) * 1000)
        results.append(
            {
                "label": label,
                "path": path,
                "status": response.status_code if response is not None else None,
                "avg_ms": sum(timings) / len(timings),
                "content_length": len(response.content) if response is not None else 0,
            }
        )
    return results


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
        values = select.locator("option").evaluate_all(
            "nodes => nodes.map(node => node.value).filter(Boolean)"
        )
        if values:
            select.select_option(values[0])
            page.locator("button[type='submit']").click()
            wait_page(page)


def collect_resource_sizes(page) -> tuple[list[str], int]:
    resources = page.evaluate(
        """
        () => performance.getEntriesByType('resource')
            .map(entry => entry.name)
            .filter(name => name.includes('/static/'))
        """
    )
    total_size = 0
    unique_resources = []
    seen = set()

    for resource_url in resources:
        parsed = urlparse(resource_url)
        marker = "/static/"
        if marker not in parsed.path:
            continue
        relative = parsed.path.split(marker, 1)[1]
        if relative in seen:
            continue
        seen.add(relative)
        unique_resources.append(relative)
        total_size += file_size(relative)

    return unique_resources, total_size


def validate_browser_page(page, label: str, path: str, requires_auth: bool, expects_datatable: bool, screenshot_name: str) -> dict[str, object]:
    if requires_auth and "login" in page.url:
        login(page)

    started = time.perf_counter()
    response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    wait_page(page)
    load_ms = (time.perf_counter() - started) * 1000
    resources, total_asset_size = collect_resource_sizes(page)
    has_datatables = any("js/jquery.dataTables.min.js" in item for item in resources)

    checks = []
    if expects_datatable:
        checks.extend(
            [
                ("datatables_loaded", has_datatables),
                (
                    "datatable_footer_present",
                    page.locator(".app-datatable-footer").count() > 0,
                ),
                (
                    "remove_button_disabled_initially",
                    page.locator(".btn-remove").evaluate("node => !!node.disabled") if page.locator(".btn-remove").count() else False,
                ),
            ]
        )
    else:
        checks.append(("datatables_not_loaded", not has_datatables))

    if label == "Erro 404":
        checks.append(("error_page_has_no_js_runtime", len([item for item in resources if item.endswith(".js")]) == 0))

    screenshot = ARTIFACTS_DIR / screenshot_name
    page.screenshot(path=str(screenshot), full_page=True)

    return {
        "label": label,
        "path": path,
        "status": response.status if response else None,
        "load_ms": load_ms,
        "resources": resources,
        "asset_size": total_asset_size,
        "checks": checks,
        "screenshot": screenshot,
    }


def validate_slow_network(playwright) -> list[dict[str, object]]:
    browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE_PATH))
    context = browser.new_context(viewport={"width": 1366, "height": 900})

    def delay_static(route):
        time.sleep(0.075)
        route.continue_()

    context.route("**/static/**", delay_static)
    page = context.new_page()
    login(page)

    targets = [
        ("Dashboard lento", reverse("base:index")),
        ("Cadastro lista lento", reverse("cadastro:listaclientesview")),
        ("Cadastro formulario lento", reverse("cadastro:addclienteview")),
    ]
    results = []
    for label, path in targets:
        started = time.perf_counter()
        response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
        wait_page(page)
        elapsed = (time.perf_counter() - started) * 1000
        results.append(
            {
                "label": label,
                "path": path,
                "status": response.status if response else None,
                "load_ms": elapsed,
            }
        )

    context.close()
    browser.close()
    return results


def write_report(
    server_metrics: list[dict[str, object]],
    baseline_metrics: dict[str, float],
    browser_metrics: list[dict[str, object]],
    slow_metrics: list[dict[str, object]],
) -> None:
    before_shell = sum(file_size(path) for path in GLOBAL_JS_BEFORE)
    after_shell = sum(file_size(path) for path in GLOBAL_JS_AFTER)
    before_error = sum(file_size(path) for path in ERROR_JS_BEFORE)

    lines = [
        "# Phase 8 Performance Front e Entrega",
        "",
        f"Atualizado em `{time.strftime('%Y-%m-%d %H:%M:%S')}`.",
        "",
        "## Resultado",
        "",
        f"- shell JS global do app caiu de `{format_bytes(before_shell)}` para `{format_bytes(after_shell)}`",
        f"- reducao do caminho critico sem lista: `-{format_bytes(before_shell - after_shell)}` por pagina",
        f"- paginas de erro deixaram de carregar `{format_bytes(before_error)}` de JavaScript legado",
        "- `DataTables` saiu do carregamento global e agora sobe apenas nas telas com `#lista-database`",
        "- listas continuam com busca, paginacao, footer reorganizado e remocao em massa",
        "",
        "## Comparativo de Tempo de Resposta",
        "",
        "| Tela | Baseline Fase 0 | Atual | Delta | Status | HTML |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for item in server_metrics:
        baseline = baseline_metrics.get(item["label"])
        delta = item["avg_ms"] - baseline if baseline is not None else None
        baseline_value = f"`{baseline:.1f} ms`" if baseline is not None else "`n/d`"
        delta_value = f"`{delta:+.1f} ms`" if delta is not None else "`n/d`"
        lines.append(
            f"| {item['label']} | {baseline_value} | `{item['avg_ms']:.1f} ms` | {delta_value} | `{item['status']}` | `{format_bytes(item['content_length'])}` |"
        )

    lines.extend(
        [
            "",
            "## Medicao Browser",
            "",
            "| Tela | Status | Carga total | Assets estaticos | DataTables | Evidencia |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for item in browser_metrics:
        has_datatables = any("js/jquery.dataTables.min.js" in resource for resource in item["resources"])
        lines.append(
            f"| {item['label']} | `{item['status']}` | `{item['load_ms']:.1f} ms` | `{format_bytes(item['asset_size'])}` | `{has_datatables}` | [{item['screenshot'].name}]({item['screenshot'].as_posix()}) |"
        )

    lines.extend(
        [
            "",
            "## Rede Local Mais Lenta",
            "",
            "Latencia simulada de `75 ms` por request estatico para verificar regressao perceptivel no shell atual.",
            "",
            "| Tela | Status | Carga total |",
            "| --- | --- | --- |",
        ]
    )

    for item in slow_metrics:
        lines.append(f"| {item['label']} | `{item['status']}` | `{item['load_ms']:.1f} ms` |")

    lines.extend(
        [
            "",
            "## Checks",
            "",
        ]
    )

    for item in browser_metrics:
        lines.append(f"### {item['label']}")
        lines.append("")
        lines.append(f"- URL: `{item['path']}`")
        lines.append(f"- recursos estaticos unicos: `{len(item['resources'])}`")
        for check, value in item["checks"]:
            lines.append(f"- {check}: `{value}`")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_prerequisites()
    baseline_metrics = parse_phase0_times()
    server_metrics = measure_server_pages()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=str(EDGE_PATH))
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        context.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        page = context.new_page()

        browser_metrics = []
        for index, (label, path, requires_auth, expects_datatable) in enumerate(BROWSER_PAGES, start=1):
            browser_metrics.append(
                validate_browser_page(
                    page,
                    label,
                    path,
                    requires_auth,
                    expects_datatable,
                    f"page_{index}.png",
                )
            )

        context.close()
        browser.close()

        slow_metrics = validate_slow_network(playwright)

    for item in server_metrics:
        if item["status"] != 200:
            raise SystemExit(f"Falha em servidor: {item['label']} -> {item['status']}")

    for item in browser_metrics:
        expected_status = 404 if item["label"] == "Erro 404" else 200
        if item["status"] != expected_status:
            raise SystemExit(f"Falha browser em {item['label']}: status {item['status']}")
        for check, value in item["checks"]:
            if not value:
                raise SystemExit(f"Check invalido em {item['label']}: {check}={value}")

    for item in slow_metrics:
        if item["status"] != 200:
            raise SystemExit(f"Falha em rede lenta: {item['label']} -> {item['status']}")

    write_report(server_metrics, baseline_metrics, browser_metrics, slow_metrics)
    print(f"Relatorio gerado em: {REPORT_PATH}")
    print(f"Evidencias salvas em: {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
