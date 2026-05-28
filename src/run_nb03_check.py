"""Smoke-test all notebook 03 computations and save figures."""
import sys, json
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from sentiment import score_text

sns.set_theme(style='whitegrid')
FIGURES_DIR = Path(__file__).parent.parent / 'reports' / 'figures'
PROC_DIR    = Path(__file__).parent.parent / 'data' / 'processed'
RAW_PATH    = Path(__file__).parent.parent / 'data' / 'raw' / 'abcd_v1.1.json'

df = pd.read_parquet(PROC_DIR / 'conversations_sentiment.parquet')

# --- Fig 1: friction impact ---
grp_means = df.groupby('has_friction')[['sent_opening','sent_closing','sent_mean']].mean()
labels = ['Sem fricção', 'Com fricção']
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
pairs = [('sent_opening','Opening',['#aec7e8','#ffbb78']),
         ('sent_closing','Closing',['#2ca02c','#d62728']),
         ('sent_mean',   'Médio',  ['#aec7e8','#ffbb78'])]
for ax, (col, title, colors) in zip(axes, pairs):
    vals = grp_means[col].values
    bars = ax.bar(labels, vals, color=colors, edgecolor='white', width=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.002, f'{val:+.3f}',
                ha='center', va='bottom', fontweight='bold')
    ax.set_title(title, fontweight='bold')
    ax.set_ylim(0, vals.max()*1.3)
plt.suptitle('Impacto da Fricção no Sentimento', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(FIGURES_DIR / '03_sentiment_friction_impact.png', bbox_inches='tight')
plt.close()
print("Fig 1 salva")

# --- Trajectory ---
with open(RAW_PATH, 'r', encoding='utf-8') as f:
    raw = json.load(f)
all_convos = [c for split, convos in raw.items() for c in convos]

def compute_trajectory(convos_subset):
    buckets = {i: [] for i in range(5)}
    for c in convos_subset:
        cust = [t[1] for t in c['original'] if t[0] == 'customer']
        n = len(cust)
        if n < 2: continue
        for rank, text in enumerate(cust):
            bucket = min(int(rank / n * 5), 4)
            buckets[bucket].append(score_text(text))
    return [np.mean(buckets[i]) if buckets[i] else 0.0 for i in range(5)]

sc_all  = [c for c in all_convos if c['scenario']['subflow'] == 'shopping_cart']
sc_nofr = [c for c in sc_all if 'try-again' not in
           [t['targets'][2] for t in c['delexed'] if t['targets'][1]=='take_action']]
sc_fr   = [c for c in sc_all if 'try-again' in
           [t['targets'][2] for t in c['delexed'] if t['targets'][1]=='take_action']]

traj_nofr = compute_trajectory(sc_nofr)
traj_fr   = compute_trajectory(sc_fr)
print(f"SEM try-again (n={len(sc_nofr)}): {[f'{v:+.3f}' for v in traj_nofr]}")
print(f"COM try-again (n={len(sc_fr)}):   {[f'{v:+.3f}' for v in traj_fr]}")

# --- Fig 2: trajectory ---
x_labels = ['Início', 'Q1', 'Meio', 'Q3', 'Fim']
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(x_labels, traj_nofr, 'o-', color='#2ca02c', linewidth=2.5, markersize=8,
        label=f'Sem try-again (n={len(sc_nofr)})')
ax.plot(x_labels, traj_fr,   's--', color='#d62728', linewidth=2.5, markersize=8,
        label=f'Com try-again (n={len(sc_fr)})')
ax.axhline(0, color='black', linewidth=0.5, linestyle=':')
diff = traj_nofr[-1] - traj_fr[-1]
ax.annotate(f'Δ closing = {diff:+.3f}', xy=(x_labels[-1], (traj_nofr[-1]+traj_fr[-1])/2),
            xytext=(3.2, (traj_nofr[-1]+traj_fr[-1])/2+0.03), fontsize=9, color='navy', fontweight='bold')
ax.set_ylabel('VADER compound')
ax.set_title('shopping_cart — Trajetória de Sentimento', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(FIGURES_DIR / '03_sentiment_trajectory_shopping_cart.png', bbox_inches='tight')
plt.close()
print("Fig 2 salva")

# --- Guardrail numbers ---
sc_df = df[df['subflow'] == 'shopping_cart']
baseline_closing = sc_df[sc_df['has_friction']==1]['sent_closing'].mean()
target_closing   = sc_df[sc_df['has_friction']==0]['sent_closing'].mean()
n  = sc_df[sc_df['has_friction']==1]['sent_closing'].count()
se = sc_df[sc_df['has_friction']==1]['sent_closing'].std() / np.sqrt(n)
ci_low  = baseline_closing - 1.96 * se
ci_high = baseline_closing + 1.96 * se

print(f"\nGUARDRAIL BASELINE (shopping_cart, com fricção):")
print(f"  Closing médio:   {baseline_closing:+.3f}")
print(f"  IC 95%:          [{ci_low:+.3f}, {ci_high:+.3f}]")
print(f"  Target (sem fr): {target_closing:+.3f}")

# Stats
no_fr  = df[df['has_friction']==0]['sent_closing']
with_fr = df[df['has_friction']==1]['sent_closing']
u, p = stats.mannwhitneyu(no_fr, with_fr, alternative='greater')
sig = "significativo" if p < 0.05 else "nao significativo"
print(f"\nMann-Whitney (closing, sem>com friccao): p={p:.4f} [{sig}]")
print("\nOK")
