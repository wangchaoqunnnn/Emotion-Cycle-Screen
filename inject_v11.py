#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1.1 功能注入脚本：板块热度、个股详情弹窗、自定义选股条件保存"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ========== 1. 版本号更新 ==========
html = html.replace('Emotion Cycle Screener v1.0', 'Emotion Cycle Screener v1.1')

# ========== 2. 新增CSS样式 ==========
new_css = '''
  /* V1.1 新增样式 */
  .modal-overlay { position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,.7); z-index: 1000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
  .modal-box { background: var(--card); border: 1px solid var(--border); border-radius: 16px; width: 560px; max-height: 85vh; overflow-y: auto; scrollbar-width: thin; }
  .modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
  .modal-body { padding: 20px; }
  .modal-close { width: 32px; height: 32px; border-radius: 50%; background: var(--card2); border: none; color: var(--text2); cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; }
  .modal-close:hover { color: var(--text); background: var(--border); }
  .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .detail-item { background: var(--card2); border-radius: 8px; padding: 12px; }
  .detail-label { font-size: 11px; color: var(--text3); margin-bottom: 4px; }
  .detail-value { font-size: 16px; font-weight: 700; }
  .sector-bar { height: 24px; border-radius: 4px; display: flex; align-items: center; padding: 0 10px; font-size: 12px; font-weight: 600; color: #fff; cursor: pointer; transition: opacity .2s; position: relative; overflow: hidden; }
  .sector-bar:hover { opacity: .85; }
  .sector-bar .sector-count { position: absolute; right: 10px; }
  .saved-condition { background: var(--card2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .saved-condition:hover { border-color: var(--blue); }
  .risk-badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 6px; }
'''
html = html.replace('</style>', new_css + '\n</style>')

# ========== 3. 新增标签页按钮（在涨停梯队后） ==========
new_tab = '''  <div class="tab-btn" onclick="switchTab('sector')">🔥 板块热度</div>
'''
html = html.replace(
    "  <div class=\"tab-btn\" onclick=\"switchTab('screener')\">🎯 选股中心</div>",
    new_tab + "  <div class=\"tab-btn\" onclick=\"switchTab('screener')\">🎯 选股中心</div>"
)

# ========== 4. 新增板块热度模块HTML（在选股中心模块前） ==========
sector_module = '''<!-- ==================== 模块V1.1: 板块热度 ==================== -->
<div id="mod-sector" class="module">
  <div class="grid grid-cols-12 gap-4">
    <!-- 板块热度排行 -->
    <div class="card p-5 col-span-8">
      <div class="flex items-center justify-between mb-4">
        <div class="stat-label text-base font-semibold" style="color:var(--text)">🔥 概念板块涨停分布</div>
        <div class="flex items-center gap-2">
          <span class="text-xs" style="color:var(--text3)">数据日期：<span id="sectorDate">--</span></span>
          <select class="input-field text-xs" style="width:100px" id="sectorSort" onchange="renderSectorHeat()">
            <option value="count">按涨停数</option>
            <option value="amount">按成交额</option>
            <option value="maxBoard">按最高连板</option>
          </select>
        </div>
      </div>
      <div id="sectorHeatList" class="space-y-2">
        <div class="text-center py-10" style="color:var(--text3)">暂无数据，请先加载涨停股票数据</div>
      </div>
    </div>

    <!-- 板块详情 -->
    <div class="card p-5 col-span-4">
      <div class="stat-label text-base font-semibold mb-3" style="color:var(--text)">📋 板块详情</div>
      <div id="sectorDetail">
        <div class="text-center py-10 text-xs" style="color:var(--text3)">点击左侧板块查看详情</div>
      </div>
    </div>
  </div>

  <!-- 板块涨停股票 -->
  <div class="card p-5 mt-4">
    <div class="flex items-center justify-between mb-3">
      <div class="stat-label text-base font-semibold" style="color:var(--text)">📊 板块涨停股票 <span id="sectorStockCount" class="text-xs ml-2" style="color:var(--text3)"></span></div>
    </div>
    <div class="overflow-x-auto scrollbar" style="max-height:400px">
      <table>
        <thead><tr><th>代码</th><th>名称</th><th>连板</th><th>现价</th><th>涨跌幅</th><th>换手率</th><th>成交额(亿)</th><th>所属概念</th></tr></thead>
        <tbody id="sectorStockTable">
          <tr><td colspan="8" class="text-center py-8" style="color:var(--text3)">选择板块后显示</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

'''
html = html.replace(
    '<!-- ==================== 模块3: 选股中心 ==================== -->',
    sector_module + '<!-- ==================== 模块3: 选股中心 ==================== -->'
)

