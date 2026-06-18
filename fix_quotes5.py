import re

path = r'G:\ai-gongju\Loop-agent\generate_promo_images.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找出所有 "body": ( 块,然后给里面所有不以逗号/右括号/反斜杠结尾的字符串行加逗号
# 简单办法:把所有以 \n"  开头(不一定是开头),且结尾是 " 且下一行不以 ),/+/,  开头的行
# 太复杂,采用更稳的策略:对 body 块内部(从 " 到 )),所有以 \n"  单独成行的加逗号
# 启发:行内容只包含 "..." 字符串(以 " 开头和结尾),且不是最后一行 ), 开头
in_body = False
brace_depth = 0
for i, line in enumerate(lines):
    stripped = line.rstrip('\n').rstrip()
    if '"body":' in stripped and '(' in stripped:
        in_body = True
        brace_depth = stripped.count('(') - stripped.count(')')
        continue
    if in_body:
        if stripped == '),':
            in_body = False
            continue
        # 内部行:如果以 "..." 开头和结尾(可能含 \n),且结尾没逗号,补一个
        if stripped.startswith('"') and stripped.endswith('"'):
            if not stripped.endswith('",'):
                lines[i] = line.rstrip('\n').rstrip() + ',\n'
        elif stripped.startswith("'") and stripped.endswith("'"):
            if not stripped.endswith("',"):
                lines[i] = line.rstrip('\n').rstrip() + ',\n'
        brace_depth += stripped.count('(') - stripped.count(')')
        if brace_depth <= 0 and in_body:
            in_body = False

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('body 块内字符串行已补齐逗号')

# 再次校验
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('✅ 语法 OK')
except py_compile.PyCompileError as e:
    print(f'❌ 仍报错: {e}')
