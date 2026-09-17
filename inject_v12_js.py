#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入V1.2 JavaScript功能函数"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_functions = r'''
// ==================== V1.2: 交易日志 ====================
function initTradeForm() {
  var today = new Date().toISOString().split('T')[0];
  var el = document.getElementById('tradeDate');
  if (el) el.value = today;
  updateTradeStageHint();
}

function updateTradeStageHint() {
  var dateEl = document.getElementById('tradeDate');
  var hintEl = document.getElementById('tradeStageHint');
  if (!dateEl || !hintEl) return;
  var date = dateEl.value;
  var stage = getStageForDate(date);
  if (stage) {
    var stageNames = { ice: '❄️ 冰点期', repair: '🌱 修复期', warm: '🔥 升温期', hot: '💥 高潮期', ebb: '🌊 退潮期' };
    var snap = appData.snapshots.find(function(s) { return s.date === date; });
    var temp = snap ? snap.temperature : '--';
    hintEl.innerHTML = '当日情绪阶段：<span style="color:var(--warm);font-weight:600">' + (stageNames[stage] || stage) + '</span> · 温度：' + temp + '°';
  } else {
    hintEl.textContent = '该日期无情绪数据，阶段将标记为"未知"';
  }
}

function getStageForDate(date) {
  var snap = appData.snapshots.find(function(s) { return s.date === date; });
  return snap ? (snap.stage || 'unknown') : null;
}

function addTrade() {
  var date = document.getElementById('tradeDate').value;
  var type = document.getElementById('tradeType').value;
  var code = document.getElementById('tradeCode').value.trim();
  var name = document.getElementById('tradeName').value.trim();
  var price = parseFloat(document.getElementById('tradePrice').value);
  var qty = parseInt(document.getElementById('tradeQty').value);
  var fee = parseFloat(document.getElementById('tradeFee').value) || 0;
  var note = document.getElementById('tradeNote').value.trim();

  if (!date || !code || !name || !price || !qty) {
    alert('请填写完整：日期、代码、名称、价格、数量');
    return;
  }

  if (!appData.trades) appData.trades = [];

  var trade = {
    id: Date.now() + '_' + Math.random().toString(36).substr(2, 5),
    date: date,
    type: type,
    code: code,
    name: name,
    price: price,
    qty: qty,
    fee: fee,
    amount: price * qty,
    note: note,
    stage: getStageForDate(date) || 'unknown',
    createdAt: new Date().toISOString()
  };

  appData.trades.push(trade);
  appData.trades.sort(function(a, b) { return b.date.localeCompare(a.date); });
  saveData();
  renderTradeList();
  renderPnlSummary();

  // 清空表单（保留日期）
  document.getElementById('tradeCode').value = '';
  document.getElementById('tradeName').value = '';
  document.getElementById('tradePrice').value = '';
  document.getElementById('tradeQty').value = '';
  document.getElementById('tradeFee').value = '0';
  document.getElementById('tradeNote').value = '';

  alert('交易记录已保存！');
}

