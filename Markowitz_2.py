"""
Package Import
"""
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import quantstats as qs
import gurobipy as gp
import warnings
import argparse
import sys

"""
Project Setup
"""
warnings.simplefilter(action="ignore", category=FutureWarning)

assets = [
    "SPY",
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
]

# Initialize Bdf and df
Bdf = pd.DataFrame()
for asset in assets:
    raw = yf.download(asset, start="2012-01-01", end="2024-04-01", auto_adjust = False)
    Bdf[asset] = raw['Adj Close']

df = Bdf.loc["2019-01-01":"2024-04-01"]

"""
Strategy Creation

Create your own strategy, you can add parameter but please remain "price" and "exclude" unchanged
"""


# class MyPortfolio:
#     """
#     NOTE: You can modify the initialization function
#     """

#     def __init__(self, price, exclude, lookback=50, gamma=0):
#         self.price = price
#         self.returns = price.pct_change().fillna(0)
#         self.exclude = exclude
#         self.lookback = lookback
#         self.gamma = gamma

#     def calculate_weights(self):
#         # Get the assets by excluding the specified column
#         assets = self.price.columns[self.price.columns != self.exclude]

#         # Calculate the portfolio weights
#         self.portfolio_weights = pd.DataFrame(
#             index=self.price.index, columns=self.price.columns
#         )

#         """
#         TODO: Complete Task 4 Below
#         """
#         # 只根據 SPY 做趨勢判斷
#         spy_price = self.price[self.exclude]

#         # 計算 SPY 的 lookback 日簡單移動平均
#         spy_ma = spy_price.rolling(window=self.lookback, min_periods=1).mean()

#         # 走訪每一天，決定當日部位
#         for i, date in enumerate(self.price.index):
#             # 前 lookback 天，資料不足就全部持有現金（保持 NaN，最後再補 0）
#             if i < self.lookback:
#                 continue

#             # 若 SPY 價格 > 移動平均線 -> 全倉 SPY
#             if spy_price.iloc[i] > spy_ma.iloc[i]:
#                 # 全倉 SPY
#                 self.portfolio_weights.loc[date, self.exclude] = 1.0
#             else:
#                 # 價格跌破均線 -> 全部持有現金（這一列先不填，之後 fillna(0)）
#                 self.portfolio_weights.loc[date, self.exclude] = 0.0      
        
#         """
#         TODO: Complete Task 4 Above
#         """

#         self.portfolio_weights.ffill(inplace=True)
#         self.portfolio_weights.fillna(0, inplace=True)

#     def calculate_portfolio_returns(self):
#         # Ensure weights are calculated
#         if not hasattr(self, "portfolio_weights"):
#             self.calculate_weights()

#         # Calculate the portfolio returns
#         self.portfolio_returns = self.returns.copy()
#         assets = self.price.columns[self.price.columns != self.exclude]
#         self.portfolio_returns["Portfolio"] = (
#             self.portfolio_returns[assets]
#             .mul(self.portfolio_weights[assets])
#             .sum(axis=1)
#         )

#     def get_results(self):
#         # Ensure portfolio returns are calculated
#         if not hasattr(self, "portfolio_returns"):
#             self.calculate_portfolio_returns()

#         return self.portfolio_weights, self.portfolio_returns

class MyPortfolio:
    """
    Low-volatility sector rotation + SPY trend filter.
    - 不偷未來資料
    - 全程 long-only，權重 >= 0
    - 每天權重和 <= 1
    """

    def __init__(self, price, exclude, lookback=252, top_k=2, gamma=0):
        self.price = price
        self.returns = price.pct_change().fillna(0)
        self.exclude = exclude     # SPY
        self.lookback = lookback   # 年波動度 & 年均線
        self.top_k = top_k         # 選最穩定的前 k 個 sector
        self.gamma = gamma

    def calculate_weights(self):
        all_assets = self.price.columns
        sectors = all_assets[all_assets != self.exclude]     
        spy = self.price[self.exclude]

        # weight
        self.portfolio_weights = pd.DataFrame(
            0.0, index=self.price.index, columns=self.price.columns
        )

        # SPY year-line
        spy_ma = spy.rolling(self.lookback, min_periods=20).mean()

        # Traverse
        for i in range(self.lookback, len(self.price)):
            date = self.price.index[i]

            # SPY trend filter
            if spy.iloc[i] < spy_ma.iloc[i]:
                continue


            window_ret = self.returns[sectors].iloc[i - self.lookback : i]

            vol = window_ret.std()

            vol_sorted = vol.sort_values()
            selected = vol_sorted.index[: self.top_k]

            w = 1.0 / len(selected)      # 等權分配

            # 設定今日權重
            for s in selected:
                self.portfolio_weights.loc[date, s] = w

        self.portfolio_weights[self.exclude] = 0.0

        self.portfolio_weights = self.portfolio_weights.fillna(0)

    def calculate_portfolio_returns(self):
        if not hasattr(self, "portfolio_weights"):
            self.calculate_weights()

        self.portfolio_returns = self.returns.copy()
        self.portfolio_returns["Portfolio"] = (
            self.portfolio_returns[self.price.columns]
            * self.portfolio_weights[self.price.columns]
        ).sum(axis=1)

    def get_results(self):
        if not hasattr(self, "portfolio_returns"):
            self.calculate_portfolio_returns()
        return self.portfolio_weights, self.portfolio_returns

if __name__ == "__main__":
    # Import grading system (protected file in GitHub Classroom)
    from grader_2 import AssignmentJudge
    
    parser = argparse.ArgumentParser(
        description="Introduction to Fintech Assignment 3 Part 12"
    )

    parser.add_argument(
        "--score",
        action="append",
        help="Score for assignment",
    )

    parser.add_argument(
        "--allocation",
        action="append",
        help="Allocation for asset",
    )

    parser.add_argument(
        "--performance",
        action="append",
        help="Performance for portfolio",
    )

    parser.add_argument(
        "--report", action="append", help="Report for evaluation metric"
    )

    parser.add_argument(
        "--cumulative", action="append", help="Cumulative product result"
    )

    args = parser.parse_args()

    judge = AssignmentJudge()
    
    # All grading logic is protected in grader_2.py
    judge.run_grading(args)
