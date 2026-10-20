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
    args = ap.parse_args()

    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    if args.check:
        cur = extract_html_data(html)
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
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