# ========== 5. 选股中心增加保存条件UI ==========
old_screen_btn = '''      <button class="btn btn-primary text-xs" onclick="runScreening()">开始选股</button>'''
new_screen_btn = '''      <div class="flex gap-2">
        <button class="btn btn-ghost text-xs" onclick="saveScreenCondition()">💾 保存条件</button>
        <button class="btn btn-primary text-xs" onclick="runScreening()">开始选股</button>
      </div>'''
html = html.replace(old_screen_btn, new_screen_btn)

# 在选股结果卡片前增加已保存条件列表
old_result_card = '''  <!-- 选股结果 -->
  <div class="card p-5">'''
new_result_card = '''  <!-- 已保存条件 -->
  <div class="card p-5 mb-4" id="savedConditionsCard" style="display:none">
    <div class="flex items-center justify-between mb-3">
      <div class="stat-label text-base font-semibold" style="color:var(--text)">📁 已保存选股条件</div>
      <button class="btn btn-ghost text-xs" onclick="clearAllSavedConditions()">清空全部</button>
    </div>
    <div id="savedConditionsList"></div>
  </div>

  <!-- 选股结果 -->
  <div class="card p-5">'''
html = html.replace(old_result_card, new_result_card)

# ========== 6. 个股详情弹窗Modal（在</body>前） ==========
modal_html = '''
<!-- 个股详情弹窗 -->
<div id="stockDetailModal" class="modal-overlay" style="display:none" onclick="if(event.target===this)closeStockDetail()">
  <div class="modal-box">
    <div class="modal-header">
      <div class="flex items-center gap-3">
        <span id="detailStockName" class="text-lg font-bold">--</span>
        <span id="detailStockCode" class="text-sm font-mono" style="color:var(--text3)">--</span>
        <span id="detailStockBoard" class="tag">--</span>
      </div>
      <button class="modal-close" onclick="closeStockDetail()">✕</button>
    </div>
    <div class="modal-body">
      <!-- 核心行情 -->
      <div class="detail-grid mb-4">
        <div class="detail-item">
          <div class="detail-label">最新价</div>
          <div class="detail-value" id="detailPrice" style="color:var(--red)">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">涨跌幅</div>
          <div class="detail-value" id="detailChange" style="color:var(--red)">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">换手率</div>
          <div class="detail-value" id="detailTurnover">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">成交额</div>
          <div class="detail-value" id="detailAmount">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">封单金额(万)</div>
          <div class="detail-value" id="detailSeal">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">量比</div>
          <div class="detail-value" id="detailVolumeRatio">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">主力净流入(万)</div>
          <div class="detail-value" id="detailInflow">--</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">流通市值(亿)</div>
          <div class="detail-value" id="detailMarketCap">--</div>
        </div>
      </div>

      <!-- 所属概念 -->
      <div class="card2 p-3 mb-4">
        <div class="detail-label mb-2">所属概念</div>
        <div id="detailConcept" class="flex flex-wrap gap-1">--</div>
      </div>

      <!-- 风险评估 -->
      <div class="card2 p-3">
        <div class="detail-label mb-2">⚠️ 风险评估</div>
        <div id="detailRisk" class="space-y-1">--</div>
      </div>
    </div>
  </div>
</div>
'''
html = html.replace('</body>', modal_html + '\n</body>')

# ========== 7. 明细表行增加点击事件 ==========
html = html.replace(
    "    return `<tr>\n      <td class=\"font-mono\">${s.code}</td>",
    "    return `<tr style=\"cursor:pointer\" onclick=\"showStockDetail('${s.code}')\">\n      <td class=\"font-mono\">${s.code}</td>"
)

# 选股结果表行也增加点击
html = html.replace(
    "`<tr><td>${s.score}</td>",
    "`<tr style=\"cursor:pointer\" onclick=\"showStockDetail('${s.code}')\"><td>${s.score}</td>"
)

# ========== 8. 在renderAll中增加板块热度渲染 ==========
html = html.replace(
    'function renderAll() {\n  renderDashboard();\n  renderLadder();',
    'function renderAll() {\n  renderDashboard();\n  renderLadder();\n  renderSectorHeat();'
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML结构注入完成！")
print("  - 版本号更新为 v1.1")
print("  - 新增CSS样式")
print("  - 新增板块热度标签页和模块")
print("  - 选股中心增加保存条件UI")
print("  - 新增个股详情弹窗Modal")
print("  - 明细表行增加点击事件")
print("  - renderAll增加板块热度渲染")
