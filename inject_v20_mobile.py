#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2.0 移动端响应式适配 - 注入移动端CSS"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

mobile_css = '''
  /* ==================== V2.0 移动端响应式适配 ==================== */
  @media (max-width: 768px) {
    body { font-size: 14px; }
    main { padding: 12px; }
    header { padding: 8px 12px; }
    header .font-bold { font-size: 14px; }
    header .text-xs { font-size: 10px; }
    .btn { padding: 8px 14px; font-size: 12px; min-height: 36px; }
    .tab-btn { padding: 8px 14px; font-size: 13px; min-height: 40px; display: flex; align-items: center; }
    .stat-value { font-size: 22px; }
    .card { padding: 12px; }
    .card p-5 { padding: 12px; }
    .grid-cols-12 { grid-template-columns: repeat(6, 1fr) !important; }
    .grid-cols-12 > .col-span-8,
    .grid-cols-12 > .col-span-7,
    .grid-cols-12 > .col-span-6,
    .grid-cols-12 > .col-span-5,
    .grid-cols-12 > .col-span-4 { grid-column: span 6 !important; }
    .grid-cols-12 > .col-span-3 { grid-column: span 3 !important; }
    .grid-cols-4 { grid-template-columns: repeat(2, 1fr) !important; }
    .grid-cols-3 { grid-template-columns: repeat(2, 1fr) !important; }
    .grid-cols-5 { grid-template-columns: repeat(2, 1fr) !important; }
    .temp-ring { width: 140px; height: 140px; }
    .modal-box { width: 95% !important; max-height: 90vh !important; margin: 10px; }
    .modal-body { padding: 12px; }
    .detail-grid { grid-template-columns: 1fr 1fr !important; gap: 8px !important; }
    .detail-item { padding: 8px; }
    .detail-value { font-size: 14px; }
    .predict-bar { height: 100px; }
    .trade-form-row { grid-template-columns: repeat(2, 1fr) !important; }
    .strategy-card { padding: 8px; }
    .strategy-card .text-2xl { font-size: 20px; }
    .strategy-card .font-bold { font-size: 12px; }
    .strategy-card .text-xs { font-size: 10px; }
    table { font-size: 12px; }
    th, td { padding: 8px 6px; }
    .sector-bar { font-size: 11px; padding: 0 8px; min-height: 28px; }
    .ladder-item { padding: 6px 8px; font-size: 12px; min-height: 32px; display: flex; align-items: center; }
    .saved-condition { padding: 8px 10px; }
    .cycle-compare-item { padding: 8px; }
    .action-card { padding: 12px; }
    .step-indicator { flex-wrap: wrap; }
    .input-field { font-size: 13px; min-height: 36px; }
    select.input-field { min-height: 36px; }
  }

  @media (max-width: 480px) {
    body { font-size: 13px; }
    main { padding: 8px; }
    .grid-cols-12 { grid-template-columns: 1fr !important; }
    .grid-cols-12 > * { grid-column: span 1 !important; }
    .grid-cols-4 { grid-template-columns: 1fr !important; }
    .grid-cols-3 { grid-template-columns: 1fr !important; }
    .grid-cols-5 { grid-template-columns: 1fr !important; }
    .grid-cols-2 { grid-template-columns: 1fr !important; }
    .stat-value { font-size: 20px; }
    .temp-ring { width: 120px; height: 120px; }
    .modal-box { width: 100% !important; border-radius: 12px 12px 0 0; position: fixed; bottom: 0; left: 0; right: 0; max-height: 85vh; }
    .detail-grid { grid-template-columns: 1fr 1fr !important; }
    .trade-form-row { grid-template-columns: 1fr !important; }
    .tab-btn { padding: 10px 12px; font-size: 12px; }
    .btn { padding: 10px 16px; font-size: 13px; min-height: 44px; }
    .card { padding: 10px; }
    .strategy-card { padding: 10px 8px; }
    .strategy-card .text-2xl { font-size: 24px; }
    .strategy-card .font-bold { font-size: 13px; }
    .predict-col .bar { max-width: 30px; }
    .sector-bar { font-size: 10px; min-height: 26px; }
    .sector-bar .sector-count { font-size: 10px; }
    table { font-size: 11px; }
    th, td { padding: 6px 4px; }
    .input-field { font-size: 14px; min-height: 40px; }
    header .btn { padding: 6px 10px; font-size: 11px; min-height: 32px; }
  }

  /* 触摸设备优化 */
  @media (hover: none) and (pointer: coarse) {
    .tab-btn:active { transform: scale(0.97); }
    .btn:active { transform: scale(0.97); }
    .ladder-item:active { transform: translateX(2px) scale(0.98); }
    .sector-bar:active { opacity: 0.8; transform: scale(0.99); }
    .cycle-compare-item:active { transform: scale(0.98); }
    tr:active td { background: rgba(59,130,246,.1); }
  }

  /* 移动端底部安全区适配 */
  @supports (padding-bottom: env(safe-area-inset-bottom)) {
    body { padding-bottom: env(safe-area-inset-bottom); }
    main { padding-bottom: calc(env(safe-area-inset-bottom) + 20px); }
  }
'''

html = html.replace('</style>', mobile_css + '\n</style>')

# 版本号更新
html = html.replace('Emotion Cycle Screener v1.2', 'Emotion Cycle Screener v2.0')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("移动端响应式CSS注入完成！")
print("  - 768px断点：平板适配（6列网格、双列布局）")
print("  - 480px断点：手机适配（单列布局、底部弹窗、大按钮）")
print("  - 触摸设备优化：active状态反馈")
print("  - 安全区适配：iPhone底部安全区")
print("  - 版本号更新为 v2.0")
