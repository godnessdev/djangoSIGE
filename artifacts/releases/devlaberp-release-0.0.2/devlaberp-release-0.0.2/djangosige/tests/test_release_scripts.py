import subprocess
import tempfile
from pathlib import Path

from django.test import SimpleTestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ReleaseScriptsTestCase(SimpleTestCase):
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

    def make_source(self, root):
        (root / 'djangosige').mkdir(parents=True, exist_ok=True)
        (root / 'djangosige' / '__init__.py').write_text("__version__ = '9.9.9'\n", encoding='utf-8')
        (root / 'app.py').write_text('print("ok")\n', encoding='utf-8')
        (root / '.env.example').write_text('DEBUG=False\n', encoding='utf-8')
        (root / 'README.md').write_text('# Projeto\n', encoding='utf-8')
        (root / 'ATUALIZANDO.md').write_text('# Atualizando\n', encoding='utf-8')
        (root / 'README_INSTALACAO_CLIENTE.md').write_text('# Instalacao\n', encoding='utf-8')
        (root / 'README_ATUALIZACAO_CLIENTE.md').write_text('# Atualizacao\n', encoding='utf-8')
        (root / '.git').mkdir(exist_ok=True)
        (root / '.venv').mkdir(exist_ok=True)

    def test_gerar_release_creates_package_manifest_and_zip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_root = temp_path / 'source'
            output_root = temp_path / 'out'
            self.make_source(source_root)

            output = self.run_script(
                'gerar-release.ps1',
                '-SourceRoot', str(source_root),
                '-OutputRoot', str(output_root),
                '-Zip',
            )

            release_root = output_root / 'devlaberp-release-9.9.9'
            package_root = release_root / 'devlaberp-release-9.9.9'

            self.assertIn('Release gerada:', output)
            self.assertTrue(release_root.exists())
            self.assertTrue(package_root.exists())
            self.assertTrue((release_root / 'release-manifest.json').exists())
            self.assertTrue((release_root / '.env.example').exists())
            self.assertTrue((release_root / 'README_INSTALACAO_CLIENTE.md').exists())
            self.assertTrue((release_root / 'README_ATUALIZACAO_CLIENTE.md').exists())
            self.assertTrue((package_root / 'app.py').exists())
            self.assertFalse((package_root / '.git').exists())
            self.assertFalse((package_root / '.venv').exists())
            self.assertTrue((output_root / 'devlaberp-release-9.9.9.zip').exists())
