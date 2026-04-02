# -*- coding: utf-8 -*-

from django.views.generic import View
from django.http import HttpResponse
from django.core import serializers
from django.shortcuts import render

from djangosige.apps.cadastro.models import Pessoa, Cliente, Fornecedor, Transportadora, Produto
from djangosige.apps.fiscal.models import ICMS, ICMSSN, IPI, ICMSUFDest


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def _empty_json_response():
    return HttpResponse('[]', content_type='application/json')


def _format_decimal(value):
    if value in (None, ''):
        return ''
    return str(value).replace('.', ',')


def _format_ie_indicator(value):
    if value == '1':
        return 'Contribuinte ICMS'
    if value == '2':
        return 'Contribuinte isento de Inscrição'
    if value == '9':
        return 'Não Contribuinte'
    return ''


def _build_pessoa_summary(pessoa, actor=None):
    summary = {
        'bairro': '',
        'cep': '',
        'cmun': '',
        'complemento': '',
        'documento': '',
        'email': '',
        'endereco': '',
        'indicador_ie': '',
        'inscricao': '',
        'limite_credito': '',
        'logradouro': '',
        'municipio': '',
        'numero': '',
        'pais': '',
        'representante': '',
        'telefone': '',
        'uf': '',
    }

    if pessoa.tipo_pessoa == 'PJ':
        jur = pessoa.pessoa_jur_info
        summary['documento'] = jur.cnpj or ''
        summary['inscricao'] = jur.inscricao_estadual or ''
        summary['representante'] = jur.responsavel or ''
    elif pessoa.tipo_pessoa == 'PF':
        fis = pessoa.pessoa_fis_info
        summary['documento'] = fis.cpf or ''
        summary['inscricao'] = fis.rg or ''

    if pessoa.endereco_padrao:
        endereco = pessoa.endereco_padrao
        summary['logradouro'] = endereco.logradouro or ''
        summary['numero'] = endereco.numero or ''
        summary['bairro'] = endereco.bairro or ''
        summary['municipio'] = endereco.municipio or ''
        summary['cmun'] = endereco.cmun or ''
        summary['uf'] = endereco.uf or ''
        summary['pais'] = endereco.pais or ''
        summary['complemento'] = endereco.complemento or ''
        summary['cep'] = endereco.cep or ''
        endereco_composto = ' '.join(part for part in [endereco.logradouro, endereco.numero] if part)
        summary['endereco'] = endereco_composto.strip()

    if pessoa.email_padrao:
        summary['email'] = pessoa.email_padrao.email or ''

    if pessoa.telefone_padrao:
        summary['telefone'] = pessoa.telefone_padrao.telefone or ''

    if actor and isinstance(actor, Cliente):
        summary['limite_credito'] = _format_decimal(actor.limite_de_credito)
        summary['indicador_ie'] = _format_ie_indicator(actor.indicador_ie)
        if actor.id_estrangeiro:
            summary['documento'] = actor.id_estrangeiro
    elif actor and hasattr(actor, 'indicador_ie'):
        summary['indicador_ie'] = _format_ie_indicator(actor.indicador_ie)

    return summary


class InfoCliente(View):

    def post(self, request, *args, **kwargs):
        pessoa_id = (request.POST.get('pessoaId') or '').strip()
        panel = request.POST.get('panel') or 'cliente'
        if not pessoa_id:
            if _is_htmx(request):
                return render(request, 'progressive/fiscal_dest_info.html' if panel == 'dest' else 'progressive/venda_cliente_info.html')
            return _empty_json_response()

        obj_list = []
        pessoa = Pessoa.objects.get(pk=pessoa_id)
        cliente = Cliente.objects.get(pk=pessoa_id)
        obj_list.append(cliente)

        if pessoa.endereco_padrao:
            obj_list.append(pessoa.endereco_padrao)
        if pessoa.email_padrao:
            obj_list.append(pessoa.email_padrao)
        if pessoa.telefone_padrao:
            obj_list.append(pessoa.telefone_padrao)

        if pessoa.tipo_pessoa == 'PJ':
            obj_list.append(pessoa.pessoa_jur_info)
        elif pessoa.tipo_pessoa == 'PF':
            obj_list.append(pessoa.pessoa_fis_info)

        data = serializers.serialize('json', obj_list, fields=('indicador_ie', 'limite_de_credito', 'cnpj', 'inscricao_estadual', 'responsavel', 'cpf', 'rg', 'id_estrangeiro', 'logradouro', 'numero', 'bairro',
                                                               'municipio', 'cmun', 'uf', 'pais', 'complemento', 'cep', 'email', 'telefone',))

        if _is_htmx(request):
            template_name = 'progressive/fiscal_dest_info.html' if panel == 'dest' else 'progressive/venda_cliente_info.html'
            return render(request, template_name, {'summary': _build_pessoa_summary(pessoa, cliente)})

        return HttpResponse(data, content_type='application/json')


