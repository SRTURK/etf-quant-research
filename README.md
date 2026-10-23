<div align="center">

# ETF Momentum Lab

**跨资产动量与趋势研究 · 可复现的组合回测与预测检验**

Python 3.12 · 8 ETFs · 2006–2025 · Monthly Rebalancing

[研究报告](RESEARCH_REPORT.md) · [方法说明](docs/METHODOLOGY.md) · [数据说明](docs/DATA.md) · [结果索引](results/README.md)

</div>

---

用一套透明的交易规则，研究动量与趋势能否改善跨资产组合的收益和风险。项目覆盖数据校验、因子构造、历史留出检验、滚动预测、交易费用与风险评估，并保留可追溯的每日持仓和交易记录。

![历史留出区间净值、回撤与收益风险比较](assets/research_overview.png)

> **研究结论**：策略在历史测试区间降低了相对 SPY 的回撤，但相对等权组合的超额收益尚无充分统计证据，预测模型也未稳定优于历史均值。历史留出不等同于真实前瞻验证。

## 研究设计

| 维度 | 设计 |
| :--- | :--- |
| 资产范围 | 股票：SPY / EFA / EEM；债券：IEF / TLT；黄金：GLD；房地产：VNQ |
| 防御配置 | SHY 短期美债 ETF |
| 因子 | 12–1 动量 + 200 日均线趋势 |
| 组合 | 符合条件的动量前两名各 50%，剩余额度配置 SHY |
| 执行 | 月末形成信号，下一交易日收盘调仓 |
| 费用 | 默认单边 10 基点；另检验 0 / 5 / 25 / 50 基点 |
| 验证 | 开发 2006–2014；验证 2015–2019；历史测试 2020–2025 |
| 统计 | 月度秩 IC、HAC 标准误、扩展窗口回归、配对区块 bootstrap |

## 快速开始

需要 **Python 3.12**。原始数据快照已包含在仓库中；安装依赖后，研究流程可离线运行。

```bash
git clone https://github.com/SRTURK/etf-quant-research.git
cd etf-quant-research
python -m venv .venv
```

激活虚拟环境：Windows 使用 `.venv\Scripts\activate`，macOS / Linux 使用 `source .venv/bin/activate`。

```bash
python -m pip install -r requirements.txt
python research.py
python make_report.py
```

Windows 也可在安装依赖后运行 `powershell -File .\run.ps1`。每次运行会重建结果、图表与报告；参数见 [config.json](config.json)。

## 项目结构

```text
etf-quant-research/
├── research.py             # 数据校验、因子、回测、统计与时序测试
├── make_report.py          # 研究报告生成
├── visualize_results.py    # 图表生成
├── config.json             # 固定研究设置
├── fetch_data.py           # 校验后恢复原始快照
├── data/
│   ├── raw/                # 原始快照
│   └── clean/              # 对齐后的复权收盘价
├── results/                # 指标、净值、权重、信号、预测与审计记录
├── assets/                 # 可复现的研究图表
├── docs/                   # 方法与数据文档
└── RESEARCH_REPORT.md      # 完整研究报告
```

## 如何阅读结果

- **表现与风险**：[研究报告](RESEARCH_REPORT.md)中的分段表现、费用敏感性及统计证据。
- **持仓与执行**：[signals.csv](results/signals.csv)、[daily_weights.csv](results/daily_weights.csv)及各组合逐日记录。
- **预测有效性**：[prediction_statistics.csv](results/prediction_statistics.csv)与逐期训练标签截止日期。
- **复现审计**：[data_audit.json](results/data_audit.json)、[tests.txt](results/tests.txt)及[结果字段说明](results/README.md)。

## 研究边界

数据来自第三方公开镜像，尚未完成第二供应商逐日核验。固定 ETF 池存在生存者选择偏差；复权收盘价无法验证真实成交容量、盘中路径或市场冲击。费用为统一情景假设，未纳入税款和跨境换汇。详细口径见[数据说明](docs/DATA.md)和[研究报告](RESEARCH_REPORT.md)。

本仓库用于研究与复现，不构成投资建议或实盘交易承诺。第三方行情的使用与再分发应遵循原数据提供方条款。
