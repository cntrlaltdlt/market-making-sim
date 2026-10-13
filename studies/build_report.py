"""Build report/REPORT.md and its figures from saved evidence; no simulations.

    python -m studies.build_report
"""
import json
import math
from pathlib import Path
from statistics import mean
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mmsim.experiments import strategy_statistics, paired_statistics
from studies.risk_study import simultaneous_mean_interval

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'report'
LABELS = {'balanced':'Balanced flow', 'informed':'25% informed',
          'buyers':'80% buyers', 'buyers_and_rising':'80% buyers + upward drift'}


def load(path):
    return json.loads(path.read_text())


def main():
    study = ROOT/'results'/'risk_v1'
    data = load(study/'results.json')
    # Verify all displayed statistics against saved per-run records.
    for market, rows in data.items():
        for skew, row in rows.items():
            runs = load(study/f'runs_{market}_{skew}.json')
            actual = strategy_statistics(runs,'adjusted')
            for key, value in actual.items():
                if not math.isclose(value,row['statistics'][key],rel_tol=1e-12,abs_tol=1e-12):
                    raise ValueError(f'Summary mismatch: {market}/{skew}/{key}')
            if skew != '0':
                interval = simultaneous_mean_interval(paired_statistics(runs))
                if interval != row['family_95_mean_interval']:
                    raise ValueError('Interval mismatch')
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    colors = ['#34495e','#087e8b','#d17a22','#a33b64']
    fig, axes = plt.subplots(2,2,figsize=(11,8),layout='constrained')
    for ax,(market,rows) in zip(axes.flat,data.items()):
        for color,(skew,row) in zip(colors,rows.items()):
            s=row['statistics']
            ax.scatter(s['pnl_standard_deviation']/100,s['mean_pnl']/100,color=color,s=70,label=f'{skew}p skew')
            ax.annotate(f' {skew}p',(s['pnl_standard_deviation']/100,s['mean_pnl']/100),xytext=(5,4),textcoords='offset points')
        ax.margins(.22)
        ax.set_title(LABELS[market]); ax.set_xlabel('P&L standard deviation (£)'); ax.set_ylabel('Mean net P&L (£)')
        ax.grid(alpha=.2)
    fig.suptitle('Profit and variability: no single risk measure tells the whole story\n500 fresh matched runs per market; all settings reported',fontsize=14)
    fig.savefig(OUT/'profit_variability.png',dpi=180)
    fig.savefig(OUT/'profit_variability.svg')
    plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    metrics=[('mean_absolute_inventory','Mean absolute inventory (shares)',1),
             ('loss_fraction','Runs ending in a loss (%)',100),
             ('worst_tail_mean_pnl','Mean P&L of worst 25 runs (£)',.01),
             ('mean_pnl','Mean net P&L (£)',.01)]
    for ax,(key,title,scale) in zip(axes.flat,metrics):
        for color,(market,rows) in zip(colors,data.items()):
            ax.plot([int(k) for k in rows],[r['statistics'][key]*scale for r in rows.values()],marker='o',color=color,label=LABELS[market])
        ax.set_title(title); ax.set_xlabel('Inventory adjustment (p/share)');ax.set_xticks([0,2,5,10]);ax.grid(alpha=.2)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=2)
    fig.suptitle('Inventory control and downside outcomes\nDescriptive estimates; lines connect tested settings only',fontsize=14)
    fig.savefig(OUT/'risk_measures.png',dpi=180);fig.savefig(OUT/'risk_measures.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,7),layout='constrained')
    labels=[]; y=0
    for market,rows in data.items():
        for skew in ('2','5','10'):
            row=rows[skew]; centre=row['paired']['mean_pnl_difference']/100
            low,high=[v/100 for v in row['family_95_mean_interval']]
            ax.errorbar(centre,y,xerr=[[centre-low],[high-centre]],fmt='o',color=colors[['2','5','10'].index(skew)+1],capsize=4)
            labels.append(f'{LABELS[market]} · {skew}p');y+=1
    ax.set_yticks(range(y),labels);ax.invert_yaxis();ax.axvline(0,color='black',lw=1)
    ax.set_xlabel('Mean net P&L difference versus fixed quotes (£)')
    ax.set_title('Nonzero adjustments versus fixed quotes\nApproximate 95% simultaneous intervals across 12 comparisons')
    ax.grid(axis='x',alpha=.2);fig.savefig(OUT/'paired_differences.png',dpi=180);fig.savefig(OUT/'paired_differences.svg');plt.close(fig)
    lines=['# Inventory-aware market making: profit, risk and model dependence','',
      '## Research question','',
      'When does shifting quotes to control inventory improve simulated market-making outcomes, and what does that control cost?','',
      '## Main findings','',
      'In the risk study, fixed quotes had the highest sample mean net P&L in all four markets. Stronger inventory adjustments reduced average absolute inventory and P&L standard deviation, but did not consistently improve loss frequency or worst-tail P&L. This distinguishes exposure control from downside protection.',
      'Exploratory runs in `examples/` with a £1 half-spread found benefits from inventory adjustment under imbalanced customer flow. The main studies used a 10p half-spread. The [exact analysis](EXACT_ANALYSIS.md) later showed why this matters: at 10p the spread, not the skew, is what limits performance.',
      'Informed customers reduced profitability despite positive execution edge. Accounting attribution showed that adverse subsequent price movements could outweigh the price advantage at execution.','',
      '## Model and accounting','',
      'The account starts with £1,000 and zero inventory. Each step posts one-share bid and ask quotes, reveals one potential customer, executes if acceptable, then updates the reference price. Fixed quotes are reference ± half-spread. Adjusted quotes move their centre by −inventory × skew. Quotes that would breach the position cap are withdrawn before the customer is revealed.',
      'Reference changes are drift plus an equally likely positive or negative shock. Ordinary customer limits are uniformly distributed within ±150p of the current reference. Informed customers know the next reference exactly, buy before rises and sell before falls, using that future reference as their limit. Only the environment/customer receives future information.',
      'All accounting uses integer pence. Net P&L equals execution edge plus post-trade inventory × subsequent price changes, minus customer fees, closing fees and closing execution costs. Step and terminal reconciliations check this against cash + inventory value − starting cash. Inventory P&L includes adverse-selection effects; these are not subtracted twice.','',
      '## Study history and evaluation discipline','',
      '1. Exploratory scripts (now in `examples/`) developed the model and investigated costs, limits, stress scenarios and informed customers.',
      '2. The selection study compared 0, 2, 5 and 10p/share skew on 300 development runs per market. Highest equal-weight mean net P&L selected zero skew. This choice was saved before 500 fresh evaluation runs per market. Because zero skew equals fixed quoting, the resulting paired zero difference was mechanical, not evidence of general equivalence.',
      '3. After inspecting that evaluation, a separately labelled profit–risk study was designed. It used fresh seeds and reported every candidate rather than selecting another winner. Both studies and their protocols are saved. The risk study is not retroactively presented as the original evaluation.',
      '4. An exact analysis then computed the full P&L distribution for the same market, checking these simulations and extending them beyond the 10p spread ([exact analysis](EXACT_ANALYSIS.md)).','',
      '## Risk study design','',
      '500 matched runs × 200 steps per market; reference starts at £100; random shocks ±30p; half-spread 10p; cap ±3 shares; fee 1p/share; closing execution cost 10p/share. All terminal inventory is closed. Skews are 0, 2, 5 and 10p/share. Balanced flow is 50% potential buyers; informed flow replaces 25% of potential customers; buyer-heavy conditions use 80% buyers; upward drift is +2p/step.',
      'Each candidate sees identical paths within each market. All candidate/market combinations are reported. Paired mean-difference intervals use a normal approximation with Bonferroni adjustment across 12 nonzero-skew comparisons. Risk statistics are descriptive; no confidence claim is made about their differences. Worst-tail P&L is the mean of the lowest 25 final P&Ls, not a guaranteed loss bound.','',
      '![Profit and variability](profit_variability.png)','',
      '![Risk measures](risk_measures.png)','']
    for market,rows in data.items():
        lines += [f'### {LABELS[market]}','', '| Skew (p/share) | Mean net P&L | P&L SD | Losing runs | Worst 25 mean | Mean absolute inventory |','|---|---|---|---|---|---|']
        for skew,row in rows.items():
            s=row['statistics']; lines.append(f"| {skew} | £{s['mean_pnl']/100:.2f} | £{s['pnl_standard_deviation']/100:.2f} | {s['loss_fraction']:.1%} | £{s['worst_tail_mean_pnl']/100:.2f} | {s['mean_absolute_inventory']:.2f} |")
        lines.append('')
    lines += ['![Paired mean differences](paired_differences.png)','',
      '## Limitations','',
      '- Synthetic prices and customer behaviour are not calibrated to market data; this is simulation, not historical backtesting.',
      '- No order book, queue position, competition, latency, partial fills, price impact, funding costs or stock-borrow constraints.',
      '- Perfect one-step customer foresight is an artificial stress assumption. Closing assumes unlimited external liquidity at a constant per-share cost.',
      '- A narrow skew grid at a single spread cannot establish good strategies; the exact analysis shows the 10p spread was far from optimal. The profit-only selection objective and artificial market weights reflect research choices.',
      '- New seeds test sampling generalisation within an existing model, not robustness to unknown real-world mechanisms. Confidence intervals omit model uncertainty.',
      '- Lower variability is not automatically preferable when expected profit also falls. Most risk measures here are sample summaries without uncertainty estimates.','',
      '## Reproduce and inspect','',
      'See the [README](../README.md). Figures and tables are generated from saved results by `studies/build_report.py`; no new simulations or parameter selection occur during report generation. The build checks every summary statistic and adjusted interval against the saved per-run records.',
      'Saved evidence: [selection protocol](../results/selection_v1/protocol.json), [frozen selection](../results/selection_v1/selection.json), [risk protocol](../results/risk_v1/protocol.json), [risk results](../results/risk_v1/results.json).','',
      '## Conclusion','',
      'At a 10p spread, inventory adjustment is a trade-off rather than an improvement: it reduced exposure and variability at a cost to mean profit, without protecting downside outcomes. The exact analysis shows this conclusion depends on the spread. The project demonstrates why matched experiments, explicit objectives, exact accounting and transparent reporting matter when evaluating a trading rule, and why a single fixed setting can hide the decision that matters most.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print('Verified saved summaries; created report and three PNG/SVG figures.')


if __name__=='__main__':
    main()
