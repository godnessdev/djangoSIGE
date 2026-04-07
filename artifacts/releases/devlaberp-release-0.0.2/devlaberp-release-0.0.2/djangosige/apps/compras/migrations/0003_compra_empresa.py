# -*- coding: utf-8 -*-

from django.db import migrations, models
import django.db.models.deletion


def preencher_empresa_compra(apps, schema_editor):
    Empresa = apps.get_model('cadastro', 'Empresa')
    Compra = apps.get_model('compras', 'Compra')

    empresa = Empresa.objects.order_by('pk').first()
    if empresa is None:
        return

    Compra.objects.filter(empresa__isnull=True).update(empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0005_usuarioempresa'),
        ('estoque', '0004_empresa_operacional'),
        ('compras', '0002_auto_20170625_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='compra',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='compras', to='cadastro.Empresa'),
        ),
        migrations.RunPython(preencher_empresa_compra, migrations.RunPython.noop),
    ]
