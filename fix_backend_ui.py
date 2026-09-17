#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复后端设置卡片注入 - 在数据管理前插入"""

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

if 'backendModeBadge' in content:
    print("后端设置卡片已存在，跳过")
    exit(0)

backend_html = '''    <!-- V2.0: 后端服务设置 -->
    <div class="card p-5 mt-4">
      <div class="stat-label text-base font-semibold mb-4" style="color:var(--text)">🔌 后端服务设置（V2.0）</div>
      <div class="grid grid-cols-2 gap-4">
        <div class="card2 p-3">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-semibold">当前模式</span>
            <span id="backendModeBadge" class="tag" style="background:rgba(59,130,246,.15);color:var(--blue)">本地模式</span>
          </div>
          <div class="text-xs" style="color:var(--text3)">本地模式：数据存储在浏览器；后端模式：数据通过API同步到服务器，支持多设备访问</div>
        </div>
        <div class="space-y-2">
          <div><label class="text-xs" style="color:var(--text2)">后端API地址</label><input type="text" class="input-field mt-1" id="backendUrl" value="http://127.0.0.1:5000"></div>
          <div><label class="text-xs" style="color:var(--text2)">API Key</label><input type="password" class="input-field mt-1" id="backendApiKey" placeholder="输入API Key"></div>
        </div>
      </div>
      <div class="flex gap-2 mt-3">
        <button class="btn btn-ghost text-xs" onclick="testBackendConnection()">🔍 测试连接</button>
        <button class="btn btn-primary text-xs" onclick="toggleBackendMode()">🔄 切换模式</button>
        <button class="btn btn-ghost text-xs" onclick="syncToBackend()">⬆️ 上传到后端</button>
        <button class="btn btn-ghost text-xs" onclick="syncFromBackend()">⬇️ 从后端拉取</button>
      </div>
      <div id="backendStatus" class="text-xs mt-2" style="color:var(--text3)">启动后端：python server.py，然后注册用户获取API Key</div>
    </div>

'''

content = content.replace('  <!-- 数据管理 -->', backend_html + '  <!-- 数据管理 -->')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("后端设置卡片已成功插入！")