function renderTradeList() {
  var listEl = document.getElementById('tradeList');
  if (!listEl) return;

  if (!appData.trades || appData.trades.length === 0) {
    listEl.innerHTML = '<tr><td colspan="11" class="text-center py-8" style="color:var(--text3)">暂无交易记录</td></tr>';
    return;
  }

  var filter = document.getElementById('tradeFilter')?.value || 'all';
  var trades = appData.trades.filter(function(t) {
    if (filter === 'all') return true;
    return t.type === filter;
  });

  var stageNames = { ice: '冰点期', repair: '修复期', warm: '升温期', hot: '高潮期', ebb: '退潮期', unknown: '未知' };

  listEl.innerHTML = trades.map(function(t) {
    var typeTag = t.type === 'buy'
      ? '<span class="tag trade-tag-buy">买入</span>'
      : '<span class="tag trade-tag-sell">卖出</span>';
    return '<tr>' +
      '<td>' + t.date + '</td>' +
      '<td>' + typeTag + '</td>' +
      '<td class="font-mono">' + t.code + '</td>' +
      '<td class="font-semibold">' + t.name + '</td>' +
      '<td>' + t.price.toFixed(2) + '</td>' +
      '<td>' + t.qty + '</td>' +
      '<td>' + t.amount.toFixed(2) + '</td>' +
      '<td>' + (t.fee || 0).toFixed(2) + '</td>' +
      '<td><span class="text-xs" style="color:var(--text2)">' + (stageNames[t.stage] || t.stage) + '</span></td>' +
      '<td style="font-size:12px;color:var(--text2)">' + (t.note || '--') + '</td>' +
      '<td><button class="btn btn-danger text-xs" onclick="deleteTrade(\'' + t.id + '\')">删除</button></td>' +
    '</tr>';
  }).join('');
}

function deleteTrade(id) {
  if (!confirm('确定删除这条交易记录吗？')) return;
  appData.trades = appData.trades.filter(function(t) { return t.id !== id; });
  saveData();
  renderTradeList();
  renderPnlSummary();
}

function clearAllTrades() {
  if (!confirm('确定清空全部交易记录吗？此操作不可恢复！')) return;
  appData.trades = [];
  saveData();
  renderTradeList();
  renderPnlSummary();
}

