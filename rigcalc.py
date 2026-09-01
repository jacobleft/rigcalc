#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RigCalc CLI — 钓鱼装备计算器（与网页版同一套公式/数据）
用法:
  正向:  rigcalc.py 鲫鱼 0.5 --depth 2 --wind 2 --mode tai
  反向:  rigcalc.py --reverse --mat nylon --line 1.5 --env 0
依赖: 无（纯标准库）
"""

import argparse
import math
import sys

# ---------------- 数据（与 index.html 保持同步） ----------------
FISH = [
    {"name": "白条",  "min": 0.02, "max": 0.2,  "k": 15,  "bite": "轻口", "salt": False},
    {"name": "罗非仔","min": 0.05, "max": 0.3,  "k": 10,  "bite": "正常", "salt": False},
    {"name": "鲫鱼",  "min": 0.1,  "max": 1.5,  "k": 4,   "bite": "轻口", "salt": False},
    {"name": "罗非",  "min": 0.3,  "max": 2.5,  "k": 3.7, "bite": "猛口", "salt": False},
    {"name": "鲮鱼",  "min": 0.3,  "max": 2,    "k": 3.7, "bite": "正常", "salt": False},
    {"name": "鲤鱼",  "min": 0.5,  "max": 15,   "k": 2.0, "bite": "正常", "salt": False},
    {"name": "草鱼",  "min": 0.5,  "max": 15,   "k": 2.2, "bite": "正常", "salt": False},
    {"name": "鲢鳙",  "min": 1,    "max": 20,   "k": 1.7, "bite": "猛口", "salt": False},
    {"name": "翘嘴",  "min": 0.2,  "max": 8,    "k": 3.0, "bite": "猛口", "salt": False},
    {"name": "沙尖",  "min": 0.05, "max": 0.3,  "k": 13,  "bite": "轻口", "salt": True},
    {"name": "黑鲷",  "min": 0.3,  "max": 4,    "k": 4.5, "bite": "猛口", "salt": True},
    {"name": "海鲈",  "min": 0.5,  "max": 10,   "k": 2.8, "bite": "猛口", "salt": True},
]

BREAK = {
    "nylon": {0.3:0.8,0.4:1.0,0.6:1.5,0.8:2.0,1.0:2.5,1.2:3.0,1.5:3.7,2.0:4.5,2.5:5.5,3.0:6.5,3.5:7.5,4.0:8.5,5.0:10.5,6.0:12.5},
    "pe":    {0.4:4,0.6:6,0.8:8,1.0:10,1.2:12,1.5:15,2.0:20,2.5:25,3.0:30},
    "carbon":{0.4:1.1,0.6:1.6,0.8:2.1,1.0:2.6,1.2:3.2,1.5:3.9,2.0:4.8,2.5:5.8,3.0:6.8},
}
LINE_ORDER = {
    "nylon": [0.3,0.4,0.6,0.8,1.0,1.2,1.5,2.0,2.5,3.0,3.5,4.0,5.0,6.0],
    "pe":    [0.4,0.6,0.8,1.0,1.2,1.5,2.0,2.5,3.0],
}
REEL = {500:80, 1000:100, 2000:200, 2500:250, 3000:300, 4000:400, 5000:500, 6000:600}
DIA_1 = 0.165
REV_ENV_FACTOR = [1.0, 0.85, 0.65]  # 静水/江河缓流/海钓

MODES = {"tai": "台钓", "lusu": "路滑", "lure": "路亚", "sea": "海钓"}
FISH_NAMES = [f["name"] for f in FISH]

# ---------------- 工具 ----------------
def dia(n): return DIA_1 * math.sqrt(n)
def fmt(x): return round(x * 100) / 100

def rod_len_tai(d):
    return 3.6 if d <= 1.5 else 4.5 if d <= 2 else 5.4 if d <= 3 else 6.3 if d <= 4 else 7.2

def pick_line(mat, need_kg):
    for g in LINE_ORDER[mat]:
        if BREAK[mat][g] >= need_kg:
            return g, BREAK[mat][g], False
    last = LINE_ORDER[mat][-1]
    return last, BREAK[mat][last], True

def pick_reel(Lm, d):
    req = Lm * (d / DIA_1) ** 2
    best = None
    for t, cap in REEL.items():
        if cap >= req and (best is None or cap < REEL[best]):
            best = t
    return (best if best else 6000), round(req), best is None

# ---------------- 正向 ----------------
def calc_forward(fish_name, W, depth, wind, cur, mode, mat, lure_w):
    f = next(x for x in FISH if x["name"] == fish_name)
    out = []
    T_req = W * f["k"]

    # 线
    if mode == "lure":
        by_lure = 0.4 if lure_w <= 3 else 0.6 if lure_w <= 7 else 0.8 if lure_w <= 12 else 1.0 if lure_w <= 20 else 1.5
        p1, _, c1 = pick_line("pe", T_req)
        p2, _, c2 = pick_line("pe", BREAK["pe"][by_lure])
        main = max(p1, p2)
        carbon_nos = sorted(BREAK["carbon"].keys())
        lead_no = min(main * 2, main + 1)
        snap = next((c for c in carbon_nos if c >= lead_no), carbon_nos[-1])
        out.append(f"主线: PE {main}号(破断{BREAK['pe'][main]}kg)  前导: 碳线 {snap}号(破断{BREAK['carbon'][snap]}kg)")
    else:
        p, br, capped = pick_line(mat, T_req)
        main = p
        warn = "  ⚠ 超出线表上限，建议换PE或降低目标体重" if capped else ""
        out.append(f"主线: {mat} {p}号(破断{br}kg)  [T_req={fmt(T_req)}kg]{warn}")
        sub_no = max(0.3, round(main * 0.6 * 10) / 10)
        sub_note = " — 主线已最细，子线同号无冗余" if sub_no >= main else ""
        out.append(f"子线: {sub_no}号{sub_note}")

    # 钩
    if mode == "lure":
        out.append("鱼钩: 拟饵自带（三本钩/曲柄钩）")
    elif f["salt"]:
        hook = "千又 1–2号" if W < 0.5 else "千又 2–3号" if W < 1 else "千又 3–5号" if W < 3 else "千又 5–7号"
        out.append(f"鱼钩: {hook}")
    else:
        hook = ("袖钩 1–2号" if W < 0.1 else "袖钩 2–3号" if W < 0.3 else "袖钩 3–5号" if W < 0.8
                else "袖钩 5–6号 / 伊豆 4–5号" if W < 2 else "伊势尼 3–5号" if W < 5
                else "伊势尼 5–8号" if W < 10 else "伊势尼 8–12号")
        out.append(f"鱼钩: {hook}")

    # 竿
    if mode == "tai":
        tune = "37调(偏软)" if f["bite"] == "轻口" else "19调(硬)" if f["bite"] == "猛口" else "28调"
        out.append(f"鱼竿: {rod_len_tai(depth)}m 手竿 · {tune}")
    elif mode == "lusu":
        no = 1.5 if W < 0.5 else 2 if W < 2 else 3 if W < 5 else 4
        out.append(f"鱼竿: {3.6 if depth<=3 else 4.5}m 矶竿 {no}号 · 大导环")
    elif mode == "lure":
        ln = 1.8 if lure_w <= 5 else 2.1 if lure_w <= 12 else 2.4 if lure_w <= 25 else 2.7
        hd = "UL/L" if lure_w <= 5 else "L/ML" if lure_w <= 12 else "M" if lure_w <= 25 else "MH"
        out.append(f"鱼竿: {ln}m {hd} 直柄/枪柄")
    else:
        no = 2 if W < 2 else 3 if W < 5 else 4 if W < 10 else 5
        lead_now = 15 + wind * 3 + (8 if cur == 2 else 0)
        out.append(f"鱼竿: {3.6 if depth<=3 else 4.5}m 海竿 {no}号（号数非锤负荷规范，以铅重≈{lead_now}g为准）")

    # 铅/漂（路亚跳过）
    if mode == "lure":
        pass
    elif mode == "sea":
        lead = 15 + wind * 3 + (8 if cur == 2 else 0)
        out.append(f"铅坠: {lead}g  浮漂: 无漂（看竿稍/铃铛）")
    else:
        rod_len = rod_len_tai(depth) if mode == "tai" else (3.6 if depth <= 3 else 4.5)
        l = 0.5 * (depth + rod_len) + max(0, wind - 2) * 0.3 + (0.5 if cur == 1 else 1.5 if cur == 2 else 0)
        if f["bite"] == "轻口" and l > 1.8:
            l = 1.8
        lead = max(0.8, round(l * 2) / 2)
        tail = "细尾/小碎目" if f["bite"] == "轻口" else ("加粗尾" if wind >= 3 else "常规尾")
        out.append(f"铅坠/漂吃铅: {lead}g  浮漂: 吃铅{lead}g · {tail}")

    # 调钓
    if mode == "tai":
        if cur == 2 or wind >= 4:
            tune_v = "调平水钓2目（跑铅）"
        elif f["bite"] == "轻口":
            tune_v = "调5钓2（差值3>基准2，更灵）"
        elif f["bite"] == "猛口":
            tune_v = "调3钓3（钝滤假口）"
        else:
            tune_v = "调4钓2"
        out.append(f"调钓: {tune_v}")
    elif mode == "lusu":
        out.append(f"调钓: {'露1目·重铅滑漂' if (cur==2 or wind>=4) else '露1–2目'}")
    elif mode == "lure":
        out.append("调钓: 无漂（手感/竿尖传口）")
    else:
        out.append("调钓: 看竿稍抖动 / 挂铃铛")

    # 轮
    if mode == "tai":
        out.append("渔轮: 不适用（手竿无轮）")
    else:
        Lm = 100 if mode == "lure" else 120 if mode == "lusu" else 150
        rtype, req, rcapped = pick_reel(Lm, dia(main))
        ratio = "5.0" if (mode == "lure" and lure_w <= 3) else "6.2" if mode == "lure" else "5.0" if mode == "lusu" else "4.8"
        warn = "  ⚠ 超出轮容量表" if rcapped else ""
        out.append(f"渔轮: {rtype}型纺车轮 · {ratio}:1（容量需求≈{req}）{warn}")

    return out

# ---------------- 反向 ----------------
def calc_reverse(mat, line_no, env):
    keys = sorted(BREAK[mat].keys())
    # 找最接近 line_no 的表内键（向下取整到最近键）
    no = min(keys, key=lambda k: abs(k - line_no))
    T = BREAK[mat][no] * REV_ENV_FACTOR[env]
    rows = []
    for f in FISH:
        if (env == 2) != f["salt"]:
            continue
        wmax = T / f["k"]
        ok = wmax >= f["min"]
        rows.append(f"  {f['name']:<6} 常见{f['min']}–{f['max']}kg  安全上限 ≤{fmt(wmax)}kg  {'✓' if ok else '✗'}")
    return no, T, rows

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(description="RigCalc 钓鱼装备计算器 CLI")
    ap.add_argument("fish", nargs="?", help="目标鱼名: " + "/".join(FISH_NAMES))
    ap.add_argument("weight", nargs="?", type=float, help="目标体重 (kg)")
    ap.add_argument("--mode", choices=MODES.keys(), default="tai", help="钓法 (默认 tai=台钓)")
    ap.add_argument("--depth", type=float, default=2.0, help="水深 (m)")
    ap.add_argument("--wind", type=int, default=2, help="风力 (级)")
    ap.add_argument("--cur", type=int, choices=[0,1,2], default=0, help="走水: 0静 1缓 2急")
    ap.add_argument("--mat", choices=["nylon","pe"], default="nylon", help="主线材质 (正向)")
    ap.add_argument("--lure", type=float, default=8.0, help="拟饵重量 g (路亚模式)")
    ap.add_argument("--reverse", action="store_true", help="反向模式: 给定线号→可钓鱼种")
    ap.add_argument("--line", type=float, default=1.5, help="反向: 主线号数")
    ap.add_argument("--env", type=int, choices=[0,1,2], default=0, help="反向: 0静水 1江河 2海钓")
    args = ap.parse_args()

    if args.reverse:
        no, T, rows = calc_reverse(args.mat, args.line, args.env)
        env_name = ["静水","江河/缓流","海钓"][args.env]
        print(f"线组: {args.mat} {no}号 (破断{BREAK[args.mat][no]}kg × 环境折损{REV_ENV_FACTOR[args.env]} = 有效{T:.1f}kg)  [{env_name}]")
        print("可钓鱼种（安全上限体重）:")
        print("\n".join(rows))
        return

    if not args.fish or args.weight is None:
        print("正向模式需要: rigcalc.py <鱼名> <体重kg> [选项]", file=sys.stderr)
        ap.print_help()
        sys.exit(1)
    if args.fish not in FISH_NAMES:
        print(f"未知鱼种: {args.fish}。可选: {', '.join(FISH_NAMES)}", file=sys.stderr)
        sys.exit(1)

    print(f"【{args.fish} {args.weight}kg · {MODES[args.mode]} · 水深{args.depth}m · {args.wind}级风】")
    for line in calc_forward(args.fish, args.weight, args.depth, args.wind, args.cur, args.mode, args.mat, args.lure):
        print("  " + line)

if __name__ == "__main__":
    main()
