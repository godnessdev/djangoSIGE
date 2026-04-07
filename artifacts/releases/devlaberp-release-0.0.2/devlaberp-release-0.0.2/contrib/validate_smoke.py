import os
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangosige.configs')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import URLPattern, URLResolver, reverse, NoReverseMatch, get_resolver


SKIP_NAMES = {
    'admin:logout',
    'admin:password_change',
    'admin:password_change_done',
    'admin:autocomplete',
    'admin:jsi18n',
    'admin:view_on_site',
    'login:logoutview',
    'login:deletarusuarioview',
    'fiscal:importarnotafiscalsaida',
    'fiscal:importarnotafiscalentrada',
}


def walk(patterns, namespaces=None):
    namespaces = namespaces or []
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            full_name = ':'.join(namespaces + [pattern.name]) if pattern.name else ''
            yield {
                'name': full_name,
                'pattern': str(pattern.pattern),
                'requires_params': '(?P<' in str(pattern.pattern) or '<' in str(pattern.pattern),
            }
        elif isinstance(pattern, URLResolver):
            next_namespaces = namespaces[:]
            if pattern.namespace:
                next_namespaces.append(pattern.namespace)
            yield from walk(pattern.url_patterns, next_namespaces)


def main():
    client = Client(HTTP_HOST='127.0.0.1')
    user = get_user_model().objects.filter(is_superuser=True).first()
    if not user:
        raise SystemExit('Nenhum superusuario encontrado para executar o smoke test.')

    client.force_login(user)

    summary = defaultdict(lambda: defaultdict(int))
    details = []

    for route in walk(get_resolver().url_patterns):
        name = route['name']
        pattern = route['pattern']

        if not name:
            continue

        module = name.split(':', 1)[0] if ':' in name else 'root'

        if route['requires_params']:
            summary[module]['requires_params'] += 1
            details.append((module, name, pattern, 'requires_params'))
            continue

        if name in SKIP_NAMES:
            summary[module]['skipped'] += 1
            details.append((module, name, pattern, 'skipped'))
            continue

        try:
            url = reverse(name)
        except NoReverseMatch:
            summary[module]['reverse_error'] += 1
            details.append((module, name, pattern, 'reverse_error'))
            continue

        response = client.get(url)
        status = response.status_code
        key = f'status_{status}'
        summary[module][key] += 1
        details.append((module, name, url, key))

    print('Resumo por modulo:')
    for module in sorted(summary):
        counts = ', '.join(f'{k}={v}' for k, v in sorted(summary[module].items()))
        print(f'- {module}: {counts}')

    print('\nDetalhes:')
    for module, name, target, status in details:
        print(f'[{module}] {name} -> {target} :: {status}')


if __name__ == '__main__':
    main()