// ==================== V1.2: 盈亏统计 ====================
function renderPnlSummary() {
  var el = document.getElementById('pnlSummary');
  if (!el) return;

  if (!appData.trades || appData.trades.length === 0) {
    el.innerHTML = '<div class="text-center py-10 text-xs" style="color:var(--text3)">暂无交易记录</div>';
    return;
  }

  var buys = appData.trades.filter(function(t) { return t.type === 'buy'; });
  var sells = appData.trades.filter(function(t) { return t.type === 'sell'; });

  var totalBuyAmount = buys.reduce(function(s, t) { return s + t.amount + (t.fee || 0); }, 0);
  var totalSellAmount = sells.reduce(function(s, t) { return s + t.amount - (t.fee || 0); }, 0);
  var totalFee = appData.trades.reduce(function(s, t) { return s + (t.fee || 0); }, 0);

  // 按股票配对计算已实现盈亏
  var positions = {};
  var realizedPnl = 0;
  var winTrades = 0;
  var totalClosed = 0;

  var sortedTrades = appData.trades.slice().sort(function(a, b) { return a.date.localeCompare(b.date); });
  sortedTrades.forEach(function(t) {
    if (!positions[t.code]) positions[t.code] = [];
    if (t.type === 'buy') {
      positions[t.code].push({ price: t.price, qty: t.qty, fee: t.fee || 0 });
    } else if (t.type === 'sell' && positions[t.code].length > 0) {
      var sellQty = t.qty;
      var sellAmount = t.amount - (t.fee || 0);
      var costAmount = 0;
      while (sellQty > 0 && positions[t.code].length > 0) {
        var lot = positions[t.code][0];
        var useQty = Math.min(sellQty, lot.qty);
        costAmount += useQty * lot.price + (lot.fee || 0) * (useQty / lot.qty);
        lot.qty -= useQty;
        sellQty -= useQty;
        if (lot.qty <= 0) positions[t.code].shift();
      }
      var pnl = sellAmount - costAmount;
      realizedPnl += pnl;
      totalClosed++;
      if (pnl > 0) winTrades++;
    }
  });

  // 浮动盈亏（持仓按最新价或买入价估算）
  var floatingPnl = 0;
  var positionCount = 0;
  Object.entries(positions).forEach(function(entry) {
    var code = entry[0], lots = entry[1];
    if (lots.length === 0) return;
    positionCount++;
    var totalQty = lots.reduce(function(s, l) { return s + l.qty; }, 0);
    var avgCost = lots.reduce(function(s, l) { return s + l.price * l.qty; }, 0) / totalQty;
    // 尝试从涨停股数据获取最新价，否则用成本价
    var stock = appData.limitUpStocks.find(function(s) { return s.code === code; });
    var currentPrice = stock ? stock.price : avgCost;
    floatingPnl += (currentPrice - avgCost) * totalQty;
  });

  var totalPnl = realizedPnl + floatingPnl;
  var winRate = totalClosed > 0 ? (winTrades / totalClosed * 100).toFixed(1) : '--';

  // 按情绪阶段统计
  var stageStats = {};
  appData.trades.forEach(function(t) {
    if (!stageStats[t.stage]) stageStats[t.stage] = { count: 0, buyAmount: 0, sellAmount: 0 };
    stageStats[t.stage].count++;
    if (t.type === 'buy') stageStats[t.stage].buyAmount += t.amount;
    else stageStats[t.stage].sellAmount += t.amount;
  });

  var stageNames = { ice: '❄️ 冰点期', repair: '🌱 修复期', warm: '🔥 升温期', hot: '💥 高潮期', ebb: '🌊 退潮期', unknown: '❓ 未知' };
  var stageOrder = ['ice', 'repair', 'warm', 'hot', 'ebb', 'unknown'];

  var pnlColor = totalPnl >= 0 ? 'pnl-positive' : 'pnl-negative';
  var pnlSign = totalPnl >= 0 ? '+' : '';

  el.innerHTML =
    '<div class="grid grid-cols-4 gap-3 mb-4">' +
      '<div class="card2 p-3"><div class="stat-mini">总盈亏</div><div class="text-xl font-bold ' + pnlColor + '">' + pnlSign + totalPnl.toFixed(2) + '元</div></div>' +
      '<div class="card2 p-3"><div class="stat-mini">已实现盈亏</div><div class="text-lg font-bold ' + (realizedPnl >= 0 ? 'pnl-positive' : 'pnl-negative') + '">' + (realizedPnl >= 0 ? '+' : '') + realizedPnl.toFixed(2) + '元</div></div>' +
      '<div class="card2 p-3"><div class="stat-mini">浮动盈亏</div><div class="text-lg font-bold ' + (floatingPnl >= 0 ? 'pnl-positive' : 'pnl-negative') + '">' + (floatingPnl >= 0 ? '+' : '') + floatingPnl.toFixed(2) + '元</div></div>' +
      '<div class="card2 p-3"><div class="stat-mini">胜率</div><div class="text-lg font-bold">' + winRate + '%</div><div class="stat-mini">' + winTrades + '/' + totalClosed + '笔平仓</div></div>' +
    '</div>' +
    '<div class="grid grid-cols-3 gap-3 mb-4">' +
      '<div class="card2 p-3"><div class="stat-mini">买入总额</div><div class="text-base font-bold">' + totalBuyAmount.toFixed(2) + '元</div></div>' +
      '<div class="card2 p-3"><div class="stat-mini">卖出总额</div><div class="text-base font-bold">' + totalSellAmount.toFixed(2) + '元</div></div>' +
      '<div class="card2 p-3"><div class="stat-mini">累计手续费</div><div class="text-base font-bold">' + totalFee.toFixed(2) + '元</div><div class="stat-mini">持仓' + positionCount + '只 · 共' + appData.trades.length + '笔</div></div>' +
    '</div>' +
    '<div class="card2 p-3">' +
      '<div class="text-xs font-semibold mb-2" style="color:var(--text2)">按情绪阶段分布</div>' +
      '<div class="grid grid-cols-3 gap-2">' +
        stageOrder.filter(function(s) { return stageStats[s]; }).map(function(s) {
          var st = stageStats[s];
          return '<div class="p-2" style="background:var(--bg);border-radius:6px">' +
            '<div class="text-xs font-semibold">' + (stageNames[s] || s) + '</div>' +
            '<div class="text-xs" style="color:var(--text3)">' + st.count + '笔 · 买' + st.buyAmount.toFixed(0) + ' / 卖' + st.sellAmount.toFixed(0) + '</div>' +
          '</div>';
        }).join('') +
      '</div>' +
    '</div>';
}

