# 结果索引

[返回首页](../README.md) · [研究报告](../RESEARCH_REPORT.md)

收益与权重均以小数记录，日期为市场交易日期。`test` 指 2020–2025 历史留出区间。

| 文件 | 内容 |
| :--- | :--- |
| `performance.csv` | 各组合、费用与参数情景的分区间指标 |
| `annual_returns.csv` | 年度复合收益 |
| `*_daily.csv` | 净值、日收益、成交额与费用占比 |
| `signals.csv` / `daily_weights.csv` | 目标权重及实际收盘权重 |
| `factor_panel.csv` | 月度因子、未来收益和标签结束日期 |
| `monthly_rank_ic.csv` / `ic_statistics.csv` | 月度秩 IC 及 HAC 检验 |
| `walkforward_predictions.csv` | 逐月预测、历史均值预测及训练标签截止日期 |
| `prediction_statistics.csv` | 预测 MSE、样本外 R² 及损失差检验 |
| `bootstrap.json` | 年化算术超额收益的重采样区间 |
| `data_audit.json` | 数据来源、哈希、范围和运行环境 |
| `large_returns_review.csv` | 绝对日收益超过 15% 的记录 |
| `tests.txt` | 时序与费用核算测试摘要 |

## 逐日字段

`nav` 为累计净值，`return` 为扣费日收益，`turnover` 为当日买卖总成交金额/调仓前净值，`fee_fraction` 为费用/调仓前净值。初始净值为 1，扣除建仓费用后可能略低于 1。

## 情景命名

`strategy_10bps` 为默认策略，其余 `strategy_*bps` 只改变成本。`lookback_126` 与 `lookback_189` 改变动量回看期，`delay_2days` 多延迟一个交易日执行。敏感性用于评估稳健性，不代表重新选参后的独立留出测试。
