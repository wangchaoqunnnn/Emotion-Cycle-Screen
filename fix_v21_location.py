#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复V2.1代码位置：从tailwind CDN块移到真正的内联script块"""

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 提取V2.1 JS代码块（在错误位置的）
import re
v21_pattern = r'\n// ==================== V2\.1: 实时行情 ====================.*?\n// ==================== V2\.0: 后端服务对接 ===================='
match = re.search(v21_pattern, content, re.DOTALL)
if not match:
    print("未找到V2.1代码块")
    exit(1)

v21_block = match.group(0)
# 去掉结尾的V2.0标记（保留它原位）
v21_code = v21_block.replace('\n// ==================== V2.0: 后端服务对接 ====================', '')
print("提取V2.1代码块, 长度:", len(v21_code))

# 2. 从错误位置删除V2.1代码（保留V2.0标记）
content = content.replace(v21_block, '\n// ==================== V2.0: 后端服务对接 ====================', 1)

# 3. 在真正的内联script块中注入V2.1代码
# 找到工作的loadBackendConfig（第二个出现的，在2553-6008块内）
# 在文件末尾的</script>前插入
real_end = content.rfind('</script>')
# 在最后一个</script>前插入V2.1代码
content = content[:real_end] + '\n' + v21_code + '\n' + content[real_end:]

# 4. 在工作的loadBackendConfig中添加自动调用
# 找第二个loadBackendConfig函数中的自动连接代码
# 实际工作的是后面那个（靠近文件末尾的）
old_auto = "    setTimeout(function() { syncFromBackend(true); }, 500);"
# 只替换最后一个出现（真正的函数）
idx = content.rfind(old_auto)
if idx > 0:
    new_auto = old_auto + "\n    setTimeout(function() { loadRealtimeData(); startRealtimeAutoRefresh(); }, 1500);"
    content = content[:idx] + new_auto + content[idx+len(old_auto):]
    print("自动调用已添加到工作的loadBackendConfig")
else:
    print("警告: 未找到自动连接代码位置")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("修复完成！V2.1代码已移到正确的script块")