// ==================== V1.2: 情绪温度预测 ====================
function runTemperaturePrediction() {
  var snapshots = appData.snapshots;
  if (!snapshots || snapshots.length < 5) {
    document.getElementById('predictionResult').innerHTML = '<div class="text-center py-8 text-xs" style="color:var(--text3)">历史数据不足5天，无法进行预测</div>';
    return;
  }

  var recent = snapshots.slice(-10);
  var temps = recent.map(function(s) { return s.temperature; });
  var currentTemp = temps[temps.length - 1];
  var currentStage = recent[recent.length - 1].stage || 'warm';

  // 1. 移动平均趋势
  var ma3 = temps.slice(-3).reduce(function(a, b) { return a + b; }, 0) / 3;
  var ma5 = temps.slice(-5).reduce(function(a, b) { return a + b; }, 0) / 5;
  var trend = ma3 > ma5 ? 'up' : ma3 < ma5 ? 'down' : 'flat';

  // 2. 动量（最近3天变化速率）
  var momentum = 0;
  for (var i = Math.max(0, temps.length - 3); i < temps.length - 1; i++) {
    momentum += temps[i + 1] - temps[i];
  }

  // 3. 周期阶段特征
  var stagePatterns = {
    ice: { drift: 5, volatility: 8, desc: '冰点期后通常有修复性反弹' },
    repair: { drift: 8, volatility: 10, desc: '修复期温度逐步抬升，确认后进入升温' },
    warm: { drift: 6, volatility: 12, desc: '升温期温度震荡上行，关注高潮信号' },
    hot: { drift: -5, volatility: 15, desc: '高潮期后大概率转退潮，防分歧' },
    ebb: { drift: -8, volatility: 12, desc: '退潮期温度快速下行，第2天更危险' }
  };
  var pattern = stagePatterns[currentStage] || stagePatterns.warm;

  // 4. 历史相似日匹配（找温度和阶段相似的日期，看后续走势）
  var similarDays = [];
  for (var j = 0; j < snapshots.length - 2; j++) {
    var s = snapshots[j];
    if (s.stage === currentStage && Math.abs(s.temperature - currentTemp) <= 10) {
      var nextTemps = [];
      for (var k = 1; k <= 5 && j + k < snapshots.length; k++) {
        nextTemps.push(snapshots[j + k].temperature - s.temperature);
      }
      if (nextTemps.length >= 3) similarDays.push(nextTemps);
    }
  }

  // 5. 综合预测未来5天
  var predictions = [];
  var baseTemp = currentTemp;
  for (var d = 0; d < 5; d++) {
    // 基础漂移
    var drift = pattern.drift * (d < 2 ? 1 : 0.5);
    // 动量衰减
    var momEffect = momentum * Math.pow(0.5, d);
    // 历史相似平均
    var histAvg = 0;
    if (similarDays.length > 0 && d < similarDays[0].length) {
      histAvg = similarDays.reduce(function(s, arr) { return s + (arr[d] || 0); }, 0) / similarDays.length;
    }
    // 均值回归（温度偏离50时拉回）
    var meanRevert = (50 - baseTemp) * 0.05;

    var delta = drift * 0.3 + momEffect * 0.2 + histAvg * 0.3 + meanRevert;
    // 波动率
    var volatility = pattern.volatility * (0.5 + d * 0.15);
    var predicted = Math.max(0, Math.min(100, baseTemp + delta));
    var lower = Math.max(0, predicted - volatility);
    var upper = Math.min(100, predicted + volatility);

    predictions.push({
      day: d + 1,
      predicted: Math.round(predicted),
      lower: Math.round(lower),
      upper: Math.round(upper),
      delta: Math.round(delta)
    });
    baseTemp = predicted;
  }

  // 置信度
  var confidence = similarDays.length >= 3 ? 70 : similarDays.length >= 1 ? 50 : 30;
  confidence = Math.min(85, confidence + (trend === 'flat' ? 5 : 0));

  // 阶段预测
  var stageNames = { ice: '❄️ 冰点期', repair: '🌱 修复期', warm: '🔥 升温期', hot: '💥 高潮期', ebb: '🌊 退潮期' };
  var predictedStage = predictions[4].predicted >= 75 ? 'hot' : predictions[4].predicted >= 50 ? 'warm' : predictions[4].predicted >= 35 ? 'repair' : 'ice';

  // 渲染
  var colors = ['#3b82f6', '#06b6d4', '#22c55e', '#eab308', '#ef4444'];
  var barsHtml = predictions.map(function(p, i) {
    var height = Math.max(10, p.predicted);
    var color = colors[i];
    var deltaSign = p.delta >= 0 ? '+' : '';
    return '<div class="predict-col">' +
      '<div class="val" style="color:' + color + '">' + p.predicted + '°</div>' +
      '<div class="bar" style="height:' + height + 'px;background:linear-gradient(180deg,' + color + ',' + color + '88)"></div>' +
      '<div class="label">D+' + p.day + '</div>' +
      '<div class="label" style="color:' + (p.delta >= 0 ? '#ef4444' : '#22c55e') + '">' + deltaSign + p.delta + '</div>' +
      '<div class="label">' + p.lower + '~' + p.upper + '</div>' +
    '</div>';
  }).join('');

  document.getElementById('predictionResult').innerHTML =
    '<div class="grid grid-cols-12 gap-4">' +
      '<div class="col-span-8">' +
        '<div class="predict-bar">' + barsHtml + '</div>' +
        '<div class="text-center text-xs mt-2" style="color:var(--text3)">D+1~D+5 预测温度（点值为预测中值，区间为波动范围）</div>' +
      '</div>' +
      '<div class="col-span-4 space-y-3">' +
        '<div class="card2 p-3"><div class="stat-mini">当前温度</div><div class="text-xl font-bold" style="color:var(--warm)">' + currentTemp + '°</div><div class="stat-mini">' + (stageNames[currentStage] || currentStage) + '</div></div>' +
        '<div class="card2 p-3"><div class="stat-mini">5日后预测</div><div class="text-xl font-bold">' + predictions[4].predicted + '°</div><div class="stat-mini">可能进入：' + (stageNames[predictedStage] || predictedStage) + '</div></div>' +
        '<div class="card2 p-3"><div class="stat-mini">预测置信度</div><div class="text-xl font-bold" style="color:' + (confidence >= 60 ? '#22c55e' : '#eab308') + '">' + confidence + '%</div><div class="stat-mini">基于' + similarDays.length + '个历史相似日</div></div>' +
        '<div class="card2 p-3"><div class="stat-mini">趋势判断</div><div class="text-sm font-bold">' + (trend === 'up' ? '📈 上行趋势' : trend === 'down' ? '📉 下行趋势' : '➡️ 横盘震荡') + '</div><div class="stat-mini">' + pattern.desc + '</div></div>' +
      '</div>' +
    '</div>' +
    '<div class="mt-3 p-3" style="background:rgba(59,130,246,.08);border-radius:8px;border-left:3px solid var(--blue)">' +
      '<div class="text-xs" style="color:var(--text2)">💡 <b>预测说明</b>：本预测基于历史温度序列的移动平均、动量、周期阶段特征和历史相似日匹配综合计算，仅供参考。情绪受突发消息、政策等外部因素影响较大，实际走势可能偏离预测。</div>' +
    '</div>';
}

