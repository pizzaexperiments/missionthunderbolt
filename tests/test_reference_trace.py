import copy
import unittest
from test_audit_resources import sample
from check_reference_trace import validate

class TraceTests(unittest.TestCase):
    def trace(self):
        return {'schema':1,'run_id':'synthetic-test','game_version':'fixture','environment':'synthetic',
                'source_sha256':'0'*64,'events':[{'step':0,'action':'fixture action','confidence':'observed',
                                               'state':{},'evidence':['synthetic fixture reference']} ]}
    def test_labeled_event(self):self.assertEqual(validate(self.trace()),1)
    def test_no_evidence_is_not_an_observation(self):
        t=self.trace();t['events'][0]['evidence']=[]
        with self.assertRaises(ValueError):validate(t)
        t['events'][0]['confidence']='unknown';self.assertEqual(validate(t),1)
    def test_invalid_order_and_source(self):
        for key,value in [('source_sha256','not-a-hash'),('events',[])]:
            t=self.trace();t[key]=value
            with self.assertRaises(ValueError):validate(t)
        t=self.trace();t['events'][0]['step']=7
        with self.assertRaises(ValueError):validate(t)
