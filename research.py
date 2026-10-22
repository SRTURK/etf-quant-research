"""Offline ETF research. Run: python research.py. No network needed."""
from pathlib import Path
import json, hashlib, math, platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT/'config.json').read_text())
OUT = ROOT/'results'
OUT.mkdir(exist_ok=True)

def features(p, lookback=None):
    lookback = CFG['lookback'] if lookback is None else lookback
    return {'momentum': p.shift(CFG['skip'])/p.shift(lookback)-1,
            'trend': p/p.rolling(CFG['trend_days'], min_periods=CFG['trend_days']).mean()-1}

def schedule(p, lookback=None, delay=1):
    f = features(p, lookback)
    targets, signals = {}, []
    # Calendar change is known at the new month's first session; no incomplete final month.
    for i in range(1, len(p)):
        if p.index[i].month == p.index[i-1].month: continue
        s = i-1; execution = s+delay
        if execution >= len(p) or p.index[execution] < pd.Timestamp(CFG['start']): continue
        mom = f['momentum'].iloc[s][CFG['universe']]
        trend = f['trend'].iloc[s][CFG['universe']]
        if mom.isna().any() or trend.isna().any(): continue
        selected = mom[(mom>0)&(trend>0)].sort_values(ascending=False, kind='stable').head(CFG['top_k']).index
        w = pd.Series(0., index=p.columns)
        w.loc[selected] = 1/CFG['top_k']
        w[CFG['defensive']] = 1-w.sum()
        targets[p.index[execution]] = w
        signals.append({'signal_date': p.index[s], 'execution_date': p.index[execution], **w.to_dict()})
    return targets, pd.DataFrame(signals)

def rebalance(pre, target, cost):
    # Solve post-fee NAV and target holdings jointly; cash is excluded from traded notional.
    nav = pre.sum(); after = nav
    for _ in range(40):
        after = nav-cost*np.abs(target*after-pre).sum()
    holdings = target*after
    traded = np.abs(holdings-pre).sum()
    return holdings, traded/nav, (nav-after)/nav

def simulate(p, targets, bps=10):
    rr=p.pct_change(fill_method=None).fillna(0.)
    h=np.zeros(p.shape[1]); cash=1.; previous=1.; rows=[]; weights=[]
    for dt,r in rr.iterrows():
        h *= 1+r.to_numpy()
        before=h.sum()+cash; turnover=fee=0.
        if dt in targets:
            target=targets[dt].to_numpy()
            if cash:
                # Initial purchase: exact cost for investing previously uninvested cash.
                h=target*before/(1+bps/10000); turnover=h.sum()/before
                fee=1-h.sum()/before; cash=0.
            else: h,turnover,fee=rebalance(h,target,bps/10000)
        nav=h.sum()+cash
        rows.append([dt,nav,nav/previous-1,turnover,fee])
        weights.append([dt,*(h/nav),cash/nav]); previous=nav
    result=pd.DataFrame(rows,columns=['Date','nav','return','turnover','fee_fraction']).set_index('Date')
    w=pd.DataFrame(weights,columns=['Date',*p.columns,'CASH']).set_index('Date')
    return result,w

def metrics(r, defensive, turnover):
    n=len(r); eq=(1+r).cumprod(); dd=eq/np.maximum.accumulate(np.r_[1.,eq.to_numpy()])[1:]-1
    excess=r-defensive.reindex(r.index)
    q=r.quantile(.05)
    return dict(days=n,CAGR=eq.iloc[-1]**(252/n)-1,volatility=r.std()*np.sqrt(252),
                Sharpe_vs_SHY=excess.mean()/excess.std()*np.sqrt(252),max_drawdown=dd.min(),
                worst_day=r.min(),CVaR95=r[r<=q].mean(),annual_traded_notional=turnover.sum()*252/n)

def hac_mean(x,lags=3):
    x=np.asarray(x); x=x[np.isfinite(x)]; n=len(x); z=x-x.mean()
    v=np.dot(z,z)/n
    for k in range(1,min(lags,n-1)+1): v+=2*(1-k/(lags+1))*np.dot(z[k:],z[:-k])/n
    se=np.sqrt(max(v,0)/n); t=x.mean()/se if se else 0
    return {'n':n,'mean':x.mean(),'HAC_t':t,'normal_approx_p':math.erfc(abs(t)/np.sqrt(2))}

