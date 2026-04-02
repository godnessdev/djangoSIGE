# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from decimal import Decimal

from djangosige.apps.base.custom_views import CustomListView

from djangosige.apps.cadastro.models import Produto
from djangosige.apps.estoque.models import LocalEstoque
from djangosige.apps.cadastro.utils import (
    get_empresa_ativa,
    get_empresas_grupo_permitidas,
    pode_consultar_consolidado_grupo,
)


class ConsultaEstoqueView(CustomListView):
    template_name = "estoque/consulta/consulta_estoque.html"
    success_url = reverse_lazy('estoque:consultaestoqueview')
    context_object_name = 'produtos_filtrados'
    permission_codename = 'consultar_estoque'

    def get_context_data(self, **kwargs):
        context = super(ConsultaEstoqueView, self).get_context_data(**kwargs)
        empresa = get_empresa_ativa(self.request.user)
        empresas_escopo = self.get_empresas_escopo()
        locais_escopo = LocalEstoque.objects.filter(empresa__in=empresas_escopo)
        context['empresa_ativa'] = empresa
        context['pode_consolidar_grupo'] = pode_consultar_consolidado_grupo(
            self.request.user, empresa)
        context['empresas_grupo'] = get_empresas_grupo_permitidas(
            self.request.user, empresa=empresa)
        context['empresa_filtro_atual'] = self.get_empresa_filtro()
        context['modo_estoque'] = self.request.GET.get('modo') or 'empresa'
        context['todos_produtos'] = Produto.objects.filter(
            controlar_estoque=True,
            produto_estocado__local__empresa__in=empresas_escopo).distinct().order_by('descricao')
        context['todos_locais'] = locais_escopo.order_by('descricao')
        context['title_complete'] = 'CONSULTA DE ESTOQUE'
        for produto in context['produtos_filtrados']:
            produto.estoque_exibicao = self.get_quantidade_produto(produto, empresas_escopo)
            empresa_referencia = self.get_empresa_filtro() or empresa
            produto.valor_unitario_exibicao = (
                produto.get_venda_empresa(empresa_referencia)
                if empresa_referencia and len(empresas_escopo) == 1 else ''
            )
            produto.locais_exibicao = produto.produto_estocado.filter(
                local__empresa__in=empresas_escopo,
                quantidade__gt=0).select_related('local', 'local__empresa').order_by(
                'local__empresa__nome_razao_social', 'local__descricao')
            produto.saldos_por_empresa_exibicao = [
                {
                    'empresa': empresa_item,
                    'quantidade': self.get_quantidade_produto(produto, [empresa_item]),
                }
                for empresa_item in empresas_escopo
            ]
        return context

    def get_empresa_filtro(self):
        empresa = get_empresa_ativa(self.request.user)
        empresa_id = self.request.GET.get('empresa')
        if not empresa_id:
            return empresa

        empresas_grupo = get_empresas_grupo_permitidas(
            self.request.user, empresa=empresa)
        return empresas_grupo.filter(pk=empresa_id).first() or empresa

    def get_empresas_escopo(self):
        empresa = get_empresa_ativa(self.request.user)
        if empresa is None:
            return []

        modo = self.request.GET.get('modo') or 'empresa'
        if modo == 'grupo' and pode_consultar_consolidado_grupo(self.request.user, empresa):
            return list(get_empresas_grupo_permitidas(
                self.request.user, empresa=empresa))
        empresa_filtro = self.get_empresa_filtro()
        return [empresa_filtro] if empresa_filtro else [empresa]

    def get_quantidade_produto(self, produto, empresas):
        quantidade_total = Decimal('0.00')
        for produto_estocado in produto.produto_estocado.filter(local__empresa__in=empresas):
            quantidade_total += produto_estocado.quantidade
        return quantidade_total

    def get_queryset(self):
        produto = self.request.GET.get('produto')
        local = self.request.GET.get('local')
        modo = self.request.GET.get('modo') or 'empresa'
        empresas_escopo = self.get_empresas_escopo()
        local_ids = LocalEstoque.objects.filter(empresa__in=empresas_escopo).values_list('pk', flat=True)

        if produto:
            produtos_filtrados = Produto.objects.filter(
                id=produto,
                controlar_estoque=True,
                produto_estocado__local__empresa__in=empresas_escopo).distinct()
        elif local:
            locais = LocalEstoque.objects.filter(id=local)
            if empresas_escopo:
                locais = locais.filter(empresa__in=empresas_escopo)
            local_obj = locais.first()
            if local_obj:
                produtos_filtrados = local_obj.produtos_estoque.filter(
                    controlar_estoque=True,
                    produto_estocado__local=local_obj,
                    produto_estocado__quantidade__gt=0).distinct()
            else:
                produtos_filtrados = Produto.objects.none()
        else:
            produtos_filtrados = Produto.objects.filter(controlar_estoque=True)
            produtos_filtrados = produtos_filtrados.filter(
                produto_estocado__local_id__in=local_ids).distinct()

        if modo == 'falta':
            produtos_filtrados = [
                produto_item for produto_item in produtos_filtrados
                if self.get_quantidade_produto(produto_item, empresas_escopo) <= produto_item.estoque_minimo
            ]
        elif modo in ('empresa', 'grupo'):
            produtos_filtrados = [
                produto_item for produto_item in produtos_filtrados
                if self.get_quantidade_produto(produto_item, empresas_escopo) > 0
            ]

        return produtos_filtrados
