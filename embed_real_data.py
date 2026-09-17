#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将真实历史数据嵌入HTML应用，替换模拟数据"""

import json
import re

# 读取真实数据
with open('data/real_historical_data.json', 'r', encoding='utf-8') as f:
    real_data = json.load(f)

# 读取HTML
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 生成真实数据的JS代码
snapshots_js = json.dumps(real_data['snapshots'], ensure_ascii=False, indent=2)
stocks_js = json.dumps(real_data['limitUpStocks'], ensure_ascii=False, indent=2)

# 新的loadDemoData函数
new_function = f'''function loadDemoData() {{
  // 真实历史数据 - 数据来源：东方财富（券商级数据源）
  // 采集日期：2026-08-28 ~ 2026-09-16，共14个交易日
  const demoSnapshots = {snapshots_js};

  demoSnapshots.forEach(s => {{
    const idx = appData.snapshots.findIndex(x => x.date === s.date);
    if (idx >= 0) appData.snapshots[idx] = s;
    else appData.snapshots.push(s);
  }});

  // 重新计算阶段
  appData.snapshots.sort((a,b) => a.date.localeCompare(b.date));
  appData.snapshots.forEach((s, i) => {{
    s.stage = detectStage(s, s.temperature, i > 0 ? appData.snapshots[i-1] : null);
  }});

  // 真实涨停股票（最新交易日2026-09-16）
  appData.limitUpStocks = {stocks_js};

  saveData();
  renderAll();
  alert('真实历史数据已加载！\\n数据来源：东方财富\\n区间：2026-08-28 ~ 2026-09-16（14个交易日）\\n最新涨停：' + appData.limitUpStocks.length + '只');
}}'''

# 替换旧的loadDemoData函数（从function loadDemoData到下一个// ====分隔符之前）
pattern = r'function loadDemoData\(\) \{.*?\n\}'
html = re.sub(pattern, new_function, html, flags=re.DOTALL)

# 更新按钮文字
html = html.replace('加载示例数据', '加载真实历史数据')

# 写回HTML
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('真实数据已嵌入HTML！')
print(f'  快照数：{len(real_data["snapshots"])}')
print(f'  涨停股数：{len(real_data["limitUpStocks"])}')
print(f'  日期范围：{real_data["snapshots"][0]["date"]} ~ {real_data["snapshots"][-1]["date"]}')
