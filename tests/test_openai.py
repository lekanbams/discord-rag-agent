import json
import os
import unittest
from unittest.mock import patch
import httpx
from ragb.services import Services

class OpenAITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env=patch.dict(os.environ,{'OPENAI_API_KEY':'test-only','SUPABASE_URL':'https://test.supabase.co','SUPABASE_SERVICE_ROLE_KEY':'test-only','EMBEDDING_MODEL':'text-embedding-3-small','CHAT_MODEL':'gpt-4.1-mini','ALL_PROXY':'','HTTPS_PROXY':'','HTTP_PROXY':'','all_proxy':'','https_proxy':'','http_proxy':''})
        self.env.start()
        self.service=Services()
        await self.service.http.aclose()
    async def asyncTearDown(self):
        await self.service.http.aclose()
        self.env.stop()
    async def test_embedding_request(self):
        def handle(r):
            self.assertEqual(str(r.url),'https://api.openai.com/v1/embeddings')
            body=json.loads(r.content)
            self.assertEqual(body['dimensions'],768)
            self.assertEqual(body['model'],'text-embedding-3-small')
            self.assertNotIn('taskType',body)
            return httpx.Response(200,json={'data':[{'embedding':[1.0]+[0.0]*767}]})
        self.service.http=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        self.assertEqual(len(await self.service.embed('question','RETRIEVAL_QUERY')),768)
    async def test_chat_json(self):
        def handle(r):
            body=json.loads(r.content)
            self.assertEqual(body['response_format'],{'type':'json_object'})
            return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'{"supported":false}'}}]})
        self.service.http=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        self.assertEqual(await self.service.generate('Return JSON'),' {"supported":false}'.strip())
    async def test_truncated_response_is_error(self):
        self.service.http=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'finish_reason':'length','message':{'content':'{}'}}]})))
        with self.assertRaises(ValueError): await self.service.generate('JSON')
