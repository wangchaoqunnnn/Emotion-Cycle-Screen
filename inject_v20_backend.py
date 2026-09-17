#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2.0 前端后端模式对接 - 注入后端设置UI和API通信JS"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ========== 1. 在数据设置模块增加后端设置卡片 ==========
backend_settings_html = '''
    <!-- V2.0: 后端服务设置 -->
    <div class="card p-5 col-span-6">
      <div class="stat-label text-base font-semibold mb-4" style="color:var(--text)">🔌 后端服务设置（V2.0）</div>
      <div class="space-y-3">
        <div class="card2 p-3">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-semibold">当前模式</span>
            <span id="backendModeBadge" class="tag" style="background:rgba(59,130,246,.15);color:var(--blue)">本地模式</span>
          </div>
          <div class="text-xs" style="color:var(--text3)">本地模式：数据存储在浏览器localStorage；后端模式：数据通过API同步到服务器，支持多设备访问</div>
        </div>
        <div>
          <label class="text-xs" style="color:var(--text2)">后端API地址</label>
          <input type="text" class="input-field mt-1" id="backendUrl" placeholder="http://127.0.0.1:5000" value="http://127.0.0.1:5000">
        </div>
        <div>
          <label class="text-xs" style="color:var(--text2)">API Key</label>
          <input type="password" class="input-field mt-1" id="backendApiKey" placeholder="输入你的API Key">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <button class="btn btn-ghost text-xs" onclick="testBackendConnection()">🔍 测试连接</button>
          <button class="btn btn-primary text-xs" onclick="toggleBackendMode()">🔄 切换模式</button>
        </div>
        <div id="backendStatus" class="text-xs" style="color:var(--text3)"></div>
        <div class="card2 p-3">
          <div class="text-xs font-semibold mb-2" style="color:var(--text2)">数据同步</div>
          <div class="grid grid-cols-2 gap-2">
            <button class="btn btn-ghost text-xs" onclick="syncToBackend()">⬆️ 上传到后端</button>
            <button class="btn btn-ghost text-xs" onclick="syncFromBackend()">⬇️ 从后端拉取</button>
          </div>
        </div>
        <div class="text-xs" style="color:var(--text3)">
          💡 启动后端：<code>python server.py</code>，然后注册用户获取API Key
        </div>
      </div>
    </div>
'''

# 在数据设置的第二个卡片（权重设置）后插入
html = html.replace(
    '    <!-- 数据导入导出 -->',
    backend_settings_html + '\n    <!-- 数据导入导出 -->'
)

