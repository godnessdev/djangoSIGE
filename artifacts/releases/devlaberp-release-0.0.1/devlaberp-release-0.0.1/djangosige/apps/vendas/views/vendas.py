# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from djangosige.apps.base.custom_views import CustomView, CustomCreateView, CustomListView, CustomUpdateView

from djangosige.apps.vendas.forms import OrcamentoVendaForm, PedidoVendaForm, ItensVendaFormSet, PagamentoFormSet
from djangosige.apps.vendas.models import OrcamentoVenda, PedidoVenda, ItensVenda, Pagamento
from djangosige.apps.cadastro.models import MinhaEmpresa
from djangosige.apps.cadastro.utils import (
    filtrar_queryset_por_empresa_ativa,
    get_empresa_ativa,
    get_empresas_grupo_permitidas,
    pode_consultar_consolidado_grupo,
)
from djangosige.apps.login.models import Usuario
from djangosige.configs.settings import MEDIA_ROOT

from datetime import datetime
import io

try:
    from geraldo.generators import PDFGenerator
    from .report_vendas import VendaReport
except ImportError:
    PDFGenerator = None
    VendaReport = None


def get_empresa_filtro_venda(request):
    empresa_ativa = get_empresa_ativa(request.user)
    if empresa_ativa is None:
        return None

    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return None

    empresas_grupo = get_empresas_grupo_permitidas(
        request.user, empresa=empresa_ativa)
    try:
        return empresas_grupo.get(pk=empresa_id)
    except Exception:
        return None


def filtrar_vendas_por_escopo(queryset, user, modo='empresa', empresa_filtro=None):
    empresa_ativa = get_empresa_ativa(user)
    if empresa_ativa is None:
        return queryset.none()

    if modo == 'grupo' and pode_consultar_consolidado_grupo(user, empresa_ativa):
        empresas_grupo = get_empresas_grupo_permitidas(user, empresa=empresa_ativa)
        if empresa_filtro and empresas_grupo.filter(pk=empresa_filtro.pk).exists():
            empresas_grupo = empresas_grupo.filter(pk=empresa_filtro.pk)
        return queryset.filter(empresa__in=empresas_grupo).distinct()

    return queryset.filter(empresa=empresa_ativa)


class AdicionarVendaView(CustomCreateView):

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        return form_class(**self.get_form_kwargs(), user=self.request.user)

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(AdicionarVendaView, self).get_context_data(**kwargs)
        return self.view_context(context)

    def get(self, request, form_class, *args, **kwargs):
        self.object = None

        form = self.get_form(form_class)
        form.initial['vendedor'] = request.user.first_name or request.user
        form.initial['data_emissao'] = datetime.today().strftime('%d/%m/%Y')

        produtos_form = ItensVendaFormSet(prefix='produtos_form')
        pagamento_form = PagamentoFormSet(prefix='pagamento_form')

        return self.render_to_response(self.get_context_data(form=form,
                                                             produtos_form=produtos_form,
                                                             pagamento_form=pagamento_form))

    def post(self, request, form_class, *args, **kwargs):
        self.object = None
        # Tirar . dos campos decimais
        req_post = request.POST.copy()

        for key in req_post:
            if ('desconto' in key or
                'quantidade' in key or
                'valor' in key or
                'frete' in key or
                'despesas' in key or
                'seguro' in key or
                    'total' in key):
                req_post[key] = req_post[key].replace('.', '')

        request.POST = req_post

        form = self.get_form(form_class)
        produtos_form = ItensVendaFormSet(request.POST, prefix='produtos_form')
        pagamento_form = PagamentoFormSet(
            request.POST, prefix='pagamento_form')

        if (form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid()):
            empresa = get_empresa_ativa(request.user)
            if empresa is None:
                form.add_error(None, 'Selecione uma empresa ativa para continuar.')
                return self.form_invalid(form=form,
                                         produtos_form=produtos_form,
                                         pagamento_form=pagamento_form)
            self.object = form.save(commit=False)
            self.object.empresa = empresa
            self.object.save()

            for pform in produtos_form:
                if pform.cleaned_data != {}:
                    itens_venda_obj = pform.save(commit=False)
                    itens_venda_obj.venda_id = self.object
                    itens_venda_obj.calcular_pis_cofins()
                    itens_venda_obj.save()

            pagamento_form.instance = self.object
            pagamento_form.save()

            return self.form_valid(form)

        return self.form_invalid(form=form,
                                 produtos_form=produtos_form,
                                 pagamento_form=pagamento_form)


