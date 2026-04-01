import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangosige.configs")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


APP_ROOT = ROOT / "djangosige"
STATIC_ROOT = APP_ROOT / "static"
TEMPLATE_ROOT = APP_ROOT / "templates"
OUTPUT_PATH = ROOT / "PHASE0_BASELINE.md"

TEXT_EXTENSIONS = {".html", ".css", ".js", ".py", ".md"}
RUNTIME_SUFFIXES = {".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".svg", ".ico", ".png", ".jpg", ".jpeg", ".gif"}
DATA_SUFFIXES = {".csv"}

PLUGIN_PATTERNS = {
    "Bootstrap 3": ["bootstrap.min.css", "bootstrap.min.js", "data-toggle="],
    "jQuery": ["jquery-3.0.0.min.js", "$.Admin", "typeof jQuery"],
    "DataTables": ["jquery.dataTables.min.js", "DataTable(", "dataTable("],
    "jQuery UI": ["jquery-ui.min.js", "jquery-ui.min.css", "autocomplete(", "datepicker("],
    "Datetimepicker": ["jquery.datetimepicker", "datetimepicker("],
    "jQuery Mask": ["jquery.mask.js", ".mask("],
    "Multi Select": ["jquery.multi-select.js", "multiSelect("],
    "Materialize": ["materialize.css", "filled-in", "chk-col-light-blue"],
    "Material Icons": ["material-icons", "MaterialIcons-Regular"],
}

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

VISUAL_BASELINE_TARGETS = [
    ("Login", "Tela de autenticacao e estado de erro", "djangosige/templates/login/login.html"),
    ("Dashboard", "Cards, tabelas e hierarquia visual da home", "djangosige/templates/base/index.html"),
    ("Lista padrao", "Tabela, busca, botoes e acao em massa", "djangosige/templates/cadastro/pessoa_list.html"),
    ("Formulario padrao", "Inputs, tabs e botoes de salvar", "djangosige/templates/cadastro/pessoa_edit.html"),
    ("Modal padrao", "Confirmacoes e acoes de usuario", "djangosige/templates/base/modal.html"),
    ("Fluxo financeiro", "Tabela densa e filtros operacionais", "djangosige/templates/financeiro/lancamento/lancamento_list.html"),
    ("Nota fiscal", "Tabs, campos densos e modais detalhados", "djangosige/templates/fiscal/nota_fiscal/nota_fiscal_edit.html"),
]


def format_bytes(size):
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def iter_text_files():
    search_roots = [TEMPLATE_ROOT, STATIC_ROOT]
    for base in search_roots:
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
                yield path


def collect_plugin_usage():
    results = {}
    for plugin, patterns in PLUGIN_PATTERNS.items():
        matches = []
        for path in iter_text_files():
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for line_number, line in enumerate(content, start=1):
                if any(pattern in line for pattern in patterns):
                    matches.append((path.relative_to(ROOT).as_posix(), line_number, line.strip()))
                    break
        results[plugin] = matches[:12]
    return results


def collect_static_sizes():
    all_files = [path for path in STATIC_ROOT.rglob("*") if path.is_file()]
    runtime_files = [path for path in all_files if path.suffix.lower() in RUNTIME_SUFFIXES]
    data_files = [path for path in all_files if path.suffix.lower() in DATA_SUFFIXES]

    return {
        "all_count": len(all_files),
        "all_size": sum(path.stat().st_size for path in all_files),
        "runtime_count": len(runtime_files),
        "runtime_size": sum(path.stat().st_size for path in runtime_files),
        "data_count": len(data_files),
        "data_size": sum(path.stat().st_size for path in data_files),
        "top_runtime": sorted(runtime_files, key=lambda p: p.stat().st_size, reverse=True)[:15],
        "top_all": sorted(all_files, key=lambda p: p.stat().st_size, reverse=True)[:15],
    }


def measure_pages():
    client = Client(HTTP_HOST="127.0.0.1")
    user = get_user_model().objects.filter(is_superuser=True).first() or get_user_model().objects.first()
    if user:
        client.force_login(user)

    results = []
    anon_client = Client(HTTP_HOST="127.0.0.1")

    for label, url, authenticated in KEY_PAGES:
        timings = []
        response = None
        active_client = client if authenticated else anon_client
        for _ in range(3):
            start = time.perf_counter()
            response = active_client.get(url)
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)
        results.append(
            {
                "label": label,
                "url": url,
                "status": response.status_code if response is not None else None,
                "avg_ms": sum(timings) / len(timings),
                "max_ms": max(timings),
                "content_length": len(response.content) if response is not None else 0,
            }
        )
    return results


def collect_base_imports():
    base_template = (TEMPLATE_ROOT / "base" / "base.html").read_text(encoding="utf-8", errors="ignore")
    return re.findall(r"static '([^']+)'", base_template)


