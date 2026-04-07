import os
import subprocess
import tempfile
from pathlib import Path

from django.test import SimpleTestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DeployScriptsTestCase(SimpleTestCase):
    maxDiff = None

    def run_script(self, script_name, *args):
        script_path = PROJECT_ROOT / script_name
        command = [
            'powershell',
            '-NoProfile',
            '-ExecutionPolicy',
            'Bypass',
            '-File',
            str(script_path),
            *args,
        ]
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()

    def make_release_source(self, root, version_text):
        root.mkdir(parents=True, exist_ok=True)
        (root / 'version.txt').write_text(version_text, encoding='utf-8')
        (root / 'djangosige').mkdir(exist_ok=True)
        (root / 'djangosige' / 'sample.txt').write_text(f'sample-{version_text}', encoding='utf-8')

    def test_instalar_creates_expected_structure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_root = temp_path / 'release'
            install_root = temp_path / 'install'
            data_root = temp_path / 'data'
            self.make_release_source(source_root, 'v1')

            self.run_script(
                'instalar.ps1',
                '-SourceRoot', str(source_root),
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
            )

            self.assertTrue((install_root / 'app' / 'version.txt').exists())
            self.assertTrue((data_root / 'env' / '.env').exists())
            self.assertTrue((data_root / 'env' / '.env.example').exists())
            self.assertTrue((data_root / 'scripts' / 'backup.ps1').exists())
            self.assertTrue((data_root / 'install-manifest.json').exists())

    def test_backup_and_rollback_restore_app_env_media_and_sqlite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            install_root = temp_path / 'install'
            data_root = temp_path / 'data'

            (install_root / 'app').mkdir(parents=True, exist_ok=True)
            (install_root / 'app' / 'version.txt').write_text('before-update', encoding='utf-8')
            (data_root / 'env').mkdir(parents=True, exist_ok=True)
            (data_root / 'env' / '.env').write_text('DB_ENGINE=sqlite\nDB_NAME=db.sqlite3\n', encoding='utf-8')
            (data_root / 'data' / 'media').mkdir(parents=True, exist_ok=True)
            (data_root / 'data' / 'media' / 'logo.txt').write_text('media-original', encoding='utf-8')
            (data_root / 'db.sqlite3').write_text('sqlite-original', encoding='utf-8')

            backup_path = self.run_script(
                'backup.ps1',
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
                '-IncludeApp',
                '-DatabaseEngine', 'sqlite',
                '-DatabasePath', str(data_root / 'db.sqlite3'),
            )
            backup_dir = Path(backup_path)

            self.assertTrue((backup_dir / 'app' / 'version.txt').exists())
            self.assertTrue((backup_dir / 'env' / '.env').exists())
            self.assertTrue((backup_dir / 'media' / 'logo.txt').exists())
            self.assertTrue((backup_dir / 'database' / 'db.sqlite3').exists())
            self.assertTrue((backup_dir / 'backup-manifest.json').exists())

            (install_root / 'app' / 'version.txt').write_text('after-update', encoding='utf-8')
            (data_root / 'env' / '.env').write_text('DB_ENGINE=sqlite\nDB_NAME=db.sqlite3\nUPDATED=yes\n', encoding='utf-8')
            (data_root / 'data' / 'media' / 'logo.txt').write_text('media-updated', encoding='utf-8')
            (data_root / 'db.sqlite3').write_text('sqlite-updated', encoding='utf-8')

            self.run_script(
                'rollback.ps1',
                '-BackupPath', str(backup_dir),
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
            )

            self.assertEqual((install_root / 'app' / 'version.txt').read_text(encoding='utf-8'), 'before-update')
            self.assertEqual((data_root / 'env' / '.env').read_text(encoding='utf-8'), 'DB_ENGINE=sqlite\nDB_NAME=db.sqlite3\n')
            self.assertEqual((data_root / 'data' / 'media' / 'logo.txt').read_text(encoding='utf-8'), 'media-original')
            self.assertEqual((data_root / 'db.sqlite3').read_text(encoding='utf-8'), 'sqlite-original')

    def test_atualizar_creates_backup_and_replaces_app(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_v1 = temp_path / 'release-v1'
            source_v2 = temp_path / 'release-v2'
            install_root = temp_path / 'install'
            data_root = temp_path / 'data'

            self.make_release_source(source_v1, 'v1')
            self.make_release_source(source_v2, 'v2')

            self.run_script(
                'instalar.ps1',
                '-SourceRoot', str(source_v1),
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
            )

            output = self.run_script(
                'atualizar.ps1',
                '-SourceRoot', str(source_v2),
                '-InstallRoot', str(install_root),
                '-DataRoot', str(data_root),
                '-DatabaseEngine', 'sqlite',
                '-DatabasePath', str(data_root / 'db.sqlite3'),
            )

            self.assertIn('Atualizacao concluida.', output)
            self.assertEqual((install_root / 'app' / 'version.txt').read_text(encoding='utf-8'), 'v2')

            last_backup_file = data_root / 'backups' / 'last-backup.txt'
            self.assertTrue(last_backup_file.exists())
            backup_path = Path(last_backup_file.read_text(encoding='utf-8').strip())
            self.assertTrue((backup_path / 'app' / 'version.txt').exists())
            self.assertEqual((backup_path / 'app' / 'version.txt').read_text(encoding='utf-8'), 'v1')