class AdicionarOrcamentoVendaView(AdicionarVendaView):
    form_class = OrcamentoVendaForm
    template_name = "vendas/orcamento_venda/orcamento_venda_add.html"
    success_url = reverse_lazy('vendas:listaorcamentovendaview')
    success_message = "<b>Orçamento de venda %(id)s </b>adicionado com sucesso."
    permission_codename = 'add_orcamentovenda'

    def view_context(self, context):
        context['title_complete'] = 'ADICIONAR ORÇAMENTO DE VENDA'
        context['return_url'] = reverse_lazy('vendas:listaorcamentovendaview')
        return context

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarOrcamentoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarOrcamentoVendaView, self).post(request, form_class, *args, **kwargs)


class AdicionarPedidoVendaView(AdicionarVendaView):
    form_class = PedidoVendaForm
    template_name = "vendas/pedido_venda/pedido_venda_add.html"
    success_url = reverse_lazy('vendas:listapedidovendaview')
    success_message = "<b>Pedido de venda %(id)s </b>adicionado com sucesso."
    permission_codename = 'add_pedidovenda'

    def view_context(self, context):
        context['title_complete'] = 'ADICIONAR PEDIDO DE VENDA'
        context['return_url'] = reverse_lazy('vendas:listapedidovendaview')
        return context

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarPedidoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarPedidoVendaView, self).post(request, form_class, *args, **kwargs)


class VendaListView(CustomListView):
    paginate_by = 100

    def get_modo_listagem(self):
        if self.request.GET.get('modo') == 'grupo' and pode_consultar_consolidado_grupo(
                self.request.user, get_empresa_ativa(self.request.user)):
            return 'grupo'
        return 'empresa'

    def get_empresa_filtro(self):
        return get_empresa_filtro_venda(self.request)

    def get_context_data(self, **kwargs):
        context = super(VendaListView, self).get_context_data(**kwargs)
        context['empresa_ativa'] = get_empresa_ativa(self.request.user)
        context['pode_consolidar_grupo'] = pode_consultar_consolidado_grupo(
            self.request.user, context['empresa_ativa'])
        context['empresas_grupo'] = get_empresas_grupo_permitidas(
            self.request.user, empresa=context['empresa_ativa'])
        context['modo_venda'] = self.get_modo_listagem()
        context['empresa_filtro_atual'] = self.get_empresa_filtro()
        return self.view_context(context)

    def get_queryset(self):
        queryset = self.model.objects.select_related(
            'empresa', 'cliente', 'local_orig').order_by('-id')
        return filtrar_vendas_por_escopo(
            queryset, self.request.user, self.get_modo_listagem(), self.get_empresa_filtro())

    def post(self, request, *args, **kwargs):
        if self.check_user_delete_permission(request, self.model):
            queryset = self.get_queryset()
            for key, value in request.POST.items():
                if value == "on" and queryset.filter(id=key).exists():
                    queryset.get(id=key).delete()
        return redirect(self.success_url)


class OrcamentoVendaListView(VendaListView):
    template_name = 'vendas/orcamento_venda/orcamento_venda_list.html'
    model = OrcamentoVenda
    context_object_name = 'all_orcamentos'
    success_url = reverse_lazy('vendas:listaorcamentovendaview')
    permission_codename = 'view_orcamentovenda'

    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE VENDA'
        context['add_url'] = reverse_lazy('vendas:addorcamentovendaview')
        return context


