# -*- coding: utf-8 -*-

import os

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .base import Pessoa
from djangosige.apps.login.models import Usuario
from djangosige.configs.settings import MEDIA_ROOT


def logo_directory_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return 'imagens/empresas/logo_{0}_{1}{2}'.format(instance.nome_razao_social, instance.id, extension)


class Empresa(Pessoa):
    TIPO_INDEPENDENTE = 'IND'
    TIPO_MATRIZ = 'MAT'
    TIPO_FILIAL = 'FIL'

    TIPO_EMPRESA_CHOICES = (
        (TIPO_INDEPENDENTE, 'Independente'),
        (TIPO_MATRIZ, 'Matriz'),
        (TIPO_FILIAL, 'Filial'),
    )

    logo_file = models.ImageField(
        upload_to=logo_directory_path, default='imagens/logo.png', blank=True, null=True)
    cnae = models.CharField(max_length=10, blank=True, null=True)
    iest = models.CharField(max_length=32, null=True, blank=True)
    tipo_empresa = models.CharField(
        max_length=3, choices=TIPO_EMPRESA_CHOICES, default=TIPO_INDEPENDENTE)
    empresa_pai = models.ForeignKey(
        'self', on_delete=models.PROTECT, related_name='filiais',
        blank=True, null=True)

    class Meta:
        verbose_name = "Empresa"

    def clean(self):
        errors = {}
        empresa_pai = self.empresa_pai

        if empresa_pai and self.pk and empresa_pai.pk == self.pk:
            errors['empresa_pai'] = 'A empresa nao pode apontar para si mesma.'

        if self.tipo_empresa == self.TIPO_FILIAL:
            if not empresa_pai:
                errors['empresa_pai'] = 'Selecione a matriz desta filial.'
            elif empresa_pai.tipo_empresa != self.TIPO_MATRIZ:
                errors['empresa_pai'] = 'A filial deve apontar para uma empresa do tipo matriz.'
        elif empresa_pai:
            errors['empresa_pai'] = 'Apenas empresas do tipo filial podem possuir matriz vinculada.'

        visited_ids = set()
        visited_objects = set()
        current = empresa_pai
        while current:
            current_object_id = id(current)
            if current_object_id in visited_objects or current == self:
                errors['empresa_pai'] = 'A hierarquia informada cria um ciclo invalido.'
                break
            visited_objects.add(current_object_id)
            if current.pk:
                if current.pk in visited_ids or (self.pk and current.pk == self.pk):
                    errors['empresa_pai'] = 'A hierarquia informada cria um ciclo invalido.'
                    break
                visited_ids.add(current.pk)
            current = current.empresa_pai

        if errors:
            raise ValidationError(errors)

    @property
    def caminho_completo_logo(self):
        if self.logo_file.name != 'imagens/logo.png':
            return os.path.join(MEDIA_ROOT, self.logo_file.name)
        else:
            return ''

    @property
    def matriz_vinculada(self):
        if self.tipo_empresa == self.TIPO_FILIAL:
            return self.empresa_pai
        return None

    def get_matriz_grupo(self):
        if self.tipo_empresa == self.TIPO_FILIAL and self.empresa_pai_id:
            return self.empresa_pai
        return self

    def get_empresas_grupo(self):
        matriz = self.get_matriz_grupo()
        if matriz.tipo_empresa == self.TIPO_MATRIZ:
            return Empresa.objects.filter(
                Q(pk=matriz.pk) | Q(empresa_pai=matriz)
            ).order_by('nome_razao_social')
        return Empresa.objects.filter(pk=self.pk)

    def pertence_ao_mesmo_grupo(self, outra_empresa):
        if not outra_empresa:
            return False
        return self.get_empresas_grupo().filter(pk=outra_empresa.pk).exists()

    def save(self, *args, **kwargs):
        # Deletar logo se ja existir um
        try:
            obj = Empresa.objects.get(id=self.id)
            if obj.logo_file != self.logo_file and obj.logo_file != 'imagens/logo.png':
                obj.logo_file.delete(save=False)
        except:
            pass
        super(Empresa, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.nome_razao_social

    def __str__(self):
        return u'%s' % self.nome_razao_social

# Deletar logo quando empresa for deletada


@receiver(post_delete, sender=Empresa)
def logo_post_delete_handler(sender, instance, **kwargs):
    # Nao deletar a imagem default 'logo.png'
    if instance.logo_file != 'imagens/logo.png':
        instance.logo_file.delete(False)


class MinhaEmpresa(models.Model):
    m_empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name='minha_empresa', blank=True, null=True)
    m_usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='empresa_usuario')

    def clean(self):
        if not self.m_empresa_id or not self.m_usuario_id:
            return
        if self.m_usuario.user.is_superuser:
            return
        if not UsuarioEmpresa.objects.filter(
                m_usuario=self.m_usuario, m_empresa=self.m_empresa).exists():
            raise ValidationError(
                {'m_empresa': 'O usuario nao possui acesso a esta empresa.'})


class UsuarioEmpresa(models.Model):
    m_empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name='usuarios_permitidos')
    m_usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='empresas_permitidas')

    class Meta:
        unique_together = ('m_empresa', 'm_usuario')
        verbose_name = 'Empresa permitida do usuario'