class InfoFornecedor(View):

    def post(self, request, *args, **kwargs):
        pessoa_id = (request.POST.get('pessoaId') or '').strip()
        panel = request.POST.get('panel') or 'fornecedor'
        if not pessoa_id:
            if _is_htmx(request):
                return render(request, 'progressive/fiscal_emit_info.html' if panel == 'emit' else 'progressive/compra_fornecedor_info.html')
            return _empty_json_response()

        obj_list = []
        pessoa = Pessoa.objects.get(pk=pessoa_id)
        fornecedor = Fornecedor.objects.get(pk=pessoa_id)
        obj_list.append(fornecedor)

        if pessoa.endereco_padrao:
            obj_list.append(pessoa.endereco_padrao)
        if pessoa.email_padrao:
            obj_list.append(pessoa.email_padrao)
        if pessoa.telefone_padrao:
            obj_list.append(pessoa.telefone_padrao)

        if pessoa.tipo_pessoa == 'PJ':
            obj_list.append(pessoa.pessoa_jur_info)
        elif pessoa.tipo_pessoa == 'PF':
            obj_list.append(pessoa.pessoa_fis_info)

        data = serializers.serialize('json', obj_list, fields=('indicador_ie', 'limite_de_credito', 'cnpj', 'inscricao_estadual', 'responsavel', 'cpf', 'rg', 'id_estrangeiro', 'logradouro', 'numero', 'bairro',
                                                               'municipio', 'cmun', 'uf', 'pais', 'complemento', 'cep', 'email', 'telefone',))

        if _is_htmx(request):
            template_name = 'progressive/fiscal_emit_info.html' if panel == 'emit' else 'progressive/compra_fornecedor_info.html'
            return render(request, template_name, {'summary': _build_pessoa_summary(pessoa, fornecedor)})

        return HttpResponse(data, content_type='application/json')


class InfoEmpresa(View):

    def post(self, request, *args, **kwargs):
        pessoa_id = (request.POST.get('pessoaId') or '').strip()
        panel = request.POST.get('panel') or 'emit'
        if not pessoa_id:
            if _is_htmx(request):
                return render(request, 'progressive/fiscal_dest_info.html' if panel == 'dest' else 'progressive/fiscal_emit_info.html')
            return _empty_json_response()

        pessoa = Pessoa.objects.get(pk=pessoa_id)
        obj_list = []
        obj_list.append(pessoa.pessoa_jur_info)

        if pessoa.endereco_padrao:
            obj_list.append(pessoa.endereco_padrao)

        data = serializers.serialize('json', obj_list, fields=('cnpj', 'inscricao_estadual', 'logradouro', 'numero', 'bairro',
                                                               'municipio', 'cmun', 'uf', 'pais', 'complemento', 'cep',))

        if _is_htmx(request):
            template_name = 'progressive/fiscal_dest_info.html' if panel == 'dest' else 'progressive/fiscal_emit_info.html'
            return render(request, template_name, {'summary': _build_pessoa_summary(pessoa)})

        return HttpResponse(data, content_type='application/json')


class InfoTransportadora(View):

    def post(self, request, *args, **kwargs):
        transportadora_id = (request.POST.get('transportadoraId') or '').strip()
        veiculo_id = request.POST.get('veiculoId')
        veiculos = []
        if transportadora_id:
            veiculos = Transportadora.objects.get(
                pk=transportadora_id).veiculo.all()
        data = serializers.serialize(
            'json', veiculos, fields=('id', 'descricao',))

        if _is_htmx(request):
            return render(
                request,
                'progressive/venda_veiculo_wrapper.html',
                {'vehicles': veiculos, 'selected_id': veiculo_id}
            )

        return HttpResponse(data, content_type='application/json')


class InfoProduto(View):

    def post(self, request, *args, **kwargs):
        produto_id = (request.POST.get('produtoId') or '').strip()
        if not produto_id:
            return _empty_json_response()

        obj_list = []
        pro = Produto.objects.get(pk=produto_id)
        obj_list.append(pro)

        if pro.grupo_fiscal:
            if pro.grupo_fiscal.regime_trib == '0':
                icms, created = ICMS.objects.get_or_create(
                    grupo_fiscal=pro.grupo_fiscal)
            else:
                icms, created = ICMSSN.objects.get_or_create(
                    grupo_fiscal=pro.grupo_fiscal)

            ipi, created = IPI.objects.get_or_create(
                grupo_fiscal=pro.grupo_fiscal)
            icms_dest, created = ICMSUFDest.objects.get_or_create(
                grupo_fiscal=pro.grupo_fiscal)
            obj_list.append(icms)
            obj_list.append(ipi)
            obj_list.append(icms_dest)

        data = serializers.serialize('json', obj_list, fields=('venda', 'controlar_estoque', 'estoque_atual',
                                                               'tipo_ipi', 'p_ipi', 'valor_fixo', 'p_icms', 'p_red_bc', 'p_icmsst', 'p_red_bcst', 'p_mvast',
                                                               'p_fcp_dest', 'p_icms_dest', 'p_icms_inter', 'p_icms_inter_part',
                                                               'ipi_incluido_preco', 'incluir_bc_icms', 'incluir_bc_icmsst', 'icmssn_incluido_preco',
                                                               'icmssnst_incluido_preco', 'icms_incluido_preco', 'icmsst_incluido_preco'))
        return HttpResponse(data, content_type='application/json')
