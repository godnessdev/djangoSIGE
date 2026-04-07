# -*- coding: utf-8 -*-

from django.urls import reverse_lazy

from djangosige.apps.base.custom_views import CustomCreateView, CustomListView, CustomUpdateView

from djangosige.apps.estoque.forms import LocalEstoqueForm
from djangosige.apps.estoque.models import LocalEstoque
from djangosige.apps.cadastro.utils import filtrar_queryset_por_empresa_ativa, get_empresa_ativa


class AdicionarLocalEstoqueView(CustomCreateView):
    form_class = LocalEstoqueForm
    template_name = "base/popup_form.html"
    success_url = reverse_lazy('estoque:listalocalview')
    success_message = "Localização de estoque <b>%(descricao)s </b>adicionada com sucesso."
    permission_codename = 'add_localestoque'

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, descricao=self.object.descricao)

    def get_context_data(self, **kwargs):
        context = super(AdicionarLocalEstoqueView,
                        self).get_context_data(**kwargs)
        return self.view_context(context)

    def view_context(self, context):
        context['titulo'] = 'ADICIONAR LOCAL DE ESTOQUE'
        return context

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        return form_class(**self.get_form_kwargs(), user=self.request.user)

    def form_valid(self, form):
        empresa = get_empresa_ativa(self.request.user)
        if empresa is None:
            form.add_error(None, 'Selecione uma empresa ativa para continuar.')
            return self.form_invalid(form)
        self.object = form.save(commit=False)
        self.object.empresa = empresa
        self.object.save()
        return super(AdicionarLocalEstoqueView, self).form_valid(form)


class LocalEstoqueListView(CustomListView):
    template_name = 'estoque/local/local_list.html'
    model = LocalEstoque
    context_object_name = 'all_locais'
    success_url = reverse_lazy('estoque:listalocalview')
    permission_codename = 'view_localestoque'

    def view_context(self, context):
        context['title_complete'] = 'LOCAIS DE ESTOQUE'
        context['add_url'] = reverse_lazy('estoque:addlocalview')
        return context

    def get_context_data(self, **kwargs):
        context = super(LocalEstoqueListView, self).get_context_data(**kwargs)
        return self.view_context(context)

    def get_queryset(self):
        return filtrar_queryset_por_empresa_ativa(
            LocalEstoque.objects.all(), self.request.user)


class EditarLocalEstoqueView(CustomUpdateView):
    form_class = LocalEstoqueForm
    model = LocalEstoque
    template_name = "base/popup_form.html"
    success_url = reverse_lazy('estoque:listalocalview')
    success_message = "Localização de estoque <b>%(descricao)s </b>editada com sucesso."
    permission_codename = 'change_localestoque'

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, descricao=self.object.descricao)

    def view_context(self, context):
        context['titulo'] = 'Editar local de estoque: ' + str(self.object)
        return context

    def get_context_data(self, **kwargs):
        context = super(EditarLocalEstoqueView,
                        self).get_context_data(**kwargs)
        return self.view_context(context)

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        return form_class(**self.get_form_kwargs(), user=self.request.user)

    def get_queryset(self):
        return filtrar_queryset_por_empresa_ativa(
            LocalEstoque.objects.all(), self.request.user)
