# -*- coding: utf-8 -*-

import json
import re
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.views.generic import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.core import serializers
from django.shortcuts import render
from django.urls import reverse

from djangosige.apps.cadastro.utils import filtrar_queryset_por_empresa_ativa, get_empresa_ativa
from djangosige.apps.cadastro.models import Pessoa, Cliente, Fornecedor, Transportadora, Produto
from djangosige.apps.fiscal.models import ICMS, ICMSSN, IPI, ICMSUFDest


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def _empty_json_response():
    return HttpResponse('[]', content_type='application/json')


def _normalize_digits(value):
    return re.sub(r'\D', '', value or '')


def _format_cnpj(value):
    digits = _normalize_digits(value)
    if len(digits) != 14:
        return value or ''
    return '{0}.{1}.{2}/{3}-{4}'.format(
        digits[0:2], digits[2:5], digits[5:8], digits[8:12], digits[12:14]
    )


def _format_phone(ddd, phone):
    digits = _normalize_digits('{0}{1}'.format(ddd or '', phone or ''))
    if len(digits) == 10:
        return '({0}) {1}-{2}'.format(digits[0:2], digits[2:6], digits[6:10])
    if len(digits) == 11:
        return '({0}) {1}-{2}'.format(digits[0:2], digits[2:7], digits[7:11])
    return digits


def _extract_cnpj_lookup_data(payload):
    qsa = payload.get('qsa') or []
    first_partner = qsa[0] if qsa and isinstance(qsa[0], dict) else {}
    return {
        'bairro': payload.get('bairro') or '',
        'cep': _normalize_digits(payload.get('cep')),
        'cnpj': _format_cnpj(payload.get('cnpj')),
        'complemento': payload.get('complemento') or '',
        'email': payload.get('email') or '',
        'inscricao_estadual': payload.get('inscricao_estadual') or '',
        'logradouro': payload.get('logradouro') or '',
        'municipio': payload.get('municipio') or '',
        'nome_fantasia': payload.get('nome_fantasia') or '',
        'nome_razao_social': payload.get('razao_social') or payload.get('nome_fantasia') or '',
        'numero': payload.get('numero') or 'S/N',
        'pais': 'Brasil',
        'responsavel': first_partner.get('nome_socio') or '',
        'telefone': _format_phone(payload.get('ddd_telefone_1'), payload.get('telefone_1')),
        'uf': payload.get('uf') or '',
    }


def _cnpj_lookup_error_message(payload, default_message):
    if isinstance(payload, dict):
        for key in ('message', 'mensagem', 'detail'):
            if payload.get(key):
                return payload[key]
    return default_message


def _format_decimal(value):
    if value in (None, ''):
        return ''
    return str(value).replace('.', ',')


def _format_currency(value):
    if value in (None, ''):
        value = 0
    normalized = '{:,.2f}'.format(value)
    normalized = normalized.replace(',', 'v').replace('.', ',').replace('v', '.')
    return 'R$ {0}'.format(normalized)


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


def _build_lookup_label(instance):
    document = ''
    if instance.tipo_pessoa == 'PJ':
        try:
            document = instance.pessoa_jur_info.cnpj or ''
        except ObjectDoesNotExist:
            document = ''
    elif instance.tipo_pessoa == 'PF':
        try:
            document = instance.pessoa_fis_info.cpf or ''
        except ObjectDoesNotExist:
            document = ''

    label = instance.nome_razao_social or ''
    if document:
        label = '{0} ({1})'.format(label, document)
    return label


class ConsultaPessoaView(View):

    model_map = {
        'cliente': Cliente,
        'fornecedor': Fornecedor,
        'transportadora': Transportadora,
    }

    def get(self, request, *args, **kwargs):
        term = (request.GET.get('term') or '').strip()
        tipo = (request.GET.get('tipo') or '').strip().lower()
        model = self.model_map.get(tipo)

        if model is None or len(term) < 2:
            return JsonResponse({'success': True, 'results': []})

        digits = _normalize_digits(term)
        queryset = filtrar_queryset_por_empresa_ativa(
            model.objects.all(), request.user, field_name='empresa_relacionada')
        search_filter = Q(nome_razao_social__icontains=term)
        if digits:
            search_filter |= Q(pessoa_jur_info__cnpj__icontains=digits)
            search_filter |= Q(pessoa_fis_info__cpf__icontains=digits)
        search_filter |= Q(pessoa_jur_info__nome_fantasia__icontains=term)

        queryset = queryset.filter(search_filter).distinct().order_by('nome_razao_social')[:8]
        results = [{
            'id': pessoa.pk,
            'label': _build_lookup_label(pessoa),
        } for pessoa in queryset]
        return JsonResponse({'success': True, 'results': results})


