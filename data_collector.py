#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪周期选股系统 - 数据采集脚本
功能：从通达信/AKShare获取A股每日行情数据，计算情绪周期指标，生成可导入JSON

使用方法：
  1. 安装依赖：pip install akshare pandas
  2. 运行：python data_collector.py
  3. 在网页端"数据设置"中导入生成的JSON文件

数据口径：
  - 含ST，不含北交所
  - 以收盘定版数据为准
  - 涨停判定：收盘价=涨停价 且 收盘有封单
"""

import json
import datetime
import os
import sys

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("=" * 60)
    print("缺少依赖库，请先安装：")
    print("  pip install akshare pandas")
    print("=" * 60)
    sys.exit(1)


class EmotionDataCollector:
    """情绪周期数据采集器"""

    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.today = datetime.date.today().strftime("%Y-%m-%d")

    def get_limit_up_stocks(self):
        """获取当日涨停股票列表（含连板数）"""
        print("[1/5] 获取涨停股票列表...")
        try:
            # AKShare 涨停板行情
            df = ak.stock_zt_pool_em(date=self.today.replace("-", ""))
            if df is None or df.empty:
                print("  警告：未获取到涨停数据，可能是非交易日")
                return []

            stocks = []
            for _, row in df.iterrows():
                stock = {
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "board": int(row.get("连板数", 1)),
                    "change": float(row.get("涨跌幅", 10)),
                    "price": float(row.get("最新价", 0)),
                    "turnover": float(row.get("换手率", 0)),
                    "amount": round(float(row.get("成交额", 0)) / 1e8, 2),
                    "sealAmount": int(row.get("封单金额", 0) / 1e4),
                    "concept": str(row.get("所属行业", "")),
                    "volumeRatio": round(float(row.get("量比", 1)), 2),
                    "mainInflow": 0,
                    "marketCap": 0
                }
                stocks.append(stock)

            print(f"  获取到 {len(stocks)} 只涨停股票")
            return stocks
        except Exception as e:
            print(f"  获取涨停数据失败: {e}")
            return []

    def get_limit_down_stocks(self):
        """获取当日跌停股票数量"""
        print("[2/5] 获取跌停股票数量...")
        try:
            df = ak.stock_zt_pool_dtgc_em(date=self.today.replace("-", ""))
            if df is None or df.empty:
                return 0
            count = len(df)
            print(f"  跌停股票: {count} 只")
            return count
        except Exception as e:
            print(f"  获取跌停数据失败: {e}")
            return 0

    def get_market_breadth(self):
        """获取市场涨跌家数（红盘率）"""
        print("[3/5] 获取市场涨跌家数...")
        try:
            # 获取A股实时行情，统计涨跌
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return 0, 0, 0

            # 排除北交所（代码8开头）
            df = df[~df["代码"].astype(str).str.startswith("8")]

            up_count = len(df[df["涨跌幅"] > 0])
            down_count = len(df[df["涨跌幅"] < 0])
            flat_count = len(df[df["涨跌幅"] == 0])
            total = up_count + down_count + flat_count
            red_rate = round(up_count / total * 100, 1) if total > 0 else 0

            print(f"  上涨: {up_count}  下跌: {down_count}  平盘: {flat_count}  红盘率: {red_rate}%")
            return up_count, down_count, red_rate
        except Exception as e:
            print(f"  获取市场广度失败: {e}")
            return 0, 0, 0

    def calc_promote_rate(self, limit_up_stocks):
        """计算连板晋级率和首板晋级率（简化版）"""
        print("[4/5] 计算晋级率...")
        # 简化计算：连板数>=2的占比作为晋级率参考
        if not limit_up_stocks:
            return 0, 0

        multi_board = len([s for s in limit_up_stocks if s.get("board", 1) >= 2])
        promote_rate = round(multi_board / len(limit_up_stocks) * 100, 1)

        # 首板晋级率需要昨日数据，这里给出估算
        first_board = len([s for s in limit_up_stocks if s.get("board", 1) == 1])
        first_promote = round((len(limit_up_stocks) - first_board) / max(first_board, 1) * 100, 1)
        first_promote = min(first_promote, 50)  # 合理范围

        print(f"  连板晋级率: {promote_rate}%  首板晋级率(估): {first_promote}%")
        return promote_rate, first_promote

    def calc_seal_rate(self, limit_up_stocks):
        """计算封板率（简化版：有封单的占比）"""
        if not limit_up_stocks:
            return 70.0
        sealed = len([s for s in limit_up_stocks if s.get("sealAmount", 0) > 0])
        return round(sealed / len(limit_up_stocks) * 100, 1)

    def collect(self):
        """执行完整数据采集"""
        print("=" * 60)
        print(f"情绪周期数据采集 - {self.today}")
        print("=" * 60)

        # 1. 涨停股票
        limit_up_stocks = self.get_limit_up_stocks()
        limit_up_count = len(limit_up_stocks)

        # 2. 跌停数量
        limit_down_count = self.get_limit_down_stocks()

        # 3. 市场广度
        up_count, down_count, red_rate = self.get_market_breadth()

        # 4. 晋级率
        promote_rate, first_promote = self.calc_promote_rate(limit_up_stocks)

        # 5. 最高连板
        max_board = max([s.get("board", 1) for s in limit_up_stocks], default=0)
        seal_rate = self.calc_seal_rate(limit_up_stocks)
        ever_limit = round(limit_up_count / (seal_rate / 100)) if seal_rate > 0 else limit_up_count

        print(f"[5/5] 最高连板: {max_board}板  封板率: {seal_rate}%")

        # 构建快照
        snapshot = {
            "date": self.today,
            "limitUp": limit_up_count,
            "limitDown": limit_down_count,
            "upCount": up_count,
            "downCount": down_count,
            "redRate": red_rate,
            "sealRate": seal_rate,
            "promoteRate": promote_rate,
            "firstPromote": first_promote,
            "maxBoard": max_board,
            "everLimit": ever_limit,
            "sealed": limit_up_count
        }

        # 输出
        output = {
            "snapshots": [snapshot],
            "reviews": [],
            "limitUpStocks": limit_up_stocks,
            "weights": {"limitUp": 20, "limitDown": 15, "redRate": 20, "sealRate": 15, "promote": 15, "maxBoard": 15}
        }

        filename = os.path.join(self.output_dir, f"emotion_{self.today}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("采集完成！")
        print(f"  涨停: {limit_up_count}  跌停: {limit_down_count}")
        print(f"  红盘率: {red_rate}%  封板率: {seal_rate}%")
        print(f"  晋级率: {promote_rate}%  最高连板: {max_board}板")
        print(f"  输出文件: {filename}")
        print("=" * 60)
        print("\n下一步：在网页端「数据设置」→「导入数据」中选择此文件")

        return output


if __name__ == "__main__":
    collector = EmotionDataCollector()
    collector.collect()
