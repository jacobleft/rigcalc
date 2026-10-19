#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RigCalc 单源构建器：data.json → index.html 内联数据块

数据单一来源：data.json
  - rigcalc.py  运行时直接读取 data.json
  - index.html  由本脚本把 data.json 内联进页面（保持 file:// 直开，零依赖）

用法:
  python3 build.py            # 重新生成 index.html（数据改动后必须跑）
  python3 build.py --check    # 校验 index.html 内联数据与 data.json 一致（不写文件）
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data.json")
HTML_PATH = os.path.join(HERE, "index.html")

BEGIN = "/*__RIGDATA_BEGIN__*/"
END = "/*__RIGDATA_END__*/"
PATTERN = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)

# ---- 钩型互换表生成（HOOK_XREF 由 HOOK_DIMS 钩门宽聚类导出，--check 强制自洽）----
XREF_CENTERS = [2.9, 3.5, 4.1, 4.8, 5.5, 6.4, 7.4, 8.2]   # 档位中心（钩门宽 mm）
XREF_BOUNDS = [3.2, 3.8, 4.45, 5.15, 5.95, 6.9, 7.8]       # 相邻中心的中点边界


def gen_hook_xref(hook_dims):
    """从 HOOK_DIMS 聚类生成互换表：每档内每钩型取距档位中心最近的号数。"""
    def band(g):
        for i, b in enumerate(XREF_BOUNDS):
            if g < b:
                return i
        return len(XREF_BOUNDS)

    slots = {}
    for t, sizes in hook_dims.items():
        for no, dims in sizes.items():
            g = dims[1]
            bi = band(g)
            cand = (abs(g - XREF_CENTERS[bi]), no, g)
            cur = slots.setdefault(bi, {}).setdefault(t)
            if cur is None or cand < cur:
                slots[bi][t] = cand

    types = list(hook_dims.keys())
    rows = []
    for bi in sorted(slots):
        row = {}
        gaps = []
        for t in types:
            c = slots[bi].get(t)
            if c:
                row[t] = c[1]
                gaps.append(c[2])
            else:
                row[t] = "—"
        row = {"gap": f"{min(gaps):.1f}–{max(gaps):.1f}", **{t: row[t] for t in types}}
        rows.append(row)
    return rows


def inline_js(data):
    """把 data.json 内容序列化成 JS 常量定义块（保留 BEGIN/END 标记）。"""
    js = json.dumps(data, ensure_ascii=False, indent=2)
    return f"{BEGIN}\nconst RIGDATA = {js};\n{END}"


def extract_html_data(html):
    m = PATTERN.search(html)
    if not m:
        return None
    block = m.group(0)
    # 从 const RIGDATA = {...}; 中提取 JSON
    start = block.find("{")
    end = block.rfind("}")
    return block[start:end + 1]


def build(html):
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    new_block = inline_js(data)
    if not PATTERN.search(html):
        raise SystemExit(f"错误: {HTML_PATH} 中找不到数据标记 {BEGIN}…{END}")
    return PATTERN.sub(lambda _: new_block, html)


def main():
    ap = argparse.ArgumentParser(description="RigCalc 单源构建器")
    ap.add_argument("--check", action="store_true", help="校验模式：比较 index.html 内联数据与 data.json，不写文件")
    ap.add_argument("--regen-xref", action="store_true", help="从 HOOK_DIMS 重新生成 HOOK_XREF 并写回 data.json")
    args = ap.parse_args()

    if args.regen_xref:
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        data["HOOK_XREF"] = gen_hook_xref(data["HOOK_DIMS"])
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"OK: HOOK_XREF 已从 HOOK_DIMS 重新生成（{len(data['HOOK_XREF'])} 档）")
        return 0

    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    if args.check:
        cur = extract_html_data(html)
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # HOOK_XREF 必须由 HOOK_DIMS 聚类导出（防双源漂移）
        if "HOOK_DIMS" in data:
            expect = gen_hook_xref(data["HOOK_DIMS"])
            if data.get("HOOK_XREF") != expect:
                print("CHECK FAIL: HOOK_XREF 与 HOOK_DIMS 不自洽 — 请运行 python3 build.py --regen-xref")
                return 1
        fresh = json.dumps(data, ensure_ascii=False, indent=2)
        # 对比时忽略空白差异
        if cur is None:
            print("CHECK FAIL: index.html 缺少内联数据块")
            return 1
        cur_js = json.dumps(json.loads(cur), ensure_ascii=False, indent=2)
        if cur_js == fresh:
            print("CHECK PASS: index.html 数据与 data.json 一致")
            return 0
        print("CHECK FAIL: index.html 数据与 data.json 不一致 — 请运行 python3 build.py")
        return 1

    new_html = build(html)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"OK: {HTML_PATH} 已更新（数据来自 data.json）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
