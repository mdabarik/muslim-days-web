import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import validate
class Integrity(unittest.TestCase):
 def setUp(self):
  self.cache={str(p):json.loads(p.read_text()) for p in validate.DIST.rglob('*.json')}
  review=validate.ROOT/'evidence/symbol-fix-2026-10-03/source-legend-audit.json';self.cache[str(review)]=json.loads(review.read_text())
 def run_mutation(self,mutate):
  values=copy.deepcopy(self.cache);mutate(values)
  with patch('validate.load',side_effect=lambda p: values[str(p)]):return validate.validate()
 def test_draft_cannot_be_released(self):
  def mutate(v):v[str(validate.DIST/'data/manifest.json')]['releaseReady']=True
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_mark_cannot_disappear(self):
  def mutate(v):v[str(validate.DIST/'data/pages/001.json')]['annotations'].pop()
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_haraka_cannot_disappear(self):
  def mutate(v):v[str(validate.DIST/'data/pages/001.json')]['graphemes']['r0w1'][0]['text']='ا'
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_unproven_anchor_cannot_be_verified(self):
  def mutate(v):v[str(validate.DIST/'data/pages/001.json')]['annotations'][0]['verified']=True
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_wrong_glyph_mapping_is_rejected(self):
  def mutate(v):
   a=next(a for a in v[str(validate.DIST/'data/pages/001.json')]['annotations'] if a.get('display',{}).get('symbolId')=='ringed-wedge');a['display']['character']='\ue002'
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_guessed_damaged_symbol_is_rejected(self):
  def mutate(v):
   a=next(a for a in v[str(validate.DIST/'data/pages/003.json')]['annotations'] if a['sourceId']=='r0-a8');a.pop('display')
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_arrow_cannot_be_attached_to_arbitrary_word(self):
  def mutate(v):
   a=next(a for a in v[str(validate.DIST/'data/pages/007.json')]['annotations'] if a['sourceId']=='r10-a2');a['displayAttachment']['targetId']='r10w2'
  with self.assertRaises(AssertionError):self.run_mutation(mutate)
 def test_known_incomplete_dataset_stays_blocked(self):
  report=validate.validate();self.assertEqual(report['structuralStatus'],'pass');self.assertEqual(report['releaseStatus'],'blocked');self.assertGreater(report['blockerCount'],0)
if __name__=='__main__':unittest.main()