// ==================== V1.2: 多周期对比 ====================
var selectedCycles = [];

function detectCycles() {
  var snapshots = appData.snapshots;
  if (!snapshots || snapshots.length < 5) return [];

  var cycles = [];
  var currentCycle = null;

  for (var i = 0; i < snapshots.length; i++) {
    var s = snapshots[i];
    var stage = s.stage || 'warm';

    // 周期起点：冰点或修复期（温度低于45）
    if ((stage === 'ice' || stage === 'repair') && (!currentCycle || currentCycle.complete)) {
      if (currentCycle && currentCycle.endIdx !== null) cycles.push(currentCycle);
      currentCycle = {
        startIdx: i,
        endIdx: null,
        startDate: s.date,
        endDate: null,
        stages: [stage],
        temps: [s.temperature],
        maxTemp: s.temperature,
        minTemp: s.temperature,
        complete: false
      };
    } else if (currentCycle && !currentCycle.complete) {
      currentCycle.stages.push(stage);
      currentCycle.temps.push(s.temperature);
      currentCycle.maxTemp = Math.max(currentCycle.maxTemp, s.temperature);
      currentCycle.minTemp = Math.min(currentCycle.minTemp, s.temperature);
      currentCycle.endIdx = i;
      currentCycle.endDate = s.date;

      // 周期终点：退潮后进入冰点/修复（完成一个循环），或温度从高点回落超过20
      if (stage === 'ebb' && i > 0 && snapshots[i - 1].stage !== 'ebb') {
        // 退潮开始，再看后面是否进入新周期
      }
      if (stage === 'ice' && currentCycle.stages.indexOf('warm') >= 0) {
        currentCycle.complete = true;
      }
    }
  }

  if (currentCycle && currentCycle.endIdx !== null) {
    cycles.push(currentCycle);
  }

  // 如果没有检测到完整周期，用温度转折点简单分段
  if (cycles.length === 0 && snapshots.length >= 5) {
    var segmentSize = Math.max(5, Math.floor(snapshots.length / 2));
    for (var idx = 0; idx < snapshots.length; idx += segmentSize) {
      var end = Math.min(idx + segmentSize - 1, snapshots.length - 1);
      var seg = snapshots.slice(idx, end + 1);
      cycles.push({
        startIdx: idx,
        endIdx: end,
        startDate: seg[0].date,
        endDate: seg[end - idx].date,
        stages: seg.map(function(s) { return s.stage; }),
        temps: seg.map(function(s) { return s.temperature; }),
        maxTemp: Math.max.apply(null, seg.map(function(s) { return s.temperature; })),
        minTemp: Math.min.apply(null, seg.map(function(s) { return s.temperature; })),
        complete: end === snapshots.length - 1 ? false : true
      });
    }
  }

  return cycles;
}

