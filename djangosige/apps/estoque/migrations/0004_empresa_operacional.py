# -*- coding: utf-8 -*-

from django.db import migrations, models
import django.db.models.deletion


def preencher_empresa_estoque(apps, schema_editor):
    Empresa = apps.get_model('cadastro', 'Empresa')
    LocalEstoque = apps.get_model('estoque', 'LocalEstoque')
    MovimentoEstoque = apps.get_model('estoque', 'MovimentoEstoque')

    empresa = Empresa.objects.order_by('pk').first()
    if empresa is None:
        return

    LocalEstoque.objects.filter(empresa__isnull=True).update(empresa=empresa)
    MovimentoEstoque.objects.filter(empresa__isnull=True).update(empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0005_usuarioempresa'),
        ('estoque', '0003_merge_20170625_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='localestoque',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='locais_estoque', to='cadastro.Empresa'),
        ),
        migrations.AddField(
            model_name='movimentoestoque',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='movimentos_estoque', to='cadastro.Empresa'),
        ),
        migrations.RunPython(preencher_empresa_estoque, migrations.RunPython.noop),
    ]
