import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dong-kehan'

class PersonaAssetsTests(unittest.TestCase):
    def test_voice_samples_match_original_spans(self):
        text = (ROOT/'references/voice.md').read_text()
        blocks = text.split('### V')[1:]
        self.assertEqual(len(blocks), 8)
        for block in blocks:
            path = re.search(r'- file: `([^`]+)`', block).group(1)
            start, end = map(int, re.search(r'- span: `\[(\d+),(\d+)\)`', block).groups())
            quote = re.search(r'```text\n(.*?)\n```', block, re.S).group(1)
            self.assertEqual(quote, (ROOT/path).read_text()[start:end])
            self.assertTrue(80 <= end-start <= 200)
    def test_casebook_article_ids_exist(self):
        rows = [json.loads(s) for s in (ROOT/'references/articles.jsonl').read_text().splitlines()]
        ids = {r['id'] for r in rows}
        book = (ROOT/'references/casebook.md').read_text()
        mentioned = set(re.findall(r'`(dkh-[a-z0-9-]+)`', book))
        self.assertTrue(mentioned)
        self.assertTrue(mentioned <= ids)
        self.assertEqual(len(re.findall(r'^## C\d\d[： ·]', book, re.M)), 6)
    def test_runtime_resource_paths_resolve(self):
        skill = (ROOT/'SKILL.md').read_text()
        references = set(re.findall(r'`(references/[^`]+\.(?:md|json|jsonl|txt))`', skill))
        self.assertGreaterEqual(len(references), 7)
        for relative in references:
            self.assertTrue((ROOT/relative).is_file(), relative)
        self.assertTrue((ROOT/'FIDELITY.md').is_file())
    def test_no_machine_paths_in_distributed_skill(self):
        pattern = re.compile(r'/(?:Users|home)/[^/\s]+/|[A-Z]:\\Users\\')
        for path in ROOT.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                self.assertIsNone(pattern.search(path.read_text()), str(path.relative_to(ROOT)))
    def test_original_bodies_have_unchanged_hashes(self):
        expected = {
            '01-bole.txt': 'e30282422facc836162fd2848b78fa093b937e33cb52f501ecdc68e6ff8f3c50',
            '02-must-build.txt': '443f44dc08390d6519c194f4923fbd76d083cc4a7df20e4a01f58e7c83ae62c2',
            '03-financing.txt': '21877f6a3f1cda61c65f1facee86baf84b72985da41818c7514f67e3c9ec63cf',
            '05-ai-paradigm.txt': '332428e668bc0c154b94949ed80e83507930420e0067bfe9318015b52360d562',
            '07-frontier-apprenticeship.txt': 'dd26c019ab8ec1b55d48aa3665452cf4eecf65dbf937c0f4a02a02436c08b696',
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/'references/user-provided/20261110'/name).read_bytes()).hexdigest(), digest)
    def test_profile_counts_do_not_imply_more_independent_sources(self):
        profile = json.loads((ROOT/'references/coverage.json').read_text())
        self.assertEqual(profile['voice_sample_count'], 8)
        self.assertEqual(profile['narrative_case_count'], 6)
        self.assertEqual(profile['candidate_mental_model_count'], 4)
        self.assertEqual(profile['local_full_text_count'], 5)
        self.assertFalse(profile['independent_holdout_tested'])
        self.assertFalse(profile['parameter_training_performed'])

if __name__ == '__main__':
    unittest.main()
