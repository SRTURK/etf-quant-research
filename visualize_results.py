"""Render publication-style figures directly from saved backtest results."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
COLORS = ['#087e8b', '#7e8ea5', '#c48335']
SERIES = ['strategy_10bps', 'equal_weight', 'SPY_buy_hold']
LABELS = ['Momentum + trend', 'Equal weight', 'SPY buy & hold']

def render_figures():
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
        'axes.spines.top':False, 'axes.spines.right':False,
        'axes.edgecolor':'#cbd5e1', 'axes.labelcolor':'#475569',
        'xtick.color':'#64748b', 'ytick.color':'#64748b',
        'text.color':'#142c41', 'svg.hashsalt':'etf-momentum-lab'})
    dest=ROOT/'assets'; dest.mkdir(exist_ok=True)
    fig=plt.figure(figsize=(13,10), facecolor='#f7f9fc')
    gs=fig.add_gridspec(3,2, height_ratios=[1.35,1,.9], hspace=.54, wspace=.28,
                        left=.085,right=.96,top=.83,bottom=.1)
    ax=fig.add_subplot(gs[0,:]); ddax=fig.add_subplot(gs[1,:]); bars=fig.add_subplot(gs[2,0]); costs=fig.add_subplot(gs[2,1])
    fig.text(.085,.945,'ETF MOMENTUM LAB',fontsize=24,weight='bold')
    fig.text(.085,.908,'Historical holdout  /  2020–2025  /  USD total-return proxy',fontsize=12,color='#64748b')
    perf=pd.read_csv(ROOT/'results/performance.csv').query("period == 'test'").set_index('strategy')
    for key,label,color in zip(SERIES,LABELS,COLORS):
        daily=pd.read_csv(ROOT/f'results/{key}_daily.csv',index_col='Date',parse_dates=True).loc['2020':'2025']
        nav=(1+daily['return']).cumprod()
        # Include pre-period NAV=1 so the first daily return is not discarded.
        nav=pd.concat([pd.Series([1.],index=[pd.Timestamp('2019-12-31')]),nav])
        ax.plot(nav.index,nav,color=color,lw=1.8,label=label)
        dd=nav/nav.cummax()-1
        ddax.plot(dd.index,dd,color=color,lw=1.3)
        expected=perf.loc[key,'max_drawdown']
        assert np.isclose(dd.min(),expected), 'Chart drawdown differs from metric table'
    for axis in [ax,ddax,bars,costs]:
        axis.set_facecolor('white'); axis.grid(axis='y',color='#e7edf3',lw=.8); axis.set_axisbelow(True)
    ax.set_title('01   Growth of $1',loc='left',pad=12,weight='bold'); ax.set_ylabel('Portfolio value')
    ax.legend(loc='upper left',frameon=False,ncol=3,fontsize=10)
    ddax.set_title('02   Drawdown from period high',loc='left',pad=12,weight='bold')
    ddax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    for axis in [ax,ddax]:
        axis.xaxis.set_major_locator(mdates.YearLocator()); axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        axis.set_xlim(pd.Timestamp('2019-12-31'),pd.Timestamp('2025-12-31'))
    values=perf.loc[SERIES,'CAGR']
    bars.barh(['Strategy','Equal weight','SPY'],values,color=COLORS,height=.55)
    bars.invert_yaxis(); bars.set_xlim(0,max(values)*1.3)
    bars.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    bars.set_title('03   Annualized net return',loc='left',pad=12,weight='bold')
    for y,v in enumerate(values): bars.text(v+.003,y,f'{v:.2%}',va='center',fontsize=10)
    levels=[0,5,10,25,50]; vals=[perf.loc[f'strategy_{b}bps','CAGR'] for b in levels]
    costs.plot(levels,vals,'o-',color=COLORS[0],lw=2,markersize=5)
    costs.set_xlabel('One-way trading cost (bps)'); costs.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    costs.set_ylim(.06,.13); costs.set_xticks(levels)
    costs.set_title('04   Cost sensitivity',loc='left',pad=12,weight='bold')
    fig.text(.085,.035,'Source: archived adjusted-close snapshot. Strategy / benchmarks: 10 bps per traded side.\nHistorical holdout, not forward validation. Excess-return confidence interval includes zero.',fontsize=9,color='#64748b',linespacing=1.6)
    fig.savefig(dest/'research_overview.png',dpi=170,facecolor=fig.get_facecolor())
    fig.savefig(dest/'research_overview.svg',facecolor=fig.get_facecolor(),metadata={'Date':None})
    plt.close(fig)

if __name__=='__main__': render_figures()
