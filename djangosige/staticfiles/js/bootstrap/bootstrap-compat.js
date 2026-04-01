(function (window, document) {
    'use strict';

    var bootstrap = window.bootstrap;
    var $ = window.jQuery;

    if (!bootstrap) {
        throw new Error('Carregar Bootstrap antes do bootstrap-compat.js.');
    }

    function syncLegacyDataAttributes(root) {
        var scope = root || document;
        var toggleNodes = scope.querySelectorAll('[data-toggle]');
        var targetNodes = scope.querySelectorAll('[data-target]');
        var dismissNodes = scope.querySelectorAll('[data-dismiss]');

        toggleNodes.forEach(function (node) {
            if (!node.hasAttribute('data-bs-toggle')) {
                node.setAttribute('data-bs-toggle', node.getAttribute('data-toggle'));
            }
        });

        targetNodes.forEach(function (node) {
            if (!node.hasAttribute('data-bs-target')) {
                node.setAttribute('data-bs-target', node.getAttribute('data-target'));
            }
        });

        dismissNodes.forEach(function (node) {
            if (!node.hasAttribute('data-bs-dismiss')) {
                node.setAttribute('data-bs-dismiss', node.getAttribute('data-dismiss'));
            }
        });
    }

    function getTargets(trigger) {
        var selector = trigger.getAttribute('data-bs-target') || trigger.getAttribute('data-target');
        if (!selector) {
            var href = trigger.getAttribute('href');
            if (href && href.charAt(0) === '#') {
                selector = href;
            }
        }

        if (!selector) {
            return [];
        }

        try {
            return Array.prototype.slice.call(document.querySelectorAll(selector));
        } catch (error) {
            return [];
        }
    }

    function legacyDisplayValue(element) {
        return element.tagName === 'TR' ? 'table-row' : '';
    }

    function isLegacyCollapseTarget(element) {
        return !element.classList.contains('collapse');
    }

    function setLegacyCollapseState(targets, expanded) {
        targets.forEach(function (target) {
            target.classList.toggle('in', expanded);
            target.classList.toggle('show', expanded);
            target.style.display = expanded ? legacyDisplayValue(target) : 'none';
        });
    }

    function handleLegacyCollapse(trigger) {
        var targets = getTargets(trigger).filter(isLegacyCollapseTarget);

        if (!targets.length) {
            return false;
        }

        var expanded = targets.some(function (target) {
            return target.classList.contains('in') || target.classList.contains('show') || target.style.display !== 'none';
        });

        setLegacyCollapseState(targets, !expanded);
        trigger.setAttribute('aria-expanded', String(!expanded));
        return true;
    }

    function activateLegacyTab(link) {
        var selector = link.getAttribute('data-bs-target') || link.getAttribute('href');

        if (!selector || selector.charAt(0) !== '#') {
            return;
        }

        var container = link.closest('ul, .nav');
        var pane = document.querySelector(selector);

        if (!container || !pane) {
            return;
        }

        container.querySelectorAll('a').forEach(function (item) {
            item.classList.remove('active');
            item.setAttribute('aria-selected', 'false');
            var parent = item.closest('li');
            if (parent) {
                parent.classList.remove('active');
            }
        });

        var tabContent = pane.parentElement;
        if (tabContent) {
            tabContent.querySelectorAll('.tab-pane').forEach(function (tabPane) {
                tabPane.classList.remove('active', 'show');
            });
        }

        link.classList.add('active');
        link.setAttribute('aria-selected', 'true');
        var li = link.closest('li');
        if (li) {
            li.classList.add('active');
        }

        pane.classList.add('active', 'show');
    }

    function syncTabParents(root) {
        var scope = root || document;
        scope.querySelectorAll('.nav-tabs a.active, .nav-pills a.active').forEach(function (link) {
            var parent = link.closest('li');
            if (parent) {
                parent.classList.add('active');
            }
        });
    }

    function wireLegacyEvents() {
        document.addEventListener('click', function (event) {
            var trigger = event.target.closest('[data-bs-toggle="collapse"], [data-toggle="collapse"]');
            if (trigger && handleLegacyCollapse(trigger)) {
                event.preventDefault();
            }
        });

        document.addEventListener('shown.bs.tab', function (event) {
            var current = event.target;
            var previous = event.relatedTarget;

            if (previous) {
                var previousParent = previous.closest('li');
                if (previousParent) {
                    previousParent.classList.remove('active');
                }
            }

            if (current) {
                var currentParent = current.closest('li');
                if (currentParent) {
                    currentParent.classList.add('active');
                }
            }
        });
    }

    function registerJqueryPlugin(name, ClassRef, defaultAction) {
        if (!$ || !ClassRef) {
            return;
        }

        $.fn[name] = function (actionOrOptions) {
            var args = Array.prototype.slice.call(arguments, 1);

            return this.each(function () {
                var instance = ClassRef.getOrCreateInstance(this, actionOrOptions && typeof actionOrOptions === 'object' ? actionOrOptions : undefined);
                var action = typeof actionOrOptions === 'string' ? actionOrOptions : defaultAction;

                if (typeof instance[action] === 'function') {
                    instance[action].apply(instance, args);
                }
            });
        };
    }

    function registerJqueryCompat() {
        if (!$) {
            return;
        }

        registerJqueryPlugin('modal', bootstrap.Modal, 'toggle');
        registerJqueryPlugin('dropdown', bootstrap.Dropdown, 'toggle');
        registerJqueryPlugin('tab', bootstrap.Tab, 'show');

        $.fn.collapse = function (actionOrOptions) {
            return this.each(function () {
                if (isLegacyCollapseTarget(this)) {
                    var action = typeof actionOrOptions === 'string' ? actionOrOptions : 'toggle';
                    var expanded = this.classList.contains('in') || this.classList.contains('show') || this.style.display !== 'none';
                    var shouldShow = action === 'show' ? true : action === 'hide' ? false : !expanded;
                    setLegacyCollapseState([this], shouldShow);
                    return;
                }

                var instance = bootstrap.Collapse.getOrCreateInstance(
                    this,
                    actionOrOptions && typeof actionOrOptions === 'object' ? actionOrOptions : undefined
                );
                var command = typeof actionOrOptions === 'string' ? actionOrOptions : 'toggle';

                if (typeof instance[command] === 'function') {
                    instance[command]();
                }
            });
        };
    }

    function initBootstrapCompat() {
        syncLegacyDataAttributes(document);
        syncTabParents(document);

        document.querySelectorAll('.tab-content > .tab-pane.active').forEach(function (pane) {
            pane.classList.add('show');
        });
    }

    initBootstrapCompat();
    registerJqueryCompat();
    wireLegacyEvents();

    window.bootstrapCompat = {
        syncLegacyDataAttributes: syncLegacyDataAttributes,
        activateLegacyTab: activateLegacyTab,
        handleLegacyCollapse: handleLegacyCollapse
    };
})(window, document);
