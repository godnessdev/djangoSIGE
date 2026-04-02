# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

from djangosige.apps.cadastro.models import Empresa, MinhaEmpresa, UsuarioEmpresa


class EmpresaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(EmpresaForm, self).__init__(*args, **kwargs)
        empresa_pai_queryset = Empresa.objects.filter(
            tipo_empresa=Empresa.TIPO_MATRIZ).order_by('nome_razao_social')

        if self.instance and self.instance.pk:
            empresa_pai_queryset = empresa_pai_queryset.exclude(pk=self.instance.pk)

        self.fields['tipo_empresa'].required = False
        self.fields['empresa_pai'].required = False
        self.fields['empresa_pai'].queryset = empresa_pai_queryset
        self.fields['empresa_pai'].empty_label = 'Selecione a matriz'

    class Meta:
        model = Empresa
        fields = ('nome_razao_social', 'tipo_empresa', 'empresa_pai',
                  'inscricao_municipal', 'cnae', 'logo_file', 'iest',
                  'informacoes_adicionais',)

        widgets = {
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_empresa': forms.Select(attrs={'class': 'form-control'}),
            'empresa_pai': forms.Select(attrs={'class': 'form-control'}),
            'cnae': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
            'logo_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'iest': forms.TextInput(attrs={'class': 'form-control'}),
            'informacoes_adicionais': forms.Textarea(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome_razao_social': _('Razao Social'),
            'tipo_empresa': _('Tipo de Empresa'),
            'empresa_pai': _('Empresa Matriz'),
            'cnae': _('CNAE'),
            'inscricao_municipal': _('Inscricao Municipal'),
            'logo_file': _('Logo'),
            'iest': _('IE do substituto tributario'),
            'informacoes_adicionais': _('Informacoes Adicionais'),
        }

    def clean(self):
        cleaned_data = super(EmpresaForm, self).clean()
        tipo_empresa = cleaned_data.get('tipo_empresa') or Empresa.TIPO_INDEPENDENTE

        cleaned_data['tipo_empresa'] = tipo_empresa
        if tipo_empresa != Empresa.TIPO_FILIAL:
            cleaned_data['empresa_pai'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super(EmpresaForm, self).save(commit=False)
        instance.tipo_pessoa = 'PJ'
        instance.tipo_empresa = self.cleaned_data.get(
            'tipo_empresa') or Empresa.TIPO_INDEPENDENTE
        instance.empresa_pai = self.cleaned_data.get('empresa_pai')
        if self.request:
            instance.criado_por = self.request.user
            if 'empresa_form-logo_file' in self.request.FILES:
                instance.logo_file = self.request.FILES['empresa_form-logo_file']
        if commit:
            instance.save()
        return instance


class MinhaEmpresaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super(MinhaEmpresaForm, self).__init__(*args, **kwargs)

        queryset = Empresa.objects.none()
        if self.usuario:
            if self.usuario.user.is_superuser:
                queryset = Empresa.objects.order_by('nome_razao_social')
            else:
                queryset = Empresa.objects.filter(
                    usuarios_permitidos__m_usuario=self.usuario).distinct().order_by('nome_razao_social')

        self.fields['m_empresa'].queryset = queryset
        self.fields['m_empresa'].required = False

    class Meta:
        model = MinhaEmpresa
        fields = ('m_empresa',)

        widgets = {
            'm_empresa': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'm_empresa': _('Minha Empresa'),
        }


class UsuarioEmpresaForm(forms.Form):
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'id': 'id_select_empresas'}),
        label='Empresas permitidas',
    )

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super(UsuarioEmpresaForm, self).__init__(*args, **kwargs)
        queryset = Empresa.objects.order_by('nome_razao_social')
        self.fields['empresas'].queryset = queryset

        if self.usuario:
            self.initial['empresas'] = UsuarioEmpresa.objects.filter(
                m_usuario=self.usuario).values_list('m_empresa_id', flat=True)
