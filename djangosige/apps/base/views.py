# -*- coding: utf-8 -*-

from decimal import Decimal
from django.views.generic import TemplateView
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse

from djangosige.apps.cadastro.models import Cliente, Fornecedor, Produto, Empresa, Transportadora
from djangosige.apps.vendas.models import OrcamentoVenda, PedidoVenda
from djangosige.apps.compras.models import OrcamentoCompra, PedidoCompra
from djangosige.apps.financeiro.models import MovimentoCaixa, Entrada, Saida

from datetime import datetime, timedelta


class IndexView(TemplateView):
    template_name = 'base/index.html'

    def _format_currency(self, value):
        value = Decimal(value or 0)
        inteiro, decimal = f"{value:.2f}".split(".")
        grupos = []
        while inteiro:
            grupos.append(inteiro[-3:])
            inteiro = inteiro[:-3]
        return "R$ {0},{1}".format(".".join(reversed(grupos)), decimal)

    def _sum_queryset(self, queryset, field_name='valor_liquido'):
        return queryset.aggregate(
            total=Coalesce(Sum(field_name), Decimal('0.00'))
        )['total']

    def _make_stat_card(self, title, value, subtitle, href, tone='neutral', icon=''):
        return {
            'title': title,
            'value': value,
            'subtitle': subtitle,
            'href': href,
            'tone': tone,
            'icon': icon,
        }

    def _make_alert_card(self, title, count, value, description, href, action_label, severity):
        is_active = bool(count)

        tone_map = {
            'danger': 'danger',
            'warning': 'warning',
        }
        status_map = {
            'danger': ('Critico', 'error_outline', 'btn-red'),
            'warning': ('Atencao', 'schedule', 'btn-dashboard-warning'),
            'neutral': ('OK', 'check_circle', ''),
        }

        tone = tone_map.get(severity, 'neutral') if is_active else 'neutral'
        status_label, status_icon, action_class = status_map[tone]

        return {
            'title': title,
            'count': count,
            'count_display': str(count) if is_active else 'OK',
            'value': value,
            'description': description,
            'href': href,
            'action_label': action_label,
            'tone': tone,
            'status_label': status_label,
            'status_icon': status_icon,
            'action_class': action_class,
            'show_action': is_active,
        }

    def _build_chart(self, movimentos, data_atual):
        chart_dates = [data_atual - timedelta(days=offset) for offset in range(6, -1, -1)]
        movements_by_date = {movimento.data_movimento: movimento for movimento in movimentos}
        chart_rows = []
        max_value = Decimal('0.00')

        for current_date in chart_dates:
            movimento = movements_by_date.get(current_date)
            entradas = movimento.entradas if movimento else Decimal('0.00')
            saidas = movimento.saidas if movimento else Decimal('0.00')
            chart_rows.append({
                'label': current_date.strftime('%d/%m'),
                'entradas': entradas,
                'saidas': saidas,
                'entradas_display': self._format_currency(entradas),
                'saidas_display': self._format_currency(saidas),
            })
            max_value = max(max_value, entradas, saidas)

        max_value = max_value or Decimal('1.00')
        width = 680
        height = 250
        left_padding = 44
        right_padding = 18
        top_padding = 20
        bottom_padding = 46
        chart_height = height - top_padding - bottom_padding
        plot_width = width - left_padding - right_padding
        step_x = plot_width / max(len(chart_rows) - 1, 1)

        def point_y(raw_value):
            ratio = float(Decimal(raw_value) / max_value)
            return top_padding + (chart_height * (1 - ratio))

        entrada_points = []
        saida_points = []
        for index, row in enumerate(chart_rows):
            x = left_padding + (index * step_x)
            entradas_y = point_y(row['entradas'])
            saidas_y = point_y(row['saidas'])
            row['x'] = round(x, 2)
            row['entradas_y'] = round(entradas_y, 2)
            row['saidas_y'] = round(saidas_y, 2)
            row['x_attr'] = f"{row['x']:.2f}"
            row['entradas_y_attr'] = f"{row['entradas_y']:.2f}"
            row['saidas_y_attr'] = f"{row['saidas_y']:.2f}"
            entrada_points.append(f"{row['x_attr']},{row['entradas_y_attr']}")
            saida_points.append(f"{row['x_attr']},{row['saidas_y_attr']}")

        return {
            'rows': chart_rows,
            'width': width,
            'height': height,
            'plot_left': f"{left_padding:.2f}",
            'plot_right': f"{(width - right_padding):.2f}",
            'plot_top': f"{top_padding:.2f}",
            'plot_middle': f"{(top_padding + (chart_height / 2)):.2f}",
            'plot_base': f"{(top_padding + chart_height):.2f}",
            'label_y': f"{(height - 12):.2f}",
            'entrada_path': " ".join(entrada_points),
            'saida_path': " ".join(saida_points),
            'grid_values': [
                self._format_currency(max_value),
                self._format_currency(max_value / 2),
                self._format_currency(Decimal('0.00')),
            ],
        }

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        quantidade_cadastro = {}
        agenda_hoje = {}
        alertas = {}
        data_atual = datetime.now().date()

        context['data_atual'] = data_atual.strftime('%d/%m/%Y')

        quantidade_cadastro['clientes'] = Cliente.objects.all().count()
        quantidade_cadastro['fornecedores'] = Fornecedor.objects.all().count()
        quantidade_cadastro['produtos'] = Produto.objects.all().count()
        quantidade_cadastro['empresas'] = Empresa.objects.all().count()
        quantidade_cadastro[
            'transportadoras'] = Transportadora.objects.all().count()
        context['quantidade_cadastro'] = quantidade_cadastro

        agenda_hoje['orcamento_venda_hoje'] = OrcamentoVenda.objects.filter(
            data_vencimento=data_atual, status='0').count()
        agenda_hoje['orcamento_compra_hoje'] = OrcamentoCompra.objects.filter(
            data_vencimento=data_atual, status='0').count()
        agenda_hoje['pedido_venda_hoje'] = PedidoVenda.objects.filter(
            data_entrega=data_atual, status='0').count()
        agenda_hoje['pedido_compra_hoje'] = PedidoCompra.objects.filter(
            data_entrega=data_atual, status='0').count()
        agenda_hoje['contas_receber_hoje'] = Entrada.objects.filter(
            data_vencimento=data_atual, status__in=['1', '2']).count()
        agenda_hoje['contas_pagar_hoje'] = Saida.objects.filter(
            data_vencimento=data_atual, status__in=['1', '2']).count()
        context['agenda_hoje'] = agenda_hoje

        alertas['produtos_baixo_estoque'] = Produto.objects.filter(
            estoque_atual__lte=F('estoque_minimo')).count()
        alertas['orcamentos_venda_vencidos'] = OrcamentoVenda.objects.filter(
            data_vencimento__lte=data_atual, status='0').count()
        alertas['pedidos_venda_atrasados'] = PedidoVenda.objects.filter(
            data_entrega__lte=data_atual, status='0').count()
        alertas['orcamentos_compra_vencidos'] = OrcamentoCompra.objects.filter(
            data_vencimento__lte=data_atual, status='0').count()
        alertas['pedidos_compra_atrasados'] = PedidoCompra.objects.filter(
            data_entrega__lte=data_atual, status='0').count()
        alertas['contas_receber_atrasadas'] = Entrada.objects.filter(
            data_vencimento__lte=data_atual, status__in=['1', '2']).count()
        alertas['contas_pagar_atrasadas'] = Saida.objects.filter(
            data_vencimento__lte=data_atual, status__in=['1', '2']).count()
        context['alertas'] = alertas

        try:
            context['movimento_dia'] = MovimentoCaixa.objects.get(
                data_movimento=data_atual)
        except (MovimentoCaixa.DoesNotExist, ObjectDoesNotExist):
            ultimo_mvmt = MovimentoCaixa.objects.filter(
                data_movimento__lt=data_atual)
            if ultimo_mvmt:
                context['saldo'] = ultimo_mvmt.latest(
                    'data_movimento').saldo_final
            else:
                context['saldo'] = '0,00'

        movimento_dia = context.get('movimento_dia')
        saldo_atual = getattr(movimento_dia, 'saldo_final', None)
        if saldo_atual is None:
            saldo_atual = ultimo_mvmt.latest('data_movimento').saldo_final if 'ultimo_mvmt' in locals() and ultimo_mvmt else Decimal('0.00')
        entradas_hoje_valor = getattr(movimento_dia, 'entradas', Decimal('0.00')) if movimento_dia else Decimal('0.00')
        saidas_hoje_valor = getattr(movimento_dia, 'saidas', Decimal('0.00')) if movimento_dia else Decimal('0.00')
        resultado_hoje_valor = entradas_hoje_valor - saidas_hoje_valor

        contas_receber_hoje_qs = Entrada.objects.filter(data_vencimento=data_atual, status__in=['1', '2'])
        contas_pagar_hoje_qs = Saida.objects.filter(data_vencimento=data_atual, status__in=['1', '2'])
        contas_receber_atrasadas_qs = Entrada.objects.filter(data_vencimento__lt=data_atual, status__in=['1', '2'])
        contas_pagar_atrasadas_qs = Saida.objects.filter(data_vencimento__lt=data_atual, status__in=['1', '2'])

        contas_receber_hoje_valor = self._sum_queryset(contas_receber_hoje_qs)
        contas_pagar_hoje_valor = self._sum_queryset(contas_pagar_hoje_qs)
        contas_receber_atrasadas_valor = self._sum_queryset(contas_receber_atrasadas_qs)
        contas_pagar_atrasadas_valor = self._sum_queryset(contas_pagar_atrasadas_qs)

        open_sales = PedidoVenda.objects.filter(status='0').count()
        open_purchases = PedidoCompra.objects.filter(status='0').count()
        open_sale_quotes = OrcamentoVenda.objects.filter(status='0').count()
        open_purchase_quotes = OrcamentoCompra.objects.filter(status='0').count()

        user = self.request.user
        kpi_cards = []
        if user.has_perm('financeiro.acesso_fluxodecaixa') or user.has_perm('financeiro.view_lancamento'):
            kpi_cards.extend([
                self._make_stat_card(
                    title='Caixa atual',
                    value=self._format_currency(saldo_atual),
                    subtitle='Saldo consolidado para o dia atual',
                    href=reverse('financeiro:fluxodecaixaview'),
                    tone='brand',
                    icon='account_balance_wallet',
                ),
                self._make_stat_card(
                    title='Receita hoje',
                    value=self._format_currency(entradas_hoje_valor),
                    subtitle='{0} recebimento(s) previsto(s) para hoje'.format(agenda_hoje['contas_receber_hoje']),
                    href=reverse('financeiro:listacontareceberhojeview'),
                    tone='success',
                    icon='trending_up',
                ),
                self._make_stat_card(
                    title='Despesa hoje',
                    value=self._format_currency(saidas_hoje_valor),
                    subtitle='{0} pagamento(s) previsto(s) para hoje'.format(agenda_hoje['contas_pagar_hoje']),
                    href=reverse('financeiro:listacontapagarhojeview'),
                    tone='warning',
                    icon='trending_down',
                ),
                self._make_stat_card(
                    title='Resultado do dia',
                    value=self._format_currency(resultado_hoje_valor),
                    subtitle='Lucro operacional do caixa de hoje' if resultado_hoje_valor >= 0 else 'Prejuizo operacional do caixa de hoje',
                    href=reverse('financeiro:fluxodecaixaview'),
                    tone='success' if resultado_hoje_valor >= 0 else 'danger',
                    icon='assessment',
                ),
            ])

        if user.has_perm('vendas.view_pedidovenda'):
            kpi_cards.append(
                self._make_stat_card(
                    title='Pedidos em aberto',
                    value=str(open_sales),
                    subtitle='{0} entrega(s) programada(s) para hoje'.format(agenda_hoje['pedido_venda_hoje']),
                    href=reverse('vendas:listapedidovendaview'),
                    tone='brand',
                    icon='shopping_basket',
                )
            )

        if user.has_perm('compras.view_pedidocompra'):
            kpi_cards.append(
                self._make_stat_card(
                    title='Compras em aberto',
                    value=str(open_purchases),
                    subtitle='{0} entrega(s) programada(s) para hoje'.format(agenda_hoje['pedido_compra_hoje']),
                    href=reverse('compras:listapedidocompraview'),
                    tone='brand',
                    icon='shopping_cart',
                )
            )

        alert_cards = []
        if user.has_perm('financeiro.view_lancamento'):
            alert_cards.extend([
                self._make_alert_card(
                    title='Contas a pagar atrasadas',
                    count=alertas['contas_pagar_atrasadas'],
                    value=self._format_currency(contas_pagar_atrasadas_valor),
                    description='Titulos pendentes e vencidos exigem acao imediata.',
                    href=reverse('financeiro:listacontapagaratrasadasview'),
                    action_label='Ver agora',
                    severity='danger',
                ),
                self._make_alert_card(
                    title='Contas a receber atrasadas',
                    count=alertas['contas_receber_atrasadas'],
                    value=self._format_currency(contas_receber_atrasadas_valor),
                    description='Recebimentos vencidos afetam o caixa projetado.',
                    href=reverse('financeiro:listacontareceberatrasadasview'),
                    action_label='Cobrar agora',
                    severity='warning',
                ),
            ])

        if user.has_perm('cadastro.view_produto'):
            alert_cards.append(self._make_alert_card(
                title='Estoque em risco',
                count=alertas['produtos_baixo_estoque'],
                value='{0} produto(s) abaixo do minimo'.format(alertas['produtos_baixo_estoque']),
                description='Itens com ruptura potencial e impacto direto na operacao.',
                href=reverse('cadastro:listaprodutosbaixoestoqueview'),
                action_label='Repor estoque',
                severity='danger',
            ))

        if user.has_perm('vendas.view_pedidovenda'):
            alert_cards.append(self._make_alert_card(
                title='Pedidos de venda atrasados',
                count=alertas['pedidos_venda_atrasados'],
                value='{0} pedido(s) fora do prazo'.format(alertas['pedidos_venda_atrasados']),
                description='Entregas atrasadas comprometem a experiencia do cliente.',
                href=reverse('vendas:listapedidovendaatrasadosview'),
                action_label='Priorizar vendas',
                severity='warning',
            ))

        operation_cards = []
        if user.has_perm('vendas.view_orcamentovenda'):
            operation_cards.append(self._make_stat_card(
                title='Orcamentos de venda abertos',
                value=str(open_sale_quotes),
                subtitle='{0} vence(m) hoje'.format(agenda_hoje['orcamento_venda_hoje']),
                href=reverse('vendas:listaorcamentovendaview'),
                tone='neutral',
                icon='assignment',
            ))
        if user.has_perm('compras.view_orcamentocompra'):
            operation_cards.append(self._make_stat_card(
                title='Orcamentos de compra abertos',
                value=str(open_purchase_quotes),
                subtitle='{0} vence(m) hoje'.format(agenda_hoje['orcamento_compra_hoje']),
                href=reverse('compras:listaorcamentocompraview'),
                tone='neutral',
                icon='assignment',
            ))
        if user.has_perm('vendas.view_pedidovenda'):
            operation_cards.append(self._make_stat_card(
                title='Pedidos de venda',
                value=str(open_sales),
                subtitle='{0} atrasado(s)'.format(alertas['pedidos_venda_atrasados']),
                href=reverse('vendas:listapedidovendaview'),
                tone='neutral',
                icon='shopping_basket',
            ))
        if user.has_perm('compras.view_pedidocompra'):
            operation_cards.append(self._make_stat_card(
                title='Pedidos de compra',
                value=str(open_purchases),
                subtitle='{0} atrasado(s)'.format(alertas['pedidos_compra_atrasados']),
                href=reverse('compras:listapedidocompraview'),
                tone='neutral',
                icon='shopping_cart',
            ))

        cadastro_cards = []
        if user.has_perm('cadastro.view_cliente'):
            cadastro_cards.append(self._make_stat_card(
                title='Clientes',
                value=str(quantidade_cadastro['clientes']),
                subtitle='Base ativa de relacionamento',
                href=reverse('cadastro:listaclientesview'),
                tone='neutral',
                icon='people',
            ))
        if user.has_perm('cadastro.view_fornecedor'):
            cadastro_cards.append(self._make_stat_card(
                title='Fornecedores',
                value=str(quantidade_cadastro['fornecedores']),
                subtitle='Parceiros cadastrados',
                href=reverse('cadastro:listafornecedoresview'),
                tone='neutral',
                icon='local_shipping',
            ))
        if user.has_perm('cadastro.view_produto'):
            cadastro_cards.append(self._make_stat_card(
                title='Produtos',
                value=str(quantidade_cadastro['produtos']),
                subtitle='{0} com estoque baixo'.format(alertas['produtos_baixo_estoque']),
                href=reverse('cadastro:listaprodutosview'),
                tone='neutral',
                icon='store',
            ))
        if user.has_perm('cadastro.view_empresa'):
            cadastro_cards.append(self._make_stat_card(
                title='Empresas',
                value=str(quantidade_cadastro['empresas']),
                subtitle='Estruturas de operacao configuradas',
                href=reverse('cadastro:listaempresasview'),
                tone='neutral',
                icon='business',
            ))

        quick_actions = []
        if user.has_perm('vendas.add_pedidovenda'):
            quick_actions.append({'label': 'Nova venda', 'href': reverse('vendas:addpedidovendaview'), 'style': 'primary'})
        if user.has_perm('financeiro.add_saida'):
            quick_actions.append({'label': 'Lancar conta', 'href': reverse('financeiro:addcontapagarview'), 'style': 'secondary'})
        if user.has_perm('fiscal.add_notafiscalsaida'):
            quick_actions.append({'label': 'Emitir NF', 'href': reverse('fiscal:addnotafiscalsaidaview'), 'style': 'secondary'})
        if user.has_perm('estoque.add_entradaestoque'):
            quick_actions.append({'label': 'Entrada estoque', 'href': reverse('estoque:addentradaestoqueview'), 'style': 'secondary'})
        if user.has_perm('financeiro.acesso_fluxodecaixa'):
            quick_actions.append({'label': 'Fluxo de caixa', 'href': reverse('financeiro:fluxodecaixaview'), 'style': 'ghost'})

        recent_movements = MovimentoCaixa.objects.filter(
            data_movimento__gte=data_atual - timedelta(days=6),
            data_movimento__lte=data_atual,
        ).order_by('data_movimento')

        context['dashboard_kpis'] = kpi_cards
        context['dashboard_alerts'] = alert_cards
        context['dashboard_operations'] = operation_cards
        context['dashboard_cadastros'] = cadastro_cards
        context['dashboard_quick_actions'] = quick_actions
        context['dashboard_chart'] = self._build_chart(recent_movements, data_atual)
        context['dashboard_financial_snapshot'] = [
            self._make_stat_card(
                title='A receber hoje',
                value=self._format_currency(contas_receber_hoje_valor),
                subtitle='{0} titulo(s) para hoje'.format(agenda_hoje['contas_receber_hoje']),
                href=reverse('financeiro:listacontareceberhojeview'),
                tone='success',
                icon='call_received',
            ),
            self._make_stat_card(
                title='A pagar hoje',
                value=self._format_currency(contas_pagar_hoje_valor),
                subtitle='{0} titulo(s) para hoje'.format(agenda_hoje['contas_pagar_hoje']),
                href=reverse('financeiro:listacontapagarhojeview'),
                tone='warning',
                icon='call_made',
            ),
        ]

        return context


def handler404(request):
    response = render(request, '404.html', {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response
