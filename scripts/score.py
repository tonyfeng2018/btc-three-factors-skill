#!/usr/bin/env python3
"""
BTC三因子评分系统 v2.0
参考：BTC三因子跟踪规则框架（2.0优化版）
"""

import sys
import json
from datetime import datetime

# ─────────────────────────────────────────────
#  一、全球流动性与风险偏好（权重45%）
# ─────────────────────────────────────────────

def score_dxy(dxy_now, dxy_7d=None):
    """
    DXY评分规则：
    +15: 持续走弱（连续3日下跌/周跌幅>1%）或绝对值<100.0
     +8: 小幅回落 / 偏弱震荡
      0: 横盘 / 偏强震荡
    -10: 强势反弹（连续上涨/周涨幅>1%）或绝对值>103.0
    """
    score = 0
    detail = ""

    if dxy_now is not None:
        if dxy_now < 100.0:
            score = 15
            detail = f"DXY={dxy_now} < 100，持续弱势 → +15"
        elif dxy_now > 103.0:
            score = -10
            detail = f"DXY={dxy_now} > 103，强势反弹 → -10"
        else:
            if dxy_7d is not None and dxy_7d > 0:
                weekly_change = (dxy_now - dxy_7d) / dxy_7d * 100
                if weekly_change < -1.0:
                    score = 15
                    detail = f"DXY周跌幅>{abs(weekly_change):.1f}%，持续走弱 → +15"
                elif weekly_change < 0:
                    score = 8
                    detail = f"DXY小幅回落（周跌{abs(weekly_change):.1f}%）→ +8"
                elif weekly_change > 1.0:
                    score = -10
                    detail = f"DXY周涨幅>{weekly_change:.1f}%，强势反弹 → -10"
                else:
                    score = 0
                    detail = f"DXY横盘（周变化{weekly_change:+.1f}%）→ 0"
            else:
                score = 0
                detail = f"DXY={dxy_now}（100-103区间，横盘）→ 0"

    return score, detail


def score_vix_risk(vix, nasdaq_change=None, spx_change=None):
    """
    VIX + 美股风险偏好评分：
    +12: VIX < 18 且 纳斯达克/SPX当日上涨 > 0.5%
     +6: VIX 18-22 或 美股小幅波动
      0: VIX > 22 或 美股明显下跌
    """
    score = 0
    detail = ""

    if vix is not None:
        if vix < 18:
            if nasdaq_change is not None and nasdaq_change > 0.5:
                score = 12
                detail = f"VIX={vix}<18 且纳指+{nasdaq_change:.2f}% → +12"
            elif spx_change is not None and spx_change > 0.5:
                score = 12
                detail = f"VIX={vix}<18 且SPX+{spx_change:.2f}% → +12"
            else:
                score = 6
                detail = f"VIX={vix}<18 但美股未明显上涨 → +6"
        elif vix <= 22:
            score = 6
            detail = f"VIX={vix}（18-22区间，偏弱波动）→ +6"
        else:
            score = 0
            detail = f"VIX={vix}>22，恐慌 → 0"
            if nasdaq_change is not None and nasdaq_change < -0.5:
                detail += f"（纳指同时下跌{nasdaq_change:.2f}%）"

    return score, detail


def score_fed_policy(fed_signal):
    """
    Fed政策预期评分：
    +10: 市场定价年内降息预期升温 或 鸽派表态
     0: 中性无明显表态
    -8: 加息预期升温 或 明确紧缩信号
    fed_signal: "dovish" / "neutral" / "hawkish"
    """
    mapping = {"dovish": 10, "neutral": 0, "hawkish": -8}
    score = mapping.get(fed_signal, 0)
    labels = {"dovish": "鸽派/降息预期升温", "neutral": "中性", "hawkish": "鹰派/紧缩"}
    detail = f"Fed={labels.get(fed_signal,'未知')} → {score:+d}"
    return score, detail


def score_global_liquidity(liquidity_signal):
    """
    全球流动性指标（M2/Fed资产负债表趋势）：
    +8: 最近7天有扩张信号（或市场定价宽松）
     0: 无明显扩张
    liquidity_signal: "expanding" / "neutral"
    """
    if liquidity_signal == "expanding":
        return 8, "流动性扩张信号 → +8"
    return 0, "无明显扩张信号 → 0"


# ─────────────────────────────────────────────
#  二、机构采用 & ETF资金流入（权重30%）
# ─────────────────────────────────────────────

