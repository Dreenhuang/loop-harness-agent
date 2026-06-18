# -*- coding: utf-8 -*-
"""
Loop Agent · 小红书宣传图 7 张批量生成
统一视觉:深空蓝 + 霓虹青 + 紫罗兰,16:9,科技感
"""
import os
import json
import time
import requests
import base64
from pathlib import Path

API_KEY = "sk-cp-JHOJy4nZ1XNkHq_xf1e-ulEr-2o2KTuDloK68mnIYaSV4k39CWFr9Ep9FxFZQ-s3iP8qsnPDJQ-EV1dJy2mLaq7IFN38X6zZQK63lwJHBTrXzi93GmVW048"
URL = "https://api.minimaxi.com/v1/image_generation"
OUTPUT_DIR = Path(r"G:\ai-gongju\Loop-agent\promo-images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL = "image-01"
ASPECT = "16:9"

# 7 张图的英文提示词
IMG_PROMPTS = {
    "01-cover.png": (
        "A cinematic dark sci-fi hero poster of an AI virtual company headquarters in deep space, "
        "with a glowing glassmorphism command center floating in the center, "
        "neon cyan and violet holographic dashboards orbiting around a central core, "
        "16 luminous agent avatars arranged in a circular formation like a virtual team, "
        "background is deep midnight blue with subtle starfield and volumetric god rays, "
        "foreground features a large glowing 3D logo placeholder in futuristic sans-serif typography, "
        "particles of light flowing through data streams connecting all elements, "
        "cinematic depth of field, ultra-wide 16:9 composition, 8K detail, hyperrealistic digital art, "
        "futuristic corporate aesthetic, glass and chrome materials, blue and violet neon glow, "
        "sense of intelligence, automation and reliability, professional tech advertising style"
    ),
    "02-agents.png": (
        "A futuristic hexagonal hive visualization showing 16 distinct AI agent avatars "
        "in a 3D holographic grid, each avatar is a glowing translucent glass cube with a unique icon, "
        "color palette deep midnight blue background with neon cyan and electric violet, "
        "connecting lines between agents forming a neural network, particles of data flowing between nodes, "
        "central larger node with golden glow, "
        "isometric perspective, clean tech illustration style, glassmorphism, "
        "floating in a digital void with subtle grid floor, "
        "ultra-wide 16:9 composition, 8K resolution, professional SaaS product visualization"
    ),
    "03-pipeline.png": (
        "A cinematic wide-angle view of a futuristic automated production line factory extending into the vanishing point, "
        "10 distinct glowing workstations arranged sequentially like a high-tech assembly line in a clean room, "
        "each station in a different accent color, "
        "automated robotic arms and holographic displays at each station, "
        "conveyor belt carrying a glowing data package through all stages, "
        "dark industrial sci-fi environment with volumetric lighting and atmospheric fog, "
        "deep blue background with neon accent lights, clean and futuristic, "
        "8K hyperrealistic digital art, ultra-wide 16:9 aspect ratio, "
        "professional industrial design visualization, sense of efficiency and progress"
    ),
    "04-gates.png": (
        "A dramatic 4-tier security checkpoint scene in a futuristic space station corridor, "
        "4 massive glowing security gates in sequence each with a distinct symbolic icon, "
        "red laser scanner lines at each gate, holographic red warning signs, "
        "green check marks for passed items floating above, "
        "dark sci-fi atmosphere with volumetric fog, neon edge lighting, "
        "concrete metal floor with reflections, blue and violet dominant palette, "
        "cinematic depth of field, ultra-wide 16:9 composition, "
        "8K hyperrealistic, conveys quality assurance and rigor"
    ),
    "05-blackboard.png": (
        "A giant glowing holographic blackboard floating in a dark futuristic control room, "
        "the blackboard shows structured project progress notes in glowing text, "
        "with sections marked with emoji-style icons, "
        "developers in silhouette pointing at the board with laser pointers, "
        "AI agent avatars gathering around the board reading the information, "
        "data streams flowing from the board into multiple screens, "
        "color palette deep midnight blue background, neon cyan text and lines, "
        "violet highlights, occasional amber warning indicators, "
        "glassmorphism panels on the blackboard, subtle particle effects, "
        "ultra-wide 16:9 cinematic composition, 8K detail, "
        "professional control room visualization, conveys memory persistence and team collaboration"
    ),
    "06-mcp-server.png": (
        "A breathtaking visualization of multiple AI brains connected to a central hub via glowing USB-like cables, "
        "the central hub is a futuristic hexagonal server module in pulsing neon cyan, "
        "6 different AI brain models connected to the hub, "
        "data packets traveling as bright light streams along the cables, "
        "background is deep space with stars and nebula in deep blue and purple, "
        "volumetric god rays from the central hub, "
        "glassmorphism panels around the hub, "
        "ultra-wide 16:9 cinematic composition, 8K hyperrealistic, "
        "concepts of standardization, interoperability, and protocol, "
        "professional tech product visualization, sci-fi atmosphere"
    ),
    "07-unattended.png": (
        "A cinematic wide shot of a smart home control room at night with floor-to-ceiling windows, "
        "outside is a starry night sky and city lights, "
        "inside a holographic dashboard glows showing automated AI workflows running, "
        "a coffee cup and sleeping cat on the desk, suggesting the human is asleep, "
        "the AI agents are visualized as small glowing robots autonomously working on different tasks, "
        "a large countdown timer showing hours remaining, "
        "morning sunrise visible on the horizon through the window, "
        "color palette deep midnight blue transitioning to warm sunrise orange and gold, "
        "neon cyan and violet dashboard glows, warm amber ambient lighting, "
        "atmospheric volumetric fog, sense of calm automation, "
        "ultra-wide 16:9 cinematic composition, 8K hyperrealistic, "
        "cozy yet futuristic, conveys trust in AI automation"
    ),
}

# 7 张图的小红书文案
COPYWRITING = {
    "01-cover.png": {
        "title": "🚀 AI 时代的产品开发流水线",
        "hook": "宝子们!我发现了一个让产品经理躺着交付项目的 AI 神器",
        "body": (
            "姐妹们兄弟们!今天必须安利这个 Loop Agent 项目——\n"
            "\n"
            "🤖 它把一家公司的全部岗位(16 个!)装进了 AI:\n"
            "产品经理、需求分析师、UX/UI 设计师、架构师、\n"
            "前后端工程师、Bug 修复员、3 道安检员、文档员、终审员……\n"
            "\n"
            "🔧 还自带 10 阶段流水线 + 4 道质量门禁 + 1 块黑板:\n"
            "需求→设计→架构→开发→测试→部署,一步不漏。\n"
            "\n"
            "💡 最绝的是:MCP Server 让 Claude/GPT/Gemini 全都能用,\n"
            "换 AI 也不丢流程!\n"
            "\n"
            "🌙 还能开无人值守模式,睡前说一声,明早直接拿成果!\n"
            "\n"
            "📌 适合:Vibe Coding 玩家、想提效的独立开发者、小团队 PM"
        ),
        "hashtags": "#AI编程 #VibeCoding #产品经理 #自动化开发 #AIAgent #开源项目 #程序员日常",
    },
    "02-agents.png": {
        "title": "👥 16 个 AI 角色,组成了你的虚拟创业公司",
        "hook": "1 个 PM + 1 套 AI 团队 = 0 个员工也能交付产品",
        "body": (
            "你以为 AI 只能写代码?Naive!\n"
            "\n"
            "Loop Agent 给你配齐了 16 个岗位的 AI 员工:\n"
            "\n"
            "📋 决策层:@Product-Manager(你)\n"
            "🎨 业务层:@Requirements / @UX / @UI / @Architect\n"
            "💻 技术层:@Backend / @Frontend / @Bug-Fixer / @DevOps\n"
            "🔍 质量层:@Code-Reviewer / @Performance / @Tester\n"
            "📚 交付层:@Documenter / @Final-Reviewer\n"
            "🧠 知识层:@Knowledge-Curator\n"
            "\n"
            "✨ 关键设计:Maker-Checker 分离!\n"
            "干活的人和检查的人不能是同一个 AI ——\n"
            "保证质量门禁不会自欺欺人!\n"
            "\n"
            "🎯 启示:真实团队也是这个道理,别让全栈扛所有活。"
        ),
        "hashtags": "#AI团队 #Agent #产品经理 #团队管理 #VibeCoding #程序员 #效率工具",
    },
    "03-pipeline.png": {
        "title": "⚙️ 10 个阶段,像工厂流水线一样稳定",
        "hook": "为什么 AI 写代码总翻车?因为你没给它剧本",
        "body": (
            "宝子们有没有这种体验:\n"
            "让 AI 写代码,要么写一半跑偏,要么写完不能用?\n"
            "\n"
            "🤔 问题不是 AI 笨,是没流程!\n"
            "\n"
            "Loop Agent 给 AI 安排了 10 阶段剧本:\n"
            "\n"
            "1️⃣ 初始化(建黑板+加载资产)\n"
            "2️⃣ 需求基线(PRD)\n"
            "3️⃣ 交互设计(用户旅程)\n"
            "4️⃣ 视觉设计(设计稿+组件库)\n"
            "5️⃣ 技术架构(选型+API)\n"
            "6️⃣ 并行开发(后端+前端)\n"
            "7️⃣ 质量门禁(3 道安检)\n"
            "8️⃣ 知识沉淀(踩坑记录)\n"
            "9️⃣ 文档归档(API+用户手册)\n"
            "🔟 部署上线\n"
            "\n"
            "🎯 启示:产品 Roadmap 也能这么拆!\n"
            "从抽象到具体,每个阶段都有明确产物。"
        ),
        "hashtags": "#产品开发流程 #Roadmap #产品经理 #AI自动化 #软件开发 #VibeCoding",
    },
    "04-gates.png": {
        "title": "🛡️ 4 道门禁:问题产品休想上线!",
        "hook": "AI 写的代码不测试就上线?等着 P0 事故吧",
        "body": (
            "质量不是测出来的,是流程里长出来的!\n"
            "\n"
            "Loop Agent 的 4 道门禁,每道只盯一个维度:\n"
            "\n"
            "🚧 Gate 1 · 代码审查\n"
            "   负责人:@Code-Reviewer\n"
            "   标准:0 Blocker + 0 Major\n"
            "   不通过 → 回到 Phase 5 重写\n"
            "\n"
            "⚡ Gate 2 · 性能压测\n"
            "   负责人:@Performance-Engineer\n"
            "   标准:P95 ≤ 300ms,错误率 ≤ 0.1%\n"
            "   不通过 → 回去优化\n"
            "\n"
            "🧪 Gate 3 · 功能测试\n"
            "   负责人:@全栈测试员\n"
            "   标准:P0/P1 Bug = 0,P2 ≤ 3 个\n"
            "   不通过 → 回去修\n"
            "\n"
            "👑 Gate 4 · 终审\n"
            "   负责人:@Final-Reviewer\n"
            "   标准:风险等级 ≤ LOW\n"
            "   不通过 → 全流程返工\n"
            "\n"
            "💡 产品经理的启示:\n"
            "需求评审、设计评审、灰度发布……本质都是门禁!"
        ),
        "hashtags": "#质量保障 #软件测试 #代码审查 #产品经理 #性能优化 #DevOps",
    },
    "05-blackboard.png": {
        "title": "📝 1 块黑板,解决 AI 的健忘病",
        "hook": "AI 聊多了就忘事?给它配个外部硬盘就行",
        "body": (
            "你肯定遇到过:\n"
            "AI 写代码写到一半,前面说过啥全忘了,只能从头来?😩\n"
            "\n"
            "Loop Agent 的解法:把记忆从 AI 脑子里搬出来!\n"
            "\n"
            "📋 项目进度记录.md(黑板)长这样:\n"
            "\n"
            "## 【2026-06-17｜Phase 5 完成】\n"
            "### ✅ 已完成:后端 API + 前端组件\n"
            "### ⚠️ 不确定:性能是否达标\n"
            "### ❌ 待解决:数据库查询慢\n"
            "### 📋 下一步:进入 Gate 1 代码审查\n"
            "\n"
            "🎯 这套机制叫 Ralph 模式:\n"
            "• AI 每轮重置上下文,但状态全在黑板\n"
            "• 切换 AI 模型不丢进度\n"
            "• 新开会话先读黑板,自动续上记忆\n"
            "\n"
            "💡 PM 启示:你的团队也需要黑板!\n"
            "周报、Slack、Trello —— 重要信息不要只装人脑里!"
        ),
        "hashtags": "#AI记忆 #团队协作 #信息管理 #产品经理 #VibeCoding #效率提升",
    },
    "06-mcp-server.png": {
        "title": "🔌 MCP Server · AI 时代的 USB 标准",
        "hook": "换 AI 模型就要重学一遍?这事儿被 MCP 终结了",
        "body": (
            "MCP = Model Context Protocol,AI 世界的 USB 接口!\n"
            "\n"
            "🤔 你可能听过这个痛点:\n"
            "今天用 Claude 写了一套 AI 工作流,\n"
            "明天想换 GPT,得重新写一遍调用代码 😭\n"
            "\n"
            "✨ Loop Agent 的解法:把调度逻辑全部包成 MCP Server!\n"
            "\n"
            "🎯 6 个标准动作,所有 AI 都能调:\n"
            "• start_loop 启动流水线\n"
            "• get_status 查进度\n"
            "• spawn_agent 派活给某个 AI 角色\n"
            "• save_blackboard 写黑板\n"
            "• list_agents 查花名册\n"
            "• abort_loop 紧急刹车\n"
            "\n"
            "🔓 好处:\n"
            "• 换 AI 不换流程(Claude→GPT→Gemini 都行)\n"
            "• 规矩由 Server 守,AI 不会偷懒或忘事\n"
            "• 多人多 AI 并行使用同一个 Server\n"
            "\n"
            "💡 产品经理启示:\n"
            "你的产品要不要 Agent 化?看有没有可被一句话描述的明确动作!"
        ),
        "hashtags": "#MCP #AI工具 #产品经理 #VibeCoding #开源项目 #AI标准 #Claude",
    },
    "07-unattended.png": {
        "title": "🌙 睡前说一声,明早直接拿成果",
        "hook": "AI 自动写代码到天亮?这不是科幻,Loop Agent 已经实现",
        "body": (
            "打工人の终极梦想:躺着也能交付项目!\n"
            "\n"
            "Loop Agent 的无人值守模式做到了:\n"
            "\n"
            "⏰ 设定时间预算(默认 9 小时)\n"
            "🛏️ 跟 AI 说:今晚帮我做完这个 PRD,明早看结果\n"
            "🤖 AI 自动跑完全流程:\n"
            "   • 遇到不确定 → 自动决策\n"
            "   • 遇到错误 → 自动重试 / 回滚\n"
            "   • 撞预算 → 自动停止 + 报告\n"
            "📊 明早醒来:完整夜间作业报告摆在你面前\n"
            "\n"
            "🎯 适合场景:\n"
            "• 周末想跑个完整 Demo?\n"
            "• 周五下班前想启动一个功能?\n"
            "• 不想半夜被叫起来 review 代码?\n"
            "\n"
            "💡 6 条铁律:\n"
            "不中断、最小影响、完整执行、决策可审计、时间有预算、早晨有报告\n"
            "\n"
            "📌 适合:Vibe Coding 重度玩家、独立开发者、小团队"
        ),
        "hashtags": "#无人值守 #AI编程 #VibeCoding #效率工具 #懒人神器 #自动化 #AI产品",
    },
}


def generate_one(filename, prompt, idx):
    print(f"\n[{idx+1}/7] 正在生成: {filename}")
    print(f"   提示词长度: {len(prompt)} 字符")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "aspect_ratio": ASPECT,
        "response_format": "base64",
    }
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data or "image_base64" not in data.get("data", {}):
            print(f"   ❌ API 返回异常: {json.dumps(data, ensure_ascii=False)[:300]}")
            return None
        img_b64 = data["data"]["image_base64"][0]
        out_path = OUTPUT_DIR / filename
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(img_b64))
        size_kb = out_path.stat().st_size / 1024
        print(f"   ✅ 已保存 ({size_kb:.1f} KB)")
        return out_path
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        return None


