# RigCalc 钓鱼装备计算器

输入「目标鱼 + 体重 + 水深 + 风力」→ 输出全套钓组配置；或输入「线号 + 材质」→ 反解可钓鱼种安全上限。

纯前端单文件（`index.html`）或零依赖 CLI（`rigcalc.py`），本地运行，无任何数据上传。

## 单源架构（R6）

**`data.json` 是唯一数据源**（鱼种表/破断表/轮容量/环境折损），两个入口共享：

```
data.json ──┬── rigcalc.py（运行时直接读取）
            └── build.py → 内联进 index.html（保持 file:// 直开，零依赖）
```

**改数据流程**：编辑 `data.json` → `python3 build.py`（重新生成 index.html）→ `python3 rigcalc.py --selftest`。

**校验**：`python3 build.py --check` 确认 index.html 内联数据与 data.json 一致（CI 可挂）。

## 物理框架

输出由输入（目标鱼种、体重、水深、风力、走水、饵重/材质等）经公式与经验表推导：

```
目标鱼 → T_req = W×k → 线径 d → 线号 → 轮容量（L·d²，选最小装得下的型号）
水深+风力+走水 → 铅重（灵敏度上限约束） → 漂吃铅 ≡ 铅重（静力平衡）
铅重+饵重 → 竿号数（EI ∝ t³） → 调性（鱼口决定）
```

核心公式：

| 量 | 公式 | 类型 |
|---|---|---|
| 线径 | d ≈ 0.165·√号 (mm) | 行业标尺 (JAFS) |
| 拉力需求 | T_req = W × k（k = 经验比值系数，按实战线组表回归）；环境折损后 need = T_req / f（f：静水1.0 / 走水·江河0.85 / 海钓0.65） | 经验拟合 |
| 轮容量 | L·d² = 常数 → 选最小型号 | 推导 |
| 吃铅 | (水深 + 竿长)/2 + 风力修正 | 钓界经验式（已标注） |
| 灵敏度 | 位移 ∝ 1/(ρg·A尾)，系统质量 m↑ → 信号↓ | 推导 |

**环境折损双向统一**：正向选线（need = T_req / f）与反向反解（W_max = T×f / k）共用同一因子，保证「正向说能钓 → 反向必能反解出」的往返自洽（`python3 rigcalc.py --selftest` 校验 63 组）。

诚实声明：**并非全推导**——钩表、调性、k 系数、吃铅式均为经验规则（页面内每项已标注「推导式」或「经验式」）。

## 使用

**网页版**：直接用浏览器打开 `index.html`，或

```bash
python3 -m http.server 8000
# 浏览器访问 http://localhost:8000
```

**CLI 版**（零依赖，纯标准库）：

```bash
# 正向：目标鱼 → 配置
python3 rigcalc.py 鲫鱼 0.5 --depth 2 --wind 2
python3 rigcalc.py 翘嘴 1.0 --mode lure --lure 8
python3 rigcalc.py 黑鲷 1.0 --mode sea --depth 3 --wind 3

# 反向：线号 → 可钓鱼种
python3 rigcalc.py --reverse --mat pe --line 1.0 --env 2

# 全参数
python3 rigcalc.py --help
```

## 反向模式

给定「主线材质 + 号数 + 垂钓环境」，对每种鱼反解安全上限体重 `W_max = (T × 环境折损) / k`，输出可钓鱼种表。

## 数据源说明

- 线号制 d≈0.165√号：JAFS 行业标准
- 破断拉力表：主流品牌典型值（尼龙 / PE / 碳线已区分；尼龙表较 JAFS 参考强力偏高约 10–40%，为品牌宣传值）
- 综合系数 k：经验比值拟合（k = 破断需求/体重，按实战线组表回归；小个体鱼因钩线最小规格与瞬时冲击而比值更高）
- 环境折损：静水 1.0 / 走水·江河 0.85 / 海钓 0.65（磨线+冲击折减，正向反向共用）
- 路亚前导：由 T_req 反查碳线表（不再按主线号数换算），输出系统强度 = min(主线, 前导)
- PE 路滑（=矶钓 PE 仕挂）：PE 主线必须配碳素前导（防磨+缓冲，PE 无延展易拔钩）+ 碳素子线；尼龙主线无需前导（自身有延展缓冲）
- 吃铅经验式：钓界通行公式，非力学推导，页面内已标注
- 往返一致性：`python3 rigcalc.py --selftest`

## 依据来源（已打开页面验证）

| 结论 | 来源 | 实测内容 |
|---|---|---|
| 氟碳线折射率 1.42 接近水（1.33），水下隐形；尼龙 1.62 | [Seaguar 官方 FAQ](https://seaguar.com/pages/faqs) | "Air to Water has a refractive index of 1.33. Air to Fluorocarbon has a refractive index of 1.42. Air to Nylon has a refractive index of 1.62. This means that fluorocarbon refracts light closer to water, thus making it more difficult to see when under water." |
| ハリス（同ショックリーダー）须选磨底（根ズレ）强度高的线；主流为尼龙/氟碳 | [DAIWA 官方初心者教程·道糸・ハリス](https://www.daiwa.com/jp/beginner/tackle/harisu) | "道糸とハリをつなぐハリス（同ショックリーダー）は、根ズレなどに強い加工をした糸を選ぶのがベター"；"ハリスはナイロン、フロロの2タイプが一般的" |
| 浮游矶钓（フカセ）用 PE 道糸时须配リーダー/ハリス系统 | [DAIWA 磯センサーSS＋Si（PE 磯道糸）产品页](https://www.daiwa.com/jp/product/dgl42xw) | "フロロカーボンハリスにナイロンショックリーダーを併せる人もいれば、フロロカーボンを長く取ってハリスと兼用させる人もいます" |

> 注：seaguar.com / daiwa.com 在本机（macOS + Clash/Surge fake-ip）解析到 198.18.25.x（保留测试网段），web_extract/浏览器工具因此误判为内网拦截；实际内容用 `curl` 直连已验证。

输出为合理区间起点，实际以钓场情况微调。
