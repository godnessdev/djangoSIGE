# -*- coding: utf-8 -*-

from django.db import models

from .base import Pessoa


class Fornecedor(Pessoa):
    empresa_relacionada = models.ForeignKey(
        'cadastro.Empresa', related_name='fornecedores',
        on_delete=models.CASCADE, null=True, blank=True)
    ramo = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        verbose_name = "Fornecedor"