class OrcamentoVendaVencidosListView(OrcamentoVendaListView):
    success_url = reverse_lazy('vendas:listaorcamentovendavencidoview')

    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE VENDA VENCIDOS'
        context['add_url'] = reverse_lazy('vendas:addorcamentovendaview')
        return context

    def get_queryset(self):
        queryset = OrcamentoVenda.objects.filter(
            data_vencimento__lte=datetime.now().date(), status='0').select_related(
                'empresa', 'cliente', 'local_orig').order_by('-id')
        return filtrar_vendas_por_escopo(
            queryset, self.request.user, self.get_modo_listagem(), self.get_empresa_filtro())


class OrcamentoVendaVencimentoHojeListView(OrcamentoVendaListView):
    success_url = reverse_lazy('vendas:listaorcamentovendahojeview')

    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE VENDA COM VENCIMENTO DIA ' + \
            datetime.now().date().strftime('%d/%m/%Y')
        context['add_url'] = reverse_lazy('vendas:addorcamentovendaview')
        return context

    def get_queryset(self):
        queryset = OrcamentoVenda.objects.filter(
            data_vencimento=datetime.now().date(), status='0').select_related(
                'empresa', 'cliente', 'local_orig').order_by('-id')
        return filtrar_vendas_por_escopo(
            queryset, self.request.user, self.get_modo_listagem(), self.get_empresa_filtro())


class PedidoVendaListView(VendaListView):
    template_name = 'vendas/pedido_venda/pedido_venda_list.html'
    model = PedidoVenda
    context_object_name = 'all_pedidos'
    success_url = reverse_lazy('vendas:listapedidovendaview')
    permission_codename = 'view_pedidovenda'

    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE VENDA'
        context['add_url'] = reverse_lazy('vendas:addpedidovendaview')
        return context


class PedidoVendaAtrasadosListView(PedidoVendaListView):
    success_url = reverse_lazy('vendas:listapedidovendaatrasadosview')

    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE VENDA ATRASADOS'
        context['add_url'] = reverse_lazy('vendas:addpedidovendaview')
        return context

    def get_queryset(self):
        queryset = PedidoVenda.objects.filter(
            data_entrega__lte=datetime.now().date(), status='0').select_related(
                'empresa', 'cliente', 'local_orig').order_by('-id')
        return filtrar_vendas_por_escopo(
            queryset, self.request.user, self.get_modo_listagem(), self.get_empresa_filtro())


class PedidoVendaEntregaHojeListView(PedidoVendaListView):
    success_url = reverse_lazy('vendas:listapedidovendahojeview')

    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE VENDA COM ENTREGA DIA ' + \
            datetime.now().date().strftime('%d/%m/%Y')
        context['add_url'] = reverse_lazy('vendas:addpedidovendaview')
        return context

    def get_queryset(self):
        queryset = PedidoVenda.objects.filter(
            data_entrega=datetime.now().date(), status='0').select_related(
                'empresa', 'cliente', 'local_orig').order_by('-id')
        return filtrar_vendas_por_escopo(
            queryset, self.request.user, self.get_modo_listagem(), self.get_empresa_filtro())


