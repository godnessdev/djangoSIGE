import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

import psycopg
from django.test import SimpleTestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class UpgradeRollbackPostgresTestCase(SimpleTestCase):
    def run_script(self, script_name, *args):
        script_path = PROJECT_ROOT / script_name
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
                ['docker', 'exec', container_name, 'pg_isready', '-U', 'devlab', '-d', 'devlab_upgrade'],
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

    def make_release_copy(self, destination, version_text):
        ignore_names = {'.git', '.venv', '__pycache__', '.pytest_cache', 'artifacts', 'build', 'dist'}
        destination.mkdir(parents=True, exist_ok=True)
        for item in PROJECT_ROOT.iterdir():
            if item.name in ignore_names:
                continue
            target = destination / item.name
            if item.is_dir():
                subprocess.run(
                    ['powershell', '-NoProfile', '-Command', f"Copy-Item -LiteralPath '{item}' -Destination '{target}' -Recurse -Force"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                target.write_bytes(item.read_bytes())
        (destination / 'deploy-version.txt').write_text(version_text, encoding='utf-8')

    def write_env(self, env_path, data_root, postgres_port):
        env_path.write_text(
            '\n'.join([
                'DEBUG=False',
                'SECRET_KEY=upgrade-phase5-secret',
                'ALLOWED_HOSTS=127.0.0.1,localhost',
                f'APP_DATA_ROOT={data_root.as_posix()}',
                f'MEDIA_ROOT={(data_root / "data" / "media").as_posix()}',
                f'STATIC_ROOT={(data_root / "data" / "staticfiles").as_posix()}',
                f'LOG_ROOT={(data_root / "logs").as_posix()}',
                'DB_ENGINE=postgresql',
                'DB_NAME=devlab_upgrade',
                'DB_USER=devlab',
                'DB_PASSWORD=devlabpass',
                'DB_HOST=127.0.0.1',
                f'DB_PORT={postgres_port}',
            ]),
            encoding='utf-8',
        )

    def connect(self, postgres_port):
        return psycopg.connect(
            host='127.0.0.1',
            port=postgres_port,
            dbname='devlab_upgrade',
            user='devlab',
            password='devlabpass',
        )

    def test_upgrade_and_rollback_restore_postgres_media_and_code(self):
        container_name = f"devlab-pg-upgrade-{uuid.uuid4().hex[:8]}"
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
                'POSTGRES_DB=devlab_upgrade',
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
                release_v2 = temp_path / 'release-v2'
                python_path = PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'

                self.run_script(
                    'instalar.ps1',
                    '-SourceRoot', str(PROJECT_ROOT),
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                )

                (install_root / 'app' / 'deploy-version.txt').write_text('v1', encoding='utf-8')
                self.write_env(data_root / 'env' / '.env', data_root, postgres_port)
                (data_root / 'data' / 'media').mkdir(parents=True, exist_ok=True)
                (data_root / 'data' / 'media' / 'logo.txt').write_text('media-v1', encoding='utf-8')

                self.run_script(
                    'migrar-banco.ps1',
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-PythonPath', str(python_path),
                )

                with self.connect(postgres_port) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute('CREATE TABLE IF NOT EXISTS deploy_marker (value text);')
                        cursor.execute('TRUNCATE TABLE deploy_marker;')
                        cursor.execute("INSERT INTO deploy_marker (value) VALUES ('v1');")
                    connection.commit()

                self.make_release_copy(release_v2, 'v2')

                self.run_script(
                    'atualizar.ps1',
                    '-SourceRoot', str(release_v2),
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-DatabaseEngine', 'postgresql',
                    '-DbName', 'devlab_upgrade',
                    '-DbUser', 'devlab',
                    '-DbPassword', 'devlabpass',
                    '-DbHost', '127.0.0.1',
                    '-DbPort', str(postgres_port),
                    '-PgContainerName', container_name,
                )

                self.assertEqual((install_root / 'app' / 'deploy-version.txt').read_text(encoding='utf-8'), 'v2')

                with self.connect(postgres_port) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute('TRUNCATE TABLE deploy_marker;')
                        cursor.execute("INSERT INTO deploy_marker (value) VALUES ('v2');")
                    connection.commit()

                (data_root / 'data' / 'media' / 'logo.txt').write_text('media-v2', encoding='utf-8')

                backup_path = (data_root / 'backups' / 'last-backup.txt').read_text(encoding='utf-8').strip()
                self.run_script(
                    'rollback.ps1',
                    '-BackupPath', backup_path,
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-DbName', 'devlab_upgrade',
                    '-DbUser', 'devlab',
                    '-DbPassword', 'devlabpass',
                    '-DbHost', '127.0.0.1',
                    '-DbPort', str(postgres_port),
                    '-PgContainerName', container_name,
                )

                self.assertEqual((install_root / 'app' / 'deploy-version.txt').read_text(encoding='utf-8'), 'v1')
                self.assertEqual((data_root / 'data' / 'media' / 'logo.txt').read_text(encoding='utf-8'), 'media-v1')

                with self.connect(postgres_port) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT value FROM deploy_marker LIMIT 1;')
                        value = cursor.fetchone()[0]
                self.assertEqual(value, 'v1')

                self.run_script(
                    'iniciar-producao.ps1',
                    '-InstallRoot', str(install_root),
                    '-DataRoot', str(data_root),
                    '-PythonPath', str(python_path),
                    '-ListenHost', '0.0.0.0',
                    '-Port', str(app_port),
                )
                self.wait_for_health(f'http://127.0.0.1:{app_port}/healthz/')
                self.run_script('parar-producao.ps1', '-DataRoot', str(data_root))
        finally:
            subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, text=True)
