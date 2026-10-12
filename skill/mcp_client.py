"""McDonald's official MCP Streamable HTTP client; standard library only.
Never log tokens, headers, or raw account information.
"""
import json
import os
import urllib.request
import urllib.error
import uuid

ENDPOINT = 'https://mcp.mcd.cn'
PROTOCOL = '2025-03-26'
READ_ONLY = {'query-nearby-stores', 'query-meals', 'query-meal-detail', 'query-store-coupons', 'calculate-price', 'list-nutrition-foods', 'now-time-info', 'campaign-calendar', 'query-order'}

class MCPError(Exception):
    pass

class McDonaldMCP:
    def __init__(self, token=None, transport=None):
        self._token = token or os.environ.get('MCD_MCP_TOKEN', '')
        if not self._token:
            raise MCPError('未设置 MCD_MCP_TOKEN；请在本机安全配置，不要发到聊天或提交到仓库。')
        self._transport = transport or self._post
        self.session_id = None
        self.next_id = 1
        self.tools = {}

    def _post(self, body, notification=False):
        headers = {'Authorization': 'Bearer '+self._token, 'Content-Type': 'application/json',
                   'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': PROTOCOL}
        if self.session_id:
            headers['Mcp-Session-Id'] = self.session_id
        req = urllib.request.Request(ENDPOINT, data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
                                     headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                self.session_id = response.headers.get('Mcp-Session-Id', self.session_id)
                raw = response.read().decode('utf-8')
                ctype = response.headers.get('Content-Type','')
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise MCPError('MCP 鉴权失败（401），检查 Token 是否有效。') from None
            if exc.code == 429:
                raise MCPError('MCP 触发限流（429），请稍后重试。') from None
            raise MCPError(f'MCP 请求失败：HTTP {exc.code}') from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise MCPError('无法连接官方 MCP 服务，请检查网络与服务状态。') from None
        if notification or not raw.strip():
            return {}
        if 'text/event-stream' in ctype or raw.startswith('event:') or raw.startswith('data:'):
            for line in reversed(raw.splitlines()):
                if line.startswith('data:'):
                    payload = line[5:].strip()
                    if payload != '[DONE]':
                        try:
                            obj = json.loads(payload)
                            if 'result' in obj or 'error' in obj:
                                return obj
                        except json.JSONDecodeError:
                            pass
            raise MCPError('收到 SSE 响应，但没有有效的 JSON-RPC 结果。')
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise MCPError('MCP 返回非 JSON 数据。') from None

    def rpc(self, method, params=None, notification=False):
        body = {'jsonrpc':'2.0','method':method}
        if not notification:
            body['id'] = self.next_id
            self.next_id += 1
        if params is not None:
            body['params'] = params
        result = self._transport(body, notification=notification)
        if 'error' in result:
            error = result['error']
            raise MCPError('MCP 返回错误：'+str(error.get('message','未知错误')))
        return result.get('result', {})

    def initialize(self):
        info = self.rpc('initialize', {'protocolVersion': PROTOCOL,
                        'capabilities': {}, 'clientInfo': {'name':'mcmealshake-nerissa','version':'0.2.0'}})
        self.rpc('notifications/initialized', notification=True)
        return info

    def list_tools(self):
        result = self.rpc('tools/list')
        tools = list(result.get('tools', []))
        cursor = result.get('nextCursor')
        while cursor:
            result = self.rpc('tools/list', {'cursor':cursor})
            tools.extend(result.get('tools', []))
            cursor = result.get('nextCursor')
        self.tools = {t['name']:t for t in tools}
        return tools

    def create_order(self, arguments, *, confirmed=False, max_total_fen=None):
        if not confirmed:
            raise MCPError('创建订单需要明确确认。')
        if type(max_total_fen) is not int or max_total_fen <= 0:
            raise MCPError('必须提供确认的总价上限（分）。')
        if not isinstance(arguments, dict):
            raise MCPError('订单参数必须是对象。')
        params = json.loads(json.dumps(arguments))
        if params.get('orderType') != 1 or params.get('beType') != 1:
            raise MCPError('当前下单入口仅支持到店自取。')
        if params.get('beCode') or not params.get('storeCode'):
            raise MCPError('自取需要门店编码且不得传 beCode。')
        items = params.get('items')
        if not isinstance(items, list) or not items:
            raise MCPError('订单餐品不能为空。')
        for item in items:
            if not isinstance(item, dict) or not item.get('productCode') or type(item.get('quantity')) is not int or item['quantity'] < 1:
                raise MCPError('餐品必须包含有效编码和正整数数量。')
        if not self.tools:
            self.list_tools()
        if 'create-order' not in self.tools:
            raise MCPError('官方 MCP 未提供 create-order。')
        allowed = self.tools.get('calculate-price', {}).get('inputSchema', {}).get('properties', {})
        quote = self.call('calculate-price', {k:v for k,v in params.items() if k in allowed})
        data = quote.get('structuredContent', {})
        if data.get('success') is not True or not isinstance(data.get('data'), dict):
            raise MCPError('未获得有效核价结果，禁止下单。')
        price = data['data'].get('price')
        if type(price) is not int or price < 0 or price > max_total_fen:
            raise MCPError('最新价格无效或超过已确认上限，请重新确认。')
        ways = {w.get('code') for w in data['data'].get('takeWayList', [])}
        if not params.get('takeWayCode') or params['takeWayCode'] not in ways:
            raise MCPError('取餐方式必须来自最新核价结果。')
        # Never automatically retry a creation request: an error can hide a successful order.
        result = self.rpc('tools/call', {'name':'create-order', 'arguments':params})
        if result.get('isError'):
            raise MCPError('创建订单返回错误；请先检查 App 订单，勿直接重复提交。')
        return result

    def call(self, name, arguments=None):
        if name not in READ_ONLY:
            raise MCPError('此版本禁止执行写入/领券/下单操作。')
        if not self.tools:
            self.list_tools()
        if name not in self.tools:
            raise MCPError(f'官方 MCP 未提供工具：{name}')
        result = self.rpc('tools/call', {'name':name, 'arguments':arguments or {}})
        if result.get('isError'):
            raise MCPError('工具调用失败：'+str(result.get('content',[]))[:250])
        return result


def safe_schema(tools):
    return [{'name':t['name'],'description':t.get('description',''),
             'inputSchema':t.get('inputSchema',{})} for t in tools if t['name'] in READ_ONLY]
