#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入V1.1 JavaScript功能函数"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_functions = r'''
// ==================== V1.1: 板块热度分析 ====================
function renderSectorHeat() {
  const stocks = appData.limitUpStocks;
  const dateEl = document.getElementById('sectorDate');
  if (dateEl) dateEl.textContent = appData.snapshots.length ? appData.snapshots[appData.snapshots.length-1].date : '--';

  if (!stocks || stocks.length === 0) {
    document.getElementById('sectorHeatList').innerHTML = '<div class="text-center py-10" style="color:var(--text3)">暂无数据，请先加载涨停股票数据</div>';
    return;
  }

  const sectorMap = {};
  stocks.forEach(s => {
    const concepts = (s.concept || '其他').split(/[,，、]/).map(c => c.trim()).filter(c => c);
    concepts.forEach(c => {
      if (!sectorMap[c]) sectorMap[c] = { name: c, stocks: [], count: 0, amount: 0, maxBoard: 0 };
      sectorMap[c].stocks.push(s);
      sectorMap[c].count++;
      sectorMap[c].amount += (s.amount || 0);
      sectorMap[c].maxBoard = Math.max(sectorMap[c].maxBoard, s.board || 1);
    });
  });

  const sectors = Object.values(sectorMap);
  const sortBy = document.getElementById('sectorSort')?.value || 'count';
  sectors.sort((a, b) => b[sortBy] - a[sortBy]);

  const maxCount = sectors[0]?.count || 1;
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899'];

  document.getElementById('sectorHeatList').innerHTML = sectors.slice(0, 30).map((sec, i) => {
    const width = Math.max(15, (sec.count / maxCount) * 100);
    const color = colors[i % colors.length];
    const safeName = sec.name.replace(/'/g, "\\'");
    return '<div class="sector-bar" style="width:' + width + '%;background:linear-gradient(90deg,' + color + 'cc,' + color + ')" onclick="showSectorDetail(\'' + safeName + '\')">' +
      '<span>' + sec.name + '</span>' +
      '<span class="sector-count">' + sec.count + '只 · 最高' + sec.maxBoard + '板</span>' +
    '</div>';
  }).join('');
}

function showSectorDetail(sectorName) {
  const stocks = appData.limitUpStocks.filter(s => {
    const concepts = (s.concept || '').split(/[,，、]/).map(c => c.trim());
    return concepts.includes(sectorName);
  });

  const totalAmount = stocks.reduce((sum, s) => sum + (s.amount || 0), 0);
  const avgBoard = stocks.reduce((sum, s) => sum + (s.board || 1), 0) / stocks.length;
  const maxBoard = Math.max(...stocks.map(s => s.board || 1));

  document.getElementById('sectorDetail').innerHTML =
    '<div class="card2 p-3 mb-3">' +
      '<div class="text-lg font-bold mb-2" style="color:var(--warm)">' + sectorName + '</div>' +
      '<div class="grid grid-cols-2 gap-2 text-sm">' +
        '<div><span style="color:var(--text3)">涨停数：</span><span class="font-bold" style="color:var(--red)">' + stocks.length + '</span></div>' +
        '<div><span style="color:var(--text3)">最高连板：</span><span class="font-bold">' + maxBoard + '板</span></div>' +
        '<div><span style="color:var(--text3)">平均连板：</span><span class="font-bold">' + avgBoard.toFixed(1) + '板</span></div>' +
        '<div><span style="color:var(--text3)">总成交额：</span><span class="font-bold">' + totalAmount.toFixed(2) + '亿</span></div>' +
      '</div>' +
    '</div>' +
    '<div class="text-xs" style="color:var(--text3)">板块内涨停股：</div>' +
    '<div class="flex flex-wrap gap-1 mt-1">' +
      stocks.map(s => '<span class="tag" style="background:var(--blue)22;color:var(--blue);cursor:pointer" onclick="showStockDetail(\'' + s.code + '\')">' + s.name + '(' + (s.board||1) + '板)</span>').join('') +
    '</div>';

  document.getElementById('sectorStockCount').textContent = '共 ' + stocks.length + ' 只';
  document.getElementById('sectorStockTable').innerHTML = stocks.map(s => {
    const boardColor = (s.board||1) >= 5 ? 'var(--hot)' : (s.board||1) >= 3 ? 'var(--warm)' : 'var(--blue)';
    return '<tr style="cursor:pointer" onclick="showStockDetail(\'' + s.code + '\')">' +
      '<td class="font-mono">' + s.code + '</td>' +
      '<td class="font-semibold">' + s.name + '</td>' +
      '<td><span class="tag" style="background:' + boardColor + '22;color:' + boardColor + '">' + (s.board||1) + '板</span></td>' +
      '<td>' + (s.price || '--') + '</td>' +
      '<td style="color:var(--red)">+' + (s.change||10).toFixed(2) + '%</td>' +
      '<td>' + (s.turnover ? s.turnover.toFixed(1) + '%' : '--') + '</td>' +
      '<td>' + (s.amount || '--') + '</td>' +
      '<td style="color:var(--text2);font-size:12px">' + (s.concept || '--') + '</td>' +
    '</tr>';
  }).join('');
}

// ==================== V1.1: 个股详情弹窗 ====================
function showStockDetail(code) {
  const stock = appData.limitUpStocks.find(s => s.code === code);
  if (!stock) { alert('未找到该股票数据'); return; }

  document.getElementById('detailStockName').textContent = stock.name;
  document.getElementById('detailStockCode').textContent = stock.code;
  const boardColor = (stock.board||1) >= 5 ? '#ef4444' : (stock.board||1) >= 3 ? '#eab308' : '#3b82f6';
  const boardEl = document.getElementById('detailStockBoard');
  boardEl.textContent = (stock.board || 1) + '板';
  boardEl.style.background = boardColor + '22';
  boardEl.style.color = boardColor;

  document.getElementById('detailPrice').textContent = stock.price ? stock.price.toFixed(2) : '--';
  document.getElementById('detailChange').textContent = '+' + (stock.change || 10).toFixed(2) + '%';
  document.getElementById('detailTurnover').textContent = stock.turnover ? stock.turnover.toFixed(2) + '%' : '--';
  document.getElementById('detailAmount').textContent = stock.amount ? stock.amount.toFixed(2) + '亿' : '--';
  document.getElementById('detailSeal').textContent = stock.sealAmount ? stock.sealAmount.toLocaleString() : (stock.sealAmount === 0 ? '0' : '--');
  document.getElementById('detailVolumeRatio').textContent = stock.volumeRatio ? stock.volumeRatio.toFixed(2) : '--';
  document.getElementById('detailInflow').textContent = stock.mainInflow ? (stock.mainInflow > 0 ? '+' : '') + stock.mainInflow.toLocaleString() : '--';
  document.getElementById('detailInflow').style.color = stock.mainInflow > 0 ? 'var(--red)' : stock.mainInflow < 0 ? 'var(--green)' : 'var(--text)';
  document.getElementById('detailMarketCap').textContent = stock.marketCap ? stock.marketCap.toFixed(1) : '--';

  const concepts = (stock.concept || '暂无').split(/[,，、]/).map(c => c.trim()).filter(c => c);
  document.getElementById('detailConcept').innerHTML = concepts.map(c =>
    '<span class="tag" style="background:var(--blue)15;color:var(--blue)">' + c + '</span>'
  ).join('');

  const risks = [];
  const board = stock.board || 1;
  if (board >= 5) risks.push({ level: 'high', text: '高位连板（' + board + '板），断板风险大，不追高' });
  else if (board >= 3) risks.push({ level: 'mid', text: '中位连板（' + board + '板），关注晋级率变化' });
  else risks.push({ level: 'low', text: '首板/低位，安全性相对较高' });

  if (stock.turnover && stock.turnover > 30) risks.push({ level: 'high', text: '换手率过高（' + stock.turnover.toFixed(1) + '%），筹码松动明显' });
  else if (stock.turnover && stock.turnover > 20) risks.push({ level: 'mid', text: '换手率偏高（' + stock.turnover.toFixed(1) + '%），注意分歧' });

  if (stock.sealAmount === 0) risks.push({ level: 'mid', text: '封单数据缺失，无法确认封板强度' });
  else if (stock.sealAmount && stock.sealAmount < 1000) risks.push({ level: 'mid', text: '封单金额较小，封板稳定性一般' });

  if (stock.amount && stock.amount > 50) risks.push({ level: 'mid', text: '成交额较大（' + stock.amount.toFixed(1) + '亿），大资金博弈激烈' });

  document.getElementById('detailRisk').innerHTML = risks.map(r => {
    const color = r.level === 'high' ? '#ef4444' : r.level === 'mid' ? '#eab308' : '#22c55e';
    const icon = r.level === 'high' ? '🔴' : r.level === 'mid' ? '🟡' : '🟢';
    return '<div class="flex items-center gap-2 text-sm"><span>' + icon + '</span><span style="color:' + color + '">' + r.text + '</span></div>';
  }).join('');

  document.getElementById('stockDetailModal').style.display = 'flex';
}

function closeStockDetail() {
  document.getElementById('stockDetailModal').style.display = 'none';
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeStockDetail();
});

