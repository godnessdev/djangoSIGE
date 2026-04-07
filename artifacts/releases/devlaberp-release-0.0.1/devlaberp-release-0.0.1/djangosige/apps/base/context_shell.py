# -*- coding: utf-8 -*-

from datetime import datetime

from django.core.cache import cache
from django.db.models import F
from django.urls import reverse

from djangosige.apps.cadastro.models import Produto
from djangosige.apps.financeiro.models import Saida
from djangosige.apps.fiscal.models import NotaFiscalSaida


SHELL_COUNTS_CACHE_KEY = "shell_navigation_counts_v1"
SHELL_COUNTS_CACHE_TTL = 60


def _compute_shell_counts():
    today = datetime.now().date()
    return {
        "contas_vencidas": Saida.objects.filter(
            data_vencimento__lt=today,
            status__in=["1", "2"],
        ).count(),
        "estoque_baixo": Produto.objects.filter(
            estoque_atual__lte=F("estoque_minimo")
        ).count(),
        "nfe_rejeitada": NotaFiscalSaida.objects.filter(status_nfe="5").count(),
    }


def shell_navigation(request):
    context = {
        "shell_notifications": [],
        "shell_notifications_total": 0,
        "shell_menu_badges": {"estoque": 0, "financeiro": 0, "fiscal": 0},
        "shell_quick_create": [],
        "shell_shortcuts": [],
        "shell_search_items": [],
    }

    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return context

    counts = cache.get(SHELL_COUNTS_CACHE_KEY)
    if counts is None:
        counts = _compute_shell_counts()
        cache.set(SHELL_COUNTS_CACHE_KEY, counts, SHELL_COUNTS_CACHE_TTL)

    user = request.user

    quick_create = []
    shortcuts = []
    search_items = []

    def add_nav_item(collection, label, href, keywords, permission=None):
        if permission and not user.has_perm(permission):
            return
        collection.append({
            "label": label,
            "href": href,
            "keywords": keywords,
        })

    def add_action(label, href, permission=None, style="secondary"):
        if permission and not user.has_perm(permission):
            return
        item = {"label": label, "href": href, "style": style}
        quick_create.append(item)
        return item

    if add_action("Nova venda", reverse("vendas:addpedidovendaview"), "vendas.add_pedidovenda", "primary"):
        shortcuts.append({"label": "Nova venda", "href": reverse("vendas:addpedidovendaview"), "style": "primary"})
    add_action("Nova compra", reverse("compras:addpedidocompraview"), "compras.add_pedidocompra")
    add_action("Novo cliente", reverse("cadastro:addclienteview"), "cadastro.add_cliente")
    add_action("Novo produto", reverse("cadastro:addprodutoview"), "cadastro.add_produto")
    if add_action("Lancar conta", reverse("financeiro:addcontapagarview"), "financeiro.add_saida"):
        shortcuts.append({"label": "Conta", "href": reverse("financeiro:addcontapagarview"), "style": "secondary"})
    if add_action("Entrada de estoque", reverse("estoque:addentradaestoqueview"), "estoque.add_entradaestoque"):
        shortcuts.append({"label": "Estoque", "href": reverse("estoque:addentradaestoqueview"), "style": "secondary"})
    if user.has_perm("cadastro.view_produto"):
        shortcuts.append({
            "label": "Pesquisar preco",
            "href": reverse("cadastro:consultaprecoproduto"),
            "style": "secondary",
            "mode": "price_lookup",
        })

    nav_specs = (
        ("Dashboard", reverse("base:index"), "inicio dashboard painel home", None),
        ("Clientes", reverse("cadastro:listaclientesview"), "buscar cliente cadastro pessoa", "cadastro.view_cliente"),
        ("Produtos", reverse("cadastro:listaprodutosview"), "buscar produto estoque cadastro item", "cadastro.view_produto"),
        ("Fornecedores", reverse("cadastro:listafornecedoresview"), "fornecedor compra cadastro parceiro", "cadastro.view_fornecedor"),
        ("Pedidos de venda", reverse("vendas:listapedidovendaview"), "pedido venda pedido comercial", "vendas.view_pedidovenda"),
        ("Pedidos de compra", reverse("compras:listapedidocompraview"), "pedido compra suprimentos", "compras.view_pedidocompra"),
        ("Notas fiscais", reverse("fiscal:listanotafiscalsaidaview"), "nf nfe nota fiscal saida", "fiscal.view_notafiscalsaida"),
        ("Financeiro", reverse("financeiro:listalancamentoview"), "lancamento conta financeiro pagar receber", "financeiro.view_lancamento"),
        ("Fluxo de caixa", reverse("financeiro:fluxodecaixaview"), "caixa fluxo financeiro", "financeiro.acesso_fluxodecaixa"),
        ("Estoque", reverse("estoque:consultaestoqueview"), "estoque consulta produto saldo", None),
    )
    for label, href, keywords, permission in nav_specs:
        add_nav_item(search_items, label, href, keywords, permission)

    notifications = []
    if user.has_perm("financeiro.view_lancamento"):
        notifications.append({
            "label": "Contas vencidas",
            "count": counts["contas_vencidas"],
            "href": reverse("financeiro:listacontapagaratrasadasview"),
            "tone": "danger" if counts["contas_vencidas"] else "neutral",
            "icon": "error",
            "description": "Titulos pendentes que exigem acao imediata.",
        })
        context["shell_menu_badges"]["financeiro"] = counts["contas_vencidas"]

    if user.has_perm("cadastro.view_produto"):
        notifications.append({
            "label": "Estoque baixo",
            "count": counts["estoque_baixo"],
            "href": reverse("cadastro:listaprodutosbaixoestoqueview"),
            "tone": "warning" if counts["estoque_baixo"] else "neutral",
            "icon": "inventory_2",
            "description": "Produtos abaixo do minimo cadastrado.",
        })
        context["shell_menu_badges"]["estoque"] = counts["estoque_baixo"]

    if user.has_perm("fiscal.view_notafiscalsaida"):
        notifications.append({
            "label": "NF rejeitada",
            "count": counts["nfe_rejeitada"],
            "href": reverse("fiscal:listanotafiscalsaidaview"),
            "tone": "danger" if counts["nfe_rejeitada"] else "neutral",
            "icon": "receipt_long",
            "description": "Notas de saida com status de rejeicao.",
        })
        context["shell_menu_badges"]["fiscal"] = counts["nfe_rejeitada"]

    context["shell_notifications"] = notifications
    context["shell_notifications_total"] = sum(item["count"] for item in notifications)
    context["shell_quick_create"] = quick_create
    context["shell_shortcuts"] = shortcuts[:4]
    context["shell_search_items"] = search_items
    return context
