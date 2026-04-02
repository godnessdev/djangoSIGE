# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from decimal import Decimal

from djangosige.apps.cadastro.models import Empresa, Produto, ProdutoEmpresa
from djangosige.apps.estoque.models import LocalEstoque, ProdutoEstocado
from djangosige.apps.fiscal.models import NaturezaOperacao, GrupoFiscal
from djangosige.tests.test_case import BaseTestCase


class EmpresaHierarquiaModelTestCase(BaseTestCase):

    def create_empresa(self, nome, tipo_empresa=Empresa.TIPO_INDEPENDENTE, empresa_pai=None):
        return Empresa.objects.create(
            nome_razao_social=nome,
            tipo_pessoa='PJ',
            tipo_empresa=tipo_empresa,
            empresa_pai=empresa_pai,
        )

    def test_filial_requires_matriz(self):
        empresa = Empresa(
            nome_razao_social='Filial Sem Matriz',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
        )

        with self.assertRaises(ValidationError) as exc:
            empresa.full_clean()

        self.assertIn('empresa_pai', exc.exception.message_dict)

    def test_filial_parent_must_be_matriz(self):
        empresa_independente = self.create_empresa('Empresa Independente')
        empresa = Empresa(
            nome_razao_social='Filial Invalida',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=empresa_independente,
        )

        with self.assertRaises(ValidationError) as exc:
            empresa.full_clean()

        self.assertIn('empresa_pai', exc.exception.message_dict)

    def test_matriz_cannot_have_parent(self):
        matriz = self.create_empresa('Matriz Principal', tipo_empresa=Empresa.TIPO_MATRIZ)
        empresa = Empresa(
            nome_razao_social='Matriz Secundaria',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_MATRIZ,
            empresa_pai=matriz,
        )

        with self.assertRaises(ValidationError) as exc:
            empresa.full_clean()

        self.assertIn('empresa_pai', exc.exception.message_dict)

    def test_empresa_cannot_point_to_itself(self):
        empresa = Empresa(
            nome_razao_social='Empresa Circular',
            tipo_pessoa='PJ',
            tipo_empresa=Empresa.TIPO_FILIAL,
        )
        empresa.empresa_pai = empresa

        with self.assertRaises(ValidationError) as exc:
            empresa.full_clean()

        self.assertIn('empresa_pai', exc.exception.message_dict)

    def test_delete_matriz_with_filiais_is_blocked(self):
        matriz = self.create_empresa('Matriz Bloqueada', tipo_empresa=Empresa.TIPO_MATRIZ)
        self.create_empresa('Filial 1', tipo_empresa=Empresa.TIPO_FILIAL, empresa_pai=matriz)

        with self.assertRaises(ProtectedError):
            matriz.delete()


class ProdutoEmpresaModelTestCase(BaseTestCase):

    def test_produto_empresa_sobrescreve_preco_e_fiscal_da_empresa_ativa(self):
        cfop_global = NaturezaOperacao.objects.create(
            empresa=self.empresa_ativa, cfop='5102')
        cfop_empresa = NaturezaOperacao.objects.create(
            empresa=self.empresa_ativa, cfop='6102')
        grupo_global = GrupoFiscal.objects.create(
            empresa=self.empresa_ativa, descricao='Grupo Global Produto', regime_trib='0')
        grupo_empresa = GrupoFiscal.objects.create(
            empresa=self.empresa_ativa, descricao='Grupo Empresa Produto', regime_trib='1')
        produto = Produto.objects.create(
            codigo='PROD-GLOBAL-1',
            descricao='Produto Global',
            venda=Decimal('100.00'),
            custo=Decimal('70.00'),
            cfop_padrao=cfop_global,
            grupo_fiscal=grupo_global,
            estoque_atual=Decimal('9.00'),
        )
        ProdutoEmpresa.objects.create(
            produto=produto,
            empresa=self.empresa_ativa,
            venda=Decimal('135.50'),
            custo=Decimal('82.40'),
            cfop_padrao=cfop_empresa,
            grupo_fiscal=grupo_empresa,
        )
        local = LocalEstoque.objects.create(
            descricao='Local Produto Empresa', empresa=self.empresa_ativa)
        ProdutoEstocado.objects.create(
            produto=produto, local=local, quantidade=Decimal('4.00'))

        self.assertEqual(produto.get_venda_empresa(self.empresa_ativa), Decimal('135.50'))
        self.assertEqual(produto.get_custo_empresa(self.empresa_ativa), Decimal('82.40'))
        self.assertEqual(produto.get_cfop_padrao(self.empresa_ativa), '6102')
        self.assertEqual(produto.get_grupo_fiscal_empresa(self.empresa_ativa), grupo_empresa)
        self.assertEqual(produto.get_estoque_atual_empresa(self.empresa_ativa), Decimal('4.00'))

    def test_produto_empresa_nao_reaproveita_fiscal_de_outra_empresa(self):
        cfop_global = NaturezaOperacao.objects.create(
            empresa=self.empresa_ativa, cfop='5101')
        grupo_global = GrupoFiscal.objects.create(
            empresa=self.empresa_ativa, descricao='Grupo Fallback Produto', regime_trib='0')
        produto = Produto.objects.create(
            codigo='PROD-FALLBACK-1',
            descricao='Produto Fallback',
            venda=Decimal('55.00'),
            custo=Decimal('30.00'),
            cfop_padrao=cfop_global,
            grupo_fiscal=grupo_global,
            estoque_atual=Decimal('8.00'),
        )
        outra_empresa = Empresa.objects.create(
            nome_razao_social='Empresa Fallback Produto',
            tipo_pessoa='PJ')

        self.assertEqual(produto.get_venda_empresa(outra_empresa), Decimal('55.00'))
        self.assertEqual(produto.get_custo_empresa(outra_empresa), Decimal('30.00'))
        self.assertEqual(produto.get_cfop_padrao(outra_empresa), '')
        self.assertIsNone(produto.get_grupo_fiscal_empresa(outra_empresa))
        self.assertEqual(produto.get_estoque_atual_empresa(outra_empresa), Decimal('8.00'))