// ==================== V1.1: 自定义选股条件保存 ====================
var SCREEN_COND_KEY = 'emotion_screener_conditions';

function getSavedConditions() {
  try { return JSON.parse(localStorage.getItem(SCREEN_COND_KEY)) || {}; }
  catch(e) { return {}; }
}

function saveScreenCondition() {
  var name = prompt('请输入条件名称：', '我的选股条件_' + new Date().toLocaleDateString());
  if (!name) return;

  var conditions = {
    strategy: currentStrategy,
    timestamp: new Date().toISOString(),
    filters: {}
  };

  document.querySelectorAll('#strategyConditions input, #strategyConditions select').forEach(function(el) {
    if (el.id) conditions.filters[el.id] = el.value;
  });

  var saved = getSavedConditions();
  saved[name] = conditions;
  localStorage.setItem(SCREEN_COND_KEY, JSON.stringify(saved));
  renderSavedConditions();
  alert('选股条件已保存：' + name);
}

function loadSavedCondition(name) {
  var saved = getSavedConditions();
  var cond = saved[name];
  if (!cond) { alert('条件不存在'); return; }

  if (cond.strategy) selectStrategy(cond.strategy);

  setTimeout(function() {
    Object.entries(cond.filters).forEach(function(entry) {
      var id = entry[0], value = entry[1];
      var el = document.getElementById(id);
      if (el) el.value = value;
    });
    alert('已加载条件：' + name + '\n点击"开始选股"运行');
  }, 100);
}

