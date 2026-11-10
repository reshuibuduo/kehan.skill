#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'dong-kehan/scripts/library.py'
spec=importlib.util.spec_from_file_location('library',SCRIPT)
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
ROWS=lib.read_library()
SELF=[r for r in ROWS if r['status']=='verified_self']

class LibraryTests(unittest.TestCase):
    def test_schema(self):
        self.assertEqual(lib.validate(ROWS),[])
    def test_financing_rank(self):
        self.assertEqual(lib.rank(SELF,'融资 投资人',3)[0]['id'],'dkh-4744893')
    def test_growth_rank(self):
        self.assertEqual(lib.rank(SELF,'结构外生长力',3)[0]['id'],'dkh-4226475')
    def test_outreach_rank(self):
        self.assertEqual(lib.rank(SELF,'冷邮件 求助',3)[0]['id'],'dkh-4829257')
    def test_unicode_normalization(self):
        self.assertEqual(lib.tokens('ＡＩ'),lib.tokens('ai'))
    def test_unknown_topic_is_not_fabricated(self):
        self.assertEqual(lib.rank(SELF,'photosynthesis zebrafish quantumfoobar'),[])
    def test_pending_has_no_invented_content(self):
        for r in ROWS:
            if r['content_evidence'] in {'index_only','mention_only'}:
                self.assertFalse(r['summary']);self.assertEqual(r['key_points'],[])
    def test_duplicate_id_rejected(self):
        self.assertTrue(any('duplicate id' in e for e in lib.validate(ROWS+[ROWS[0]])))
    def test_duplicate_article_url_rejected(self):
        bad=copy.deepcopy(ROWS[0]);bad['id']='test-duplicate-url'
        self.assertTrue(any('duplicate WeChat' in e for e in lib.validate(ROWS+[bad])))
    def test_forged_authorship_rejected(self):
        bad=copy.deepcopy(SELF[0]);bad['byline']=['N1']
        self.assertTrue(any('byline' in e for e in lib.validate([bad])))
    def test_index_only_summary_rejected(self):
        bad=copy.deepcopy(next(r for r in ROWS if r['content_evidence']=='index_only'))
        bad['summary']='invented body'
        self.assertTrue(any('inferred content' in e for e in lib.validate([bad])))
    def test_cli_default_scope_and_cwd_independence(self):
        with tempfile.TemporaryDirectory() as td:
            result=subprocess.run(['python3',str(SCRIPT),'search','创业','--limit','100','--json'],cwd=td,capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertTrue(json.loads(result.stdout))
        self.assertTrue(all(r['status'] in {'verified_self','user_supplied'} for r in json.loads(result.stdout)))
        self.assertTrue(any(r['status']=='user_supplied' for r in json.loads(result.stdout)))
    def test_cli_unknown_id_exit(self):
        result=subprocess.run(['python3',str(SCRIPT),'show','missing-id'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'NOT_FOUND: missing-id\n')
    def test_conflicting_byline_remains_pending(self):
        r=next(r for r in ROWS if r['id']=='dkh-4872563')
        self.assertEqual(r['status'],'unresolved')
        self.assertEqual({x['author'] for x in r['byline_claims']},{'N1','董科含'})
        self.assertNotIn(r,SELF)
    def test_coverage_does_not_claim_full_history(self):
        c=json.loads((lib.ROOT/'references/coverage.json').read_text())
        self.assertFalse(c['full_history_verified'])
        self.assertEqual(c['verified_self_wechat_count'],len(SELF))
        self.assertEqual(c['total_unique_records'],len(ROWS))
    def test_publication_date_separation(self):
        r=next(r for r in ROWS if r['id']=='dkh-4226475')
        self.assertIsNone(r['wechat_publication_date'])
        self.assertEqual(r['reprint_date'],'2025-04-11')
    def test_citations_survive_retrieval(self):
        for r in lib.rank(SELF,'创业 融资 成长',10):
            self.assertTrue(r['authorship_evidence_url'].startswith('https://www.huxiu.com/article/'))
            self.assertTrue(r['wechat_url'].startswith('https://mp.weixin.qq.com/s'))

class ProvidedTextTests(unittest.TestCase):
    def test_strict_self_scope_preserves_authorship_boundary(self):
        selected=lib.select_rows(ROWS,'self')
        self.assertEqual(len(selected),6)
        self.assertTrue(all(r['status']=='verified_self' and r['byline']==['董科含'] for r in selected))
        self.assertFalse(any(r['id'].startswith('dkh-user-') for r in selected))
    def test_supplied_scope_has_five_bodies_not_six(self):
        selected=lib.select_rows(ROWS,'supplied')
        self.assertEqual(len(selected),5)
        self.assertEqual(len({r['full_text']['sha256'] for r in selected}),5)
        self.assertIn('dkh-4744893',{r['id'] for r in selected})
    def test_body_hashes_and_character_counts(self):
        expected={'dkh-user-20261110-01':4882,'dkh-user-20261110-02':3450,'dkh-4744893':8946,'dkh-user-20261110-05':4803,'dkh-user-20261110-07':10419}
        for rid,size in expected.items():
            row=next(r for r in ROWS if r['id']==rid)
            self.assertEqual(len(lib.local_text(row)),size)
    def test_duplicate_inputs_share_one_body(self):
        m=json.loads((lib.ROOT/'references/user-provided/20261110/submission.json').read_text())
        p5=next(p for p in m['passages'] if p['input_number']==5)
        p6=next(p for p in m['passages'] if p['input_number']==6)
        self.assertEqual(p5['sha256'],p6['sha256'])
        self.assertEqual(p5['body_file'],p6['body_file'])
        self.assertEqual(p6['duplicate_of_input_number'],5)
        self.assertEqual(next(r for r in ROWS if r['id']=='dkh-user-20261110-05')['full_text']['input_numbers'],[5,6])
    def test_user_text_not_promoted_to_verified_self(self):
        supplied=[r for r in ROWS if r['status']=='user_supplied']
        self.assertEqual(len(supplied),4)
        for row in supplied:
            self.assertEqual(row['byline'],[])
            self.assertIsNone(row['authorship_evidence_url'])
            self.assertTrue(row['title_is_provisional'])
            bad=copy.deepcopy(row);bad['status']='verified_self'
            self.assertTrue(lib.validate([bad]))
    def test_full_body_only_phrase_is_searchable(self):
        results=lib.rank(lib.select_rows(ROWS,'usable'),'湿的水泥',1)
        self.assertEqual(results[0]['id'],'dkh-user-20261110-07')
    def test_cli_default_finds_new_apprenticeship_text(self):
        result=subprocess.run(['python3',str(SCRIPT),'search','前沿学徒期 问题距离','--limit','1','--json'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)[0]['id'],'dkh-user-20261110-07')
    def test_body_tampering_rejected(self):
        row=copy.deepcopy(next(r for r in ROWS if r.get('full_text')))
        row['full_text']['sha256']='0'*64
        self.assertTrue(any('SHA256 mismatch' in e for e in lib.validate([row])))
    def test_body_path_escape_rejected(self):
        row=copy.deepcopy(next(r for r in ROWS if r.get('full_text')))
        row['full_text']['path']='../../outside.txt'
        self.assertTrue(any('local body' in e for e in lib.validate([row])))
    def test_duplicate_body_record_rejected(self):
        row=copy.deepcopy(next(r for r in ROWS if r['status']=='user_supplied'))
        row['id']='duplicate-body-test'
        self.assertTrue(any('duplicate local body' in e for e in lib.validate(ROWS+[row])))
    def test_unconfirmed_match_does_not_delete_original_candidate(self):
        row=next(r for r in ROWS if r['id']=='dkh-user-20261110-02')
        self.assertEqual(row['possible_match_ids'],['dkh-pending-must-build'])
        candidate=next(r for r in ROWS if r['id']=='dkh-pending-must-build')
        self.assertEqual(candidate['status'],'unresolved')
    def test_cli_text_preserves_input(self):
        row=next(r for r in ROWS if r['id']=='dkh-user-20261110-01')
        result=subprocess.run(['python3',str(SCRIPT),'text',row['id'],'--offset','0','--length','120'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertEqual(result.stdout.split('\n',1)[1],lib.local_text(row)[:120]+'\n')
    def test_unknown_body_has_explicit_status(self):
        result=subprocess.run(['python3',str(SCRIPT),'text','dkh-4226475'],capture_output=True,text=True)
        self.assertEqual(result.returncode,3)
        self.assertEqual(result.stdout,'NO_LOCAL_TEXT: dkh-4226475\n')
    def test_coverage_keeps_verified_and_provided_separate(self):
        c=json.loads((lib.ROOT/'references/coverage.json').read_text())
        self.assertEqual(c['local_full_text_count'],5)
        self.assertEqual(c['user_supplied_record_count'],4)
        self.assertEqual(c['user_submission_duplicate_input_numbers'],[[5,6]])
        self.assertEqual(c['verified_self_wechat_count'],6)

if __name__=='__main__':unittest.main(verbosity=2)