function renderCycleList() {
  var listEl = document.getElementById('cycleList');
  if (!listEl) return;

  var cycles = detectCycles();
  if (cycles.length === 0) {
    listEl.innerHTML = '<div class="text-center py-4 text-xs" style="color:var(--text3)">暂无足够数据识别周期</div>';
    return;
  }

  var stageNames = { ice: '冰', repair: '修', warm: '温', hot: '高', ebb: '退' };

  listEl.innerHTML = cycles.map(function(c, i) {
    var isSelected = selectedCycles.indexOf(i) >= 0;
    var days = c.endIdx - c.startIdx + 1;
    var stageFlow = c.stages.filter(function(s, idx, arr) { return idx === 0 || s !== arr[idx - 1]; })
      .map(function(s) { return stageNames[s] || s; }).join('→');
    return '<div class="cycle-compare-item ' + (isSelected ? 'selected' : '') + '" onclick="selectCycle(' + i + ')">' +
      '<div class="flex items-center justify-between mb-1">' +
        '<span class="text-sm font-bold">周期' + (i + 1) + (c.complete ? '' : ' (进行中)') + '</span>' +
        '<span class="text-xs" style="color:var(--text3)">' + days + '天</span>' +
      '</div>' +
      '<div class="text-xs" style="color:var(--text2)">' + c.startDate + ' ~ ' + c.endDate + '</div>' +
      '<div class="text-xs mt-1" style="color:var(--warm)">' + stageFlow + '</div>' +
      '<div class="text-xs mt-1" style="color:var(--text3)">温度 ' + c.minTemp + '°~' + c.maxTemp + '°</div>' +
    '</div>';
  }).join('');
}

