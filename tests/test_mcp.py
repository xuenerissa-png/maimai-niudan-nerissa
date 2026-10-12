import unittest
from skill.mcp_client import McDonaldMCP, MCPError, safe_schema

class TestMCP(unittest.TestCase):
    def test_handshake_and_discovery(self):
        calls=[]
        def fake(body,notification=False):
            calls.append(body['method'])
            if body['method']=='initialize': return {'result':{'serverInfo':{'name':'mock'}}}
            if body['method']=='tools/list': return {'result':{'tools':[{'name':'query-meals','inputSchema':{'type':'object'}}]}}
            if body['method']=='tools/call': return {'result':{'content':[{'type':'text','text':'mock'}]}}
            return {}
        client=McDonaldMCP(token='FAKE_FOR_TEST_ONLY',transport=fake)
        self.assertEqual(client.initialize()['serverInfo']['name'],'mock')
        self.assertEqual(len(client.list_tools()),1)
        self.assertEqual(client.call('query-meals',{})['content'][0]['text'],'mock')
        self.assertEqual(calls,['initialize','notifications/initialized','tools/list','tools/call'])
    def test_no_writes(self):
        client=McDonaldMCP(token='FAKE_FOR_TEST_ONLY',transport=lambda *a,**k:{})
        with self.assertRaises(MCPError):client.call('create-order',{})
    def test_missing_token(self):
        from unittest.mock import patch
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(MCPError):McDonaldMCP()
    def test_schema_filter(self):
        self.assertEqual([x['name'] for x in safe_schema([{'name':'create-order'},{'name':'query-meals'}])],['query-meals'])

if __name__=='__main__': unittest.main()
