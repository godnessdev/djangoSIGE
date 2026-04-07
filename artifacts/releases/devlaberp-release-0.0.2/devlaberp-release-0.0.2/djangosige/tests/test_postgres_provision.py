import socket
import subprocess
import time
import uuid

import psycopg
from django.test import SimpleTestCase


class PostgresProvisionTestCase(SimpleTestCase):
    def run_script(self, script_name, *args):
        completed = subprocess.run(
            [
                'powershell',
                '-NoProfile',
                '-ExecutionPolicy',
                'Bypass',
                '-File',
                script_name,
                *args,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()

    def find_free_port(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            return sock.getsockname()[1]

    def wait_for_postgres(self, container_name, timeout=40):
        deadline = time.time() + timeout
        while time.time() < deadline:
            probe = subprocess.run(
                ['docker', 'exec', container_name, 'pg_isready', '-U', 'postgres', '-d', 'postgres'],
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0:
                return
            time.sleep(1)
        self.fail('PostgreSQL de provisionamento nao ficou pronto em tempo')

    def test_provisionar_postgres_cria_usuario_e_banco(self):
        container_name = f"devlab-pg-provision-{uuid.uuid4().hex[:8]}"
        postgres_port = self.find_free_port()

        try:
            subprocess.run(
                [
                    'docker', 'run', '-d', '--rm',
                    '--name', container_name,
                    '-e', 'POSTGRES_PASSWORD=postgrespass',
                    '-p', f'{postgres_port}:5432',
                    'postgres:16-alpine',
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.wait_for_postgres(container_name)

            output = self.run_script(
                'provisionar-postgres.ps1',
                '-AdminHost', '127.0.0.1',
                '-AdminPort', str(postgres_port),
                '-AdminDatabase', 'postgres',
                '-AdminUser', 'postgres',
                '-AdminPassword', 'postgrespass',
                '-AppDatabase', 'devlab_cliente',
                '-AppUser', 'devlab_app',
                '-AppPassword', 'devlabpass',
                '-PgContainerName', container_name,
            )

            self.assertIn('Provisionamento concluido.', output)

            with psycopg.connect(
                host='127.0.0.1',
                port=postgres_port,
                dbname='devlab_cliente',
                user='devlab_app',
                password='devlabpass',
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT current_database(), current_user;')
                    database_name, user_name = cursor.fetchone()

            self.assertEqual(database_name, 'devlab_cliente')
            self.assertEqual(user_name, 'devlab_app')

            second_output = self.run_script(
                'provisionar-postgres.ps1',
                '-AdminHost', '127.0.0.1',
                '-AdminPort', str(postgres_port),
                '-AdminDatabase', 'postgres',
                '-AdminUser', 'postgres',
                '-AdminPassword', 'postgrespass',
                '-AppDatabase', 'devlab_cliente',
                '-AppUser', 'devlab_app',
                '-AppPassword', 'devlabpass',
                '-PgContainerName', container_name,
            )
            self.assertIn('Provisionamento concluido.', second_output)
        finally:
            subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, text=True)
