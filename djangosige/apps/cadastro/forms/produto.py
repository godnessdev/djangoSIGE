# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

from djangosige.apps.cadastro.models import Produto, ProdutoEmpresa, Unidade, Marca, Categoria, Fornecedor
from djangosige.apps.cadastro.utils import get_empresa_ativa
from djangosige.apps.estoque.models import LocalEstoque
from djangosige.apps.fiscal.models import GrupoFiscal, NaturezaOperacao

from decimal import Decimal


class ProdutoForm(forms.ModelForm):
    custo = forms.DecimalField(max_digits=16, decimal_places=2, localize=True, widget=forms.TextInput(
        attrs={'class': 'form-control decimal-mask', 'placeholder': 'R$ 0,00'}), initial=Decimal('0.00'), label='Custo', required=False)
    venda = forms.DecimalField(max_digits=16, decimal_places=2, localize=True, widget=forms.TextInput(
        attrs={'class': 'form-control decimal-mask', 'placeholder': 'R$ 0,00'}), initial=Decimal('0.00'), label='Venda', required=False)

    # Estoque
    estoque_inicial = forms.DecimalField(max_digits=16, decimal_places=2, localize=True, widget=forms.TextInput(
        attrs={'class': 'form-control decimal-mask'}), label='Qtd. em estoque inicial', initial=Decimal('0.00'), required=False)
    fornecedor = forms.ModelChoiceField(queryset=Fornecedor.objects.none(), widget=forms.Select(
        attrs={'class': 'form-control'}), label='Fornecedor', required=False, empty_label='----------')
    local_dest = forms.ModelChoiceField(queryset=LocalEstoque.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control'}), empty_label=None, label='Localização do estoque de destino', required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProdutoForm, self).__init__(*args, **kwargs)
        self.fields['estoque_minimo'].localize = True
        self.empresa_ativa = get_empresa_ativa(self.user)
        self.fields['cfop_padrao'].queryset = NaturezaOperacao.objects.none()
        self.fields['grupo_fiscal'].queryset = GrupoFiscal.objects.none()
        if self.empresa_ativa:
            self.fields['fornecedor'].queryset = Fornecedor.objects.filter(
                empresa_relacionada=self.empresa_ativa).order_by('nome_razao_social')
            self.fields['local_dest'].queryset = LocalEstoque.objects.filter(
                empresa=self.empresa_ativa)
            self.fields['cfop_padrao'].queryset = NaturezaOperacao.objects.filter(
                empresa=self.empresa_ativa).order_by('cfop', 'descricao')
            self.fields['grupo_fiscal'].queryset = GrupoFiscal.objects.filter(
                empresa=self.empresa_ativa).order_by('descricao')
            if self.instance.pk:
                self.fields['venda'].initial = self.instance.get_venda_empresa(
                    self.empresa_ativa)
                self.fields['custo'].initial = self.instance.get_custo_empresa(
                    self.empresa_ativa)
                self.fields['cfop_padrao'].initial = self.instance.get_cfop_padrao_obj(
                    self.empresa_ativa)
                self.fields['grupo_fiscal'].initial = self.instance.get_grupo_fiscal_empresa(
                    self.empresa_ativa)

    def save(self, commit=True):
        produto_existente = None
        if self.instance.pk:
            produto_existente = Produto.objects.get(pk=self.instance.pk)

        instance = super(ProdutoForm, self).save(commit=False)
        venda = self.cleaned_data.get('venda')
        custo = self.cleaned_data.get('custo')
        cfop_padrao = self.cleaned_data.get('cfop_padrao')
        grupo_fiscal = self.cleaned_data.get('grupo_fiscal')

        if produto_existente and self.empresa_ativa:
            instance.venda = produto_existente.venda
            instance.custo = produto_existente.custo
            instance.cfop_padrao = produto_existente.cfop_padrao
            instance.grupo_fiscal = produto_existente.grupo_fiscal

        if commit:
            instance.save()
            self.save_company_configuration(instance)
            self.save_m2m()
        return instance

    def save_company_configuration(self, instance):
        if not self.empresa_ativa or not instance.pk:
            return

        ProdutoEmpresa.objects.update_or_create(
            produto=instance,
            empresa=self.empresa_ativa,
            defaults={
                'venda': self.cleaned_data.get('venda'),
                'custo': self.cleaned_data.get('custo'),
                'cfop_padrao': self.cleaned_data.get('cfop_padrao'),
                'grupo_fiscal': self.cleaned_data.get('grupo_fiscal'),
            }
        )
        if hasattr(instance, '_configuracao_empresa_cache'):
            instance._configuracao_empresa_cache[self.empresa_ativa.pk] = instance.configuracoes_empresa.filter(
                empresa=self.empresa_ativa).first()

    class Meta:
        model = Produto
        fields = ('codigo', 'codigo_barras', 'descricao', 'categoria', 'marca', 'unidade', 'ncm', 'venda', 'custo', 'inf_adicionais',
                  'origem', 'cest', 'cfop_padrao', 'grupo_fiscal', 'estoque_minimo', 'controlar_estoque',)
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.Select(attrs={'class': 'form-control'}),
            'unidade': forms.Select(attrs={'class': 'form-control'}),
            'ncm': forms.TextInput(attrs={'class': 'form-control'}),
            'inf_adicionais': forms.Textarea(attrs={'class': 'form-control'}),
            'origem': forms.Select(attrs={'class': 'form-control'}),
            'cest': forms.TextInput(attrs={'class': 'form-control'}),
            'cfop_padrao': forms.Select(attrs={'class': 'form-control'}),
            'grupo_fiscal': forms.Select(attrs={'class': 'form-control'}),
            'estoque_minimo': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'controlar_estoque': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'codigo': _('Código'),
            'codigo_barras': _('Código de Barras (GTIN/EAN)'),
            'descricao': _('Descrição'),
            'categoria': _('Categoria'),
            'marca': _('Marca'),
            'unidade': _('Unidade'),
            'ncm': _('NCM'),
            'inf_adicionais': _('Informações adicionais'),
            'origem': _('Origem'),
            'cest': _('CEST'),
            'cfop_padrao': _('CFOP (Padrão)'),
            'grupo_fiscal': _('Grupo Fiscal (Padrão)'),
            'estoque_minimo': _('Qtd. em estoque mínima'),
            'controlar_estoque': _('Controlar estoque deste produto?'),
        }


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ('categoria_desc',)
        widgets = {
            'categoria_desc': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'categoria_desc': _('Categoria'),
        }


class MarcaForm(forms.ModelForm):

    class Meta:
        model = Marca
        fields = ('marca_desc',)
        widgets = {
            'marca_desc': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'marca_desc': _('Marca'),
        }


class UnidadeForm(forms.ModelForm):

    class Meta:
        model = Unidade
        fields = ('sigla_unidade', 'unidade_desc',)
        widgets = {
            'unidade_desc': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla_unidade': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'unidade_desc': _('Nome descritivo'),
            'sigla_unidade': _('Sigla'),
        }
