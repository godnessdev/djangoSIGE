import os
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

from django.test import SimpleTestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PostgresDeployTestCase(SimpleTestCase):
    def run_script(self, script_name, *args):
        script_path = PROJECT_ROOT / script_name
        env = dict(os.environ)
        env.pop('DJANGO_SETTINGS_MODULE', None)
        completed = subprocess.run(
            [
                'powershell',
                '-NoProfile',
                '-ExecutionPolicy',
                'Bypass',
                '-File',
                str(script_path),
                *args,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return completed.stdout.strip()

    def run_docker(self, *args):
        completed = subprocess.run(
            ['docker', *args],
            cwd=PROJECT_ROOT,
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
                ['docker', 'exec', container_name, 'pg_isready', '-U', 'devlab', '-d', 'devlab_test'],
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0:
                return
            time.sleep(1)
        self.fail('PostgreSQL do container nao ficou pronto em tempo')

    def wait_for_health(self, url, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with urlopen(url, timeout=2) as response:
                    body = response.read().decode('utf-8')
                    if response.status == 200 and '"status": "ok"' in body:
                        return
            except Exception:
                time.sleep(0.5)
        self.fail(f'Healthcheck nao respondeu em tempo: {url}')

    def wait_for_page(self, url, expected_text, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with urlopen(url, timeout=2) as response:
                    body = response.read().decode('utf-8')
                    if response.status == 200 and expected_text in body:
                        return
            except Exception:
                time.sleep(0.5)
        self.fail(f'Pagina nao respondeu em tempo: {url}')

    def test_postgres_migrate_verify_and_start(self):
        container_name = f"devlab-pg-test-{uuid.uuid4().hex[:8]}"
        postgres_port = self.find_free_port()
        app_port = self.find_free_port()

        try:
            self.run_docker(
                'run',
                '-d',
                '--rm',
                '--name',
                container_name,
                '-e',
                'POSTGRES_DB=devlab_test',
                '-e',
                'POSTGRES_USER=devlab',
                '-e',
                'POSTGRES_PASSWORD=devlabpass',
                '-p',
                f'{postgres_port}:5432',
                'postgres:16-alpine',
            )

            self.wait_for_postgres(container_name)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                install_root = temp_path / 'install'
                data_root = temp_path / 'data'
                python_path = PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'

                self.run_script(
                    'instalar.ps1',
                    '-SourceRoot', str(PROJECT_ROOT),
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                )

                env_path = data_root / 'env' / '.env'
                env_path.write_text(
                    '\n'.join([
                        'DEBUG=False',
                        'SECRET_KEY=postgres-phase4-secret',
                        'ALLOWED_HOSTS=127.0.0.1,localhost',
                        f'APP_DATA_ROOT={data_root.as_posix()}',
                        f'MEDIA_ROOT={(data_root / "data" / "media").as_posix()}',
                        f'STATIC_ROOT={(data_root / "data" / "staticfiles").as_posix()}',
                        f'LOG_ROOT={(data_root / "logs").as_posix()}',
                        'DB_ENGINE=postgresql',
                        'DB_NAME=devlab_test',
                        'DB_USER=devlab',
                        'DB_PASSWORD=devlabpass',
                        'DB_HOST=127.0.0.1',
                        f'DB_PORT={postgres_port}',
                    ]),
                    encoding='utf-8',
                )

                self.run_script(
                    'migrar-banco.ps1',
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-PythonPath', str(python_path),
                )

                verify_output = self.run_script(
                    'verificar-ambiente.ps1',
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-PythonPath', str(python_path),
                )
                self.assertIn('DB_OK', verify_output)

                self.run_script(
                    'iniciar-producao.ps1',
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-PythonPath', str(python_path),
                    '-ListenHost', '0.0.0.0',
                    '-Port', str(app_port),
                )
                self.wait_for_health(f'http://127.0.0.1:{app_port}/healthz/')
                self.wait_for_page(
                    f'http://127.0.0.1:{app_port}/login/',
                    'Primeiro acesso: cadastre a empresa principal',
                )
                self.run_script('parar-producao.ps1', '-DataRoot', str(data_root))
        finally:
            subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, text=True)
