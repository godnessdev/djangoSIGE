# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from django.contrib import messages

from djangosige.apps.base.custom_views import CustomListView
from djangosige.apps.cadastro.utils import (
    get_empresa_ativa,
    get_empresas_grupo_permitidas,
    pode_consultar_consolidado_grupo,
)

from djangosige.apps.financeiro.models import MovimentoCaixa

from datetime import datetime
from decimal import Decimal


class FluxoCaixaView(CustomListView):
    template_name = "financeiro/fluxo_de_caixa/fluxo.html"
    success_url = reverse_lazy('financeiro:fluxodecaixaview')
    context_object_name = 'movimentos'
    permission_codename = 'acesso_fluxodecaixa'

    def get_modo_listagem(self):
        if self.request.GET.get('modo') == 'grupo' and pode_consultar_consolidado_grupo(
                self.request.user, get_empresa_ativa(self.request.user)):
            return 'grupo'
        return 'empresa'

    def get_empresa_filtro(self):
        empresa_ativa = get_empresa_ativa(self.request.user)
        if empresa_ativa is None:
            return None
        empresa_id = self.request.GET.get('empresa')
        if not empresa_id:
            return None
        empresas_grupo = get_empresas_grupo_permitidas(
            self.request.user, empresa=empresa_ativa)
        try:
            return empresas_grupo.get(pk=empresa_id)
        except Exception:
            return None

    def filtrar_queryset(self, queryset):
        empresa_ativa = get_empresa_ativa(self.request.user)
        if empresa_ativa is None:
            return queryset.none()

        if self.get_modo_listagem() == 'grupo' and pode_consultar_consolidado_grupo(
                self.request.user, empresa_ativa):
            empresas_grupo = get_empresas_grupo_permitidas(
                self.request.user, empresa=empresa_ativa)
            empresa_filtro = self.get_empresa_filtro()
            if empresa_filtro and empresas_grupo.filter(pk=empresa_filtro.pk).exists():
                empresas_grupo = empresas_grupo.filter(pk=empresa_filtro.pk)
            return queryset.filter(empresa__in=empresas_grupo).distinct()

        return queryset.filter(empresa=empresa_ativa)

    def get_context_data(self, **kwargs):
        context = super(FluxoCaixaView, self).get_context_data(**kwargs)
        context['empresa_ativa'] = get_empresa_ativa(self.request.user)
        context['pode_consolidar_grupo'] = pode_consultar_consolidado_grupo(
            self.request.user, context['empresa_ativa'])
        context['empresas_grupo'] = get_empresas_grupo_permitidas(
            self.request.user, empresa=context['empresa_ativa'])
        context['modo_financeiro'] = self.get_modo_listagem()
        context['empresa_filtro_atual'] = self.get_empresa_filtro()

        comparativo = []
        if context['modo_financeiro'] == 'grupo':
            movimentos = context.get('movimentos', [])
            for empresa in context['empresas_grupo']:
                movimentos_empresa = [m for m in movimentos if m.empresa_id == empresa.id]
                if not movimentos_empresa:
                    continue
                comparativo.append({
                    'empresa': empresa,
                    'entradas': sum((m.entradas for m in movimentos_empresa), Decimal('0.00')),
                    'saidas': sum((m.saidas for m in movimentos_empresa), Decimal('0.00')),
                    'saldo_final': movimentos_empresa[-1].saldo_final,
                })
        context['comparativo_empresas'] = comparativo
        return context

    def get_queryset(self):
        try:
            data_inicial = self.request.GET.get('from')
            data_final = self.request.GET.get('to')

            if data_inicial and data_final:
                data_inicial = datetime.strptime(data_inicial, '%d/%m/%Y')
                data_final = datetime.strptime(data_final, '%d/%m/%Y')
            elif data_inicial:
                data_inicial = datetime.strptime(data_inicial, '%d/%m/%Y')
                data_final = data_inicial
            elif data_final:
                data_final = datetime.strptime(data_final, '%d/%m/%Y')
                data_inicial = data_final
            else:
                data_final = data_inicial = datetime.today().strftime('%Y-%m-%d')

        except ValueError:
            data_final = data_inicial = datetime.today().strftime('%Y-%m-%d')
            messages.error(
                self.request, 'Formato de data incorreto, deve ser no formato DD/MM/AAAA')

        queryset = MovimentoCaixa.objects.filter(
            data_movimento__range=(data_inicial, data_final)).select_related('empresa').order_by(
                'data_movimento', 'empresa__nome_razao_social')
        return self.filtrar_queryset(queryset)