# ========== 2. 注入后端模式JavaScript ==========
backend_js = r'''
// ==================== V2.0: 后端服务对接 ====================
var BACKEND_CONFIG_KEY = 'emotion_screener_backend_config';
var backendConfig = { enabled: false, url: 'http://127.0.0.1:5000', apiKey: '' };

function loadBackendConfig() {
  try {
    var saved = localStorage.getItem(BACKEND_CONFIG_KEY);
    if (saved) backendConfig = JSON.parse(saved);
  } catch(e) { console.error('加载后端配置失败', e); }
  var urlEl = document.getElementById('backendUrl');
  var keyEl = document.getElementById('backendApiKey');
  var badgeEl = document.getElementById('backendModeBadge');
  if (urlEl) urlEl.value = backendConfig.url;
  if (keyEl) keyEl.value = backendConfig.apiKey;
  if (badgeEl) {
    badgeEl.textContent = backendConfig.enabled ? '后端模式' : '本地模式';
    badgeEl.style.background = backendConfig.enabled ? 'rgba(34,197,94,.15)' : 'rgba(59,130,246,.15)';
    badgeEl.style.color = backendConfig.enabled ? '#22c55e' : 'var(--blue)';
  }
}

function saveBackendConfig() {
  backendConfig.url = document.getElementById('backendUrl')?.value || 'http://127.0.0.1:5000';
  backendConfig.apiKey = document.getElementById('backendApiKey')?.value || '';
  localStorage.setItem(BACKEND_CONFIG_KEY, JSON.stringify(backendConfig));
}

function apiRequest(path, method, data) {
  return new Promise(function(resolve, reject) {
    var url = backendConfig.url.replace(/\/$/, '') + path;
    var opts = {
      method: method || 'GET',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': backendConfig.apiKey }
    };
    if (data) opts.body = JSON.stringify(data);
    fetch(url, opts).then(function(r) {
      return r.json().then(function(j) { return { status: r.status, data: j }; });
    }).then(function(result) {
      if (result.status >= 400) reject(result.data);
      else resolve(result.data);
    }).catch(reject);
  });
}

function testBackendConnection() {
  saveBackendConfig();
  var statusEl = document.getElementById('backendStatus');
  statusEl.textContent = '正在测试连接...';
  statusEl.style.color = 'var(--text3)';
  fetch(backendConfig.url.replace(/\/$/, '') + '/api/health')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.status === 'ok') {
        statusEl.innerHTML = '✅ 连接成功！服务版本: ' + data.version;
        statusEl.style.color = '#22c55e';
      } else {
        statusEl.textContent = '❌ 连接失败: ' + JSON.stringify(data);
        statusEl.style.color = '#ef4444';
      }
    })
    .catch(function(e) {
      statusEl.textContent = '❌ 无法连接: ' + e.message;
      statusEl.style.color = '#ef4444';
    });
}

function toggleBackendMode() {
  saveBackendConfig();
  if (!backendConfig.apiKey) {
    alert('请先输入API Key');
    return;
  }
  backendConfig.enabled = !backendConfig.enabled;
  saveBackendConfig();
  loadBackendConfig();
  if (backendConfig.enabled) {
    alert('已切换到后端模式\n正在从后端拉取数据...');
    syncFromBackend();
  } else {
    alert('已切换到本地模式\n数据将存储在浏览器中');
    renderAll();
  }
}

function syncToBackend() {
  if (!backendConfig.apiKey) { alert('请先输入API Key'); return; }
  var statusEl = document.getElementById('backendStatus');
  statusEl.textContent = '正在上传数据到后端...';
  statusEl.style.color = 'var(--text3)';

  Promise.all([
    apiRequest('/api/snapshots/batch', 'POST', { snapshots: appData.snapshots }),
    apiRequest('/api/stocks', 'POST', { stocks: appData.limitUpStocks, date: appData.snapshots.length ? appData.snapshots[appData.snapshots.length-1].date : new Date().toISOString().split('T')[0] }),
  ]).then(function(results) {
    // 上传交易记录
    var promises = (appData.trades || []).map(function(t) {
      return apiRequest('/api/trades', 'POST', t).catch(function() {});
    });
    return Promise.all(promises).then(function() { return results; });
  }).then(function() {
    statusEl.innerHTML = '✅ 数据上传成功！快照: ' + appData.snapshots.length + '条, 股票: ' + appData.limitUpStocks.length + '只, 交易: ' + (appData.trades||[]).length + '笔';
    statusEl.style.color = '#22c55e';
  }).catch(function(e) {
    statusEl.textContent = '❌ 上传失败: ' + (e.error || e.message || JSON.stringify(e));
    statusEl.style.color = '#ef4444';
  });
}

function syncFromBackend() {
  if (!backendConfig.apiKey) { alert('请先输入API Key'); return; }
  var statusEl = document.getElementById('backendStatus');
  statusEl.textContent = '正在从后端拉取数据...';
  statusEl.style.color = 'var(--text3)';

  Promise.all([
    apiRequest('/api/snapshots', 'GET'),
    apiRequest('/api/stocks', 'GET'),
    apiRequest('/api/trades', 'GET'),
  ]).then(function(results) {
    appData.snapshots = results[0] || [];
    // 股票只取最新日期的
    var stocks = results[1] || [];
    if (stocks.length > 0) {
      var latestDate = stocks[0].date;
      appData.limitUpStocks = stocks.filter(function(s) { return s.date === latestDate; });
    } else {
      appData.limitUpStocks = [];
    }
    appData.trades = results[2] || [];
    saveData();
    renderAll();
    statusEl.innerHTML = '✅ 数据拉取成功！快照: ' + appData.snapshots.length + '条, 股票: ' + appData.limitUpStocks.length + '只, 交易: ' + appData.trades.length + '笔';
    statusEl.style.color = '#22c55e';
  }).catch(function(e) {
    statusEl.textContent = '❌ 拉取失败: ' + (e.error || e.message || JSON.stringify(e));
    statusEl.style.color = '#ef4444';
  });
}
'''

# 在V1.2 JS函数后、启动代码前插入
html = html.replace(
    '// 启动（V1.2增强）',
    backend_js + '\n// 启动（V1.2增强）'
)

# 在启动代码中增加loadBackendConfig调用
html = html.replace(
    "  initTradeForm();\n  var tradeDateEl = document.getElementById('tradeDate');",
    "  initTradeForm();\n  loadBackendConfig();\n  var tradeDateEl = document.getElementById('tradeDate');"
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("前端后端模式对接注入完成！")
print("  - 数据设置增加后端服务设置卡片")
print("  - API通信函数: apiRequest / testBackendConnection")
print("  - 模式切换: toggleBackendMode")
print("  - 数据同步: syncToBackend / syncFromBackend")
print("  - 启动时自动加载后端配置")