class InfoCliente(View):

    def post(self, request, *args, **kwargs):
        pessoa_id = (request.POST.get('pessoaId') or '').strip()
        panel = request.POST.get('panel') or 'cliente'
        if not pessoa_id:
            if _is_htmx(request):
                return render(request, 'progressive/fiscal_dest_info.html' if panel == 'dest' else 'progressive/venda_cliente_info.html')
            return _empty_json_response()

        obj_list = []
        cliente = filtrar_queryset_por_empresa_ativa(
            Cliente.objects.all(), request.user, field_name='empresa_relacionada').filter(pk=pessoa_id).first()
        if cliente is None:
            return _empty_json_response()
        pessoa = Pessoa.objects.get(pk=cliente.pk)
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
        fornecedor = filtrar_queryset_por_empresa_ativa(
            Fornecedor.objects.all(), request.user, field_name='empresa_relacionada').filter(pk=pessoa_id).first()
        if fornecedor is None:
            return _empty_json_response()
        pessoa = Pessoa.objects.get(pk=fornecedor.pk)
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
            transportadora = filtrar_queryset_por_empresa_ativa(
                Transportadora.objects.all(), request.user, field_name='empresa_relacionada').filter(
                pk=transportadora_id).first()
            if transportadora:
                veiculos = transportadora.veiculo.all()
        data = serializers.serialize(
            'json', veiculos, fields=('id', 'descricao',))

        if _is_htmx(request):
            return render(
                request,
                'progressive/venda_veiculo_wrapper.html',
                {'vehicles': veiculos, 'selected_id': veiculo_id}
            )

        return HttpResponse(data, content_type='application/json')


class ConsultaCNPJ(View):

    def get(self, request, *args, **kwargs):
        cnpj = _normalize_digits(request.GET.get('cnpj'))
        if len(cnpj) != 14:
            return JsonResponse({'success': False, 'error': 'Informe um CNPJ valido com 14 digitos.'}, status=400)

        lookup_url = settings.CNPJ_LOOKUP_URL_TEMPLATE.format(cnpj=cnpj)
        req = urllib_request.Request(lookup_url, headers={'User-Agent': settings.APP_DISPLAY_NAME})

        try:
            with urllib_request.urlopen(req, timeout=settings.CNPJ_LOOKUP_TIMEOUT) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except urllib_error.HTTPError as exc:
            raw_payload = exc.read().decode('utf-8', errors='ignore')
            try:
                payload = json.loads(raw_payload)
            except ValueError:
                payload = {}
            return JsonResponse({
                'success': False,
                'error': _cnpj_lookup_error_message(payload, 'Nao foi possivel consultar o CNPJ informado.'),
            }, status=exc.code or 502)
        except (urllib_error.URLError, TimeoutError, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Servico de consulta de CNPJ indisponivel no momento.',
            }, status=502)

        return JsonResponse({
            'success': True,
            'data': _extract_cnpj_lookup_data(payload),
        })


class ConsultaPrecoProduto(View):

    def get(self, request, *args, **kwargs):
        term = (request.GET.get('term') or '').strip()
        if len(term) < 2:
            return JsonResponse({'success': True, 'results': []})
        empresa = get_empresa_ativa(request.user)

        queryset = Produto.objects.filter(descricao__istartswith=term).order_by('descricao')[:8]
        if not queryset.exists():
            queryset = Produto.objects.filter(codigo__istartswith=term).order_by('descricao')[:8]

        results = []
        for produto in queryset:
            results.append({
                'id': produto.pk,
                'codigo': produto.codigo or '',
                'descricao': produto.descricao or '',
                'estoque': _format_decimal(produto.get_estoque_atual_empresa(empresa)),
                'preco': _format_currency(produto.get_venda_empresa(empresa)),
                'unidade': produto.get_sigla_unidade() or '',
                'edit_url': reverse('cadastro:editarprodutoview', kwargs={'pk': produto.pk}),
            })

        return JsonResponse({'success': True, 'results': results})


class InfoProduto(View):

    def post(self, request, *args, **kwargs):
        produto_id = (request.POST.get('produtoId') or '').strip()
        if not produto_id:
            return _empty_json_response()
        empresa = get_empresa_ativa(request.user)

        obj_list = []
        pro = Produto.objects.get(pk=produto_id)
        pro.venda = pro.get_venda_empresa(empresa)
        pro.estoque_atual = pro.get_estoque_atual_empresa(empresa)
        obj_list.append(pro)

        grupo_fiscal = pro.get_grupo_fiscal_empresa(empresa)
        if grupo_fiscal:
            if grupo_fiscal.regime_trib == '0':
                icms, created = ICMS.objects.get_or_create(
                    grupo_fiscal=grupo_fiscal)
            else:
                icms, created = ICMSSN.objects.get_or_create(
                    grupo_fiscal=grupo_fiscal)

            ipi, created = IPI.objects.get_or_create(
                grupo_fiscal=grupo_fiscal)
            icms_dest, created = ICMSUFDest.objects.get_or_create(
                grupo_fiscal=grupo_fiscal)
            obj_list.append(icms)
            obj_list.append(ipi)
            obj_list.append(icms_dest)

        data = serializers.serialize('json', obj_list, fields=('venda', 'controlar_estoque', 'estoque_atual',
                                                               'tipo_ipi', 'p_ipi', 'valor_fixo', 'p_icms', 'p_red_bc', 'p_icmsst', 'p_red_bcst', 'p_mvast',
                                                               'p_fcp_dest', 'p_icms_dest', 'p_icms_inter', 'p_icms_inter_part',
                                                               'ipi_incluido_preco', 'incluir_bc_icms', 'incluir_bc_icmsst', 'icmssn_incluido_preco',
                                                               'icmssnst_incluido_preco', 'icms_incluido_preco', 'icmsst_incluido_preco'))
        return HttpResponse(data, content_type='application/json')
