import io

with open(r'G:\ai-gongju\Loop-agent\generate_promo_images.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 把所有中文引号字符统一替换为单引号,避免与Python字符串边界冲突
content = content.replace('\u201c', "'")   # " left double quote
content = content.replace('\u201d', "'")   # " right double quote
content = content.replace('\u2018', "'")   # ' left single quote
content = content.replace('\u2019', "'")   # ' right single quote

with open(r'G:\ai-gongju\Loop-agent\generate_promo_images.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('替换完成')
