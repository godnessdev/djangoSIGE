# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from djangosige.apps.cadastro.models import (
    Categoria,
    Cliente,
    Email,
    Empresa,
    Endereco,
    Fornecedor,
    Marca,
    MinhaEmpresa,
    Pessoa,
    PessoaJuridica,
    Produto,
    ProdutoEmpresa,
    Telefone,
    UF_SIGLA,
    Unidade,
    UsuarioEmpresa,
)
from djangosige.apps.compras.models import ItensCompra, PedidoCompra
from djangosige.apps.estoque.models import (
    EntradaEstoque,
    ItensMovimento,
    LocalEstoque,
    ProdutoEstocado,
    SaidaEstoque,
    TransferenciaEstoque,
)
from djangosige.apps.financeiro.models import Entrada, Lancamento, MovimentoCaixa, PlanoContasGrupo, Saida
from djangosige.apps.fiscal.models import (
    COFINS,
    ConfiguracaoNotaFiscal,
    GrupoFiscal,
    ICMSUFDest,
    ICMSSN,
    IPI,
    NaturezaOperacao,
    PIS,
)
from djangosige.apps.login.models import Usuario
from djangosige.apps.vendas.models import CondicaoPagamento, ItensVenda, PedidoVenda


class Command(BaseCommand):
    help = "Testa o fluxo base matriz/filial e popula carga massiva para uso local."

    def add_arguments(self, parser):
        parser.add_argument('--admin-user', default='admin')
        parser.add_argument('--prefix', default='LOADTEST')
        parser.add_argument('--products', type=int, default=10000)
        parser.add_argument('--clients', type=int, default=10000)
        parser.add_argument('--suppliers', type=int, default=10000)
        parser.add_argument('--payables', type=int, default=10000)
        parser.add_argument('--receivables', type=int, default=10000)
        parser.add_argument('--sales', type=int, default=200)
        parser.add_argument('--purchases', type=int, default=200)
        parser.add_argument('--transfers', type=int, default=20)
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **options):
        self.prefix = options['prefix'].strip() or 'LOADTEST'
        self.batch_size = max(100, options['batch_size'])
        self.now = timezone.now()

        admin_user = self.ensure_admin(options['admin_user'])
        self.stdout.write(self.style.NOTICE('Executando bootstrap operacional matriz/filial...'))

        with transaction.atomic():
            context = self.bootstrap_core(admin_user)

        self.stdout.write(self.style.NOTICE('Gerando carga massiva...'))
        with transaction.atomic():
            products = self.ensure_products(context, target=options['products'])
            clients = self.ensure_people_load(
                model=Cliente,
                target=options['clients'],
                label='CLIENTE',
                empresa_ids=[context['matriz'].id, context['filial'].id],
            )
            suppliers = self.ensure_people_load(
                model=Fornecedor,
                target=options['suppliers'],
                label='FORNECEDOR',
                empresa_ids=[context['matriz'].id, context['filial'].id],
            )
            self.ensure_lancamentos_load(
                model=Saida,
                target=options['payables'],
                label='A PAGAR',
                empresa_to_related_ids={
                    context['matriz'].id: suppliers[context['matriz'].id],
                    context['filial'].id: suppliers[context['filial'].id],
                },
                grupo_por_empresa={
                    context['matriz'].id: context['planos_saida'][context['matriz'].id].id,
                    context['filial'].id: context['planos_saida'][context['filial'].id].id,
                },
                related_field='fornecedor_id',
                status='1',
            )
            self.ensure_lancamentos_load(
                model=Entrada,
                target=options['receivables'],
                label='A RECEBER',
                empresa_to_related_ids={
                    context['matriz'].id: clients[context['matriz'].id],
                    context['filial'].id: clients[context['filial'].id],
                },
                grupo_por_empresa={
                    context['matriz'].id: context['planos_entrada'][context['matriz'].id].id,
                    context['filial'].id: context['planos_entrada'][context['filial'].id].id,
                },
                related_field='cliente_id',
                status='1',
            )
            self.create_smoke_flows(
                context=context,
                products=products,
                clients=clients,
                suppliers=suppliers,
                sales_target=options['sales'],
                purchases_target=options['purchases'],
                transfer_target=options['transfers'],
            )

        summary = self.collect_summary(context)
        self.validate_summary(
            summary=summary,
            expected={
                'products': options['products'],
                'clients': options['clients'],
                'suppliers': options['suppliers'],
                'payables': options['payables'],
                'receivables': options['receivables'],
                'sales': options['sales'],
                'purchases': options['purchases'],
                'transfers': options['transfers'],
            },
        )

        self.stdout.write(self.style.SUCCESS('Fluxo concluido com sucesso.'))
        for key, value in summary.items():
            self.stdout.write(f'{key}: {value}')

    def ensure_admin(self, username):
        admin = User.objects.filter(username=username).first()
        if admin is None:
            admin = User.objects.create_superuser(
                username=username,
                email=f'{username}@local.test',
                password='Admin123!@#',
            )
            self.stdout.write(self.style.WARNING(
                f'Usuario administrador criado: {username} / senha temporaria Admin123!@#'
            ))
        elif not admin.is_superuser:
            raise CommandError(f'O usuario "{username}" existe, mas nao e superuser.')
        return admin

    def bootstrap_core(self, admin_user):
        usuario = Usuario.objects.get_or_create(user=admin_user)[0]
        groups = {
            'gestor_matriz': Group.objects.get_or_create(name='gestor_matriz')[0],
            'operador_filial': Group.objects.get_or_create(name='operador_filial')[0],
        }

        gestor_user = self.ensure_operational_user(
            username=f'{self.prefix.lower()}_gestor',
            email=f'{self.prefix.lower()}_gestor@local.test',
            groups=[groups['gestor_matriz']],
        )
        filial_user = self.ensure_operational_user(
            username=f'{self.prefix.lower()}_filial',
            email=f'{self.prefix.lower()}_filial@local.test',
            groups=[groups['operador_filial']],
        )

        matriz = self.ensure_empresa(
            nome=f'{self.prefix} MATRIZ',
            nome_fantasia=f'{self.prefix} MATRIZ',
            cnpj='10000000000001',
            tipo_empresa=Empresa.TIPO_MATRIZ,
            user=admin_user,
        )
        filial = self.ensure_empresa(
            nome=f'{self.prefix} FILIAL 01',
            nome_fantasia=f'{self.prefix} FILIAL 01',
            cnpj='10000000000002',
            tipo_empresa=Empresa.TIPO_FILIAL,
            empresa_pai=matriz,
            user=admin_user,
        )

        for company in (matriz, filial):
            UsuarioEmpresa.objects.get_or_create(m_usuario=usuario, m_empresa=company)
            UsuarioEmpresa.objects.get_or_create(
                m_usuario=Usuario.objects.get_or_create(user=gestor_user)[0],
                m_empresa=company,
            )
        UsuarioEmpresa.objects.get_or_create(
            m_usuario=Usuario.objects.get_or_create(user=filial_user)[0],
            m_empresa=filial,
        )
        MinhaEmpresa.objects.update_or_create(
            m_usuario=usuario,
            defaults={'m_empresa': matriz},
        )
        MinhaEmpresa.objects.update_or_create(
            m_usuario=Usuario.objects.get_or_create(user=gestor_user)[0],
            defaults={'m_empresa': matriz},
        )
        MinhaEmpresa.objects.update_or_create(
            m_usuario=Usuario.objects.get_or_create(user=filial_user)[0],
            defaults={'m_empresa': filial},
        )

        locals_map = {
            matriz.id: self.ensure_local_estoque(matriz, f'{self.prefix} ESTOQUE MATRIZ'),
            filial.id: self.ensure_local_estoque(filial, f'{self.prefix} ESTOQUE FILIAL'),
        }
        cond_pagamento = CondicaoPagamento.objects.get_or_create(
            descricao=f'{self.prefix} A VISTA',
            defaults={
                'forma': '01',
                'n_parcelas': 1,
                'dias_recorrencia': 0,
                'parcela_inicial': 0,
            },
        )[0]

        planos_entrada = {}
        planos_saida = {}
        naturezas_saida = {}
        naturezas_entrada = {}
        grupos_fiscais = {}
        configs_nfe = {}
        for empresa in (matriz, filial):
            planos_entrada[empresa.id] = PlanoContasGrupo.objects.get_or_create(
                empresa=empresa,
                codigo='100',
                tipo_grupo='0',
                defaults={'descricao': f'{self.prefix} RECEITAS {empresa.id}'},
            )[0]
            planos_saida[empresa.id] = PlanoContasGrupo.objects.get_or_create(
                empresa=empresa,
                codigo='200',
                tipo_grupo='1',
                defaults={'descricao': f'{self.prefix} DESPESAS {empresa.id}'},
            )[0]
            naturezas_saida[empresa.id] = self.ensure_natureza_operacao(
                empresa, '5102', 'Venda de mercadoria'
            )
            naturezas_entrada[empresa.id] = self.ensure_natureza_operacao(
                empresa, '1102', 'Compra para comercializacao'
            )
            grupos_fiscais[empresa.id] = self.ensure_grupo_fiscal(empresa)
            configs_nfe[empresa.id] = ConfiguracaoNotaFiscal.objects.get_or_create(
                empresa=empresa,
                defaults={
                    'serie_atual': '101',
                    'ambiente': '2',
                    'imp_danfe': '1',
                },
            )[0]

        categories = self.ensure_reference_rows(Categoria, 'categoria_desc', 10, f'{self.prefix} CATEGORIA')
        brands = self.ensure_reference_rows(Marca, 'marca_desc', 10, f'{self.prefix} MARCA')
        units = self.ensure_unidades()

        return {
            'admin_user': admin_user,
            'usuario': usuario,
            'gestor_user': gestor_user,
            'filial_user': filial_user,
            'matriz': matriz,
            'filial': filial,
            'locals': locals_map,
            'cond_pagamento': cond_pagamento,
            'planos_entrada': planos_entrada,
            'planos_saida': planos_saida,
            'naturezas_saida': naturezas_saida,
            'naturezas_entrada': naturezas_entrada,
            'grupos_fiscais': grupos_fiscais,
            'configs_nfe': configs_nfe,
            'categories': categories,
            'brands': brands,
            'units': units,
        }

    def ensure_operational_user(self, username, email, groups):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_active': True,
            },
        )
        if created:
            user.set_password('Admin123!@#')
            user.save(update_fields=['password'])
        for group in groups:
            user.groups.add(group)
        Usuario.objects.get_or_create(user=user)
        return user

    def ensure_empresa(self, nome, nome_fantasia, cnpj, tipo_empresa, user, empresa_pai=None):
        empresa = Empresa.objects.filter(nome_razao_social=nome).first()
        if empresa is None:
            empresa = Empresa(
                nome_razao_social=nome,
                tipo_pessoa='PJ',
                tipo_empresa=tipo_empresa,
                empresa_pai=empresa_pai,
                inscricao_municipal='',
                cnae='6201500',
                iest='',
                criado_por=user,
            )
            empresa.data_criacao = self.now
            empresa.data_edicao = self.now
        else:
            empresa.tipo_empresa = tipo_empresa
            empresa.empresa_pai = empresa_pai
            empresa.criado_por = empresa.criado_por or user
            empresa.data_edicao = self.now
        empresa.full_clean()
        empresa.save()

        pessoa_jur, _ = PessoaJuridica.objects.get_or_create(
            pessoa_id=empresa,
            defaults={
                'cnpj': cnpj,
                'nome_fantasia': nome_fantasia,
                'inscricao_estadual': f'IE-{cnpj[-4:]}',
                'sit_fiscal': 'SN',
            },
        )
        changed = False
        if not pessoa_jur.cnpj:
            pessoa_jur.cnpj = cnpj
            changed = True
        if not pessoa_jur.nome_fantasia:
            pessoa_jur.nome_fantasia = nome_fantasia
            changed = True
        if not pessoa_jur.inscricao_estadual:
            pessoa_jur.inscricao_estadual = f'IE-{cnpj[-4:]}'
            changed = True
        if not pessoa_jur.sit_fiscal:
            pessoa_jur.sit_fiscal = 'SN'
            changed = True
        if changed:
            pessoa_jur.save()

        if empresa.endereco_padrao_id is None:
            endereco = Endereco.objects.create(
                pessoa_end=empresa,
                tipo_endereco='UNI',
                logradouro='Rua de Teste',
                numero=str(empresa.id or 1),
                bairro='Centro',
                municipio='Sao Paulo',
                cmun='3550308',
                cep='01000000',
                uf='SP',
            )
            empresa.endereco_padrao = endereco
        if empresa.telefone_padrao_id is None:
            telefone = Telefone.objects.create(
                pessoa_tel=empresa,
                tipo_telefone='FIX',
                telefone='1130000000',
            )
            empresa.telefone_padrao = telefone
        if empresa.email_padrao_id is None:
            email = Email.objects.create(
                pessoa_email=empresa,
                email=f'{self.prefix.lower()}.{empresa.id or "empresa"}@local.test',
            )
            empresa.email_padrao = email
        empresa.save()
        return empresa

    def ensure_local_estoque(self, empresa, descricao):
        return LocalEstoque.objects.get_or_create(
            empresa=empresa,
            descricao=descricao,
        )[0]

    def ensure_natureza_operacao(self, empresa, cfop, descricao):
        natureza, created = NaturezaOperacao.objects.get_or_create(
            empresa=empresa,
            cfop=cfop,
            defaults={'descricao': descricao},
        )
        if created or not natureza.tp_operacao or not natureza.id_dest:
            natureza.descricao = natureza.descricao or descricao
            natureza.set_values_by_cfop()
            natureza.save()
        return natureza

    def ensure_grupo_fiscal(self, empresa):
        grupo, _ = GrupoFiscal.objects.get_or_create(
            empresa=empresa,
            descricao=f'{self.prefix} GRUPO FISCAL {empresa.id}',
            defaults={'regime_trib': '1'},
        )
        ICMSSN.objects.get_or_create(
            grupo_fiscal=grupo,
            defaults={
                'csosn': '102',
                'mod_bc': '3',
                'mod_bcst': '4',
            },
        )
        ICMSUFDest.objects.get_or_create(
            grupo_fiscal=grupo,
            defaults={
                'p_fcp_dest': Decimal('2.00'),
                'p_icms_dest': Decimal('18.00'),
                'p_icms_inter': Decimal('12.00'),
                'p_icms_inter_part': Decimal('100.00'),
            },
        )
        IPI.objects.get_or_create(
            grupo_fiscal=grupo,
            defaults={'cst': '99', 'tipo_ipi': '0'},
        )
        PIS.objects.get_or_create(
            grupo_fiscal=grupo,
            defaults={'cst': '07'},
        )
        COFINS.objects.get_or_create(
            grupo_fiscal=grupo,
            defaults={'cst': '07'},
        )
        return grupo

    def ensure_reference_rows(self, model, field_name, total, prefix):
        values = []
        existing = list(
            model.objects.filter(**{f'{field_name}__startswith': prefix}).order_by('id')
        )
        if len(existing) >= total:
            return existing[:total]

        for index in range(len(existing) + 1, total + 1):
            values.append(model(**{field_name: f'{prefix} {index:02d}'}))
        model.objects.bulk_create(values, batch_size=self.batch_size)
        return list(model.objects.filter(**{f'{field_name}__startswith': prefix}).order_by('id')[:total])

    def ensure_unidades(self):
        units = []
        for sigla, descricao in (('UN', 'Unidade'), ('CX', 'Caixa'), ('KG', 'Quilo')):
            unidade, _ = Unidade.objects.get_or_create(
                sigla_unidade=sigla,
                defaults={'unidade_desc': descricao},
            )
            units.append(unidade)
        return units

    def ensure_products(self, context, target):
        existing_qs = Produto.objects.filter(descricao__startswith=f'{self.prefix} PRODUTO ').order_by('id')
        existing = list(existing_qs[:target])
        if len(existing) < target:
            to_create = []
            categories = context['categories']
            brands = context['brands']
            units = context['units']
            start = len(existing) + 1
            for index in range(start, target + 1):
                to_create.append(
                    Produto(
                        codigo=f'LT{index:013d}',
                        codigo_barras=f'{7890000000000 + index}',
                        descricao=f'{self.prefix} PRODUTO {index:05d}',
                        categoria=categories[(index - 1) % len(categories)],
                        marca=brands[(index - 1) % len(brands)],
                        unidade=units[(index - 1) % len(units)],
                        custo=Decimal('10.00') + Decimal(index % 50),
                        venda=Decimal('20.00') + Decimal(index % 80),
                        ncm='22030000',
                        origem='0',
                        cest='1234567',
                        estoque_minimo=Decimal('5.00'),
                        estoque_atual=Decimal('150.00'),
                        controlar_estoque=True,
                    )
                )
            Produto.objects.bulk_create(to_create, batch_size=self.batch_size)
            existing = list(Produto.objects.filter(
                descricao__startswith=f'{self.prefix} PRODUTO '
            ).order_by('id')[:target])

        self.ensure_product_configs_and_stock(context, existing)
        return existing

    def ensure_product_configs_and_stock(self, context, products):
        company_ids = [context['matriz'].id, context['filial'].id]
        naturezas_saida = context['naturezas_saida']
        grupos_fiscais = context['grupos_fiscais']
        locals_map = context['locals']

        product_ids = [product.id for product in products]
        existing_config_keys = set(
            ProdutoEmpresa.objects.filter(
                produto_id__in=product_ids,
                empresa_id__in=company_ids,
            ).values_list('produto_id', 'empresa_id')
        )
        config_to_create = []
        stock_keys = set(
            ProdutoEstocado.objects.filter(
                produto_id__in=product_ids,
                local_id__in=[locals_map[company_id].id for company_id in company_ids],
            ).values_list('produto_id', 'local_id')
        )
        stock_to_create = []

        for product in products:
            for company_id in company_ids:
                if (product.id, company_id) not in existing_config_keys:
                    multiplier = Decimal('1.00') if company_id == context['matriz'].id else Decimal('1.15')
                    config_to_create.append(
                        ProdutoEmpresa(
                            produto_id=product.id,
                            empresa_id=company_id,
                            custo=(product.custo * multiplier).quantize(Decimal('0.01')),
                            venda=(product.venda * multiplier).quantize(Decimal('0.01')),
                            cfop_padrao=naturezas_saida[company_id],
                            grupo_fiscal=grupos_fiscais[company_id],
                        )
                    )
                local_id = locals_map[company_id].id
                if (product.id, local_id) not in stock_keys:
                    quantity = Decimal('100.00') if company_id == context['matriz'].id else Decimal('50.00')
                    stock_to_create.append(
                        ProdutoEstocado(
                            produto_id=product.id,
                            local_id=local_id,
                            quantidade=quantity,
                        )
                    )

        if config_to_create:
            ProdutoEmpresa.objects.bulk_create(config_to_create, batch_size=self.batch_size, ignore_conflicts=True)
        if stock_to_create:
            ProdutoEstocado.objects.bulk_create(stock_to_create, batch_size=self.batch_size, ignore_conflicts=True)

    def ensure_people_load(self, model, target, label, empresa_ids):
        existing = model.objects.filter(
            nome_razao_social__startswith=f'{self.prefix} {label} '
        ).count()
        if existing < target:
            remaining = target - existing
            self.bulk_create_people(
                model=model,
                label=label,
                start_index=existing + 1,
                total=remaining,
                empresa_ids=empresa_ids,
            )

        queryset = model.objects.filter(
            nome_razao_social__startswith=f'{self.prefix} {label} '
        ).order_by('id')

        per_company = defaultdict(list)
        for row in queryset.values('id', 'empresa_relacionada_id'):
            per_company[row['empresa_relacionada_id']].append(row['id'])
        return per_company

    def bulk_create_people(self, model, label, start_index, total, empresa_ids):
        now = timezone.now()
        parent_objects = []
        for offset in range(total):
            index = start_index + offset
            parent_objects.append(
                Pessoa(
                    nome_razao_social=f'{self.prefix} {label} {index:05d}',
                    tipo_pessoa='PJ',
                    inscricao_municipal='',
                    informacoes_adicionais='Carga automatica',
                    criado_por=None,
                    data_criacao=now,
                    data_edicao=now,
                )
            )

        Pessoa.objects.bulk_create(parent_objects, batch_size=self.batch_size)

        juridicas = []
        cliente_rows = []
        fornecedor_rows = []
        for offset, parent in enumerate(parent_objects):
            index = start_index + offset
            empresa_id = empresa_ids[(index - 1) % len(empresa_ids)]
            juridicas.append(
                PessoaJuridica(
                    pessoa_id_id=parent.id,
                    cnpj=f'{30 + (index % 60):02d}{index:012d}'[:14],
                    nome_fantasia=f'{label} {index:05d}',
                    inscricao_estadual=f'IE{index:010d}'[:32],
                    sit_fiscal='SN',
                )
            )
            if model is Cliente:
                cliente_rows.append((
                    parent.id,
                    empresa_id,
                    Decimal('10000.00'),
                    '9',
                    None,
                ))
            else:
                fornecedor_rows.append((
                    parent.id,
                    empresa_id,
                    '',
                ))
        PessoaJuridica.objects.bulk_create(juridicas, batch_size=self.batch_size)

        if model is Cliente:
            self.bulk_insert_child_rows(
                model=Cliente,
                field_names=['pessoa_ptr_id', 'empresa_relacionada_id', 'limite_de_credito', 'indicador_ie', 'id_estrangeiro'],
                rows=cliente_rows,
            )
        else:
            self.bulk_insert_child_rows(
                model=Fornecedor,
                field_names=['pessoa_ptr_id', 'empresa_relacionada_id', 'ramo'],
                rows=fornecedor_rows,
            )

    def ensure_lancamentos_load(
        self,
        model,
        target,
        label,
        empresa_to_related_ids,
        grupo_por_empresa,
        related_field,
        status,
    ):
        existing = model.objects.filter(
            descricao__startswith=f'{self.prefix} {label} '
        ).count()
        if existing < target:
            remaining = target - existing
            self.bulk_create_lancamentos(
                model=model,
                label=label,
                start_index=existing + 1,
                total=remaining,
                empresa_to_related_ids=empresa_to_related_ids,
                grupo_por_empresa=grupo_por_empresa,
                related_field=related_field,
                status=status,
            )

    def bulk_create_lancamentos(
        self,
        model,
        label,
        start_index,
        total,
        empresa_to_related_ids,
        grupo_por_empresa,
        related_field,
        status,
    ):
        parent_objects = []
        company_ids = list(empresa_to_related_ids.keys())
        for offset in range(total):
            index = start_index + offset
            company_id = company_ids[(index - 1) % len(company_ids)]
            due_date = (self.now.date() + timedelta(days=(index % 60) + 1))
            amount = Decimal('100.00') + Decimal(index % 500)
            parent_objects.append(
                Lancamento(
                    empresa_id=company_id,
                    data_vencimento=due_date,
                    data_pagamento=None,
                    descricao=f'{self.prefix} {label} {index:05d}',
                    conta_corrente=None,
                    valor_total=amount,
                    abatimento=Decimal('0.00'),
                    juros=Decimal('0.00'),
                    valor_liquido=amount,
                    movimentar_caixa=False,
                    movimento_caixa=None,
                )
            )

        Lancamento.objects.bulk_create(parent_objects, batch_size=self.batch_size)
        rows = []
        for offset, parent in enumerate(parent_objects):
            index = start_index + offset
            company_id = parent.empresa_id
            related_ids = empresa_to_related_ids[company_id]
            related_id = related_ids[(index - 1) % len(related_ids)]
            rows.append(
                (
                    parent.id,
                    related_id,
                    status,
                    grupo_por_empresa[company_id],
                )
            )

        field_names = ['lancamento_ptr_id', related_field, 'status', 'grupo_plano_id']
        self.bulk_insert_child_rows(model=model, field_names=field_names, rows=rows)

    def bulk_insert_child_rows(self, model, field_names, rows):
        if not rows:
            return
        table = connection.ops.quote_name(model._meta.db_table)
        columns = ', '.join(connection.ops.quote_name(field_name) for field_name in field_names)
        placeholders = ', '.join(['%s'] * len(field_names))
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        with connection.cursor() as cursor:
            cursor.executemany(query, rows)

    def create_smoke_flows(self, context, products, clients, suppliers, sales_target, purchases_target, transfer_target):
        venda_count = PedidoVenda.objects.filter(observacoes=f'{self.prefix} SMOKE').count()
        compra_count = PedidoCompra.objects.filter(observacoes=f'{self.prefix} SMOKE').count()
        transfer_count = TransferenciaEstoque.objects.filter(observacoes=f'{self.prefix} SMOKE').count()

        selected_products = products[:max(sales_target, purchases_target, transfer_target, 1)]
        matriz_id = context['matriz'].id
        filial_id = context['filial'].id
        matriz_local = context['locals'][matriz_id]
        filial_local = context['locals'][filial_id]

        if compra_count < purchases_target:
            for index in range(compra_count, purchases_target):
                empresa_id = matriz_id if index % 2 == 0 else filial_id
                empresa = context['matriz'] if empresa_id == matriz_id else context['filial']
                local = matriz_local if empresa_id == matriz_id else filial_local
                fornecedor_id = suppliers[empresa_id][index % len(suppliers[empresa_id])]
                product = selected_products[index % len(selected_products)]
                unit_cost = product.get_custo_empresa(empresa) or product.custo
                quantidade = Decimal('5.00')
                subtotal = (unit_cost * quantidade).quantize(Decimal('0.01'))
                pedido = PedidoCompra.objects.create(
                    empresa=empresa,
                    empresa_destino=empresa,
                    fornecedor_id=fornecedor_id,
                    local_dest=local,
                    movimentar_estoque=True,
                    data_emissao=self.now.date(),
                    data_entrega=self.now.date() + timedelta(days=7),
                    valor_total=subtotal,
                    tipo_desconto='0',
                    desconto=Decimal('0.00'),
                    despesas=Decimal('0.00'),
                    frete=Decimal('0.00'),
                    seguro=Decimal('0.00'),
                    total_icms=Decimal('0.00'),
                    total_ipi=Decimal('0.00'),
                    cond_pagamento=context['cond_pagamento'],
                    observacoes=f'{self.prefix} SMOKE',
                    status='0',
                )
                ItensCompra.objects.create(
                    compra_id=pedido,
                    produto=product,
                    quantidade=quantidade,
                    valor_unit=unit_cost,
                    tipo_desconto='0',
                    desconto=Decimal('0.00'),
                    subtotal=subtotal,
                )
                movimento = EntradaEstoque.objects.create(
                    empresa=empresa,
                    data_movimento=self.now.date(),
                    quantidade_itens=1,
                    valor_total=subtotal,
                    observacoes=f'{self.prefix} SMOKE',
                    tipo_movimento='1',
                    pedido_compra=pedido,
                    fornecedor_id=fornecedor_id,
                    local_dest=local,
                )
                ItensMovimento.objects.create(
                    movimento_id=movimento,
                    produto=product,
                    quantidade=quantidade,
                    valor_unit=unit_cost,
                    subtotal=subtotal,
                )
                self.adjust_stock(local, product, quantidade)
                Saida.objects.create(
                    empresa=empresa,
                    data_vencimento=self.now.date() + timedelta(days=30),
                    descricao=f'{self.prefix} PAGAMENTO COMPRA {pedido.id}',
                    fornecedor_id=fornecedor_id,
                    status='1',
                    grupo_plano=context['planos_saida'][empresa_id],
                    valor_total=subtotal,
                    valor_liquido=subtotal,
                    movimentar_caixa=False,
                    abatimento=Decimal('0.00'),
                    juros=Decimal('0.00'),
                )

        if venda_count < sales_target:
            for index in range(venda_count, sales_target):
                empresa_id = matriz_id if index % 2 == 0 else filial_id
                empresa = context['matriz'] if empresa_id == matriz_id else context['filial']
                local = matriz_local if empresa_id == matriz_id else filial_local
                cliente_id = clients[empresa_id][index % len(clients[empresa_id])]
                product = selected_products[index % len(selected_products)]
                unit_price = product.get_venda_empresa(empresa) or product.venda
                quantidade = Decimal('2.00')
                subtotal = (unit_price * quantidade).quantize(Decimal('0.01'))
                pedido = PedidoVenda.objects.create(
                    empresa=empresa,
                    cliente_id=cliente_id,
                    local_orig=local,
                    movimentar_estoque=True,
                    ind_final=False,
                    mod_frete='9',
                    data_emissao=self.now.date(),
                    valor_total=subtotal,
                    tipo_desconto='0',
                    desconto=Decimal('0.00'),
                    despesas=Decimal('0.00'),
                    frete=Decimal('0.00'),
                    seguro=Decimal('0.00'),
                    impostos=Decimal('0.00'),
                    cond_pagamento=context['cond_pagamento'],
                    observacoes=f'{self.prefix} SMOKE',
                    status='0',
                )
                ItensVenda.objects.create(
                    venda_id=pedido,
                    produto=product,
                    quantidade=quantidade,
                    valor_unit=unit_price,
                    tipo_desconto='0',
                    desconto=Decimal('0.00'),
                    subtotal=subtotal,
                )
                movimento = SaidaEstoque.objects.create(
                    empresa=empresa,
                    data_movimento=self.now.date(),
                    quantidade_itens=1,
                    valor_total=subtotal,
                    observacoes=f'{self.prefix} SMOKE',
                    tipo_movimento='1',
                    pedido_venda=pedido,
                    local_orig=local,
                )
                ItensMovimento.objects.create(
                    movimento_id=movimento,
                    produto=product,
                    quantidade=quantidade,
                    valor_unit=unit_price,
                    subtotal=subtotal,
                )
                self.adjust_stock(local, product, -quantidade)
                Entrada.objects.create(
                    empresa=empresa,
                    data_vencimento=self.now.date() + timedelta(days=30),
                    descricao=f'{self.prefix} RECEBIMENTO VENDA {pedido.id}',
                    cliente_id=cliente_id,
                    status='1',
                    grupo_plano=context['planos_entrada'][empresa_id],
                    valor_total=subtotal,
                    valor_liquido=subtotal,
                    movimentar_caixa=False,
                    abatimento=Decimal('0.00'),
                    juros=Decimal('0.00'),
                )

        if transfer_count < transfer_target:
            for index in range(transfer_count, transfer_target):
                product = selected_products[index % len(selected_products)]
                quantidade = Decimal('1.00')
                movimento = TransferenciaEstoque.objects.create(
                    empresa=context['matriz'],
                    empresa_destino=context['filial'],
                    data_movimento=self.now.date(),
                    quantidade_itens=1,
                    valor_total=Decimal('0.00'),
                    observacoes=f'{self.prefix} SMOKE',
                    local_estoque_orig=matriz_local,
                    local_estoque_dest=filial_local,
                    impacto_custo='MAN',
                )
                ItensMovimento.objects.create(
                    movimento_id=movimento,
                    produto=product,
                    quantidade=quantidade,
                    valor_unit=product.get_custo_empresa(context['matriz']) or product.custo,
                    subtotal=Decimal('0.00'),
                )
                self.adjust_stock(matriz_local, product, -quantidade)
                self.adjust_stock(filial_local, product, quantidade)

        self.ensure_caixa_smoke(context)

    def ensure_caixa_smoke(self, context):
        for empresa in (context['matriz'], context['filial']):
            MovimentoCaixa.objects.get_or_create(
                empresa=empresa,
                data_movimento=self.now.date(),
                defaults={
                    'saldo_inicial': Decimal('1000.00'),
                    'saldo_final': Decimal('1000.00'),
                    'entradas': Decimal('0.00'),
                    'saidas': Decimal('0.00'),
                },
            )

    def adjust_stock(self, local, product, quantity_delta):
        produto_estocado, _ = ProdutoEstocado.objects.get_or_create(
            local=local,
            produto=product,
            defaults={'quantidade': Decimal('0.00')},
        )
        produto_estocado.quantidade = (produto_estocado.quantidade + quantity_delta).quantize(Decimal('0.01'))
        if produto_estocado.quantidade < 0:
            raise CommandError(
                f'Estoque negativo detectado para o produto {product.id} no local {local.id}.'
            )
        produto_estocado.save(update_fields=['quantidade'])
        total_stock = Decimal('0.00')
        for row in product.produto_estocado.all().values_list('quantidade', flat=True):
            total_stock += row
        product.estoque_atual = total_stock
        product.save(update_fields=['estoque_atual'])

    def collect_summary(self, context):
        return {
            'companies': Empresa.objects.filter(
                nome_razao_social__startswith=self.prefix
            ).count(),
            'products': Produto.objects.filter(
                descricao__startswith=f'{self.prefix} PRODUTO '
            ).count(),
            'clients': Cliente.objects.filter(
                nome_razao_social__startswith=f'{self.prefix} CLIENTE '
            ).count(),
            'suppliers': Fornecedor.objects.filter(
                nome_razao_social__startswith=f'{self.prefix} FORNECEDOR '
            ).count(),
            'payables': Saida.objects.filter(
                descricao__startswith=f'{self.prefix} A PAGAR '
            ).count(),
            'receivables': Entrada.objects.filter(
                descricao__startswith=f'{self.prefix} A RECEBER '
            ).count(),
            'sales': PedidoVenda.objects.filter(
                observacoes=f'{self.prefix} SMOKE'
            ).count(),
            'purchases': PedidoCompra.objects.filter(
                observacoes=f'{self.prefix} SMOKE'
            ).count(),
            'transfers': TransferenciaEstoque.objects.filter(
                observacoes=f'{self.prefix} SMOKE'
            ).count(),
            'matriz_active': MinhaEmpresa.objects.filter(
                m_usuario=context['usuario'], m_empresa=context['matriz']
            ).exists(),
        }

    def validate_summary(self, summary, expected):
        for key in ('products', 'clients', 'suppliers', 'payables', 'receivables'):
            if summary[key] < expected[key]:
                raise CommandError(
                    f'Quantidade insuficiente para {key}: {summary[key]} < {expected[key]}'
                )
        for key in ('sales', 'purchases', 'transfers'):
            if summary[key] < expected[key]:
                raise CommandError(
                    f'Fluxo insuficiente para {key}: {summary[key]} < {expected[key]}'
                )
        if not summary['matriz_active']:
            raise CommandError('A empresa ativa do usuario admin nao foi configurada para a matriz.')
