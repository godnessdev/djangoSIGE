import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from django.test import SimpleTestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ProductionScriptsTestCase(SimpleTestCase):
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

    def find_free_port(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            return sock.getsockname()[1]

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

    def write_runtime_env(self, env_path, data_root):
        env_path.write_text(
            '\n'.join([
                'DEBUG=False',
                'SECRET_KEY=test-secret-key',
                'ALLOWED_HOSTS=127.0.0.1,localhost',
                f'APP_DATA_ROOT={data_root.as_posix()}',
                f'MEDIA_ROOT={(data_root / "data" / "media").as_posix()}',
                f'STATIC_ROOT={(data_root / "data" / "staticfiles").as_posix()}',
                f'LOG_ROOT={(data_root / "logs").as_posix()}',
                'DB_ENGINE=sqlite',
                f'DB_NAME={(data_root / "db.sqlite3").as_posix()}',
            ]),
            encoding='utf-8',
        )

    def test_start_stop_and_restart_production_server(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            install_root = temp_path / 'install'
            data_root = temp_path / 'data'
            port = self.find_free_port()
            health_url = f'http://127.0.0.1:{port}/healthz/'

            self.run_script(
                'instalar.ps1',
                '-SourceRoot', str(PROJECT_ROOT),
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
            )

            env_path = data_root / 'env' / '.env'
            self.write_runtime_env(env_path, data_root)

            python_path = PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'

            self.run_script(
                'migrar-banco.ps1',
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
                '-PythonPath', str(python_path),
            )

            self.run_script(
                'iniciar-producao.ps1',
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
                '-PythonPath', str(python_path),
                '-ListenHost', '127.0.0.1',
                '-Port', str(port),
            )
            self.wait_for_health(health_url)
            self.wait_for_page(
                f'http://127.0.0.1:{port}/login/',
                'Primeiro acesso: cadastre a empresa principal',
            )

            health_output = self.run_script('healthcheck.ps1', '-Url', health_url)
            self.assertIn('"status": "ok"', health_output)

            stop_output = self.run_script('parar-producao.ps1', '-DataRoot', str(data_root))
            self.assertIn('Processo de producao finalizado', stop_output)

            self.run_script(
                'iniciar-producao.ps1',
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
                '-PythonPath', str(python_path),
                '-ListenHost', '127.0.0.1',
                '-Port', str(port),
            )
            self.wait_for_health(health_url)

            self.run_script('parar-producao.ps1', '-DataRoot', str(data_root))

    def test_registrar_servico_emit_only_generates_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_root = temp_path / 'data'
            install_root = temp_path / 'install'

            output = self.run_script(
                'registrar-servico.ps1',
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
                '-EmitOnly',
            )

            self.assertIn('iniciar-producao.ps1', output)
            self.assertTrue((data_root / 'service-manifest.json').exists())
