import os
import tempfile

from django.test import SimpleTestCase

from djangosige.configs.runtime import (
    build_database_url,
    read_env_file,
    resolve_env_path,
    resolve_runtime_paths,
)


class RuntimeConfigTestCase(SimpleTestCase):
    def test_read_env_file_ignores_comments_and_blank_lines(self):
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as env_file:
            env_file.write('# comentario\n')
            env_file.write('\n')
            env_file.write('DEBUG=True\n')
            env_file.write('APP_DATA_ROOT=C:/dados\n')
            env_path = env_file.name

        self.addCleanup(lambda: os.path.exists(env_path) and os.remove(env_path))

        data = read_env_file(env_path)

        self.assertEqual(data['DEBUG'], 'True')
        self.assertEqual(data['APP_DATA_ROOT'], 'C:/dados')
        self.assertEqual(len(data), 2)

    def test_resolve_env_path_prefers_explicit_env_variable(self):
        project_root = r'C:\devlab'
        env_path = resolve_env_path(project_root, {'SIGE_ENV_PATH': r'D:\cliente\.env'})
        self.assertEqual(env_path, os.path.abspath(r'D:\cliente\.env'))

    def test_resolve_runtime_paths_defaults_to_app_root(self):
        project_root = r'C:\devlab'
        app_root = os.path.join(project_root, 'djangosige')

        paths = resolve_runtime_paths(project_root, app_root, {}, {})

        self.assertEqual(paths['APP_DATA_ROOT'], os.path.abspath(app_root))
        self.assertEqual(paths['MEDIA_ROOT'], os.path.abspath(os.path.join(app_root, 'media')))
        self.assertEqual(paths['STATIC_ROOT'], os.path.abspath(os.path.join(app_root, 'staticfiles')))
        self.assertEqual(paths['LOG_ROOT'], os.path.abspath(os.path.join(app_root, 'logs')))

    def test_resolve_runtime_paths_supports_external_data_root(self):
        project_root = r'C:\devlab'
        app_root = os.path.join(project_root, 'djangosige')

        paths = resolve_runtime_paths(
            project_root,
            app_root,
            {'APP_DATA_ROOT': r'C:\ProgramData\DevLabERP'},
            {},
        )

        self.assertEqual(paths['APP_DATA_ROOT'], os.path.abspath(r'C:\ProgramData\DevLabERP'))
        self.assertEqual(paths['MEDIA_ROOT'], os.path.abspath(r'C:\ProgramData\DevLabERP\media'))
        self.assertEqual(paths['STATIC_ROOT'], os.path.abspath(r'C:\ProgramData\DevLabERP\staticfiles'))
        self.assertEqual(paths['LOG_ROOT'], os.path.abspath(r'C:\ProgramData\DevLabERP\logs'))

    def test_build_database_url_uses_explicit_database_url_when_present(self):
        url = build_database_url(
            default_database_url='',
            app_data_root=r'C:\dados',
            project_env={'DATABASE_URL': 'postgresql://app:pwd@127.0.0.1:5432/devlab'},
            environ={},
        )

        self.assertEqual(url, 'postgresql://app:pwd@127.0.0.1:5432/devlab')

    def test_build_database_url_builds_postgresql_from_db_variables(self):
        url = build_database_url(
            default_database_url='',
            app_data_root=r'C:\dados',
            project_env={
                'DB_ENGINE': 'postgresql',
                'DB_NAME': 'devlab_cliente',
                'DB_USER': 'devlab_app',
                'DB_PASSWORD': 'senha forte',
                'DB_HOST': '192.168.0.10',
                'DB_PORT': '5433',
            },
            environ={},
        )

        self.assertEqual(
            url,
            'postgresql://devlab_app:senha%20forte@192.168.0.10:5433/devlab_cliente',
        )

    def test_build_database_url_builds_sqlite_under_app_data_root(self):
        url = build_database_url(
            default_database_url='',
            app_data_root=r'C:\ProgramData\DevLabERP',
            project_env={'DB_ENGINE': 'sqlite', 'DB_NAME': 'data\\cliente.sqlite3'},
            environ={},
        )

        self.assertEqual(
            url,
            'sqlite:///' + os.path.abspath(r'C:\ProgramData\DevLabERP\data\cliente.sqlite3'),
        )

    def test_build_database_url_uses_default_database_url_when_no_override_exists(self):
        url = build_database_url(
            default_database_url='postgresql://base:123@127.0.0.1:5432/padrao',
            app_data_root=r'C:\dados',
            project_env={},
            environ={},
        )

        self.assertEqual(url, 'postgresql://base:123@127.0.0.1:5432/padrao')
