#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1.2 功能注入脚本：交易日志、盈亏统计、多周期对比、情绪温度预测"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ========== 1. 版本号更新 ==========
html = html.replace('Emotion Cycle Screener v1.1', 'Emotion Cycle Screener v1.2')

# ========== 2. 新增CSS样式 ==========
new_css = '''
  /* V1.2 新增样式 */
  .trade-form-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }
  .trade-tag-buy { background: rgba(239,68,68,.15); color: #ef4444; }
  .trade-tag-sell { background: rgba(34,197,94,.15); color: #22c55e; }
  .pnl-positive { color: #ef4444; }
  .pnl-negative { color: #22c55e; }
  .predict-bar { display: flex; align-items: flex-end; gap: 4px; height: 120px; padding: 10px 0; }
  .predict-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
  .predict-col .bar { width: 100%; max-width: 40px; border-radius: 4px 4px 0 0; position: relative; }
  .predict-col .label { font-size: 11px; color: var(--text3); }
  .predict-col .val { font-size: 12px; font-weight: 700; }
  .cycle-compare-item { background: var(--card2); border: 1px solid var(--border); border-radius: 8px; padding: 12px; cursor: pointer; transition: all .2s; }
  .cycle-compare-item:hover { border-color: var(--blue); }
  .cycle-compare-item.selected { border-color: var(--blue); background: rgba(59,130,246,.1); }
  .stat-mini { font-size: 11px; color: var(--text3); }
'''
html = html.replace('</style>', new_css + '\n</style>')

# ========== 3. 新增交易日志标签页按钮 ==========
new_tab = '''  <div class="tab-btn" onclick="switchTab('trade')">💰 交易日志</div>
'''
html = html.replace(
    "  <div class=\"tab-btn\" onclick=\"switchTab('settings')\">⚙️ 数据设置</div>",
    new_tab + "  <div class=\"tab-btn\" onclick=\"switchTab('settings')\">⚙️ 数据设置</div>"
)

# ========== 4. 历史周期模块增加：多周期对比 + 情绪温度预测 ==========
# 在"规律总结"卡片前插入两个新卡片
v12_history = '''  <!-- V1.2: 情绪温度预测 -->
  <div class="card p-5 mt-4">
    <div class="flex items-center justify-between mb-4">
      <div class="stat-label text-base font-semibold" style="color:var(--text)">🔮 情绪温度预测（未来5日）</div>
      <button class="btn btn-primary text-xs" onclick="runTemperaturePrediction()">开始预测</button>
    </div>
    <div id="predictionResult">
      <div class="text-center py-8 text-xs" style="color:var(--text3)">点击"开始预测"，基于历史温度规律预测未来5日情绪温度区间</div>
    </div>
  </div>

  <!-- V1.2: 多周期对比 -->
  <div class="card p-5 mt-4">
    <div class="stat-label text-base font-semibold mb-4" style="color:var(--text)">⚖️ 多周期对比（本轮 vs 历史相似周期）</div>
    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-3">
        <div class="text-xs font-semibold mb-2" style="color:var(--text2)">识别到的周期段</div>
        <div id="cycleList" class="space-y-2 overflow-y-auto scrollbar" style="max-height:350px">
          <div class="text-center py-4 text-xs" style="color:var(--text3)">暂无足够数据</div>
        </div>
      </div>
      <div class="col-span-9">
        <div class="flex items-center justify-between mb-3">
          <div class="text-xs font-semibold" style="color:var(--text2)">对比结果（选择左侧两个周期）</div>
          <button class="btn btn-ghost text-xs" onclick="clearCycleSelection()">清除选择</button>
        </div>
        <div id="cycleCompareResult">
          <div class="text-center py-10 text-xs" style="color:var(--text3)">点击左侧周期段进行选择，最多选2个进行对比</div>
        </div>
      </div>
    </div>
  </div>

'''
html = html.replace(
    '  <!-- 规律总结 -->',
    v12_history + '  <!-- 规律总结 -->'
)