function selectCycle(index) {
  var pos = selectedCycles.indexOf(index);
  if (pos >= 0) {
    selectedCycles.splice(pos, 1);
  } else {
    if (selectedCycles.length >= 2) {
      selectedCycles.shift();
    }
    selectedCycles.push(index);
  }
  renderCycleList();
  if (selectedCycles.length === 2) {
    compareCycles();
  } else {
    document.getElementById('cycleCompareResult').innerHTML =
      '<div class="text-center py-10 text-xs" style="color:var(--text3)">已选' + selectedCycles.length + '个周期，再选1个进行对比</div>';
  }
}

function clearCycleSelection() {
  selectedCycles = [];
  renderCycleList();
  document.getElementById('cycleCompareResult').innerHTML =
    '<div class="text-center py-10 text-xs" style="color:var(--text3)">点击左侧周期段进行选择，最多选2个进行对比</div>';
}

function compareCycles() {
  var cycles = detectCycles();
  var c1 = cycles[selectedCycles[0]];
  var c2 = cycles[selectedCycles[1]];
  if (!c1 || !c2) return;

  var s1 = appData.snapshots.slice(c1.startIdx, c1.endIdx + 1);
  var s2 = appData.snapshots.slice(c2.startIdx, c2.endIdx + 1);

  var avg1 = c1.temps.reduce(function(a, b) { return a + b; }, 0) / c1.temps.length;
  var avg2 = c2.temps.reduce(function(a, b) { return a + b; }, 0) / c2.temps.length;
  var days1 = c1.temps.length;
  var days2 = c2.temps.length;

  // 相似度计算（按天数对齐后比较温度曲线）
  var minDays = Math.min(days1, days2);
  var diffSum = 0;
  for (var i = 0; i < minDays; i++) {
    var t1 = c1.temps[Math.floor(i * days1 / minDays)];
    var t2 = c2.temps[Math.floor(i * days2 / minDays)];
    diffSum += Math.abs(t1 - t2);
  }
  var avgDiff = diffSum / minDays;
  var similarity = Math.max(0, Math.round(100 - avgDiff * 1.5));

  // 涨停/跌停统计
  var lu1 = s1.reduce(function(a, s) { return a + (s.limitUp || 0); }, 0);
  var ld1 = s1.reduce(function(a, s) { return a + (s.limitDown || 0); }, 0);
  var lu2 = s2.reduce(function(a, s) { return a + (s.limitUp || 0); }, 0);
  var ld2 = s2.reduce(function(a, s) { return a + (s.limitDown || 0); }, 0);

  document.getElementById('cycleCompareResult').innerHTML =
    '<div class="card2 p-3 mb-3" style="background:rgba(59,130,246,.08);border-color:var(--blue)">' +
      '<div class="flex items-center justify-between">' +
        '<span class="text-sm font-bold">周期' + (selectedCycles[0] + 1) + ' vs 周期' + (selectedCycles[1] + 1) + '</span>' +
        '<span class="text-lg font-bold" style="color:var(--blue)">相似度 ' + similarity + '%</span>' +
      '</div>' +
    '</div>' +
    '<table>' +
      '<thead><tr><th>指标</th><th style="color:var(--blue)">周期' + (selectedCycles[0] + 1) + '</th><th style="color:var(--warm)">周期' + (selectedCycles[1] + 1) + '</th><th>差异</th></tr></thead>' +
      '<tbody>' +
        '<tr><td>时间区间</td><td>' + c1.startDate + ' ~ ' + c1.endDate + '</td><td>' + c2.startDate + ' ~ ' + c2.endDate + '</td><td>--</td></tr>' +
        '<tr><td>持续天数</td><td>' + days1 + '天</td><td>' + days2 + '天</td><td>' + (days1 - days2) + '天</td></tr>' +
        '<tr><td>最高温度</td><td style="color:var(--hot)">' + c1.maxTemp + '°</td><td style="color:var(--hot)">' + c2.maxTemp + '°</td><td>' + (c1.maxTemp - c2.maxTemp) + '°</td></tr>' +
        '<tr><td>最低温度</td><td style="color:var(--ice)">' + c1.minTemp + '°</td><td style="color:var(--ice)">' + c2.minTemp + '°</td><td>' + (c1.minTemp - c2.minTemp) + '°</td></tr>' +
        '<tr><td>平均温度</td><td>' + avg1.toFixed(1) + '°</td><td>' + avg2.toFixed(1) + '°</td><td>' + (avg1 - avg2).toFixed(1) + '°</td></tr>' +
        '<tr><td>累计涨停</td><td style="color:var(--red)">' + lu1 + '家</td><td style="color:var(--red)">' + lu2 + '家</td><td>' + (lu1 - lu2) + '家</td></tr>' +
        '<tr><td>累计跌停</td><td style="color:var(--green)">' + ld1 + '家</td><td><td style="color:var(--green)">' + ld2 + '家</td><td>' + (ld1 - ld2) + '家</td></tr>' +
        '<tr><td>日均涨停</td><td>' + (lu1 / days1).toFixed(1) + '家</td><td>' + (lu2 / days2).toFixed(1) + '家</td><td>' + ((lu1/days1) - (lu2/days2)).toFixed(1) + '家</td></tr>' +
      '</tbody>' +
    '</table>' +
    '<div class="mt-3 p-3" style="background:var(--card2);border-radius:8px">' +
      '<div class="text-xs" style="color:var(--text2)">💡 <b>对比解读</b>：' +
      (similarity >= 70 ? '两个周期温度走势高度相似，可参考周期' + (selectedCycles[0] + 1) + '的后续走势预判当前周期。' :
       similarity >= 50 ? '两个周期有一定相似性，但存在明显差异，参考时需注意当前周期的特殊性。' :
       '两个周期差异较大，不宜简单类比。当前周期有其独特的盘面特征。') +
      '</div>' +
    '</div>';
}

