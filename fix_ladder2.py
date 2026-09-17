#!/usr/bin/env python3
# -*- coding: utf-8 -*-
with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 第2863行(index 2862)
for i in range(2860, 2868):
    if 'const stocks = appData.limitUpStocks;' in lines[i]:
        lines[i] = lines[i].replace(
            'const stocks = appData.limitUpStocks;',
            "const stocks = (appData.realtimeStocks && appData.realtimeStocks.length > 0) ? appData.realtimeStocks : appData.limitUpStocks;"
        )
        print(f"已修改第{i+1}行")
        break

with open('index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("完成")
