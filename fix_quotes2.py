import re
import sys

path = r'G:\ai-gongju\Loop-agent\generate_promo_images.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 扫描每一行,如果在双引号字符串中出现 ASCII 的 " 字符,标记出来
for i, line in enumerate(lines, 1):
    # 简单启发: 查找 ": "..." 模式,且字符串里又出现 " 字符
    if '"' in line:
        # 统计 ASCII 双引号数量
        count = line.count('"')
        if count > 2 and count % 2 == 0:
            # 看是不是成对出现
            # 如果在 ": "..." 内部还有 ",说明有问题
            # 启发:字符串开始: ": "  字符串结束: ",  或 "}
            m = re.search(r':\s*"(.*)"', line)
            if m:
                inner = m.group(1)
                if '"' in inner:
                    print(f"L{i}: {line.rstrip()}")
                    # 显示所有 " 的位置
                    pos = [j for j, c in enumerate(line) if c == '"']
                    print(f"     \" at columns: {pos}")