def main():
    raw=ROOT/'data/raw/daily_adjclose.csv'
    expected='361efb287116fc8200582c15fcd315bcce2e218fa1e50b416bacc5acebff37b9'
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==expected, 'Snapshot hash changed; audit source before running'
    d=pd.read_csv(raw,index_col='Date',parse_dates=True)
    assert d.index.is_unique and d.index.is_monotonic_increasing
    assert len(d)==5688 and d.index.max()==pd.Timestamp('2026-08-11'), 'Snapshot truncated or changed: review before research'
    assert round(d.loc['2020-03-16','^VIX'],2)==82.69
    assert round(d.loc['2018-02-05','^VIX'],2)==37.32
    assert str(d.SPY.pct_change(fill_method=None).idxmin().date())=='2020-03-16'
    assert '2011-09-05' not in d.index.astype(str)
    cols=CFG['universe']+[CFG['defensive']]
    p=d.loc[:CFG['end'],cols].copy()
    first=max(p[c].first_valid_index() for c in cols)
    p=p.loc[first:]
    assert not p.isna().any().any(), 'Interior missing value: stop, never forward-fill'
    assert np.isfinite(p.to_numpy()).all() and (p>0).all().all()
    p.to_csv(ROOT/'data/clean/prices.csv')
    audit={'raw_rows':len(d),'clean_rows':len(p),'clean_first':str(p.index.min().date()),
           'clean_last':str(p.index.max().date()),'missing_after_common_inception':int(p.isna().sum().sum()),
           'max_calendar_gap_days':int(p.index.to_series().diff().dt.days.max()),
           'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
           'source':'https://raw.githubusercontent.com/manisahni/marketdata/main/daily_adjclose.csv',
           'retrieved_date':'2026-10-22','numpy':np.__version__,'pandas':pd.__version__,'python':platform.python_version()}
    (OUT/'data_audit.json').write_text(json.dumps(audit,indent=2))
    anomalies=p.pct_change(fill_method=None).stack(); anomalies[anomalies.abs()>.15].to_csv(OUT/'large_returns_review.csv')
    t,s=schedule(p); s.to_csv(OUT/'signals.csv',index=False)
    start=min(t); ptest=p.loc[start:]; defensive=p.pct_change(fill_method=None)[CFG['defensive']]
    base,w=simulate(p,t,CFG['cost_bps']); base=base.loc[start:]; w.loc[start:].to_csv(OUT/'daily_weights.csv')
    runs={'strategy_10bps':base}
    for name,target in [('equal_weight',pd.Series([1/7]*7+[0.],index=p.columns)),('SPY_buy_hold',pd.Series([1.]+[0.]*7,index=p.columns))]:
        bt={dt:target for dt in t} if name=='equal_weight' else {start:target}
        runs[name]=simulate(p,bt,10)[0].loc[start:]
    for cost in [0,5,25,50]: runs[f'strategy_{cost}bps']=simulate(p,t,cost)[0].loc[start:]
    for look in [126,189]: runs[f'lookback_{look}']=simulate(p,schedule(p,look)[0],10)[0].loc[start:]
    runs['delay_2days']=simulate(p,schedule(p,delay=2)[0],10)[0].loc[start:]
    periods={'development':('2006','2014'),'validation':('2015','2019'),'test':('2020','2025'),'all':('2006','2025')}
    rows=[]
    for name,b in runs.items():
        b.to_csv(OUT/f'{name}_daily.csv')
        for period,(a,z) in periods.items():
            v=b.loc[a:z]
            rows.append({'strategy':name,'period':period,**metrics(v['return'],defensive,v.turnover)})
    pd.DataFrame(rows).to_csv(OUT/'performance.csv',index=False)
    pd.DataFrame({k:(1+b['return']).groupby(b.index.year).prod()-1 for k,b in runs.items()}).to_csv(OUT/'annual_returns.csv')
    f=features(p); samples=[]; dates=list(t)
    for i in range(len(dates)-1):
        execution=dates[i]; end=dates[i+1]; sig=s.loc[s.execution_date==execution,'signal_date'].iloc[0]
        for c in CFG['universe']:
            samples.append(dict(date=execution,end=end,symbol=c,momentum=f['momentum'].loc[sig,c],trend=f['trend'].loc[sig,c],y=p.loc[end,c]/p.loc[execution,c]-1))
    panel=pd.DataFrame(samples); panel.to_csv(OUT/'factor_panel.csv',index=False)
    ic=[]
    for dt,g in panel.groupby('date'):
        for factor in ['momentum','trend']:
            ic.append({'date':dt,'factor':factor,'IC':g[factor].rank().corr(g.y.rank())})
    ic=pd.DataFrame(ic); ic.to_csv(OUT/'monthly_rank_ic.csv',index=False)
    stats=[]
    for period,(a,z) in periods.items():
        for factor in ['momentum','trend']:
            x=ic[(ic.factor==factor)&ic.date.dt.year.between(int(a),int(z))].IC
            stats.append({'period':period,'factor':factor,**hac_mean(x)})
    pd.DataFrame(stats).to_csv(OUT/'ic_statistics.csv',index=False)
    # Expanding regression refit each month: only labels fully observed before prediction date.
    predictions=[]
    for dt,g in panel.groupby('date'):
        if dt.year<2015: continue
        train=panel[panel.end<dt]
        x=train[['momentum','trend']].to_numpy(); mu=x.mean(0); sd=x.std(0)
        X=np.column_stack([np.ones(len(x)),(x-mu)/sd]); beta=np.linalg.lstsq(X,train.y,rcond=None)[0]
        pred=np.column_stack([np.ones(len(g)),(g[['momentum','trend']].to_numpy()-mu)/sd])@beta
        for (_,row),v in zip(g.iterrows(),pred): predictions.append({**row.to_dict(),'prediction':v,'historical_mean':train.y.mean(),'latest_training_label':train.end.max()})
    pr=pd.DataFrame(predictions); pr.to_csv(OUT/'walkforward_predictions.csv',index=False)
    predstats=[]
    for period,a,z in [('validation',2015,2019),('test',2020,2025)]:
        q=pr[pr.date.dt.year.between(a,z)]
        mse=((q.y-q.prediction)**2).mean(); baseline=((q.y-q.historical_mean)**2).mean()
        loss=q.assign(diff=(q.y-q.historical_mean)**2-(q.y-q.prediction)**2).groupby('date')['diff'].mean()
        predstats.append({'period':period,'OOS_R2':1-mse/baseline,'MSE':mse,'baseline_MSE':baseline,**hac_mean(loss)})
    pd.DataFrame(predstats).to_csv(OUT/'prediction_statistics.csv',index=False)
    # Paired circular block bootstrap of daily excess over investable equal-weight benchmark.
    diff=(base['return']-runs['equal_weight']['return']).loc['2020':'2025'].to_numpy()
    rng=np.random.default_rng(CFG['seed']); n=len(diff); means=[]
    for _ in range(2000):
        idx=((rng.integers(0,n,size=math.ceil(n/21))[:,None]+np.arange(21))%n).ravel()[:n]
        means.append(diff[idx].mean()*252)
    boot={'test_annualized_arithmetic_excess':float(diff.mean()*252),'block_days':21,'replicates':2000,
          '95pct_interval':np.quantile(means,[.025,.975]).tolist()}
    (OUT/'bootstrap.json').write_text(json.dumps(boot,indent=2))
    tests(p,t,base,pr)
    print(pd.DataFrame(rows).query("period == 'test'").to_string(index=False))
    print(json.dumps(boot)); print(pd.DataFrame(predstats).to_string(index=False))

