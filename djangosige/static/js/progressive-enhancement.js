(function (window, document) {
    'use strict';

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(function (cookie) {
                var trimmed = cookie.trim();
                if (trimmed.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }

    function configureHtmx() {
        if (!window.htmx) {
            return;
        }

        window.htmx.config.historyRestoreAsHxRequest = false;
        document.body.addEventListener('htmx:configRequest', function (event) {
            event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
        });
    }

    function installLegacyTableEnhancement() {
        if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.DataTable) {
            return;
        }

        var $ = window.jQuery;
        if (!$.Admin || !$.Admin.table || $.Admin.table._phase7Wrapped) {
            return;
        }

        var originalInit = $.Admin.table.init;
        var syncRemoveButton = function () {
            var $btnRemove = $('.btn-remove');
            var checkedCount = $('.lista-remove input[type=checkbox]:checked').length;

            if (!$btnRemove.length) {
                return;
            }

            $btnRemove.prop('disabled', checkedCount === 0);
            $btnRemove.toggleClass('is-disabled', checkedCount === 0);
            if (checkedCount > 0) {
                $btnRemove.attr('title', 'Remover ' + checkedCount + ' item(ns) selecionado(s)');
            } else {
                $btnRemove.attr('title', 'Selecione ao menos um item para remover');
            }
        };

        var rebuildTableFooter = function ($table, tableApi) {
            var $wrapper = $table.closest('.dataTables_wrapper');
            var $footer = $wrapper.find('.app-datatable-footer');
            var $length = $wrapper.find('.dataTables_length').first();
            var $info = $wrapper.find('.dataTables_info').first();
            var $paginate = $wrapper.find('.dataTables_paginate').first();

            if (!$wrapper.length) {
                return;
            }

            if (!$footer.length) {
                $footer = $('<div class="app-datatable-footer"></div>');
                $table.after($footer);
            }

            if ($length.length && !$footer.find('.app-datatable-length').length) {
                $('<div class="app-datatable-length"></div>').append($length).appendTo($footer);
            }

            if ($info.length && !$footer.find('.app-datatable-meta').length) {
                $('<div class="app-datatable-meta"></div>').append($info).appendTo($footer);
            }

            if ($paginate.length && !$footer.find('.app-datatable-pager').length) {
                $('<div class="app-datatable-pager"></div>').append($paginate).appendTo($footer);
            }

            if (tableApi && tableApi.page.len() !== 25) {
                tableApi.page.len(25).draw(false);
            }
        };

        $.Admin.table.init = function () {
            originalInit.apply(this, arguments);

            var $table = $('#lista-database');
            var tableApi = $.fn.DataTable.isDataTable($table[0]) ? $table.DataTable() : null;

            $('#search-bar').off('input.phase7').on('input.phase7', function () {
                if (tableApi) {
                    tableApi.search($(this).val()).draw();
                }
            });

            $('body').off('change.phase7remove').on('change.phase7remove', '.lista-remove input[type=checkbox]', function () {
                syncRemoveButton();
            });

            if ($table.length && tableApi) {
                rebuildTableFooter($table, tableApi);
            }

            syncRemoveButton();
        };

        $.Admin.table._phase7Wrapped = true;
    }

    function postInto(url, target, values, source) {
        if (!window.htmx || !url) {
            return;
        }

        window.htmx.ajax('POST', url, {
            source: source || null,
            target: target,
            swap: 'outerHTML',
            values: values || {}
        });
    }

    function wireSelect(select, url, target, valuesBuilder) {
        if (!select || !window.htmx) {
            return;
        }

        select.setAttribute('data-progressive', 'htmx');

        var refresh = function () {
            postInto(url, target, valuesBuilder(select), select);
        };

        select.addEventListener('change', refresh);
        refresh();
    }

    function initVenda(reqUrls) {
        wireSelect(
            document.getElementById('id_cliente'),
            reqUrls.info_cliente_url,
            '#cliente-info-panel',
            function (select) {
                return {
                    pessoaId: select.value || '',
                    panel: 'cliente'
                };
            }
        );

        wireSelect(
            document.getElementById('id_transportadora'),
            reqUrls.info_transportadora_url,
            '#veiculo-wrapper',
            function (select) {
                var veiculo = document.getElementById('id_veiculo');
                return {
                    transportadoraId: select.value || '',
                    veiculoId: veiculo ? veiculo.value : ''
                };
            }
        );
    }

    function initCompra(reqUrls) {
        wireSelect(
            document.getElementById('id_fornecedor'),
            reqUrls.info_fornecedor_url,
            '#fornecedor-info-panel',
            function (select) {
                return {
                    pessoaId: select.value || '',
                    panel: 'fornecedor'
                };
            }
        );
    }

    function initNotaFiscal(reqUrls, tipoNf) {
        var emitSelect = tipoNf === 'saida'
            ? document.getElementById('id_emit_saida')
            : document.getElementById('id_emit_entrada');
        var destSelect = tipoNf === 'saida'
            ? document.getElementById('id_dest_saida')
            : document.getElementById('id_dest_entrada');

        wireSelect(
            emitSelect,
            reqUrls.info_emit_url,
            '#emit-info-panel',
            function (select) {
                return {
                    pessoaId: select.value || '',
                    panel: 'emit'
                };
            }
        );

        wireSelect(
            destSelect,
            reqUrls.info_dest_url,
            '#dest-info-panel',
            function (select) {
                return {
                    pessoaId: select.value || '',
                    panel: 'dest'
                };
            }
        );
    }

    function submitGerarLancamento(reqUrls) {
        if (!window.htmx || !reqUrls.gerar_lancamento_url) {
            return;
        }

        var confirmButton = document.getElementById('baixar_conta_confirma');
        if (!confirmButton) {
            return;
        }

        confirmButton.setAttribute('data-progressive', 'htmx');

        confirmButton.addEventListener('click', function () {
            var dataInput = document.getElementById('id_data_pagamento');
            var tipoConta = document.getElementById('id_tipo_conta');
            var contaId = document.getElementById('id_conta_id');

            if (!dataInput || !tipoConta || !contaId) {
                return;
            }

            if (!dataInput.value || !/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(dataInput.value)) {
                dataInput.style.borderColor = 'red';
                return;
            }

            dataInput.style.borderColor = '';
            window.htmx.ajax('POST', reqUrls.gerar_lancamento_url, {
                source: confirmButton,
                target: '.modal_selecionar_data',
                swap: 'none',
                values: {
                    tipoConta: tipoConta.value,
                    contaId: contaId.value,
                    dataPagamento: dataInput.value
                }
            });
        });
    }

    configureHtmx();
    installLegacyTableEnhancement();

    window.ProgressiveEnhancement = {
        initCompra: initCompra,
        initLancamento: submitGerarLancamento,
        initNotaFiscal: initNotaFiscal,
        initVenda: initVenda
    };
})(window, document);
