import hashlib
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_skill', BASE/'scripts/package_skill.py')
pkg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)

class PackageTests(unittest.TestCase):
    def test_package_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a.skill'; b=Path(td)/'b.skill'
            pkg.build(a); pkg.build(b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
    def test_archive_matches_all_skill_files(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'kehan.skill'; pkg.build(out)
            expected={p.relative_to(pkg.SKILL).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in pkg.SKILL.rglob('*') if p.is_file()
                      and '__pycache__' not in p.parts and p.name!='.DS_Store'}
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                actual={n.removeprefix('dong-kehan/'):hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
                self.assertTrue(all(n.startswith('dong-kehan/') and '..' not in Path(n).parts for n in z.namelist()))
            self.assertEqual(actual,expected)
    def test_symlink_source_is_rejected(self):
        previous=pkg.SKILL
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'skill';source.mkdir()
            (source/'SKILL.md').write_text('test')
            (root/'outside.txt').write_text('not a skill resource')
            (source/'outside.txt').symlink_to(root/'outside.txt')
            pkg.SKILL=source
            try:
                with self.assertRaises(ValueError):pkg.build(root/'bad.skill')
            finally:pkg.SKILL=previous

if __name__=='__main__':unittest.main()
