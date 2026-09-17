#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复HTML中alert多行字符串语法错误"""
import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 用正则匹配多行alert并替换为单行
pattern = r"alert\('真实历史数据已加载！.*?' \+ appData\.limitUpStocks\.length \+ '只'\);"
replacement = "alert('真实历史数据已加载！数据来源：东方财富，区间：2026-08-28 ~ 2026-09-16（14个交易日），最新涨停：' + appData.limitUpStocks.length + '只');"

new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
print(f"替换了 {count} 处")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("修复完成！")
