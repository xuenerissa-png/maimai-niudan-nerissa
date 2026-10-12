import unittest
from skill.nutrition import estimate
from skill.mcp_client import MCPError

R={'structuredContent':{'success':True,'data':'[3]{productName,energyKj,energyKcal}:\n  麦辣鸡翅-2块,937,224\n  圆筒冰淇淋,391,93\n  圆筒冰淇淋,391,93'}}
class TestNutrition(unittest.TestCase):
    def test_portion_counts_and_kcal_not_kj(self):
        r=estimate(R,{'items':[{'name':'麦辣鸡翅2块','quantity':2},{'name':'圆筒冰淇淋','quantity':1}],'maxKcal':500})
        self.assertEqual(r['totalKcal'],541)
        self.assertFalse(r['withinTarget'])
    def test_unknown_portion_prevents_complete_total(self):
        r=estimate(R,{'items':[{'name':'麦辣鸡翅','quantity':1},{'name':'圆筒冰淇淋','quantity':1}],'maxKcal':500})
        self.assertIsNone(r['totalKcal'])
        self.assertIsNone(r['withinTarget'])
        self.assertEqual(r['knownKcal'],93)
    def test_modified_unknown(self):
        r=estimate(R,{'items':[{'name':'圆筒冰淇淋','quantity':1,'modified':True}]})
        self.assertFalse(r['complete'])
    def test_invalid_quantity(self):
        with self.assertRaises(MCPError):estimate(R,{'items':[{'name':'圆筒冰淇淋','quantity':-1}]})
    def test_incomplete_source_rejected(self):
        with self.assertRaises(MCPError):estimate({'structuredContent':{'success':True,'data':'[2]{productName,energyKcal}:\n圆筒冰淇淋,93'}},{'items':[{'name':'圆筒冰淇淋','quantity':1}]})
