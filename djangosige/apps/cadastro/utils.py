# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db.models import Q

from djangosige.apps.cadastro.models import Empresa, MinhaEmpresa, UsuarioEmpresa
from djangosige.apps.login.models import Usuario


def get_usuario_from_user(user):
    if isinstance(user, Usuario):
        return user
    if isinstance(user, User):
        return Usuario.objects.get_or_create(user=user)[0]
    return None


def get_empresa_ativa(user):
    usuario = get_usuario_from_user(user)
    if not usuario:
        return None

    try:
        return MinhaEmpresa.objects.select_related('m_empresa').get(
            m_usuario=usuario).m_empresa
    except MinhaEmpresa.DoesNotExist:
        empresas_permitidas = UsuarioEmpresa.objects.select_related(
            'm_empresa').filter(m_usuario=usuario)
        if empresas_permitidas.count() == 1:
            return empresas_permitidas.first().m_empresa
        return None


def filtrar_queryset_por_empresa_ativa(queryset, user, field_name='empresa'):
    empresa = get_empresa_ativa(user)
    if empresa is None:
        return queryset.none()
    return queryset.filter(**{field_name: empresa})


def get_empresas_permitidas(user):
    usuario = get_usuario_from_user(user)
    if not usuario:
        return Empresa.objects.none()
    if usuario.user.is_superuser:
        return Empresa.objects.all().order_by('nome_razao_social')
    return Empresa.objects.filter(
        usuarios_permitidos__m_usuario=usuario).order_by('nome_razao_social').distinct()


def get_empresas_grupo_permitidas(user, empresa=None, include_empresa_ativa=True):
    empresa = empresa or get_empresa_ativa(user)
    if empresa is None:
        return Empresa.objects.none()

    empresas_grupo = empresa.get_empresas_grupo()
    empresas_permitidas = get_empresas_permitidas(user)
    queryset = empresas_grupo.filter(pk__in=empresas_permitidas.values('pk')).distinct()
    if include_empresa_ativa:
        return queryset
    return queryset.exclude(pk=empresa.pk)


def pode_consultar_consolidado_grupo(user, empresa=None):
    empresa = empresa or get_empresa_ativa(user)
    if empresa is None:
        return False
    if empresa.tipo_empresa == Empresa.TIPO_MATRIZ:
        return True
    return user.groups.filter(name__in=['gestor_matriz', 'auditoria_retaguarda']).exists()


def filtrar_transferencias_por_empresa(queryset, empresa):
    if empresa is None:
        return queryset.none()
    return queryset.filter(Q(empresa=empresa) | Q(empresa_destino=empresa)).distinct()


def get_primeira_empresa():
    return Empresa.objects.order_by('pk').first()