def tests(p,t,base,pr):
    cut=pd.Timestamp('2019-12-31'); changed=p.copy(); changed.loc[changed.index>cut]*=3
    t2,_=schedule(changed)
    for dt in t:
        if dt<=cut: np.testing.assert_allclose(t[dt],t2[dt])
    prefix=simulate(changed,t2,10)[0].loc[base.index.min():cut]
    np.testing.assert_allclose(base.loc[:cut,'nav'],prefix.nav)
    assert (pr.latest_training_label<pr.date).all()
    assert all(abs(v.sum()-1)<1e-12 and v.min()>=0 for v in t.values())
    idx=pd.bdate_range('2020-01-01',periods=4)
    toy=pd.DataFrame({'A':[100,200,400,800],'B':[100]*4},index=idx)
    bt,_=simulate(toy,{idx[1]:pd.Series([1.,0.],index=toy.columns)},0)
    assert bt.loc[idx[1],'nav']==1 and bt.loc[idx[2],'nav']==2
    h,turn,fee=rebalance(np.array([.5,.5]),np.array([1.,0.]),.001)
    assert abs(h.sum()+fee-1)<1e-12 and abs(fee-.001*turn)<1e-12
    initial=simulate(toy,{idx[0]:pd.Series([1.,0.],index=toy.columns)},10)[0]
    assert abs(initial.nav.iloc[0]-1/1.001)<1e-12
    (OUT/'tests.txt').write_text('PASS: future-price perturbation invariance\nPASS: pre-cutoff NAV invariance\nPASS: matured training labels only\nPASS: long-only unit weights\nPASS: next-close execution timing\nPASS: fee conservation and initial cost\n')

if __name__=='__main__': main()