function deleteSavedCondition(name) {
  if (!confirm('确定删除条件 "' + name + '" 吗？')) return;
  var saved = getSavedConditions();
  delete saved[name];
  localStorage.setItem(SCREEN_COND_KEY, JSON.stringify(saved));
  renderSavedConditions();
}

function clearAllSavedConditions() {
  if (!confirm('确定清空所有已保存的选股条件吗？')) return;
  localStorage.removeItem(SCREEN_COND_KEY);
  renderSavedConditions();
}

function renderSavedConditions() {
  var saved = getSavedConditions();
  var card = document.getElementById('savedConditionsCard');
  var list = document.getElementById('savedConditionsList');

  if (!card || !list) return;

  var names = Object.keys(saved);
  if (names.length === 0) {
    card.style.display = 'none';
    return;
  }

  card.style.display = 'block';
  var stageNames = { ice: '冰点期', repair: '修复期', warm: '升温期', hot: '高潮期', ebb: '退潮期' };
  list.innerHTML = names.map(function(name) {
    var cond = saved[name];
    var date = cond.timestamp ? new Date(cond.timestamp).toLocaleDateString() : '';
    var safeName = name.replace(/'/g, "\\'");
    return '<div class="saved-condition">' +
      '<div>' +
        '<div class="text-sm font-semibold">' + name + '</div>' +
        '<div class="text-xs" style="color:var(--text3)">' + (stageNames[cond.strategy] || cond.strategy) + ' · 保存于 ' + date + '</div>' +
      '</div>' +
      '<div class="flex gap-2">' +
        '<button class="btn btn-primary text-xs" onclick="loadSavedCondition(\'' + safeName + '\')">加载</button>' +
        '<button class="btn btn-danger text-xs" onclick="deleteSavedCondition(\'' + safeName + '\')">删除</button>' +
      '</div>' +
    '</div>';
  }).join('');
}

// 启动
window.addEventListener('DOMContentLoaded', function() {
  init();
  renderSavedConditions();
});
'''

# 替换原有的启动代码
old_start = '// 启动\nwindow.addEventListener(\'DOMContentLoaded\', init);'
html = html.replace(old_start, js_functions)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("V1.1 JavaScript函数注入完成！")
print("  - renderSectorHeat / showSectorDetail")
print("  - showStockDetail / closeStockDetail")
print("  - saveScreenCondition / loadSavedCondition")
print("  - deleteSavedCondition / clearAllSavedConditions / renderSavedConditions")