class EditarVendaView(CustomUpdateView):

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        return form_class(**self.get_form_kwargs(), user=self.request.user)

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(EditarVendaView, self).get_context_data(**kwargs)
        return self.view_context(context)

    def get(self, request, form_class, *args, **kwargs):

        form = form = self.get_form(form_class)
        form.initial['total_sem_imposto'] = self.object.get_total_sem_imposto()

        produtos_form = ItensVendaFormSet(
            instance=self.object, prefix='produtos_form')
        itens_list = ItensVenda.objects.filter(venda_id=self.object.id)
        produtos_form.initial = [{'total_sem_desconto': item.get_total_sem_desconto(),
                                  'total_impostos': item.get_total_impostos(),
                                  'total_com_impostos': item.get_total_com_impostos()} for item in itens_list]

        pagamento_form = PagamentoFormSet(
            instance=self.object, prefix='pagamento_form')

        if ItensVenda.objects.filter(venda_id=self.object.pk).count():
            produtos_form.extra = 0
        if Pagamento.objects.filter(venda_id=self.object.pk).count():
            pagamento_form.extra = 0

        return self.render_to_response(self.get_context_data(form=form, produtos_form=produtos_form, pagamento_form=pagamento_form))

    def post(self, request, form_class, *args, **kwargs):
        # Tirar . dos campos decimais
        req_post = request.POST.copy()

        for key in req_post:
            if ('desconto' in key or
                'quantidade' in key or
                'valor' in key or
                'frete' in key or
                'despesas' in key or
                'seguro' in key or
                    'total' in key):
                req_post[key] = req_post[key].replace('.', '')

        request.POST = req_post

        form = self.get_form(form_class)
        produtos_form = ItensVendaFormSet(
            request.POST, prefix='produtos_form', instance=self.object)
        pagamento_form = PagamentoFormSet(
            request.POST, prefix='pagamento_form', instance=self.object)

        if (form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid()):
            empresa = get_empresa_ativa(request.user)
            if empresa is None:
                form.add_error(None, 'Selecione uma empresa ativa para continuar.')
                return self.form_invalid(form=form,
                                         produtos_form=produtos_form,
                                         pagamento_form=pagamento_form)
            self.object = form.save(commit=False)
            self.object.empresa = empresa
            self.object.save()

            for pform in produtos_form:
                if pform.cleaned_data != {}:
                    itens_venda_obj = pform.save(commit=False)
                    itens_venda_obj.venda_id = self.object
                    itens_venda_obj.calcular_pis_cofins()
                    itens_venda_obj.save()

            pagamento_form.instance = self.object
            pagamento_form.save()

            return self.form_valid(form)

        return self.form_invalid(form=form,
                                 produtos_form=produtos_form,
                                 pagamento_form=pagamento_form)


class EditarOrcamentoVendaView(EditarVendaView):
    form_class = OrcamentoVendaForm
    model = OrcamentoVenda
    template_name = "vendas/orcamento_venda/orcamento_venda_edit.html"
    success_url = reverse_lazy('vendas:listaorcamentovendaview')
    success_message = "<b>Orçamento de venda %(id)s </b>editado com sucesso."
    permission_codename = 'change_orcamentovenda'

    def view_context(self, context):
        context['title_complete'] = 'EDITAR ORÇAMENTO DE VENDA N°' + \
            str(self.object.id)
        context['return_url'] = reverse_lazy('vendas:listaorcamentovendaview')
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarOrcamentoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarOrcamentoVendaView, self).post(request, form_class, *args, **kwargs)

    def get_queryset(self):
        return filtrar_queryset_por_empresa_ativa(
            OrcamentoVenda.objects.all(), self.request.user)


class EditarPedidoVendaView(EditarVendaView):
    form_class = PedidoVendaForm
    model = PedidoVenda
    template_name = "vendas/pedido_venda/pedido_venda_edit.html"
    success_url = reverse_lazy('vendas:listapedidovendaview')
    success_message = "<b>Pedido de venda %(id)s </b>editado com sucesso."
    permission_codename = 'change_pedidovenda'

    def view_context(self, context):
        context['title_complete'] = 'EDITAR PEDIDO DE VENDA N°' + \
            str(self.object.id)
        context['return_url'] = reverse_lazy('vendas:listapedidovendaview')
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarPedidoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarPedidoVendaView, self).post(request, form_class, *args, **kwargs)

    def get_queryset(self):
        return filtrar_queryset_por_empresa_ativa(
            PedidoVenda.objects.all(), self.request.user)


