#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入后端自动连接逻辑到index.html"""

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 在loadBackendConfig函数中注入自动检测逻辑
old = """  } catch(e) { console.error('加载后端配置失败', e); }
  var urlEl = document.getElementById('backendUrl');"""

new = """  } catch(e) { console.error('加载后端配置失败', e); }
  // 后端自动注入模式：通过Flask后端访问时，自动配置并连接
  if (window.__SERVER_API_KEY__) {
    backendConfig.url = window.__SERVER_ORIGIN__ || window.location.origin;
    backendConfig.apiKey = window.__SERVER_API_KEY__;
    backendConfig.enabled = true;
    localStorage.setItem(BACKEND_CONFIG_KEY, JSON.stringify(backendConfig));
  }
  var urlEl = document.getElementById('backendUrl');"""

if '__SERVER_API_KEY__' in content:
    print("自动连接逻辑已存在，跳过")
else:
    content = content.replace(old, new)
    # 在loadBackendConfig函数末尾添加自动拉取数据
    old2 = """    badgeEl.style.color = backendConfig.enabled ? '#22c55e' : 'var(--blue)';
  }
}

function saveBackendConfig()"""
    new2 = """    badgeEl.style.color = backendConfig.enabled ? '#22c55e' : 'var(--blue)';
  }
  // 后端自动模式：连接成功后自动从后端加载数据
  if (window.__SERVER_API_KEY__) {
    setTimeout(function() { syncFromBackend(true); }, 500);
  }
}

function saveBackendConfig()"""
    content = content.replace(old2, new2)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("自动连接逻辑注入成功！")
