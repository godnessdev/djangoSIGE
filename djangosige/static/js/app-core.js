(function (window, document) {
    'use strict';

    var BREAKPOINT = 1170;
    var confirmClickHandler = null;

    function ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
            return;
        }
        callback();
    }

    function toArray(nodeList) {
        return Array.prototype.slice.call(nodeList || []);
    }

    function qsa(selector, root) {
        return toArray((root || document).querySelectorAll(selector));
    }

    function setDisplay(element, visible, displayValue) {
        if (!element) {
            return;
        }
        element.style.display = visible ? (displayValue || '') : 'none';
    }

    function getBootstrapModalInstance(element) {
        if (!element || !window.bootstrap || !window.bootstrap.Modal) {
            return null;
        }
        return window.bootstrap.Modal.getOrCreateInstance(element);
    }

    function getBody() {
        return document.body;
    }

    function getOverlay() {
        return document.querySelector('.overlay');
    }

    function showOverlay() {
        var body = getBody();
        var overlay = getOverlay();
        if (body) {
            body.classList.add('overlay-open');
        }
        setDisplay(overlay, true, 'block');
    }

    function hideOverlay() {
        var body = getBody();
        var overlay = getOverlay();
        if (body) {
            body.classList.remove('overlay-open');
        }
        setDisplay(overlay, false);
    }

    function syncMenuState(toggle, open) {
        var content = toggle ? toggle.nextElementSibling : null;
        if (!toggle || !content) {
            return;
        }
        toggle.classList.toggle('toggled', open);
        setDisplay(content, open, 'block');
    }

    function closeSiblingMenus(toggle) {
        var parentList = toggle ? toggle.parentElement && toggle.parentElement.parentElement : null;
        if (!parentList || !parentList.classList.contains('list')) {
            return;
        }

        toArray(parentList.children).forEach(function (item) {
            var siblingToggle = item.firstElementChild;
            if (!siblingToggle || siblingToggle === toggle || !siblingToggle.classList.contains('menu-toggle')) {
                return;
            }
            syncMenuState(siblingToggle, false);
        });
    }

    function toggleMenu(toggle) {
        if (!toggle) {
            return;
        }
        var willOpen = !toggle.classList.contains('toggled');
        closeSiblingMenus(toggle);
        syncMenuState(toggle, willOpen);
    }

    function markMenuActive() {
        var currentUrl = window.location.href;
        var menuLinks = qsa('.menu .list a[href]').filter(function (link) {
            var href = link.getAttribute('href') || '';
            return href && href !== '#' && href.indexOf('javascript:') !== 0;
        });
        var bestMatch = null;
        var bestLength = -1;

        menuLinks.forEach(function (link) {
            if (currentUrl === link.href || currentUrl.indexOf(link.href) === 0) {
                if (link.href.length > bestLength) {
                    bestMatch = link;
                    bestLength = link.href.length;
                }
            }
        });

        if (!bestMatch) {
            return;
        }

        var currentItem = bestMatch.closest('li');
        while (currentItem) {
            currentItem.classList.add('active');
            var parentMenu = currentItem.parentElement;
            if (parentMenu && parentMenu.classList.contains('ml-menu')) {
                setDisplay(parentMenu, true, 'block');
                if (parentMenu.previousElementSibling && parentMenu.previousElementSibling.classList.contains('menu-toggle')) {
                    parentMenu.previousElementSibling.classList.add('toggled');
                }
            }
            currentItem = parentMenu ? parentMenu.closest('li') : null;
        }
    }

    function checkStatusForResize(firstTime) {
        var body = getBody();
        var openCloseBar = document.querySelector('.navbar .navbar-header .bars');
        if (!body) {
            return;
        }

        if (firstTime) {
            qsa('.content, .sidebar').forEach(function (element) {
                element.classList.add('no-animate');
            });
            window.setTimeout(function () {
                qsa('.content, .sidebar').forEach(function (element) {
                    element.classList.remove('no-animate');
                });
            }, 1000);
        }

        if (body.clientWidth < BREAKPOINT) {
            body.classList.add('ls-closed');
            setDisplay(openCloseBar, true, '');
            return;
        }

        body.classList.remove('ls-closed');
        hideOverlay();
        setDisplay(openCloseBar, false);
    }

    function openWindow(url, title, width, height) {
        if (!url) {
            return null;
        }

        var dualScreenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screen.left;
        var dualScreenTop = window.screenTop !== undefined ? window.screenTop : window.screen.top;
        var viewportWidth = window.innerWidth || document.documentElement.clientWidth || screen.width;
        var viewportHeight = window.innerHeight || document.documentElement.clientHeight || screen.height;
        var left = ((viewportWidth / 2) - (width / 2)) + dualScreenLeft;
        var top = ((viewportHeight / 2) - (height / 2)) + dualScreenTop;
        var child = window.open(
            url,
            title || '',
            'scrollbars=yes,width=' + width + ',height=' + height + ',top=' + top + ',left=' + left
        );

        if (child && window.focus) {
            child.focus();
        }

        return child;
    }

    function isIgnoredInteractiveTarget(target) {
        return !!target.closest('input, label, i, .prevent-click-row');
    }

    function bindGlobalInteractions() {
        document.addEventListener('click', function (event) {
            var barsButton = event.target.closest('.bars');
            var menuToggle = event.target.closest('.menu-toggle');
            var popupTrigger = event.target.closest('a.popup, tr.popup');
            var newWindowTrigger = event.target.closest('a.newwindow, tr.newwindow');
            var clickableRow = event.target.closest('.clickable-row');
            var sidebar = document.getElementById('barralateral');

            if (barsButton) {
                event.preventDefault();
                if (getBody().classList.contains('overlay-open')) {
                    hideOverlay();
                } else {
                    showOverlay();
                }
                return;
            }

            if (menuToggle) {
                event.preventDefault();
                toggleMenu(menuToggle);
                return;
            }

            if (popupTrigger) {
                if (event.target.closest('input, label')) {
                    return;
                }
                event.preventDefault();
                openWindow(
                    popupTrigger.getAttribute('href') || popupTrigger.dataset.href,
                    popupTrigger.getAttribute('title'),
                    600,
                    500
                );
                return;
            }

            if (newWindowTrigger) {
                event.preventDefault();
                window.open(newWindowTrigger.getAttribute('href') || newWindowTrigger.dataset.href, newWindowTrigger.getAttribute('title') || '');
                return;
            }

            if (clickableRow && !clickableRow.classList.contains('popup') && !isIgnoredInteractiveTarget(event.target)) {
                var rowUrl = clickableRow.dataset.href || clickableRow.getAttribute('href');
                if (rowUrl) {
                    window.location.href = rowUrl;
                    return;
                }
            }

            if (
                getBody().classList.contains('overlay-open') &&
                !event.target.closest('#barralateral') &&
                !event.target.closest('.bars') &&
                !event.target.closest('.dropdown-backdrop')
            ) {
                hideOverlay();
            }

            if (sidebar && event.target.closest('#btn-sim')) {
                return;
            }
        });

        window.addEventListener('resize', function () {
            checkStatusForResize(false);
        });
    }

    function annotateFieldActions() {
        qsa('.input-group > a.input-group-addon, .input-group > button.input-group-addon').forEach(function (action) {
            action.classList.add('field-action');
            if (!action.getAttribute('aria-label')) {
                action.setAttribute('aria-label', action.getAttribute('title') || 'Abrir acao relacionada');
            }
        });

        qsa('.form-group').forEach(function (group) {
            if (group.querySelector('label.error')) {
                group.classList.add('has-validation-error');
            }
            if (group.querySelector('.input-group > .input-group-addon')) {
                group.classList.add('has-field-action');
            }
            if (group.querySelector('input[type="checkbox"], input[type="radio"]')) {
                group.classList.add('is-choice-group');
            }
        });
    }

    function annotateDateFields() {
        qsa('input.datepicker').forEach(function (field) {
            if (!field.getAttribute('placeholder')) {
                field.setAttribute('placeholder', 'dd/mm/aaaa');
            }
            field.setAttribute('inputmode', 'numeric');
            field.setAttribute('autocomplete', 'off');
        });

        qsa('input.datetimepicker').forEach(function (field) {
            if (!field.getAttribute('placeholder')) {
                field.setAttribute('placeholder', 'dd/mm/aaaa hh:mm');
            }
            field.setAttribute('inputmode', 'numeric');
            field.setAttribute('autocomplete', 'off');
        });
    }

    function getMessageElements() {
        return {
            body: document.querySelector('#modal-msg .modal-body p'),
            icon: document.querySelector('#modal-msg .modal-header i'),
            modal: document.getElementById('modal-msg'),
            noButton: document.getElementById('btn-nao'),
            okButton: document.getElementById('btn-ok'),
            simButton: document.getElementById('btn-sim'),
            title: document.querySelector('#modal-msg .modal-title')
        };
    }

    function resetConfirmHandler(button) {
        if (!button || !confirmClickHandler) {
            return;
        }
        button.removeEventListener('click', confirmClickHandler);
        confirmClickHandler = null;
    }

    function showMessage(options) {
        var elements = getMessageElements();
        var modal = getBootstrapModalInstance(elements.modal);
        if (!elements.modal || !modal) {
            return;
        }

        resetConfirmHandler(elements.simButton);
        elements.icon.classList.remove('icon-success', 'icon-alert');
        elements.icon.textContent = options.icon || '';
        if (options.variant === 'success') {
            elements.icon.classList.add('icon-success');
        } else {
            elements.icon.classList.add('icon-alert');
        }

        elements.title.textContent = options.title || '';
        elements.body.textContent = options.message || '';

        setDisplay(elements.okButton, !!options.showOk, '');
        setDisplay(elements.simButton, !!options.showYes, '');
        setDisplay(elements.noButton, !!options.showNo, '');

        if (options.onConfirm && elements.simButton) {
            confirmClickHandler = function () {
                options.onConfirm();
            };
            elements.simButton.addEventListener('click', confirmClickHandler, { once: true });
        }

        modal.show();
    }

    var messages = {
        alert: function (message) {
            showMessage({
                icon: 'error_outline',
                message: message,
                showOk: true,
                title: 'Operacao nao permitida',
                variant: 'alert'
            });
        },
        confirm: function (message, onConfirm) {
            showMessage({
                icon: 'error_outline',
                message: message,
                onConfirm: onConfirm,
                showNo: true,
                showYes: true,
                title: 'Tem certeza?',
                variant: 'alert'
            });
        },
        success: function (message) {
            showMessage({
                icon: 'done',
                message: message,
                showOk: true,
                title: 'Sucesso',
                variant: 'success'
            });
        }
    };

    var loader = {
        hide: function () {
            setDisplay(document.querySelector('.page-loader-wrapper'), false);
        },
        show: function (message) {
            var messageNode = document.querySelector('.loader .loader-message');
            setDisplay(document.querySelector('.page-loader-wrapper'), true, 'block');
            if (messageNode && message) {
                messageNode.textContent = message;
            }
        }
    };

    function init() {
        bindGlobalInteractions();
        checkStatusForResize(true);
        markMenuActive();
        annotateFieldActions();
        annotateDateFields();
        window.setTimeout(loader.hide, 50);
    }

    window.AppCore = {
        init: init,
        loader: loader,
        messages: messages,
        openWindow: openWindow
    };

    ready(init);
})(window, document);