def build_markdown():
    plugin_usage = collect_plugin_usage()
    static_sizes = collect_static_sizes()
    page_metrics = measure_pages()
    base_imports = collect_base_imports()

    lines = []
    lines.append("# Phase 0 Baseline")
    lines.append("")
    lines.append("Atualizado em `2026-04-01`.")
    lines.append("")
    lines.append("## Resumo")
    lines.append("")
    lines.append("- baseline tecnico consolidado antes da modernizacao estrutural do frontend")
    lines.append("- foco em stack atual, plugins ativos, peso dos assets e tempos aproximados das telas principais")
    lines.append("- baseline visual manual deve partir das telas-alvo listadas neste arquivo")
    lines.append("")
    lines.append("## Stack Atual")
    lines.append("")
    lines.append("- renderizacao: `Django templates`")
    lines.append("- framework CSS principal: `Bootstrap 3.4.1`")
    lines.append("- CSS legado adicional: `Materialize 0.97.7` importado por [style.css](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/css/style.css)")
    lines.append("- JavaScript principal: `jQuery 3.7.1` e [admin.js](c:/Users/lojac/OneDrive/Documentos/GitHub/devlab-system/djangosige/static/js/admin.js)")
    lines.append("- estaticos: `WhiteNoise` + `collectstatic`")
    lines.append("")
    lines.append("## Imports Base")
    lines.append("")
    for asset in base_imports:
        lines.append(f"- `{asset}`")
    lines.append("")
    lines.append("## Assets Estaticos")
    lines.append("")
    lines.append(f"- total de arquivos em `djangosige/static`: `{static_sizes['all_count']}`")
    lines.append(f"- tamanho total em `djangosige/static`: `{format_bytes(static_sizes['all_size'])}`")
    lines.append(f"- arquivos de runtime UI: `{static_sizes['runtime_count']}`")
    lines.append(f"- tamanho de runtime UI: `{format_bytes(static_sizes['runtime_size'])}`")
    lines.append(f"- arquivos de dados auxiliares (`csv`): `{static_sizes['data_count']}`")
    lines.append(f"- tamanho de dados auxiliares: `{format_bytes(static_sizes['data_size'])}`")
    lines.append("")
    lines.append("### Top 15 Assets de Runtime")
    lines.append("")
    for path in static_sizes["top_runtime"]:
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"- `{relative}`: `{format_bytes(path.stat().st_size)}`")
    lines.append("")
    lines.append("### Top 15 Assets Gerais")
    lines.append("")
    for path in static_sizes["top_all"]:
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"- `{relative}`: `{format_bytes(path.stat().st_size)}`")
    lines.append("")
    lines.append("## Plugins e Bibliotecas Encontradas")
    lines.append("")
    for plugin, matches in plugin_usage.items():
        lines.append(f"### {plugin}")
        lines.append("")
        if not matches:
            lines.append("- nenhum ponto encontrado")
        else:
            for file_path, line_number, line in matches:
                lines.append(f"- `{file_path}:{line_number}`")
                lines.append(f"  Trecho: `{line[:140]}`")
        lines.append("")
    lines.append("## Telas-Alvo para Baseline Visual")
    lines.append("")
    for title, reason, template in VISUAL_BASELINE_TARGETS:
        lines.append(f"- `{title}`: {reason}")
        lines.append(f"  Template base: `{template}`")
    lines.append("")
    lines.append("## Tempos Aproximados de Resposta")
    lines.append("")
    lines.append("Medicao feita com `Django test client`, 3 requisicoes por pagina, usando usuario autenticado nas telas protegidas.")
    lines.append("")
    lines.append("| Tela | URL | Status | Media | Pico | Tamanho HTML |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for metric in page_metrics:
        lines.append(
            f"| {metric['label']} | `{metric['url']}` | `{metric['status']}` | `{metric['avg_ms']:.1f} ms` | `{metric['max_ms']:.1f} ms` | `{format_bytes(metric['content_length'])}` |"
        )
    lines.append("")
    lines.append("## Componentes Legados com Maior Impacto")
    lines.append("")
    lines.append("- `Materialize`: ainda entra via `@import` em `style.css` e influencia checkboxes, radios e estilos de form")
    lines.append("- `Bootstrap 3`: base de layout, navbar, modal, tabs e dropdowns")
    lines.append("- `jQuery + admin.js`: controla menu lateral, modal de mensagens, DataTables, formsets, datepickers, masks e automacoes de formulario")
    lines.append("- `DataTables`: padrao de listas administrativas")
    lines.append("- `jQuery UI`: datepicker e autocomplete")
    lines.append("- `jquery.datetimepicker`: campos de data e hora")
    lines.append("- `jquery.mask`: mascaras de moeda e campos numericos")
    lines.append("- `jquery.multi-select`: selecao multipla em pontos especificos")
    lines.append("")
    lines.append("## Baseline de Validacao")
    lines.append("")
    lines.append("- `python manage.py check`: executar a cada fase")
    lines.append("- `python manage.py test djangosige.tests.validation`: baseline funcional principal")
    lines.append("- `python contrib/validate_smoke.py`: smoke de rotas sem parametros")
    lines.append("")
    lines.append("## Observacoes")
    lines.append("")
    lines.append("- o maior peso absoluto em `static/` nao esta no runtime, e sim nas tabelas CSV auxiliares do dominio")
    lines.append("- os maiores pesos de runtime concentram-se em `admin.js`, `bootstrap.min.css`, `jquery`, `DataTables`, `jQuery UI`, `datetimepicker` e fontes de icones")
    lines.append("- a migracao mais sensivel sera a retirada de `Materialize` e a troca de `Bootstrap 3` por `Bootstrap 5`, porque essas camadas afetam praticamente todo o markup")
    lines.append("")
    return "\n".join(lines)


def main():
    OUTPUT_PATH.write_text(build_markdown(), encoding="utf-8")
    print(f"Baseline gerado em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
