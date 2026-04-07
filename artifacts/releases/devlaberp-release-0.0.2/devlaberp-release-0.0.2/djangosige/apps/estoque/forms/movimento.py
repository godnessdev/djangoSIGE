# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

from djangosige.apps.base.form_helpers import (
    configure_remote_model_choice_field,
    get_selected_model_choice_value,
)
from djangosige.apps.estoque.models import MovimentoEstoque, ItensMovimento, EntradaEstoque, SaidaEstoque, TransferenciaEstoque
from djangosige.apps.cadastro.models import Produto
from djangosige.apps.cadastro.utils import get_empresa_ativa, get_empresas_grupo_permitidas


class MovimentoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(MovimentoForm, self).__init__(*args, **kwargs)
        self.fields['quantidade_itens'].localize = True
        self.fields['valor_total'].localize = True

    class Meta:
        fields = ('data_movimento', 'quantidade_itens',
                  'valor_total', 'observacoes',)
        widgets = {
            'data_movimento': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'quantidade_itens': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_total': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control'}),
        }
        labels = {
            'quantidade_itens': _('Nº de itens'),
            'valor_total': _('Valor total dos produtos (R$)'),
            'observacoes': _('Observações'),
        }


class EntradaEstoqueForm(MovimentoForm):

    def __init__(self, *args, **kwargs):
        super(EntradaEstoqueForm, self).__init__(*args, **kwargs)
        empresa = get_empresa_ativa(self.user)
        if empresa:
            self.fields['local_dest'].queryset = self.fields['local_dest'].queryset.filter(
                empresa=empresa)
            self.fields['pedido_compra'].queryset = self.fields['pedido_compra'].queryset.filter(
                empresa=empresa)
            self.fields['fornecedor'].queryset = self.fields['fornecedor'].queryset.filter(
                empresa_relacionada=empresa).order_by('nome_razao_social')

        configure_remote_model_choice_field(
            self.fields['fornecedor'],
            self.fields['fornecedor'].queryset,
            '%s?tipo=fornecedor' % reverse_lazy('cadastro:consultapessoa'),
            'Buscar fornecedor por nome ou documento',
            get_selected_model_choice_value(self, 'fornecedor'),
        )

    class Meta(MovimentoForm.Meta):
        model = EntradaEstoque
        fields = MovimentoForm.Meta.fields + \
            ('tipo_movimento', 'pedido_compra', 'fornecedor', 'local_dest',)
        widgets = MovimentoForm.Meta.widgets
        widgets['tipo_movimento'] = forms.Select(
            attrs={'class': 'form-control'})
        widgets['pedido_compra'] = forms.Select(
            attrs={'class': 'form-control'})
        widgets['fornecedor'] = forms.Select(attrs={'class': 'form-control'})
        widgets['local_dest'] = forms.Select(attrs={'class': 'form-control'})
        labels = MovimentoForm.Meta.labels
        labels['data_movimento'] = _('Data da entrada')
        labels['tipo_movimento'] = _('Tipo')
        labels['pedido_compra'] = _('Pedido de compra')
        labels['fornecedor'] = _('Fornecedor')
        labels['local_dest'] = _('Local de destino')


class SaidaEstoqueForm(MovimentoForm):

    def __init__(self, *args, **kwargs):
        super(SaidaEstoqueForm, self).__init__(*args, **kwargs)
        empresa = get_empresa_ativa(self.user)
        if empresa:
            self.fields['local_orig'].queryset = self.fields['local_orig'].queryset.filter(
                empresa=empresa)
            self.fields['pedido_venda'].queryset = self.fields['pedido_venda'].queryset.filter(
                empresa=empresa)

    class Meta(MovimentoForm.Meta):
        model = SaidaEstoque
        fields = MovimentoForm.Meta.fields + \
            ('tipo_movimento', 'pedido_venda', 'local_orig',)
        widgets = MovimentoForm.Meta.widgets
        widgets['tipo_movimento'] = forms.Select(
            attrs={'class': 'form-control'})
        widgets['pedido_venda'] = forms.Select(attrs={'class': 'form-control'})
        widgets['local_orig'] = forms.Select(attrs={'class': 'form-control'})
        labels = MovimentoForm.Meta.labels
        labels['data_movimento'] = _('Data da saída')
        labels['tipo_movimento'] = _('Tipo')
        labels['pedido_venda'] = _('Pedido de venda')
        labels['local_orig'] = _('Local de origem')


