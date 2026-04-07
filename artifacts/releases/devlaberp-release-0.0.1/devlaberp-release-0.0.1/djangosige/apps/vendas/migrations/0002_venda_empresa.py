# -*- coding: utf-8 -*-

from django.db import migrations, models
import django.db.models.deletion


def preencher_empresa_venda(apps, schema_editor):
    Empresa = apps.get_model('cadastro', 'Empresa')
    Venda = apps.get_model('vendas', 'Venda')

    empresa = Empresa.objects.order_by('pk').first()
    if empresa is None:
        return

    Venda.objects.filter(empresa__isnull=True).update(empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0005_usuarioempresa'),
        ('estoque', '0004_empresa_operacional'),
        ('vendas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='venda',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vendas', to='cadastro.Empresa'),
        ),
        migrations.RunPython(preencher_empresa_venda, migrations.RunPython.noop),
    ]