def score_etf_flows(etf_daily_net, etf_weekly_net=None):
    """
    US Spot BTC ETF日/周净流入：
    +18: 日净流入 >$300M 或 周流入 >$1B
    +10: $100M-$300M
     0: $0-$100M
    -10: 净流出
    单位：美元，传入数字
    """
    score = 0
    detail = ""

    if etf_daily_net is not None:
        if etf_daily_net < 0:
            score = -10
            detail = f"ETF日净流出${abs(etf_daily_net)/1e6:.1f}M → -10"
        elif etf_daily_net > 300e6:
            score = 18
            detail = f"ETF日净流入${etf_daily_net/1e6:.0f}M>$300M → +18"
        elif etf_daily_net >= 100e6:
            score = 10
            detail = f"ETF日净流入${etf_daily_net/1e6:.0f}M（$100-300M）→ +10"
        else:
            score = 0
            detail = f"ETF日净流入${etf_daily_net/1e6:.0f}M（<$100M）→ 0"
    elif etf_weekly_net is not None:
        if etf_weekly_net > 1e9:
            score = 18
            detail = f"ETF周净流入${etf_weekly_net/1e9:.1f}B>$1B → +18"
        elif etf_weekly_net > 0:
            score = 10
            detail = f"ETF周净流入${etf_weekly_net/1e6:.0f}M → +10"
        else:
            score = 0
            detail = f"ETF周净流入${etf_weekly_net/1e6:.0f}M → 0"

    return score, detail


def score_institutional_news(has_news):
    """
    机构/企业动态：
    +8: 当日或48小时内有重大正面公告
     0: 无
    """
    if has_news:
        return 8, "重大机构/企业利好公告 → +8"
    return 0, "无重大机构动态 → 0"


def score_stablecoin_supply(supply_change_7d=None):
    """
    稳定币供应增长（USDT/USDC）：
    +4: 7天内明显扩张（>$1B）
     0: 持平或萎缩
    """
    if supply_change_7d is not None and supply_change_7d > 1e9:
        return 4, f"稳定币7天扩张${supply_change_7d/1e9:.1f}B → +4"
    return 0, "稳定币供应无明显扩张 → 0"


# ─────────────────────────────────────────────
#  三、监管环境与衍生品（权重25%）
# ─────────────────────────────────────────────

def score_regulatory_news(reg_status):
    """
    监管新闻：
    +12: 当日或48小时内有明确利好进展
     +6: 谈判进行中无突破
      0: 负面或无进展
    reg_status: "bullish" / "neutral" / "bearish"
    """
    mapping = {"bullish": 12, "neutral": 6, "bearish": 0}
    score = mapping.get(reg_status, 0)
    labels = {"bullish": "明确利好", "neutral": "谈判中无突破", "bearish": "负面或无进展"}
    detail = f"监管={labels.get(reg_status,'未知')} → {score:+d}"
    return score, detail


def score_onchain_supply(onchain_signal):
    """
    On-chain供给信号：
    +8: 交易所BTC储备持续下降 或 LTH供给>14.5M且稳定
     0: 持平或上升
    """
    if onchain_signal == "bullish":
        return 8, "交易所BTC储备下降/LTH稳定 → +8"
    return 0, "On-chain供给无明显利好 → 0"


def score_derivatives(funding_rate=None, cvd_signal=None):
    """
    衍生品微观结构：
    +5: 资金费率健康（无极端多头过热）且CVD买盘偏强
     0: 资金费率极度狂热或CVD卖盘主导
    """
    score = 0
    detail = ""

    funding_ok = funding_rate is not None and -0.01 <= funding_rate <= 0.01
    cvd_ok = cvd_signal == "buy" or cvd_signal == "neutral"

    if funding_ok and cvd_signal == "buy":
        score = 5
        detail = "资金费率健康 + CVD买盘偏强 → +5"
    elif funding_ok:
        score = 3
        detail = f"资金费率健康（CVD={cvd_signal}）→ +3"
    elif cvd_signal == "sell":
        score = 0
        detail = "CVD卖盘主导 → 0"
    else:
        detail = "资金费率过热 → 0"

    return score, detail


# ─────────────────────────────────────────────
#  核心信号判断
# ─────────────────────────────────────────────

def get_signal(total):
    if total >= 72:
        return "🟢 买入/加仓", "BTC短期上涨条件已满足，流动性充裕+ETF大额流入+情绪高涨"
    elif total >= 56:
        return "⚪ 观望（持仓不动）", "市场有一定支撑，但不具备立刻爆发动能"
    elif total >= 26:
        return "🟡 风险提示：动能衰退", "缺乏增量资金，宏观信号偏弱，建议对冲或部分止盈"
    else:
        return "🔴 卖出/减仓", "BTC短期下跌风险极高，明确卖出信号"


def check_momentum_crash(total_now, total_24h_ago):
    """检查动量崩盘信号：24h内总分骤降≥30分"""
    if total_24h_ago is not None and total_now is not None:
        drop = total_24h_ago - total_now
        if drop >= 30:
            return True, drop
    return False, 0