class GerarPedidoVendaView(CustomView):
    permission_codename = ['add_pedidovenda', 'change_pedidovenda', ]

    def get(self, request, *args, **kwargs):
        orcamento_id = kwargs.get('pk', None)
        orcamento = get_object_or_404(
            filtrar_queryset_por_empresa_ativa(
                OrcamentoVenda.objects.all(), request.user),
            id=orcamento_id)
        itens_venda = orcamento.itens_venda.all()
        pagamentos = orcamento.parcela_pagamento.all()
        novo_pedido = PedidoVenda()

        for field in orcamento._meta.fields:
            setattr(novo_pedido, field.name, getattr(orcamento, field.name))

        novo_pedido.venda_ptr = None
        novo_pedido.pk = None
        novo_pedido.id = None
        novo_pedido.status = '0'
        orcamento.status = '1'  # Baixado
        orcamento.save()
        novo_pedido.orcamento = orcamento
        novo_pedido.save()

        for item in itens_venda:
            item.pk = None
            item.id = None
            item.save()
            novo_pedido.itens_venda.add(item)

        for pagamento in pagamentos:
            pagamento.pk = None
            pagamento.id = None
            pagamento.save()
            novo_pedido.parcela_pagamento.add(pagamento)

        return redirect(reverse_lazy('vendas:editarpedidovendaview', kwargs={'pk': novo_pedido.id}))


class CancelarOrcamentoVendaView(CustomView):
    permission_codename = 'change_orcamentovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = get_object_or_404(
            filtrar_queryset_por_empresa_ativa(
                OrcamentoVenda.objects.all(), request.user),
            id=venda_id)
        instance.status = '2'
        instance.save()
        return redirect(reverse_lazy('vendas:editarorcamentovendaview', kwargs={'pk': instance.id}))


class CancelarPedidoVendaView(CustomView):
    permission_codename = 'change_pedidovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = get_object_or_404(
            filtrar_queryset_por_empresa_ativa(
                PedidoVenda.objects.all(), request.user),
            id=venda_id)
        instance.status = '2'
        instance.save()
        return redirect(reverse_lazy('vendas:editarpedidovendaview', kwargs={'pk': instance.id}))


class GerarCopiaVendaView(CustomView):

    def get(self, request, instance, redirect_url, *args, **kwargs):
        itens_venda = instance.itens_venda.all()
        pagamentos = instance.parcela_pagamento.all()

        instance.pk = None
        instance.id = None
        instance.status = '0'
        instance.save()

        for item in itens_venda:
            item.pk = None
            item.id = None
            item.save()
            instance.itens_venda.add(item)

        for pagamento in pagamentos:
            pagamento.pk = None
            pagamento.id = None
            pagamento.save()
            instance.parcela_pagamento.add(pagamento)

        return redirect(reverse_lazy(redirect_url, kwargs={'pk': instance.id}))


class GerarCopiaOrcamentoVendaView(GerarCopiaVendaView):
    permission_codename = 'add_orcamentovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = get_object_or_404(
            filtrar_queryset_por_empresa_ativa(
                OrcamentoVenda.objects.all(), request.user),
            id=venda_id)
        redirect_url = 'vendas:editarorcamentovendaview'
        return super(GerarCopiaOrcamentoVendaView, self).get(request, instance, redirect_url, *args, **kwargs)


class GerarCopiaPedidoVendaView(GerarCopiaVendaView):
    permission_codename = 'add_pedidovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = get_object_or_404(
            filtrar_queryset_por_empresa_ativa(
                PedidoVenda.objects.all(), request.user),
            id=venda_id)
        redirect_url = 'vendas:editarpedidovendaview'
        return super(GerarCopiaPedidoVendaView, self).get(request, instance, redirect_url, *args, **kwargs)


