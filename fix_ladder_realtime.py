#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""让renderLadder优先使用实时股票数据"""
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = """function renderLadder() {
  const stocks = appData.limitUpStocks;
  document.getElementById('ladderDate').textContent = appData.snapshots.length ? appData.snapshots[appData.snapshots.length-1].date : '';"""

new = """function renderLadder() {
  const stocks = (appData.realtimeStocks && appData.realtimeStocks.length > 0) ? appData.realtimeStocks : appData.limitUpStocks;
  var dateEl = document.getElementById('ladderDate');
  dateEl.textContent = appData.snapshots.length ? appData.snapshots[appData.snapshots.length-1].date : '';
  if (appData.realtimeStocks && appData.realtimeStocks.length > 0) dateEl.textContent += ' · 📡实时';"""

if 'appData.realtimeStocks' in content:
    print("已修改，跳过")
else:
    content = content.replace(old, new, 1)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("renderLadder已更新为优先使用实时数据")
