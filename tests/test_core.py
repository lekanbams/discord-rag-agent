import json
import tempfile
import unittest
from ragb.core import Memory, supported_answer, split_message

class CoreTests(unittest.TestCase):
    def test_missing_evidence(self):
        self.assertIsNone(supported_answer(json.dumps({'supported':False,'answer':'guessed','sources':[]}),[]))
    def test_invalid_source_rejected(self):
        self.assertIsNone(supported_answer(json.dumps({'supported':True,'answer':'guess','sources':[2]}),[{'content':'one'}]))
    def test_valid_source(self):
        self.assertEqual(supported_answer(json.dumps({'supported':True,'answer':'Fact','sources':[1]}),[{'metadata':{'filename':'FAQ.md'}}]),'Fact')
    def test_session_isolation_and_restart(self):
        with tempfile.NamedTemporaryFile() as f:
            m=Memory(f.name); m.add('guild:channel:user','Q','A')
            self.assertEqual(m.history('other'),[])
            self.assertEqual(Memory(f.name).history('guild:channel:user'),[('user','Q'),('assistant','A')])
    def test_long_unbroken_reply(self):
        chunks=split_message('x'*5000)
        self.assertEqual(''.join(chunks),'x'*5000)
        self.assertTrue(all(len(c)<=1900 for c in chunks))
