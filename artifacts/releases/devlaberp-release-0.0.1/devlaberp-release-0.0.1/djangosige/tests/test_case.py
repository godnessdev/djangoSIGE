# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.db.models.fields.files import FieldFile

import json

from djangosige.apps.cadastro.models import Empresa, MinhaEmpresa, UsuarioEmpresa, Cliente, Fornecedor, Transportadora
from djangosige.apps.compras.models import Compra
from djangosige.apps.estoque.models import LocalEstoque, MovimentoEstoque
from djangosige.apps.financeiro.models import Lancamento, MovimentoCaixa
from djangosige.apps.financeiro.models import PlanoContasGrupo
from djangosige.apps.fiscal.models import ConfiguracaoNotaFiscal, GrupoFiscal, NaturezaOperacao, NotaFiscalSaida, NotaFiscalEntrada
from djangosige.apps.login.models import Usuario
from djangosige.apps.vendas.models import Venda

TEST_USERNAME = "test"
TEST_PASSWORD = "testpass"
TEST_EMAIL = "test@test.com"


class BaseTestCase(TestCase):
    fixtures = ["initial_user.json", "test_db_backup.json", ]

    def setUp(self):
        try:
            self.user = User.objects.get(
                username=TEST_USERNAME, email=TEST_EMAIL)
        except User.DoesNotExist:
            self.user = User.objects.create_user(
                TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD)

        self.usuario = Usuario.objects.get_or_create(user=self.user)[0]
        self.empresa_ativa = Empresa.objects.order_by('pk').first() or Empresa.objects.create(
            nome_razao_social='Empresa Teste', tipo_pessoa='PJ')
        UsuarioEmpresa.objects.get_or_create(
            m_usuario=self.usuario, m_empresa=self.empresa_ativa)
        MinhaEmpresa.objects.update_or_create(
            m_usuario=self.usuario,
            defaults={'m_empresa': self.empresa_ativa})
        self._backfill_empresa_operacional()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

    def _backfill_empresa_operacional(self):
        LocalEstoque.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        Compra.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        Venda.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        MovimentoEstoque.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        Cliente.objects.filter(empresa_relacionada__isnull=True).update(
            empresa_relacionada=self.empresa_ativa)
        Fornecedor.objects.filter(empresa_relacionada__isnull=True).update(
            empresa_relacionada=self.empresa_ativa)
        Transportadora.objects.filter(empresa_relacionada__isnull=True).update(
            empresa_relacionada=self.empresa_ativa)
        Lancamento.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        MovimentoCaixa.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        PlanoContasGrupo.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        NaturezaOperacao.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        GrupoFiscal.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        ConfiguracaoNotaFiscal.objects.filter(empresa__isnull=True).update(
            empresa=self.empresa_ativa)
        NotaFiscalSaida.objects.filter(emit_saida__isnull=True).update(
            emit_saida=self.empresa_ativa)
        NotaFiscalEntrada.objects.filter(dest_entrada__isnull=True).update(
            dest_entrada=self.empresa_ativa)

    def check_user_get_permission(self, url, permission_codename):
        if not isinstance(permission_codename, list):
            permission_codename = [permission_codename]
        self.user.is_superuser = False
        perms = Permission.objects.get(codename__in=permission_codename)
        self.user.user_permissions.remove(perms)
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url, follow=True)
        message_tags = " ".join(str(m.tags)
                                for m in list(response.context['messages']))
        self.assertIn("permission_warning", message_tags)
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

    def check_list_view_delete(self, url, deleted_object, context_object_key='object_list'):
        # Testar GET request lista
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(deleted_object in response.context[context_object_key])

        # Deletar objeto criado por POST request
        data = {
            deleted_object.pk: 'on',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(deleted_object in response.context[
                         context_object_key])

    def check_json_response(self, url, post_data, obj_pk, model):
        response = self.client.post(url, post_data, follow=True)
        response_content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        for c in response_content:
            if c['model'] == model:
                self.assertEqual(c['pk'], obj_pk)


def replace_none_values_in_dictionary(dictionary):
    for key, value in dictionary.items():
        if value is None or isinstance(value, FieldFile):
            dictionary[key] = ''
