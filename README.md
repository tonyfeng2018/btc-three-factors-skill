# BTC三因子评分系统 (v2.0)

## 概要

BTC已从纯投机资产演化为"前瞻性宏观资产"。三因子体系从三个维度打分，满分100分：

| 因子 | 权重 | 满分 |
|------|------|------|
| 全球流动性与风险偏好 | 45% | 45分 |
| 机构采用 & ETF资金流入 | 30% | 30分 |
| 监管环境 & 衍生品 | 25% | 25分 |
| **合计** | **100%** | **100分** |

## 信号阈值

| 分数 | 信号 | 操作 |
|------|------|------|
| ≥72 | 🟢 极强买入 | 立即买入/加仓 |
| 56-71 | ⚪ 观望 | 持仓不动 |
| 26-55 | 🟡 风险提示 | 对冲或部分止盈 |
| ≤25 + 核心扣分项 | 🔴 明确卖出 | 卖出/减仓 |

> 🚨 **动量崩盘**：24h内总分骤降≥30分 → 立即卖出/对冲

## 使用方法

```bash
# 运行评分（最少参数）
python3 scripts/score.py [DXY] [VIX] [ETF日净流入(M)] [Fed信号] [监管状态]

# 示例
python3 scripts/score.py 98.8 16 500 dovish bullish
```

详细参数说明见 `references/scoring.md`

## 目录结构

```
btc-three-factors/
├── SKILL.md                    ← Skill主文件
├── scripts/score.py            ← 评分脚本
└── references/scoring.md       ← 详细评分参考
```

## 数据来源

- ETF数据：Farside / SoSoValue / Bitwise
- On-chain数据：Glassnode / CryptoQuant / Dune
- 宏观数据：TradingView / Yahoo Finance / FRED
- 衍生品数据：Coinglass

## License

MIT