class TransferenciaEstoqueForm(MovimentoForm):

    def __init__(self, *args, **kwargs):
        super(TransferenciaEstoqueForm, self).__init__(*args, **kwargs)
        empresa = get_empresa_ativa(self.user)
        if empresa:
            self.fields['local_estoque_orig'].queryset = self.fields['local_estoque_orig'].queryset.filter(
                empresa=empresa)
            empresas_destino = get_empresas_grupo_permitidas(
                self.user, empresa=empresa)
            self.fields['empresa_destino'].queryset = empresas_destino
            self.fields['empresa_destino'].initial = empresa.pk
            self.fields['local_estoque_dest'].queryset = self.fields['local_estoque_dest'].queryset.filter(
                empresa__in=empresas_destino)
            self.fields['impacto_custo'].initial = 'MAN'

    class Meta(MovimentoForm.Meta):
        model = TransferenciaEstoque
        fields = MovimentoForm.Meta.fields + \
            ('empresa_destino', 'local_estoque_orig', 'local_estoque_dest', 'impacto_custo',)
        widgets = MovimentoForm.Meta.widgets
        widgets['empresa_destino'] = forms.Select(
            attrs={'class': 'form-control'})
        widgets['local_estoque_orig'] = forms.Select(
            attrs={'class': 'form-control'})
        widgets['local_estoque_dest'] = forms.Select(
            attrs={'class': 'form-control'})
        widgets['impacto_custo'] = forms.Select(
            attrs={'class': 'form-control'})
        labels = MovimentoForm.Meta.labels
        labels['data_movimento'] = _('Data da transferência')
        labels['empresa_destino'] = _('Empresa de destino')
        labels['local_estoque_orig'] = _('Local de origem')
        labels['local_estoque_dest'] = _('Local de destino')
        labels['impacto_custo'] = _('Impacto no custo')


class ItensMovimentoForm(forms.ModelForm):
    estoque_atual = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': True}), label='Estoque atual', required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ItensMovimentoForm, self).__init__(*args, **kwargs)
        new_order = ['produto', 'quantidade',
                     'estoque_atual', 'valor_unit', 'subtotal']
        self.fields = type(self.fields)((f, self.fields[f]) for f in new_order)

        self.fields['quantidade'].localize = True
        self.fields['valor_unit'].localize = True
        self.fields['subtotal'].localize = True

        empresa = get_empresa_ativa(self.user)
        produtos = Produto.objects.filter(controlar_estoque=True)
        if empresa:
            produtos = produtos.filter(
                produto_estocado__local__empresa=empresa).distinct()
        configure_remote_model_choice_field(
            self.fields['produto'],
            produtos.order_by('descricao'),
            reverse_lazy('cadastro:consultaprecoproduto'),
            'Buscar produto por nome ou codigo',
            get_selected_model_choice_value(self, 'produto'),
        )

    class Meta:
        model = ItensMovimento
        fields = ('produto', 'quantidade', 'valor_unit', 'subtotal',)

        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control select-produto'}),
            'quantidade': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'valor_unit': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'subtotal': forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}),

        }
        labels = {
            'produto': _('Produto'),
            'quantidade': _('Quantidade'),
            'valor_unit': _('Vl. Unit.'),
            'subtotal': _('Subtotal'),
        }

    def is_valid(self):
        valid = super(ItensMovimentoForm, self).is_valid()
        if self.cleaned_data.get('produto', None) is None:
            self.cleaned_data = {}
        return valid


BaseItensMovimentoFormSet = inlineformset_factory(
    MovimentoEstoque, ItensMovimento, form=ItensMovimentoForm, extra=1, can_delete=True)


class ItensMovimentoFormSet(BaseItensMovimentoFormSet):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ItensMovimentoFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.user = user
            empresa = get_empresa_ativa(user)
            produtos = Produto.objects.filter(controlar_estoque=True)
            if empresa:
                produtos = produtos.filter(
                    produto_estocado__local__empresa=empresa).distinct()
            configure_remote_model_choice_field(
                form.fields['produto'],
                produtos.order_by('descricao'),
                reverse_lazy('cadastro:consultaprecoproduto'),
                'Buscar produto por nome ou codigo',
                get_selected_model_choice_value(form, 'produto'),
            )