# ─────────────────────────────────────────────
#  主评分函数
# ─────────────────────────────────────────────

def score_btc(
    # Factor 1: 流动性（45分）
    dxy_now=None,
    dxy_7d=None,
    vix=None,
    nasdaq_change=None,
    spx_change=None,
    fed_signal="neutral",
    liquidity_signal="neutral",
    # Factor 2: 机构采用（30分）
    etf_daily_net=None,
    etf_weekly_net=None,
    has_inst_news=False,
    stablecoin_change_7d=None,
    # Factor 3: 监管+衍生品（25分）
    reg_status="neutral",
    onchain_signal="neutral",
    funding_rate=None,
    cvd_signal="neutral",
    #  Optional: 24h前总分（用于动量崩盘检测）
    total_24h_ago=None,
):
    """
    BTC三因子综合评分

    参数说明：
    dxy_now          当前DXY指数（如 98.8）
    dxy_7d           7天前DXY指数（用于计算周变化）
    vix              VIX恐慌指数（如 18.5）
    nasdaq_change    纳斯达克当日涨跌幅（如 1.5 代表 +1.5%）
    spx_change       标普500当日涨跌幅
    fed_signal       Fed政策信号：dovish / neutral / hawkish
    liquidity_signal 流动性信号：expanding / neutral

    etf_daily_net    ETF日净流入（美元，如 500e6 = $500M）
    etf_weekly_net   ETF周净流入（美元）
    has_inst_news    是否有重大机构动态（True/False）
    stablecoin_change_7d 稳定币7天供应变化（美元）

    reg_status       监管状态：bullish / neutral / bearish
    onchain_signal   On-chain信号：bullish / neutral
    funding_rate     资金费率（如 0.001 = 0.1%）
    cvd_signal       CVD信号：buy / neutral / sell

    total_24h_ago    24小时前总分（用于动量崩盘检测）

    返回: (总分, 详细结果dict)
    """

    # ── Factor 1 ──
    dxy_score, dxy_detail = score_dxy(dxy_now, dxy_7d)
    vix_score, vix_detail = score_vix_risk(vix, nasdaq_change, spx_change)
    fed_score, fed_detail = score_fed_policy(fed_signal)
    liq_score, liq_detail = score_global_liquidity(liquidity_signal)

    factor1 = dxy_score + vix_score + fed_score + liq_score

    # ── Factor 2 ──
    etf_score, etf_detail = score_etf_flows(etf_daily_net, etf_weekly_net)
    inst_score, inst_detail = score_institutional_news(has_inst_news)
    stable_score, stable_detail = score_stablecoin_supply(stablecoin_change_7d)

    factor2 = etf_score + inst_score + stable_score

    # ── Factor 3 ──
    reg_score, reg_detail = score_regulatory_news(reg_status)
    onchain_score, onchain_detail = score_onchain_supply(onchain_signal)
    deriv_score, deriv_detail = score_derivatives(funding_rate, cvd_signal)

    factor3 = reg_score + onchain_score + deriv_score

    # ── Total ──
    total = factor1 + factor2 + factor3

    # ── Signal ──
    signal, signal_desc = get_signal(total)

    # ── Momentum crash ──
    momentum_crash = False
    crash_drop = 0
    if total_24h_ago is not None:
        momentum_crash, crash_drop = check_momentum_crash(total, total_24h_ago)

    # ── Core penalty flags ──
    core_penalty_triggered = (
        etf_score == -10 or      # ETF日净流出
        dxy_score == -10 or      # 美元强势
        fed_score == -8          # 美联储鹰派
    )

    # ── 结果 ──
    result = {
        "总分": total,
        "信号": signal,
        "信号说明": signal_desc,
        "因子1_流动性": {
            "小计": factor1,
            "DXY": {"得分": dxy_score, "说明": dxy_detail},
            "VIX+风险偏好": {"得分": vix_score, "说明": vix_detail},
            "Fed政策": {"得分": fed_score, "说明": fed_detail},
            "全球流动性": {"得分": liq_score, "说明": liq_detail},
        },
        "因子2_机构采用": {
            "小计": factor2,
            "ETF资金流": {"得分": etf_score, "说明": etf_detail},
            "机构动态": {"得分": inst_score, "说明": inst_detail},
            "稳定币供应": {"得分": stable_score, "说明": stable_detail},
        },
        "因子3_监管+衍生品": {
            "小计": factor3,
            "监管新闻": {"得分": reg_score, "说明": reg_detail},
            "On-chain供给": {"得分": onchain_score, "说明": onchain_detail},
            "衍生品结构": {"得分": deriv_score, "说明": deriv_detail},
        },
        "动量崩盘": momentum_crash,
        "动量崩盘跌幅": crash_drop,
        "核心扣分项触发": core_penalty_triggered,
    }

    return total, result