// 启动（V1.2增强）
window.addEventListener('DOMContentLoaded', function() {
  init();
  renderSavedConditions();
  initTradeForm();
  var tradeDateEl = document.getElementById('tradeDate');
  if (tradeDateEl) tradeDateEl.addEventListener('change', updateTradeStageHint);
});
'''

# 替换原有的启动代码（V1.1版本的）
old_start = '''// 启动（V1.1增强）
window.addEventListener('DOMContentLoaded', function() {
  init();
  renderSavedConditions();
});'''

if old_start in html:
    html = html.replace(old_start, js_functions)
else:
    # 尝试匹配原始启动代码
    old_start2 = "// 启动\nwindow.addEventListener('DOMContentLoaded', init);"
    if old_start2 in html:
        html = html.replace(old_start2, js_functions)
    else:
        print("WARNING: 未找到启动代码，在</script>前追加")
        html = html.replace('</script>', js_functions + '\n</script>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("V1.2 JavaScript函数注入完成！")
print("  - 交易日志: addTrade / renderTradeList / deleteTrade / clearAllTrades")
print("  - 盈亏统计: renderPnlSummary（FIFO配对、已实现/浮动盈亏、胜率、按阶段分布）")
print("  - 情绪温度预测: runTemperaturePrediction（移动平均+动量+周期特征+历史相似日）")
print("  - 多周期对比: detectCycles / renderCycleList / selectCycle / compareCycles")
