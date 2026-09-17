#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入实时行情功能到 index.html（复用renderDashboard）"""

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

if 'realtimeBanner' in content:
    print("实时功能已存在，跳过")
    exit(0)

# 1. 在仪表盘模块开头插入实时数据横幅
banner_html = '''  <!-- 实时数据横幅 -->
  <div id="realtimeBanner" class="card p-3 mb-4 flex items-center justify-between" style="display:none;background:linear-gradient(135deg,rgba(59,130,246,.12),rgba(34,197,94,.08));border:1px solid rgba(59,130,246,.3)">
    <div class="flex items-center gap-3" style="align-items:center">
      <span id="rtDot" class="w-2.5 h-2.5 rounded-full" style="width:10px;height:10px;background:#22c55e;box-shadow:0 0 8px #22c55e;display:inline-block"></span>
      <div>
        <div class="text-sm font-semibold" style="color:var(--text)">📡 实时行情 <span id="rtStatus" class="tag" style="background:rgba(34,197,94,.15);color:#22c55e;font-size:11px">已连接</span></div>
        <div id="rtMeta" class="text-xs" style="color:var(--text3)">--</div>
      </div>
    </div>
    <button class="btn btn-primary text-xs" onclick="loadRealtimeData()" id="rtRefreshBtn">🔄 刷新实时数据</button>
  </div>

'''
content = content.replace(
    '<div id="mod-dashboard" class="module active">',
    '<div id="mod-dashboard" class="module active">\n' + banner_html,
    1
)

# 2. 注入JS函数
rt_js = '''
// ==================== V2.1: 实时行情 ====================
var realtimeData = null;

async function loadRealtimeData() {
  var btn = document.getElementById('rtRefreshBtn');
  var banner = document.getElementById('realtimeBanner');
  var status = document.getElementById('rtStatus');
  var meta = document.getElementById('rtMeta');
  if (!banner) return;
  if (!backendConfig.enabled) {
    banner.style.display = 'flex';
    if (status) { status.textContent = '未连接后端'; status.style.color = '#ef4444'; }
    if (meta) meta.textContent = '请先在「数据设置」中配置后端API并切换到后端模式';
    return;
  }
  if (btn) { btn.disabled = true; btn.textContent = '⏳ 获取中...'; }
  banner.style.display = 'flex';
  if (status) { status.textContent = '加载中'; status.style.color = '#eab308'; }

  try {
    var data = await apiRequest('/api/realtime', 'GET');
    realtimeData = data;
    // 更新横幅
    if (meta) meta.textContent = data.date + ' ' + data.time + ' · ' + data.marketStatus +
      ' · 涨停' + data.limitUp + '家 跌停' + data.limitDown + '家 温度' + data.temperature + '°';
    if (status) {
      status.textContent = data.marketStatus;
      status.style.color = data.isTrading ? '#22c55e' : '#f59e0b';
      status.style.background = data.isTrading ? 'rgba(34,197,94,.15)' : 'rgba(245,158,11,.15)';
    }
    var dot = document.getElementById('rtDot');
    if (dot) {
      dot.style.background = data.isTrading ? '#22c55e' : '#f59e0b';
      dot.style.boxShadow = data.isTrading ? '0 0 8px #22c55e' : '0 0 8px #f59e0b';
    }
    // 把实时数据upsert到appData.snapshots作为今日快照，复用现有渲染
    var today = data.date;
    var idx = appData.snapshots.findIndex(function(s){ return s.date === today; });
    var snapData = {
      date: today,
      limitUp: data.limitUp, limitDown: data.limitDown,
      upCount: data.upCount, downCount: data.downCount,
      redRate: data.redRate, sealRate: data.sealRate,
      promoteRate: data.promoteRate, firstPromote: data.promoteRate * 0.8,
      maxBoard: data.maxBoard, everLimit: data.everLimit, sealed: data.sealed,
      temperature: data.temperature, stage: data.stage,
      isRealtime: true
    };
    if (idx >= 0) {
      appData.snapshots[idx] = Object.assign(appData.snapshots[idx], snapData);
    } else {
      appData.snapshots.push(snapData);
    }
    // 实时涨停股存入appData.limitUpStocks
    appData.realtimeStocks = data.stocks || [];
    // 重新渲染仪表盘和涨停梯队
    renderDashboard();
    renderLadder();
    if (btn) { btn.disabled = false; btn.textContent = '🔄 刷新实时数据'; }
    console.log('实时数据加载成功', data.limitUp, '只涨停, 温度', data.temperature);
  } catch (e) {
    if (status) { status.textContent = '获取失败'; status.style.color = '#ef4444'; }
    if (meta) meta.textContent = '错误: ' + e.message;
    if (btn) { btn.disabled = false; btn.textContent = '🔄 重试'; }
  }
}

// 交易时段每30秒自动刷新
var rtTimer = null;
function startRealtimeAutoRefresh() {
  if (rtTimer) clearInterval(rtTimer);
  rtTimer = setInterval(function() {
    if (currentTab === 'dashboard' && backendConfig.enabled) {
      loadRealtimeData();
    }
  }, 30000);
}
'''
content = content.replace(
    '// ==================== V2.0: 后端服务对接 ====================',
    rt_js + '\n// ==================== V2.0: 后端服务对接 ====================',
    1
)

# 3. 自动连接成功后自动加载实时数据
old_auto = "    setTimeout(function() { syncFromBackend(true); }, 500);"
new_auto = "    setTimeout(function() { syncFromBackend(true); }, 500);\n    setTimeout(function() { loadRealtimeData(); startRealtimeAutoRefresh(); }, 1500);"
content = content.replace(old_auto, new_auto, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("实时行情功能注入成功！")
