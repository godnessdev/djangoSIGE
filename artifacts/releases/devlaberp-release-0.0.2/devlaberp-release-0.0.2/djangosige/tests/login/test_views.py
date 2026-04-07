# -*- coding: utf-8 -*-

from djangosige.tests.test_case import BaseTestCase, TEST_USERNAME, TEST_PASSWORD
from djangosige.apps.cadastro.models import Empresa, MinhaEmpresa, UsuarioEmpresa
from djangosige.apps.login.models import Usuario

from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.test import TestCase
from django.db.models import Q
from unittest.mock import patch
import json


class UserFormViewTestCase(BaseTestCase):

    def test_user_logged_in_redirect(self):
        url = reverse('login:loginview')

        # Assert login redirect se usuario logado
        response = self.client.get(url)
        self.assertEqual(response.url, '/')

        # Assert abre pagina se usuario nao logado
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')

    def test_user_login(self):
        url = reverse('login:loginview')
        self.client.logout()
        data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base/index.html')


class InitialSetupFlowTestCase(TestCase):

    def test_login_shows_initial_setup_when_database_is_empty(self):
        response = self.client.get(reverse('login:loginview'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/instalacao_inicial.html')
        self.assertEqual(response.context['install_step'], 'empresa')
        self.assertContains(response, reverse('login:consultacnpjview'))
        self.assertContains(response, 'js-cnpj-lookup')

    def test_initial_setup_creates_company_then_admin(self):
        url = reverse('login:loginview')
        response = self.client.post(url, {
            'nome_razao_social': 'Empresa Inicial',
            'nome_fantasia': 'Empresa Inicial',
            'cnpj': '00.000.000/0001-91',
            'inscricao_estadual': '123456789',
            'tipo_empresa': Empresa.TIPO_MATRIZ,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/instalacao_inicial.html')
        self.assertEqual(response.context['install_step'], 'admin')
        empresa = Empresa.objects.get(nome_razao_social='Empresa Inicial')
        self.assertEqual(empresa.tipo_empresa, Empresa.TIPO_MATRIZ)
        self.assertEqual(empresa.pessoa_jur_info.nome_fantasia, 'Empresa Inicial')

        response = self.client.post(url, {
            'username': 'admin',
            'first_name': 'Administrador',
            'email': 'admin@test.com',
            'password': 'admin123',
            'confirm': 'admin123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base/index.html')
        user = User.objects.get(username='admin')
        self.assertTrue(user.is_superuser)
        usuario = Usuario.objects.get(user=user)
        self.assertEqual(MinhaEmpresa.objects.get(m_usuario=usuario).m_empresa, empresa)

    @patch('djangosige.apps.cadastro.views.ajax_views.urllib_request.urlopen')
    def test_initial_setup_cnpj_lookup_is_available_without_login(self, mocked_urlopen):
        class _MockHTTPResponse(object):
            def __init__(self, payload):
                self.payload = payload

            def read(self):
                return json.dumps(self.payload).encode('utf-8')

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        mocked_urlopen.return_value = _MockHTTPResponse({
            'cnpj': '27865757000102',
            'razao_social': 'EMPRESA LOGIN LTDA',
            'nome_fantasia': 'EMPRESA LOGIN',
            'logradouro': 'Rua Exemplo',
            'numero': '100',
            'complemento': 'Sala 1',
            'bairro': 'Centro',
            'municipio': 'Belo Horizonte',
            'uf': 'MG',
            'cep': '30110000',
            'ddd_telefone_1': '31',
            'telefone_1': '33334444',
            'email': 'contato@login.com',
            'qsa': [{'nome_socio': 'SOCIO LOGIN'}],
        })

        response = self.client.get(
            reverse('login:consultacnpjview'),
            {'cnpj': '27.865.757/0001-02'}
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode('utf-8'))
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['nome_razao_social'], 'EMPRESA LOGIN LTDA')
        self.assertEqual(payload['data']['cnpj'], '27.865.757/0001-02')


class UserRegistrationFormViewTestCase(BaseTestCase):

    def test_registration_view_get_request(self):
        url = reverse('login:registrarview')
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/registrar.html')

    def test_user_registration(self):
        url = reverse('login:registrarview')
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        data = {
            'username': 'newUser',
            'password': 'password1234',
            'confirm': 'password1234',
            'email': 'newUser@email.com',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newUser').exists())

        # Assert form invalido (senhas diferentes)
        data = {
            'username': 'newUser2',
            'password': 'password1234',
            'confirm': 'diferente',
            'email': 'newUser2@email.com',
        }
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response, 'form', 'password', 'Senhas diferentes.')

    def test_superuser_required(self):
        url = reverse('login:registrarview')
        # Assert usuario redirect para index se nao e administrador
        self.user.is_superuser = False
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.url, '/')


class UserLogoutViewTestCase(BaseTestCase):

    def test_user_logout_redirect(self):
        url = reverse('login:logoutview')
        response = self.client.get(url)
        self.assertEqual(response.url, '/login/')


class ForgotPasswordViewTestCase(BaseTestCase):

    def test_forgot_view_get_request(self):
        url = reverse('login:esqueceuview')

        # Assert login redirect se usuario logado
        response = self.client.get(url)
        self.assertEqual(response.url, '/')

        # Assert abre pagina se usuario nao logado
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/esqueceu_senha.html')


class MeuPerfilViewTestCase(BaseTestCase):

    def test_perfil_get_request(self):
        url = reverse('login:perfilview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class EditarPerfilViewTestCase(BaseTestCase):

    def test_editar_perfil_view(self):
        url = reverse('login:editarperfilview')
        m_empresa = Empresa.objects.create()
        usuario = Usuario.objects.get(user=self.user)
        UsuarioEmpresa.objects.create(m_usuario=usuario, m_empresa=m_empresa)

        # Sem MinhaEmpresa cadastrada
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Adicionar MinhaEmpresa pela view
        data = response.context['form'].initial
        data['username'] = response.context['user'].username
        data['first_name'] = response.context['user'].first_name
        data['last_name'] = response.context['user'].last_name
        data['email'] = response.context['user'].email
        data['m_empresa_form-m_empresa'] = m_empresa.pk

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/perfil.html')
        self.assertEqual(usuario.empresa_usuario.all()[
                         0].m_empresa.pk, m_empresa.pk)


class SelecionarMinhaEmpresaViewTestCase(BaseTestCase):

    def test_selecionar_empresa_view(self):
        url = reverse('login:selecionarempresaview')
        self.user.is_superuser = False
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        m_empresa = Empresa.objects.create()
        outra_empresa = Empresa.objects.filter(
            ~Q(id__in=[m_empresa.pk, self.empresa_ativa.pk])).first() or Empresa.objects.create()
        usuario = Usuario.objects.get(user=self.user)
        UsuarioEmpresa.objects.get_or_create(m_usuario=usuario, m_empresa=m_empresa)
        UsuarioEmpresa.objects.get_or_create(m_usuario=usuario, m_empresa=outra_empresa)
        MinhaEmpresa.objects.filter(m_usuario=usuario).delete()

        # Usuario sem MinhaEmpresa
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'login/selecionar_minha_empresa.html')

        data = {'m_empresa': m_empresa.pk, }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario.empresa_usuario.all()[
                         0].m_empresa.pk, m_empresa.pk)

        # Usuario com MinhaEmpresa
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'login/selecionar_minha_empresa.html')

        m_empresa = outra_empresa
        data = {'m_empresa': m_empresa.pk, }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario.empresa_usuario.all()[
                         0].m_empresa.pk, m_empresa.pk)

    def test_usuario_nao_pode_selecionar_empresa_nao_autorizada(self):
        url = reverse('login:selecionarempresaview')
        self.user.is_superuser = False
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        empresa_autorizada = Empresa.objects.create()
        empresa_nao_autorizada = Empresa.objects.create()
        usuario = Usuario.objects.get(user=self.user)
        UsuarioEmpresa.objects.get_or_create(
            m_usuario=usuario, m_empresa=empresa_autorizada)

        response = self.client.post(
            url, {'m_empresa': empresa_nao_autorizada.pk}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('m_empresa', response.context['form'].errors)


class UsuariosListViewTestCase(BaseTestCase):

    def test_deletar_usuario(self):
        url = reverse('login:usuariosview')
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        # Testar GET request lista
        obj = User.objects.create()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(obj in response.context['object_list'])
        self.assertTemplateUsed(response, 'login/lista_users.html')

        # Deletar objeto criado por POST request
        data = {
            obj.pk: 'on',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(obj in response.context['object_list'])


class UsuarioDetailViewTestCase(BaseTestCase):

    def test_usuario_detail_get_request(self):
        url = reverse('login:usuariodetailview', kwargs={'pk': self.user.pk})
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/detalhe_users.html')


class EditarPermissoesUsuarioViewTestCase(BaseTestCase):

    def test_editar_permissoes_salva_empresas_permitidas(self):
        empresa_1 = Empresa.objects.create(nome_razao_social='Empresa 1', tipo_pessoa='PJ')
        empresa_2 = Empresa.objects.create(nome_razao_social='Empresa 2', tipo_pessoa='PJ')
        usuario_target_user = User.objects.create_user(
            'usuario-empresas', 'usuario-empresas@test.com', 'testpass')
        usuario_target = Usuario.objects.get_or_create(user=usuario_target_user)[0]

        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        url = reverse('login:permissoesusuarioview', kwargs={'pk': usuario_target_user.pk})
        response = self.client.post(url, {
            'empresas': [empresa_1.pk, empresa_2.pk],
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(usuario_target.empresas_permitidas.values_list('m_empresa_id', flat=True)),
            {empresa_1.pk, empresa_2.pk}
        )
        self.assertEqual(
            MinhaEmpresa.objects.get(m_usuario=usuario_target).m_empresa_id,
            empresa_1.pk
        )

    def test_editar_permissoes_salva_perfil_operacional(self):
        empresa_1 = Empresa.objects.create(nome_razao_social='Empresa Perfil', tipo_pessoa='PJ')
        usuario_target_user = User.objects.create_user(
            'usuario-perfil', 'usuario-perfil@test.com', 'testpass')
        usuario_target = Usuario.objects.get_or_create(user=usuario_target_user)[0]

        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        url = reverse('login:permissoesusuarioview', kwargs={'pk': usuario_target_user.pk})
        response = self.client.post(url, {
            'empresas': [empresa_1.pk],
            'perfil_usuario': 'gestor_filial',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            usuario_target_user.groups.filter(name='gestor_filial').exists())
        self.assertTrue(Group.objects.filter(name='gestor_matriz').exists())


class DeletarUsuarioViewTestCase(BaseTestCase):

    def test_deletar_usuario_view(self):
        new_user = User.objects.create()
        url = reverse('login:deletarusuarioview', kwargs={'pk': new_user.pk})
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(new_user in response.context['object_list'])