# ========== 5. 新增交易日志模块（在数据设置模块前） ==========
trade_module = '''<!-- ==================== 模块V1.2: 交易日志 ==================== -->
<div id="mod-trade" class="module">
  <div class="grid grid-cols-12 gap-4">
    <!-- 交易录入表单 -->
    <div class="card p-5 col-span-5">
      <div class="stat-label text-base font-semibold mb-4" style="color:var(--text)">📝 记录交易</div>
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs" style="color:var(--text2)">日期</label>
            <input type="date" class="input-field mt-1" id="tradeDate">
          </div>
          <div>
            <label class="text-xs" style="color:var(--text2)">操作类型</label>
            <select class="input-field mt-1" id="tradeType">
              <option value="buy">买入</option>
              <option value="sell">卖出</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs" style="color:var(--text2)">股票代码</label>
            <input type="text" class="input-field mt-1" id="tradeCode" placeholder="如 000001">
          </div>
          <div>
            <label class="text-xs" style="color:var(--text2)">股票名称</label>
            <input type="text" class="input-field mt-1" id="tradeName" placeholder="如 平安银行">
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="text-xs" style="color:var(--text2)">价格(元)</label>
            <input type="number" step="0.01" class="input-field mt-1" id="tradePrice">
          </div>
          <div>
            <label class="text-xs" style="color:var(--text2)">数量(股)</label>
            <input type="number" step="100" class="input-field mt-1" id="tradeQty">
          </div>
          <div>
            <label class="text-xs" style="color:var(--text2)">手续费(元)</label>
            <input type="number" step="0.01" class="input-field mt-1" id="tradeFee" value="0">
          </div>
        </div>
        <div>
          <label class="text-xs" style="color:var(--text2)">备注</label>
          <input type="text" class="input-field mt-1" id="tradeNote" placeholder="操作理由、情绪阶段判断等">
        </div>
        <div class="card2 p-3 text-xs" style="color:var(--text3)">
          <span id="tradeStageHint">选择日期后自动关联当日情绪阶段</span>
        </div>
        <button class="btn btn-primary w-full" onclick="addTrade()">💾 保存交易记录</button>
      </div>
    </div>

    <!-- 盈亏统计 -->
    <div class="card p-5 col-span-7">
      <div class="stat-label text-base font-semibold mb-4" style="color:var(--text)">📊 盈亏统计</div>
      <div id="pnlSummary">
        <div class="text-center py-10 text-xs" style="color:var(--text3)">暂无交易记录</div>
      </div>
    </div>
  </div>

  <!-- 交易记录列表 -->
  <div class="card p-5 mt-4">
    <div class="flex items-center justify-between mb-4">
      <div class="stat-label text-base font-semibold" style="color:var(--text)">📋 交易记录</div>
      <div class="flex gap-2 items-center">
        <select class="input-field text-xs" style="width:120px" id="tradeFilter" onchange="renderTradeList()">
          <option value="all">全部</option>
          <option value="buy">仅买入</option>
          <option value="sell">仅卖出</option>
        </select>
        <button class="btn btn-danger text-xs" onclick="clearAllTrades()">清空全部</button>
      </div>
    </div>
    <div class="overflow-x-auto scrollbar" style="max-height:400px">
      <table>
        <thead>
          <tr><th>日期</th><th>类型</th><th>代码</th><th>名称</th><th>价格</th><th>数量</th><th>金额</th><th>手续费</th><th>情绪阶段</th><th>备注</th><th>操作</th></tr>
        </thead>
        <tbody id="tradeList">
          <tr><td colspan="11" class="text-center py-8" style="color:var(--text3)">暂无交易记录</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

'''
html = html.replace(
    '<!-- ==================== 模块6: 数据设置 ==================== -->',
    trade_module + '<!-- ==================== 模块6: 数据设置 ==================== -->'
)

# ========== 6. renderAll中增加交易日志渲染 ==========
html = html.replace(
    'function renderAll() {\n  renderDashboard();\n  renderLadder();\n  renderSectorHeat();',
    'function renderAll() {\n  renderDashboard();\n  renderLadder();\n  renderSectorHeat();\n  renderTradeList();\n  renderPnlSummary();\n  renderCycleList();'
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("V1.2 HTML结构注入完成！")
print("  - 版本号更新为 v1.2")
print("  - 新增CSS样式")
print("  - 新增交易日志标签页和模块")
print("  - 历史周期增加情绪温度预测和多周期对比")
print("  - renderAll增加交易日志、盈亏统计、周期列表渲染")