def print_report(result):
    """打印可读的评分报告"""
    total = result["总分"]
    signal = result["信号"]
    signal_desc = result["信号说明"]
    f1 = result["因子1_流动性"]
    f2 = result["因子2_机构采用"]
    f3 = result["因子3_监管+衍生品"]

    print(f"【BTC三因子评分】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 52)
    print(f"总分：{total}分 → {signal}")
    print(f"说明：{signal_desc}")
    print()

    # 动量崩盘警告
    if result["动量崩盘"]:
        print(f"🚨 动量崩盘警报！24h内骤降 {result['动量崩盘跌幅']} 分！")
        print("   核心逻辑证伪，立即卖出/对冲！")
        print()

    # 核心扣分项
    if result["核心扣分项触发"]:
        print("⚠️ 核心扣分项触发（ETF流出/美元强势/Fed鹰派）")
        print()

    print(f"一、全球流动性与风险偏好（满分45）：{f1['小计']}分")
    print(f"   DXY：           {f1['DXY']['得分']:+d}分  {f1['DXY']['说明']}")
    print(f"   VIX+风险偏好：  {f1['VIX+风险偏好']['得分']:+d}分  {f1['VIX+风险偏好']['说明']}")
    print(f"   Fed政策预期：   {f1['Fed政策']['得分']:+d}分  {f1['Fed政策']['说明']}")
    print(f"   全球流动性：    {f1['全球流动性']['得分']:+d}分  {f1['全球流动性']['说明']}")
    print()

    print(f"二、机构采用 & ETF资金流入（满分30）：{f2['小计']}分")
    print(f"   ETF资金流：     {f2['ETF资金流']['得分']:+d}分  {f2['ETF资金流']['说明']}")
    print(f"   机构动态：      {f2['机构动态']['得分']:+d}分  {f2['机构动态']['说明']}")
    print(f"   稳定币供应：    {f2['稳定币供应']['得分']:+d}分  {f2['稳定币供应']['说明']}")
    print()

    print(f"三、监管环境 & 衍生品（满分25）：{f3['小计']}分")
    print(f"   监管新闻：      {f3['监管新闻']['得分']:+d}分  {f3['监管新闻']['说明']}")
    print(f"   On-chain供给：  {f3['On-chain供给']['得分']:+d}分  {f3['On-chain供给']['说明']}")
    print(f"   衍生品结构：    {f3['衍生品结构']['得分']:+d}分  {f3['衍生品结构']['说明']}")
    print()

    # 信号阈值参考
    print("─── 信号阈值参考 ───")
    print(f"  🟢 ≥72分：买入/加仓（当前{total}分 {'✅' if total>=72 else '❌'}）")
    print(f"  ⚪ 56-71分：观望（持仓不动）{'✅' if 56<=total<=71 else ''}")
    print(f"  🟡 26-55分：风险提示，对冲/部分止盈{'✅' if 26<=total<=55 else ''}")
    print(f"  🔴 ≤25分：卖出/减仓（需含核心扣分项）{'✅' if total<=25 else ''}")


def main():
    args = sys.argv[1:]

    # 解析参数（简化版：无参数时用默认值）
    if len(args) >= 1 and args[0] == "--help":
        print("""
BTC三因子评分系统 v2.0

用法：
  python3 score.py [DXY] [VIX] [ETF日净流入(M)] [Fed信号] [监管状态]

参数说明：
  DXY          当前美元指数（如 98.8）
  VIX          VIX恐慌指数（如 18）
  ETF日净流入  ETF日净流入（百万美元，如 500 = $500M，负数表示流出）
  Fed信号      dovish / neutral / hawkish
  监管状态     bullish / neutral / bearish

示例：
  # 正常市场（流动性好+ETF流入）
  python3 score.py 98.8 16 500 dovish bullish

  # ETF大额流出+鹰派
  python3 score.py 103.5 25 -200 hawkish bearish

  # 全参数版本（含VIX + 美股 + 流动性 + ETF + 稳定币等）
  # 参看 score.py 源码中的完整参数列表
""")
        return

    # 默认值（当前市场基准）
    dxy = float(args[0]) if len(args) > 0 else 98.8
    vix = float(args[1]) if len(args) > 1 else 18.0
    etf_net = float(args[2]) * 1e6 if len(args) > 2 else 100e6  # $100M 默认
    fed = args[3] if len(args) > 3 else "neutral"
    reg = args[4] if len(args) > 4 else "neutral"

    total, result = score_btc(
        dxy_now=dxy,
        vix=vix,
        etf_daily_net=etf_net,
        fed_signal=fed,
        reg_status=reg,
    )

    print_report(result)


if __name__ == "__main__":
    main()