def main():
    print("=" * 60)
    print("🎨 Loop Agent · 小红书宣传图 7 张批量生成")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    results = []
    files = list(IMG_PROMPTS.keys())
    for i, filename in enumerate(files):
        path = generate_one(filename, IMG_PROMPTS[filename], i)
        results.append({
            "index": i + 1,
            "filename": filename,
            "path": str(path) if path else None,
            "success": path is not None,
            "copy": COPYWRITING[filename],
        })
        if i < len(files) - 1:
            time.sleep(2)

    # 写出文案总览
    summary_path = OUTPUT_DIR / "文案总览.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 同时输出 markdown 版文案,方便复制到小红书
    md_path = OUTPUT_DIR / "文案总览.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Loop Agent 小红书宣传图 · 文案总览\n\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        for r in results:
            c = r["copy"]
            f.write(f"## {r['index']}. {c['title']}\n\n")
            f.write(f"**图片文件**: `{r['filename']}`\n\n")
            f.write(f"**Hook(首行)**: {c['hook']}\n\n")
            f.write(f"**正文**:\n\n{c['body']}\n\n")
            f.write(f"**话题标签**: {c['hashtags']}\n\n")
            f.write("---\n\n")

    success = sum(1 for r in results if r["success"])
    print("\n" + "=" * 60)
    print(f"🎉 完成!{success}/7 张图片生成成功")
    print(f"📂 图片: {OUTPUT_DIR}")
    print(f"📋 文案 JSON: {summary_path}")
    print(f"📋 文案 Markdown: {md_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
