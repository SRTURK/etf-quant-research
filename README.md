# ETF 动量与趋势研究

本项目于 2026-10-22 建立。所引用的旧聊天只有“继续完成 ETF 量化研究项目”，当前目录开始时没有文件，因此本项目是按用户授权创建的研究基线，没有假称恢复旧策略。

先读 [研究报告](RESEARCH_REPORT.md)。研究完成了数据快照、清洗、因子、统计检验、滚动预测、含费用回测与风险比较；数据采用第三方镜像，尚不具备生产交易的数据核验标准。

## 复现

当前电脑：在此目录运行 `powershell -ExecutionPolicy Bypass -File .\run.ps1`，使用已存在的 Python 3.12.14、numpy 2.3.5、pandas 3.0.1，不需联网。

其他电脑：使用 Python 3.12，安装 `pip install -r requirements.txt`，依次运行 `python research.py` 和 `python make_report.py`。工作路径不影响运行，文件路径相对于脚本定位。输出覆盖 results 内同名研究产物。

`config.json` 固定研究设置，`research.py` 含完整引擎和测试，`make_report.py` 从结果生成报告。修改配置属于新研究，不应把后验选择称为原始留出检验。

原始文件已随项目保存。只有快照丢失时才运行 `python fetch_data.py`；上游内容若变化，哈希校验会拒绝覆盖。原始数据来源与校验值在 `results/data_audit.json`。项目使用离线镜像不等于获得数据商业再分发权，未另行核实授权。

## 结果文件

- `data/raw/daily_adjclose.csv`：完整来源快照；只使用截至 2025 年的八个 ETF。
- `data/clean/prices.csv`：清洗后八个 ETF 的复权收盘价，无填充。
- `results/performance.csv`、`annual_returns.csv`：分区间指标、费用与参数敏感性、年度收益。
- `results/signals.csv`、`daily_weights.csv`、`*_daily.csv`：信号日、成交日、权重、净值、逐日收益、交易额与费用占比。
- `results/factor_panel.csv`、`monthly_rank_ic.csv`、`ic_statistics.csv`：因子、目标收益及 HAC 检验。
- `results/walkforward_predictions.csv`、`prediction_statistics.csv`：逐期预测和最后可用训练标签日期。
- `results/bootstrap.json`：配对区块重采样置信区间；`tests.txt`：引擎测试。
- `results/large_returns_review.csv`：绝对日收益超过 15% 的记录，保留而不按事后判断删除。

所有收益和权重以小数保存，费用单位为基点。10 个基点 = 成交金额的 0.1%；买卖两侧分别计费。
