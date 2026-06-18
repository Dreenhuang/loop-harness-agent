path = r'G:\ai-gongju\Loop-agent\generate_promo_images.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 精确替换这 6 处
replacements = [
    ('"hook": "宝子们!我发现了一个让产品经理"躺着交付"项目的 AI 神器",',
     '"hook": \'宝子们!我发现了一个让产品经理"躺着交付"项目的 AI 神器\','),

    ('"title": "👥 16 个 AI 角色,组成了你的"虚拟创业公司"",',
     '"title": \'👥 16 个 AI 角色,组成了你的"虚拟创业公司"\','),

    ('"hook": "为什么 AI 写代码总翻车?因为你没给它"剧本"",',
     '"hook": \'为什么 AI 写代码总翻车?因为你没给它"剧本"\','),

    ('"title": "📝 1 块黑板,解决 AI 的"健忘病"",',
     '"title": \'📝 1 块黑板,解决 AI 的"健忘病"\','),

    ('"hook": "AI 聊多了就忘事?给它配个"外部硬盘"就行",',
     '"hook": \'AI 聊多了就忘事?给它配个"外部硬盘"就行\','),

    ('"🛏️ 跟 AI 说:"今晚帮我做完这个 PRD,明早看结果"\\n"',
     '\'🛏️ 跟 AI 说:"今晚帮我做完这个 PRD,明早看结果"\\n\''),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f'✅ 已替换: {old[:50]}...')
    else:
        print(f'❌ 未找到: {old[:50]}...')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('\n所有替换完成')
