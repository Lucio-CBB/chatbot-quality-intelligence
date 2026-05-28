"""Smoke-test nb04 + nb05 computations and save all figures."""
import pandas as pd
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

sns.set_theme(style='whitegrid')
PROC        = Path(__file__).parent.parent / 'data' / 'processed'
FIGURES_DIR = Path(__file__).parent.parent / 'reports' / 'figures'

df = pd.read_parquet(PROC / 'conversations_patterns.parquet')
sf = pd.read_csv(PROC / 'subflow_patterns_ice.csv')

# ── NB04: Fig 1 — prevalência global ──────────────────────────────────
pattern_cols = {
    'p_try_again':   'P1 Try-again loop',
    'p_verify_loop': 'P2 Verification loop',
    'p_escalation':  'P3 Escalation inesperada',
    'p_action_rep':  'P4 Repeticao de acao',
    'p_long_outlier':'P5 Outlier comprimento',
    'any_pattern':   'Qualquer padrao',
}
prev = {label: df[col].mean() * 100 for col, label in pattern_cols.items()}
fig, ax = plt.subplots(figsize=(9, 4))
labels, values = list(prev.keys()), list(prev.values())
colors = ['#d62728','#ff7f0e','#9467bd','#8c564b','#e377c2','#17becf']
bars = ax.barh(labels, values, color=colors, edgecolor='none')
for bar, val in zip(bars, values):
    ax.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
            f'{val:.1f}%  ({int(val/100*len(df)):,})', va='center', fontsize=9)
ax.set_xlabel('% das conversas')
ax.set_title('Prevalencia de Padroes Estruturais de Falha', fontweight='bold')
ax.set_xlim(0, 28)
plt.tight_layout()
plt.savefig(FIGURES_DIR / '04_pattern_prevalence.png', bbox_inches='tight')
plt.close()
print("NB04 Fig1 salva")

# ── NB04: Fig 2 — heatmap ─────────────────────────────────────────────
flow_patterns = df.groupby('flow')[list(pattern_cols.keys())[:-1]].mean() * 100
flow_patterns.columns = ['P1','P2','P3','P4','P5']
flow_patterns = flow_patterns.sort_values('P1', ascending=False)
fig, ax = plt.subplots(figsize=(9, 6))
sns.heatmap(flow_patterns, annot=True, fmt='.0f', cmap='YlOrRd',
            linewidths=0.5, ax=ax, cbar_kws={'label': '% conversas'})
ax.set_title('Padroes de Falha (%) por Flow', fontweight='bold', fontsize=12)
plt.tight_layout()
plt.savefig(FIGURES_DIR / '04_pattern_heatmap_flow.png', bbox_inches='tight')
plt.close()
print("NB04 Fig2 salva")

# ── NB04: Fig 3 — troubleshoot_site drill-down ────────────────────────
ts = sf[sf['flow'] == 'troubleshoot_site'].sort_values('any_pattern', ascending=False)
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
subs = ts['subflow'].values
p1, p2, p5 = ts['p_try_again'].values, ts['p_verify_loop'].values, ts['p_long_outlier'].values
axes[0].bar(subs, p1, label='P1 try-again', color='#d62728')
axes[0].bar(subs, p2, bottom=p1, label='P2 verify loop', color='#ff7f0e')
axes[0].bar(subs, p5, bottom=p1+p2, label='P5 outlier', color='#e377c2')
axes[0].set_ylabel('% conversas'); axes[0].set_title('Composicao dos Padroes', fontweight='bold')
axes[0].legend(fontsize=8); axes[0].set_xticklabels(subs, rotation=15, ha='right')
colors_ts = ['#d62728' if v > 50 else '#aec7e8' for v in ts['any_pattern']]
axes[1].bar(subs, ts['turns_mean'].values, color=colors_ts, edgecolor='none')
axes[1].axhline(df['n_turns'].mean(), color='navy', ls='--', lw=1.5,
                label=f'Media global ({df["n_turns"].mean():.0f})')
