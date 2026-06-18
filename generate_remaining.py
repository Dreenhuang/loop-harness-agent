# -*- coding: utf-8 -*-
"""只生成剩余的 4~7 张"""
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

REMAIN = {
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

headers = {"Authorization": f"Bearer {API_KEY}"}
for i, (filename, prompt) in enumerate(REMAIN.items()):
    out_path = OUTPUT_DIR / filename
    if out_path.exists() and out_path.stat().st_size > 50000:
        print(f"[{i+1}/4] 跳过(已存在): {filename}")
        continue
    print(f"[{i+1}/4] 生成中: {filename} (prompt {len(prompt)} chars)")
    try:
        resp = requests.post(URL, headers=headers, json={
            "model": "image-01",
            "prompt": prompt,
            "n": 1,
            "aspect_ratio": "16:9",
            "response_format": "base64",
        }, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        if "data" in data and "image_base64" in data["data"]:
            img_b64 = data["data"]["image_base64"][0]
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            print(f"   ✅ 已保存 ({out_path.stat().st_size/1024:.1f} KB)")
        else:
            print(f"   ❌ 异常: {json.dumps(data)[:200]}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    if i < len(REMAIN) - 1:
        time.sleep(2)

print("\n🎉 全部完成")
