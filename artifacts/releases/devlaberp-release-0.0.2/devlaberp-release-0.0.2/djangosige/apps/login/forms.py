# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from .models import Usuario
from djangosige.apps.cadastro.models import Empresa, PessoaJuridica, MinhaEmpresa, UsuarioEmpresa

# Form para login do usuario


class UserLoginForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'password')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control line-input', 'placeholder': 'Nome de usuário'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control line-input', 'placeholder': 'Senha'}),
        }
        labels = {
            'username': _(u'person'),
            'password': _(u'lock'),
        }

    # Validar/autenticar campos de login
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError(u"Usuário ou senha inválidos.")
        return self.cleaned_data

    def authenticate_user(self, username, password):
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError(u"Usuário ou senha inválidos.")
        return user


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control line-input', 'placeholder': 'Senha'}), min_length=6, label='lock')
    confirm = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control line-input', 'placeholder': 'Confirme a senha'}), min_length=6, label='lock')
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control line-input', 'placeholder': 'Nome de usuário'}), label='person')
    email = forms.CharField(widget=forms.EmailInput(attrs={
                            'class': 'form-control line-input', 'placeholder': 'Email'}), label='email', required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password',)


class PasswordResetForm(forms.Form):
    email_or_username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control line-input', 'placeholder': 'Email/Usuário'}))


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control line-input', 'placeholder': 'Nova senha'}), min_length=6)
    new_password_confirm = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control line-input', 'placeholder': 'Confirmar a nova senha'}), min_length=6)


class PerfilUsuarioForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}), label='Nome de usuário')
    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}), label='Nome', required=False)
    last_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}), label='Sobrenome', required=False)
    email = forms.CharField(widget=forms.EmailInput(
        attrs={'class': 'form-control'}), label='Email', required=False)
    user_foto = forms.ImageField(widget=forms.FileInput(
        attrs={'class': 'form-control', 'accept': 'image/*'}), label='Foto de perfil', required=False)

    def __init__(self, *args, **kwargs):
        super(PerfilUsuarioForm, self).__init__(*args, **kwargs)
        self.fields['username'].initial = self.instance.user.username
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['email'].initial = self.instance.user.email

    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'username', 'email', 'user_foto',)


class InitialSetupEmpresaForm(forms.Form):
    nome_razao_social = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Ex.: ACME Comercio Ltda'}
        ),
        label='business',
    )
    nome_fantasia = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Ex.: ACME'}
        ),
        label='store',
        required=False,
    )
    cnpj = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control line-input',
                'placeholder': '00.000.000/0000-00',
                'data-cnpj-lookup-field': 'cnpj',
                'data-cnpj-autolookup': 'true',
                'autocomplete': 'off',
            }
        ),
        label='badge',
        required=False,
    )
    inscricao_estadual = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Ex.: 123.456.789.000'}
        ),
        label='assignment',
        required=False,
    )
    tipo_empresa = forms.ChoiceField(
        choices=(
            (Empresa.TIPO_MATRIZ, 'Matriz'),
            (Empresa.TIPO_INDEPENDENTE, 'Independente'),
        ),
        widget=forms.Select(attrs={'class': 'form-control line-input'}),
        label='apartment',
        initial=Empresa.TIPO_MATRIZ,
    )

    def save(self):
        empresa = Empresa(
            nome_razao_social=self.cleaned_data['nome_razao_social'],
            tipo_pessoa='PJ',
            tipo_empresa=self.cleaned_data['tipo_empresa'],
        )
        empresa.clean()
        empresa.save()
        PessoaJuridica.objects.create(
            pessoa_id=empresa,
            nome_fantasia=self.cleaned_data.get('nome_fantasia'),
            cnpj=self.cleaned_data.get('cnpj'),
            inscricao_estadual=self.cleaned_data.get('inscricao_estadual'),
        )
        return empresa


class InitialSetupAdminForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Ex.: admin'}
        ),
        label='person',
    )
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Ex.: Leonardo'}
        ),
        label='badge',
        required=False,
    )
    email = forms.CharField(
        widget=forms.EmailInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Ex.: admin@empresa.com.br'}
        ),
        label='email',
        required=False,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Minimo de 6 caracteres'}
        ),
        min_length=6,
        label='lock',
    )
    confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control line-input', 'placeholder': 'Repita a senha'}
        ),
        min_length=6,
        label='lock',
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ja existe um usuario com este nome.')
        return username

    def clean(self):
        cleaned_data = super(InitialSetupAdminForm, self).clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm')
        if password and confirm and password != confirm:
            self.add_error('password', 'Senhas diferentes.')
        return cleaned_data

    def save(self, empresa):
        user = User.objects.create_superuser(
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data['password'],
        )
        user.first_name = self.cleaned_data.get('first_name', '')
        user.save(update_fields=['first_name'])

        usuario = Usuario.objects.get_or_create(user=user)[0]
        if empresa:
            UsuarioEmpresa.objects.get_or_create(m_usuario=usuario, m_empresa=empresa)
            MinhaEmpresa.objects.update_or_create(
                m_usuario=usuario,
                defaults={'m_empresa': empresa},
            )
        return user