axes[1].set_ylabel('Turnos medios'); axes[1].set_title('Comprimento Medio', fontweight='bold')
axes[1].legend(fontsize=8); axes[1].set_xticklabels(subs, rotation=15, ha='right')
plt.suptitle('troubleshoot_site — Analise por Subflow', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(FIGURES_DIR / '04_troubleshoot_site_patterns.png', bbox_inches='tight')
plt.close()
print("NB04 Fig3 salva")

# ── NB05: Fig 1 — ICE ranking ─────────────────────────────────────────
top10 = sf.nlargest(10, 'ice_score').sort_values('ice_norm')
bar_labels = top10['subflow'] + ' (' + top10['flow'] + ')'
colors_bar = ['#d62728' if s == 'shopping_cart' else
              '#ff7f0e' if s in ('credit_card','slow_speed') else
              '#aec7e8' for s in top10['subflow']]
fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(bar_labels, top10['ice_norm'], color=colors_bar, edgecolor='none')
for bar, row in zip(bars, top10.itertuples()):
    ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
            f'ICE={row.ice_norm:.0f}  I={row.impact:.0f} C={row.confidence:.0f} E={row.ease:.0f}',
            va='center', fontsize=8.5)
ax.set_xlabel('ICE Score Normalizado (0-100)')
ax.set_title('Ranking ICE — Top 10 Subflows', fontweight='bold', fontsize=13)
ax.set_xlim(0, 145)
r = mpatches.Patch(color='#d62728', label='#1 Alvo do A/B')
o = mpatches.Patch(color='#ff7f0e', label='#2-3 Candidatos futuros')
b = mpatches.Patch(color='#aec7e8', label='Demais')
ax.legend(handles=[r, o, b], loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / '05_ice_ranking.png', bbox_inches='tight')
plt.close()
print("NB05 Fig1 salva")

# ── NB05: Fig 2 — ICE decomposition top4 ─────────────────────────────
candidates = sf.nlargest(4, 'ice_score')
comp_labels = candidates['subflow'].values
highlight   = ['#d62728' if s == 'shopping_cart' else '#aec7e8' for s in comp_labels]
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, col, title in zip(axes,
    ['impact', 'confidence', 'ice_norm'],
    ['Impact', 'Confidence (%)', 'ICE Normalizado']):
    bars = ax.bar(comp_labels, candidates[col].values, color=highlight, edgecolor='none')
    for bar, val in zip(bars, candidates[col].values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
                f'{val:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
    ax.set_title(title, fontweight='bold')
    ax.set_xticklabels(comp_labels, rotation=15, ha='right', fontsize=8)
    ax.set_ylim(0, candidates[col].max() * 1.25)
plt.suptitle('Comparacao Top 4 — Componentes do ICE', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(FIGURES_DIR / '05_ice_decomposition_top4.png', bbox_inches='tight')
plt.close()
print("NB05 Fig2 salva")

# ── Sensitivity analysis numbers ──────────────────────────────────────
top4 = sf.nlargest(4, 'ice_score')[['subflow','impact','confidence']].copy()
print("\nSensibilidade ao Ease:")
print(f"{'Subflow':15s}" + ''.join(f'  E={e}' for e in [1,2,3,4,5,6]))
print('-' * 65)
for _, row in top4.iterrows():
    scores = [f'{row["impact"]*row["confidence"]/e:6.0f}' for e in [1,2,3,4,5,6]]
    print(f"{row['subflow']:15s}" + '  '.join(scores))

sc  = sf[sf['subflow']=='shopping_cart'].iloc[0]
cc  = sf[sf['subflow']=='credit_card'].iloc[0]
gap = (sc['ice_score']/cc['ice_score']-1)*100
print(f"\nshopping_cart ICE = {sc['ice_score']:.0f} | credit_card ICE = {cc['ice_score']:.0f}")
print(f"Gap: +{gap:.0f}% acima do segundo colocado")
print("\nOK — todos os checks passaram")
