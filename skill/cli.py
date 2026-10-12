"""Connection discovery CLI. Never accepts a token as command-line argument."""
import argparse
import json
from .mcp_client import McDonaldMCP, MCPError, safe_schema, READ_ONLY

def main():
    parser = argparse.ArgumentParser(description='麦麦扭蛋：麦当劳 MCP 查询与确认下单')
    parser.add_argument('command', choices=['test','tools','schema','call','order','nutrition'])
    parser.add_argument('name', nargs='?')
    parser.add_argument('--args-file', help='工具参数 JSON 文件路径（不包含 Token）')
    parser.add_argument('--confirm-order', action='store_true', help='已明确确认门店、餐品、取餐方式和价格上限')
    parser.add_argument('--max-total-fen', type=int, help='确认的总价上限，单位分')
    args = parser.parse_args()
    try:
        client = McDonaldMCP()
        info = client.initialize()
        tools = client.list_tools()
        if args.command == 'test':
            print(json.dumps({'connected':True,'server':info.get('serverInfo',{}),
                              'read_only_tools':[t['name'] for t in tools if t['name'] in READ_ONLY]},ensure_ascii=False,indent=2))
        elif args.command == 'tools':
            print(json.dumps(safe_schema(tools),ensure_ascii=False,indent=2))
        elif args.command == 'schema':
            if args.name not in READ_ONLY | {'create-order'} or args.name not in client.tools:
                raise MCPError('该工具不可用或不在只读白名单内')
            print(json.dumps(client.tools[args.name].get('inputSchema',{}),ensure_ascii=False,indent=2))
        elif args.command == 'nutrition':
            if not args.args_file:
                raise MCPError('nutrition 需要 --args-file，包含 items 的具体份量名称、quantity 和可选 maxKcal')
            from .nutrition import estimate
            with open(args.args_file, encoding='utf-8') as f:
                request = json.load(f)
            print(json.dumps(estimate(client.call('list-nutrition-foods', {}), request), ensure_ascii=False, indent=2))
        elif args.command == 'order':
            if not args.args_file:
                raise MCPError('order 需要 --args-file')
            with open(args.args_file, encoding='utf-8') as f:
                params = json.load(f)
            print(json.dumps(client.create_order(params, confirmed=args.confirm_order, max_total_fen=args.max_total_fen), ensure_ascii=False, indent=2))
        elif args.command == 'call':
            if not args.name or not args.args_file:
                raise MCPError('call 需要工具名和 --args-file')
            with open(args.args_file,encoding='utf-8') as f:
                params=json.load(f)
            print(json.dumps(client.call(args.name,params),ensure_ascii=False,indent=2))
    except MCPError as exc:
        parser.exit(1, '连接失败：'+str(exc)+'\n')

if __name__ == '__main__':
    main()
