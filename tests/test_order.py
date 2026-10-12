import unittest
from skill.mcp_client import McDonaldMCP, MCPError

class TestOrder(unittest.TestCase):
    def client(self, price=2000):
        self.calls=[]
        def transport(body, notification=False):
            self.calls.append(body)
            if body.get('params', {}).get('name') == 'calculate-price':
                return {'result': {'structuredContent': {'success':True,'data':{'price':price,'takeWayList':[{'code':'locker-in'}]}}}}
            return {'result': {'structuredContent': {'success':True,'data':{'orderId':'test-only'}}}}
        c=McDonaldMCP(token='TEST_ONLY',transport=transport)
        c.tools={'create-order':{}, 'calculate-price':{'inputSchema':{'properties':{k:{} for k in ['storeCode','orderType','beType','items']}}}}
        return c

    def args(self):
        return {'storeCode':'1400116','orderType':1,'beType':1,'takeWayCode':'locker-in','items':[{'productCode':'1700','quantity':1}]}

    def test_requires_confirmation(self):
        c=self.client()
        with self.assertRaises(MCPError): c.create_order(self.args(),max_total_fen=2000)
        self.assertEqual(self.calls,[])

    def test_over_budget_never_creates(self):
        c=self.client(2001)
        with self.assertRaises(MCPError):c.create_order(self.args(),confirmed=True,max_total_fen=2000)
        self.assertEqual([x['params']['name'] for x in self.calls],['calculate-price'])

    def test_requote_then_create(self):
        c=self.client()
        c.create_order(self.args(),confirmed=True,max_total_fen=2000)
        self.assertEqual([x['params']['name'] for x in self.calls],['calculate-price','create-order'])
        self.assertNotIn('takeWayCode',self.calls[0]['params']['arguments'])

    def test_invalid_pickup_never_creates(self):
        c=self.client();a=self.args();a['takeWayCode']='invented'
        with self.assertRaises(MCPError):c.create_order(a,confirmed=True,max_total_fen=2000)
        self.assertEqual(len(self.calls),1)
