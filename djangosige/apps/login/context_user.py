# -*- coding: utf-8 -*-

from .models import Usuario
from djangosige.apps.cadastro.models import Empresa, MinhaEmpresa, UsuarioEmpresa

# Manter foto do perfil na sidebar


def foto_usuario(request):
    context_dict = {}
    # Foto do usuario
    try:
        user_foto = Usuario.objects.get(user=request.user).user_foto
        context_dict['user_foto_sidebar'] = user_foto
    except:
        pass

    # Empresa do usuario
    try:
        usuario = Usuario.objects.get(user=request.user)
        user_empresa = MinhaEmpresa.objects.get(
            m_usuario=usuario).m_empresa
        if user_empresa:
            context_dict['user_empresa'] = user_empresa
    except:
        pass

    try:
        usuario = Usuario.objects.get(user=request.user)
        if usuario.user.is_superuser:
            context_dict['user_empresas_permitidas'] = list(
                Empresa.objects.order_by('nome_razao_social'))
        else:
            empresas_permitidas = UsuarioEmpresa.objects.filter(
                m_usuario=usuario).select_related('m_empresa')
            context_dict['user_empresas_permitidas'] = [
                acesso.m_empresa for acesso in empresas_permitidas]
    except:
        pass

    return context_dict
