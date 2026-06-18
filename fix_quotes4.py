path = r'G:\ai-gongju\Loop-agent\generate_promo_images.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复:第 186 行末尾的 hook 字符串少了一个逗号
old = '"hook": \'宝子们!我发现了一个让产品经理"躺着交付"项目的 AI 神器\',\n'
new = '"hook": \'宝子们!我发现了一个让产品经理"躺着交付"项目的 AI 神器\',\n'
# 实际差异是原行末尾的 '"' 后面没逗号
# 先看具体行内容
import re
m = re.search(r'(\"hook\": \'宝子们!我发现了一个让产品经理\"躺着交付\"项目的 AI 神器\')([^\n]*)', content)
if m:
    print(f"找到: |{m.group(1)}|{m.group(2)}|")
    # 把 group(2) 设为 ','
    content = content.replace(m.group(0), m.group(1) + ',', 1)
    print("已添加逗号")
else:
    print("未找到,尝试备用方案")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
