# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from django.shortcuts import redirect

from djangosige.apps.base.custom_views import CustomCreateView, CustomListView, CustomUpdateView
from djangosige.apps.cadastro.utils import get_empresa_ativa
from djangosige.apps.fiscal.forms import NaturezaOperacaoForm
from djangosige.apps.fiscal.models import NaturezaOperacao


class AdicionarNaturezaOperacaoView(CustomCreateView):
    form_class = NaturezaOperacaoForm
    template_name = "fiscal/natureza_operacao/natureza_operacao_add.html"
    success_url = reverse_lazy('fiscal:listanaturezaoperacaoview')
    success_message = "Natureza da opera\xc3\xa7\xc3\xa3o <b>%(cfop)s </b>adicionada com sucesso."
    permission_codename = 'add_naturezaoperacao'

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, cfop=self.object.cfop)

    def get_context_data(self, **kwargs):
        context = super(AdicionarNaturezaOperacaoView, self).get_context_data(**kwargs)
        context['title_complete'] = 'ADICIONAR NATUREZA DA OPERA\xc3\x87\xc3\x83O'
        context['return_url'] = reverse_lazy('fiscal:listanaturezaoperacaoview')
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.empresa = get_empresa_ativa(request.user)
            self.object.save()
            return self.form_valid(form)
        return self.form_invalid(form)


class NaturezaOperacaoListView(CustomListView):
    template_name = 'fiscal/natureza_operacao/natureza_operacao_list.html'
    model = NaturezaOperacao
    context_object_name = 'all_natops'
    success_url = reverse_lazy('fiscal:listanaturezaoperacaoview')
    permission_codename = 'view_naturezaoperacao'

    def get_queryset(self):
        empresa = get_empresa_ativa(self.request.user)
        return NaturezaOperacao.objects.filter(empresa=empresa).order_by('cfop')

    def post(self, request, *args, **kwargs):
        if self.check_user_delete_permission(request, self.model):
            queryset = self.get_queryset()
            for key, value in request.POST.items():
                if value == "on":
                    queryset.filter(id=key).delete()
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super(NaturezaOperacaoListView, self).get_context_data(**kwargs)
        context['title_complete'] = 'NATUREZAS DA OPERA\xc3\x87\xc3\x83O CADASTRADAS'
        context['add_url'] = reverse_lazy('fiscal:addnaturezaoperacaoview')
        return context


class EditarNaturezaOperacaoView(CustomUpdateView):
    form_class = NaturezaOperacaoForm
    model = NaturezaOperacao
    template_name = "fiscal/natureza_operacao/natureza_operacao_edit.html"
    success_url = reverse_lazy('fiscal:listanaturezaoperacaoview')
    success_message = "Natureza da opera\xc3\xa7\xc3\xa3o <b>%(cfop)s </b>editada com sucesso."
    permission_codename = 'change_naturezaoperacao'

    def get_queryset(self):
        empresa = get_empresa_ativa(self.request.user)
        return NaturezaOperacao.objects.filter(empresa=empresa)

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, cfop=self.object.cfop)

    def get_context_data(self, **kwargs):
        context = super(EditarNaturezaOperacaoView, self).get_context_data(**kwargs)
        context['return_url'] = reverse_lazy('fiscal:listanaturezaoperacaoview')
        return context