class GerarPDFVenda(CustomView):

    def gerar_pdf(self, title, venda, user_id):
        if PDFGenerator is None or VendaReport is None:
            return HttpResponse(
                'Geracao de PDF indisponivel. Instale as dependencias opcionais em requirements_optional.txt.',
                status=503,
            )

        resp = HttpResponse(content_type='application/pdf')

        venda_pdf = io.BytesIO()
        venda_report = VendaReport(queryset=[venda, ])
        venda_report.title = title

        venda_report.band_page_footer = venda_report.banda_foot

        try:
            usuario = Usuario.objects.get(pk=user_id)
            m_empresa = MinhaEmpresa.objects.get(m_usuario=usuario)
            flogo = m_empresa.m_empresa.logo_file
            logo_path = '{0}{1}'.format(MEDIA_ROOT, flogo.name)
            if flogo != 'imagens/logo.png':
                venda_report.topo_pagina.inserir_logo(logo_path)

            venda_report.band_page_footer.inserir_nome_empresa(
                m_empresa.m_empresa.nome_razao_social)
            if m_empresa.m_empresa.endereco_padrao:
                venda_report.band_page_footer.inserir_endereco_empresa(
                    m_empresa.m_empresa.endereco_padrao.format_endereco_completo)
            if m_empresa.m_empresa.telefone_padrao:
                venda_report.band_page_footer.inserir_telefone_empresa(
                    m_empresa.m_empresa.telefone_padrao.telefone)
        except:
            pass

        venda_report.topo_pagina.inserir_data_emissao(venda.data_emissao)
        if isinstance(venda, OrcamentoVenda):
            venda_report.topo_pagina.inserir_data_validade(
                venda.data_vencimento)
        elif isinstance(venda, PedidoVenda):
            venda_report.topo_pagina.inserir_data_entrega(venda.data_entrega)
        venda_report.band_page_header = venda_report.topo_pagina

        if venda.cliente.tipo_pessoa == 'PJ':
            venda_report.dados_cliente.inserir_informacoes_pj()
        elif venda.cliente.tipo_pessoa == 'PF':
            venda_report.dados_cliente.inserir_informacoes_pf()

        if venda.cliente.endereco_padrao:
            venda_report.dados_cliente.inserir_informacoes_endereco()
        if venda.cliente.telefone_padrao:
            venda_report.dados_cliente.inserir_informacoes_telefone()
        if venda.cliente.email_padrao:
            venda_report.dados_cliente.inserir_informacoes_email()

        venda_report.band_page_header.child_bands.append(
            venda_report.dados_cliente)

        venda_report.dados_produtos.band_detail.set_band_height(
            len(ItensVenda.objects.filter(venda_id=venda)))
        venda_report.banda_produtos.elements.append(
            venda_report.dados_produtos)
        venda_report.band_page_header.child_bands.append(
            venda_report.banda_produtos)

        venda_report.band_page_header.child_bands.append(
            venda_report.totais_venda)

        if venda.cond_pagamento:
            venda_report.banda_pagamento.elements.append(
                venda_report.dados_pagamento)
            venda_report.band_page_header.child_bands.append(
                venda_report.banda_pagamento)

        venda_report.observacoes.inserir_vendedor()
        venda_report.band_page_header.child_bands.append(
            venda_report.observacoes)

        venda_report.generate_by(PDFGenerator, filename=venda_pdf)
        pdf = venda_pdf.getvalue()
        resp.write(pdf)

        return resp


class GerarPDFOrcamentoVenda(GerarPDFVenda):
    permission_codename = 'change_orcamentovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)

        if not venda_id:
            return HttpResponse('Objeto não encontrado.')

        obj = filtrar_queryset_por_empresa_ativa(
            OrcamentoVenda.objects.all(), request.user)
        obj = get_object_or_404(obj, pk=venda_id)
        title = 'Orçamento de venda nº {}'.format(venda_id)

        return self.gerar_pdf(title, obj, request.user.id)


class GerarPDFPedidoVenda(GerarPDFVenda):
    permission_codename = 'change_pedidovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)

        if not venda_id:
            return HttpResponse('Objeto não encontrado.')

        obj = filtrar_queryset_por_empresa_ativa(
            PedidoVenda.objects.all(), request.user)
        obj = get_object_or_404(obj, pk=venda_id)
        title = 'Pedido de venda nº {}'.format(venda_id)

        return self.gerar_pdf(title, obj, request.user.id)
