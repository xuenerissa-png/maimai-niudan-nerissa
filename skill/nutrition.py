"""Portion-specific estimates from the official nutrition response."""
import csv
import math
import re
import unicodedata
from .mcp_client import MCPError


def normalized(name):
    return re.sub(r'[\s\-－—]', '', unicodedata.normalize('NFKC', name))


def parse_foods(response):
    structured = response.get('structuredContent', {})
    if structured.get('success') is not True:
        raise MCPError('未获得有效官方营养数据。')
    raw = structured.get('data')
    if not isinstance(raw, str):
        raise MCPError('官方营养格式变化，需要更新适配。')
    lines = raw.strip().splitlines()
    header = re.fullmatch(r'\[(\d+)\]\{([^}]+)\}:', lines[0]) if lines else None
    if not header:
        raise MCPError('无法识别官方营养表。')
    fields = header.group(2).split(',')
    rows = list(csv.reader([line.strip() for line in lines[1:]]))
    if len(rows) != int(header.group(1)):
        raise MCPError('官方营养表不完整。')
    index = {}
    for row in rows:
        if len(row) != len(fields):
            raise MCPError('营养数据列数不符。')
        record = dict(zip(fields, row))
        try:
            kcal = float(record['energyKcal'])
        except (ValueError, KeyError):
            raise MCPError('营养热量字段无效。') from None
        if not math.isfinite(kcal) or kcal < 0:
            raise MCPError('营养热量数值无效。')
        key = normalized(record['productName'])
        index.setdefault(key, []).append({'name':record['productName'], 'kcal':kcal})
    return index


def estimate(response, request):
    foods = parse_foods(response)
    items = request.get('items')
    limit = request.get('maxKcal')
    if limit is not None and (type(limit) not in (int,float) or not math.isfinite(limit) or limit <= 0):
        raise MCPError('单餐热量上限必须是正数（千卡）。')
    if not isinstance(items, list) or not items:
        raise MCPError('请提供餐品及份数。')
    results, known = [], 0
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not item['name'].strip() or type(item.get('quantity')) is not int or item['quantity'] < 1:
            raise MCPError('每项需要具体份量名称和正整数份数。')
        matches = foods.get(normalized(item['name']), [])
        calories = {m['kcal'] for m in matches}
        if len(calories) != 1 or item.get('modified') or item.get('modification'):
            results.append({'name':item['name'],'quantity':item['quantity'],'kcal':None,'reason':'特调、份量未匹配或官方数据缺失/冲突'})
            continue
        value = matches[0]['kcal'] * item['quantity']
        known += value
        results.append({'name':item['name'],'officialPortion':matches[0]['name'],'quantity':item['quantity'],'kcal':value})
    complete = all(i['kcal'] is not None for i in results)
    return {'source':'麦当劳官方 list-nutrition-foods', 'unit':'kcal', 'items':results,
            'complete':complete,'knownKcal':known,'totalKcal':known if complete else None,
            'maxKcal':limit,'withinTarget':(known <= limit) if complete and limit is not None else None,
            'note':'按官方列示标准份量估算；实际制作有差异。未知项不按0计算，套餐需拆成实际子项，特调不能沿用标准值。'}
