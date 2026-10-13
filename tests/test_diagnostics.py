import os
import unittest
from unittest.mock import patch
import httpx
from bot import safe_http_error

class DiagnosticTests(unittest.TestCase):
    def test_telegram_description_without_token(self):
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'123:secret'}):
            req=httpx.Request('GET','https://api.telegram.org/bot123:secret/getUpdates')
            response=httpx.Response(409,request=req,json={'description':'Conflict: webhook is active 123:secret'})
            error=httpx.HTTPStatusError('secret URL',request=req,response=response)
            result=safe_http_error(error)
            self.assertIn('HTTP 409',result)
            self.assertIn('webhook is active',result)
            self.assertNotIn('123:secret',result)
            self.assertNotIn('https://',result)
    def test_other_provider_body_hidden(self):
        req=httpx.Request('POST','https://api.openai.com/v1/embeddings')
        response=httpx.Response(401,request=req,json={'description':'sensitive body'})
        self.assertEqual(safe_http_error(httpx.HTTPStatusError('secret',request=req,response=response)),'HTTP 401')
