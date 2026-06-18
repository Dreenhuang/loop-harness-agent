# -*- coding: utf-8 -*-
"""输出 7 张图的最终交付清单"""
import os
from pathlib import Path

OUT = Path(r"G:\ai-gongju\Loop-agent\promo-images")
files = sorted(OUT.glob("*.png"))

print("="*70)
print("🎨 Loop Agent 小红书宣传图 · 最终交付清单")
print("="*70)
print()
total_kb = 0
for f in files:
    kb = f.stat().st_size / 1024
    total_kb += kb
    print(f"  {f.name:25s}  {kb:>8.1f} KB")
print()
print(f"  共 {len(files)} 张图,总大小 {total_kb/1024:.2f} MB")
print(f"  路径: {OUT}")
print()
print("="*70)
print("📋 文案交付物:")
print("="*70)
for f in OUT.glob("*.md"):
    print(f"  {f.name}  ({f.stat().st_size/1024:.1f} KB)")
for f in OUT.glob("*.json"):
    print(f"  {f.name}  ({f.stat().st_size/1024:.1f} KB)")
