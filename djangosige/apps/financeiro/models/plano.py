# -*- coding: utf-8 -*-

from django.db import models

TIPO_GRUPO_ESCOLHAS = (
    (u'0', u'Entrada'),
    (u'1', u'Saída'),
)


class PlanoContasGrupo(models.Model):
    empresa = models.ForeignKey(
        'cadastro.Empresa', related_name='planos_conta',
        on_delete=models.CASCADE, null=True, blank=True)
    codigo = models.CharField(max_length=6)
    tipo_grupo = models.CharField(max_length=1, choices=TIPO_GRUPO_ESCOLHAS)
    descricao = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Grupo do Plano de Contas"

    def __unicode__(self):
        s = u'%s' % (self.descricao)
        return s

    def __str__(self):
        s = u'%s' % (self.descricao)
        return s


class PlanoContasSubgrupo(PlanoContasGrupo):
    grupo = models.ForeignKey('financeiro.PlanoContasGrupo',
                              related_name="subgrupos", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.grupo_id and not self.empresa_id:
            self.empresa = self.grupo.empresa
        super(PlanoContasSubgrupo, self).save(*args, **kwargs)
