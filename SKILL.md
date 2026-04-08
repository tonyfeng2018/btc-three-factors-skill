---
name: btc-three-factors
description: BTC三因子评分与短期买卖信号跟踪系统。当用户提到BTC走势分析、BTC评分、BTC买入卖出信号、BTC因子打分、BTC每日跟踪、BTC短期信号、BTC ETF资金流、加密货币宏观分析时激活。
---

# BTC三因子评分系统 v2.0

## 核心概念

BTC已演化为"前瞻性宏观资产"，不再只是风险资产。三因子体系从**全球流动性**、**机构采用**、**监管+衍生品**三个维度打分，满分100分，每日（08:00/21:30北京时间）或重大事件时评分。

---

## 快速执行

```bash
# 快速评分（最少参数）
python3 skills/btc-three-factors/scripts/score.py [DXY] [VIX] [ETF日净流入(M)] [Fed信号] [监管状态]

# 示例：流动性好+ETF大流入+监管利好
python3 skills/btc-three-factors/scripts/score.py 98.8 16 500 dovish bullish

# 全参数版本
python3 skills/btc-three-factors/scripts/score.py 98.8 16 500 dovish bullish
# 配合手动设置：vix=16, etf_daily_net=500e6, fed_signal=dovish, reg_status=bullish
```

---

## 完整参数说明

```python
score_btc(
    # ── Factor 1: 全球流动性（45分）──────────────
    dxy_now=98.8,           # 美元指数当前值
    dxy_7d=99.5,            # 7天前DXY（计算周变化）
    vix=18,                 # VIX恐慌指数
    nasdaq_change=1.5,      # 纳斯达克当日涨跌幅（%）
    spx_change=1.0,         # 标普500当日涨跌幅（%）
    fed_signal="neutral",   # dovish / neutral / hawkish
    liquidity_signal="neutral",  # expanding / neutral

    # ── Factor 2: 机构采用（30分）───────────────
    etf_daily_net=300e6,    # ETF日净流入（美元）
    etf_weekly_net=1e9,     # ETF周净流入（美元）
    has_inst_news=False,    # 有无重大机构动态
    stablecoin_change_7d=0, # 稳定币7天供应变化（美元）

    # ── Factor 3: 监管+衍生品（25分）───────────
    reg_status="neutral",   # bullish / neutral / bearish
    onchain_signal="neutral", # bullish / neutral
    funding_rate=0.001,     # 永续合约资金费率（年化）
    cvd_signal="neutral",   # buy / neutral / sell

    # ── 动量崩盘检测 ──────────────────────────
    total_24h_ago=None,     # 24小时前总分（用于检测动量崩盘）
)
```

---

## 信号与操作

| 分数 | 信号 | 操作 |
|------|------|------|
| **≥ 72** | 🟢 极强买入 | 立即买入/加仓，流动性充裕+ETF流入+情绪高涨 |
| **56-71** | ⚪ 观望 | 持仓不动，市场有支撑但缺爆发动能 |
| **26-55** | 🟡 风险提示 | 不宜追多，对冲或部分止盈 |
| **≤ 25** + 核心扣分项 | 🔴 明确卖出 | 卖出/减仓（ETF流出/美元强势/Fed鹰派任意触发）|

### 🚨 动量崩盘（抢跑规则）
**24h内总分骤降 ≥ 30分** → 无论绝对分数，立即通知"核心逻辑证伪，动量崩盘"，建议立即卖出/对冲。

---

## 数据获取指引

### 必须获取（DXY、VIX、美股）
```bash
# DXY
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=10d"

# VIX
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?interval=1d&range=5d"

# 纳斯达克
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC?interval=1d&range=5d"

# 标普500
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d&range=5d"
```

### ETF数据
- **Farside**: https://farside.co.uk/bitcoin/
- **SoSoValue**: https://sosovalue.com/
- **Bitwise**: https://bitwise.co/

### On-chain数据
- **Glassnode**: 交易所BTC储备、长期持有者供给
- **CryptoQuant**: 稳定币供应、链上流量
- **Dune Analytics**: 稳定币总供应量

### 衍生品数据
- **Coinglass**: 资金费率、CVD

### 监管动态
- 路透/彭博/官方公告
- SEC Twitter / CFTC 最新声明
- 特朗普推文（加密相关内容）

---

## 参考文档

详细评分规则（各子指标得分条件、数据源、操作参数）请见：
→ `references/scoring.md`

---

## BTC特有宏观联动（背景知识）

BTC走势与以下宏观变量强相关：

| 变量 | 相关性 | 说明 |
|------|--------|------|
| DXY | **负相关** | 美元弱 = BTC强（美元信用分流） |
| VIX | **负相关** | 市场恐慌 = 流动性紧张 = 风险资产承压 |
| 美股 | **正相关** | 风险偏好联动（纳指 > 标普） |
| 黄金 | **正相关** | 避险/滞胀叙事共享 |
| M2/美联储资产负债表 | **正相关** | 流动性扩张 = BTC受益 |
| ETF净流入 | **最强正相关** | ETF已是BTC边际定价者 |

---

## 执行流程

1. **收集数据**：获取DXY、VIX、当日美股涨跌、ETF数据、监管新闻
2. **输入参数**：调用 `score_btc()` 或直接运行脚本
3. **解读信号**：根据阈值判断操作
4. **动量检查**：如有24h前数据，检查是否触发动量崩盘
5. **推送报告**：格式化后发送到Telegram

---

## 注意事项

- **ETF平淡日**：无新闻时ETF默认为0，属正常现象，不代表负面
- **DXY周变化**：需要7天前数据才能精确评分，无7天数据时以绝对值为准
- **BTC定位**：BTC已从纯风险资产演化为"数字黄金+宏观前瞻资产"，分析时需并重流动性+机构采用+监管三重框架
- **参数保守原则**：数据不确定时，取中性值（0分）而非乐观值
