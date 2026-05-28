"""
Compute structural patterns (nb04) and ICE scores (nb05).
Run once to get all numbers needed for both notebooks.
"""
import json
import numpy as np
import pandas as pd
from collections import Counter
from pathlib import Path

PROC = Path(__file__).parent.parent / "data" / "processed"
RAW  = Path(__file__).parent.parent / "data" / "raw" / "abcd_v1.1.json"

with open(RAW, "r", encoding="utf-8") as f:
    raw = json.load(f)

all_convos = []
for _split, _convos in raw.items():
    for _c in _convos:
        _c["_split"] = _split
        all_convos.append(_c)

# ─── PATTERN DETECTION ───────────────────────────────────────────────
records = []
for c in all_convos:
    sf   = c["scenario"]["subflow"]
    fl   = c["scenario"]["flow"]
    turns = c["original"]
    actions = [t["targets"][2] for t in c["delexed"]
               if t["targets"][1] == "take_action"]
    last_action = actions[-1] if actions else None

    n_try_again = actions.count("try-again")
    n_verify    = actions.count("verify-identity")
    n_logout    = actions.count("log-out-in")

    # Pattern 1: try-again loop
    p_try_again = int(n_try_again >= 1)
    # Pattern 2: verification loop (same step repeated)
    p_verify_loop = int(n_verify > 1)
    # Pattern 3: unexpected escalation
    p_escalation = int(last_action == "notify-team" and sf != "out_of_stock_general")
    # Pattern 4: action repetition (any action >= 3x, excl. retrieve_utterance)
    action_freq = Counter(a for a in actions if a)
    p_action_rep = int(any(v >= 3 for v in action_freq.values()))
    # Pattern 5: long outlier (computed per subflow later)

    any_pattern = int(p_try_again or p_verify_loop or p_escalation or p_action_rep)

    records.append({
        "convo_id":      c["convo_id"],
        "split":         c.get("_split", "?"),
        "flow":          fl,
        "subflow":       sf,
        "n_turns":       len(turns),
        "n_actions":     len(actions),
        "n_try_again":   n_try_again,
        "n_verify":      n_verify,
        "n_logout":      n_logout,
        "last_action":   last_action,
        "resolution":    0 if p_escalation else 1,
        "p_try_again":   p_try_again,
        "p_verify_loop": p_verify_loop,
        "p_escalation":  p_escalation,
        "p_action_rep":  p_action_rep,
        "any_pattern":   any_pattern,
    })

df = pd.DataFrame(records)

# Pattern 5: long outlier per subflow
sf_stats = df.groupby("subflow")["n_turns"].agg(["mean", "std"]).reset_index()
sf_stats.columns = ["subflow", "turns_mean", "turns_std"]
df = df.merge(sf_stats, on="subflow", how="left")
df["p_long_outlier"] = ((df["n_turns"] > df["turns_mean"] + 1.5 * df["turns_std"])
                         .astype(int))
df["any_pattern"] = df[["p_try_again","p_verify_loop","p_escalation",
                          "p_action_rep","p_long_outlier"]].max(axis=1)

# ─── PATTERN SUMMARY ─────────────────────────────────────────────────
print("=== PADRÕES GLOBAIS ===")
patterns = {
    "try-again loop":     df["p_try_again"].mean(),
    "verification loop":  df["p_verify_loop"].mean(),
    "escalation":         df["p_escalation"].mean(),
    "action repetition":  df["p_action_rep"].mean(),
    "long outlier":       df["p_long_outlier"].mean(),
    "any pattern":        df["any_pattern"].mean(),
}
for k, v in patterns.items():
    n = int(v * len(df))
    print(f"  {k:22s}: {v:.1%}  ({n:,} conversas)")

# ─── PATTERN × SUBFLOW ───────────────────────────────────────────────
sf_patterns = df.groupby(["flow","subflow"]).agg(
    n=("convo_id","count"),
    resolution=("resolution","mean"),
    p_try_again=("p_try_again","mean"),
    p_verify_loop=("p_verify_loop","mean"),
    p_escalation=("p_escalation","mean"),
    p_action_rep=("p_action_rep","mean"),
    p_long_outlier=("p_long_outlier","mean"),
    any_pattern=("any_pattern","mean"),
    turns_mean=("n_turns","mean"),
).reset_index()

for col in ["resolution","p_try_again","p_verify_loop","p_escalation",
            "p_action_rep","p_long_outlier","any_pattern"]:
    sf_patterns[col] = (sf_patterns[col] * 100).round(1)
sf_patterns["turns_mean"] = sf_patterns["turns_mean"].round(1)

print("\n=== TOP 15 SUBFLOWS POR any_pattern ===")
top = sf_patterns.nlargest(15, "any_pattern")[
    ["flow","subflow","n","any_pattern","p_try_again","p_verify_loop",
     "p_escalation","p_action_rep","p_long_outlier"]]
print(top.to_string(index=False))

# ─── ICE SCORING ─────────────────────────────────────────────────────
# Impact  = n × any_pattern_rate   (volume × taxa de padrão problemático)
# Confidence: baseado na dominância do padrão principal (% do padrão mais comum)
# Ease: inverso da complexidade da intervenção (definido manualmente por subflow-tipo)

# Ease = dificuldade da intervenção (1=trivial, 10=muito complexo)
# Escala inversa à intuição: MAIOR Ease = MAIS difícil = PENALIZA o score
# Justificativa inline:
EASE_MAP = {
    # Troubleshoot: add 1 diagnostic question before suggesting solution
    "shopping_cart":   2,   # 1 question added to opening → trivial change
    "credit_card":     3,   # 1-2 questions (expiry? typo?) → small change
    "slow_speed":      5,   # requires redesigning diagnostic flow (multi-cause)
    "search_results":  6,   # mixed patterns; less clear single intervention
    # Subscription / account: business logic change needed
    "manage_extension": 6,
    "out_of_stock_one_item": 5,
    "manage_change_name":    5,
    "manage_payment_method": 6,
    # Shipping / order: multi-step, integration complexity
    "recover_username": 4,
    "manage_pay_bill":  5,
    "manage":           6,
    "status":           5,
    "status_payment_method": 5,
    "manage_dispute_bill": 6,
}
DEFAULT_EASE = 5

def compute_confidence(row):
    """
    Confidence = dominância do padrão principal.
    Se um único padrão domina (>80% das conversas com padrão), confiança alta.
    """
    pattern_rates = [
        row["p_try_again"], row["p_verify_loop"],
        row["p_escalation"], row["p_action_rep"]
    ]
    total = row["any_pattern"]
    if total == 0:
        return 0.0
    dominant = max(pattern_rates)
    return min(dominant / total * 100, 100.0)  # % que o padrão dominante representa

sf_patterns["impact"]     = (sf_patterns["n"] * sf_patterns["any_pattern"] / 100).round(1)
sf_patterns["confidence"] = sf_patterns.apply(compute_confidence, axis=1).round(1)
sf_patterns["ease"]       = sf_patterns["subflow"].map(EASE_MAP).fillna(DEFAULT_EASE)
sf_patterns["ice_score"]  = (sf_patterns["impact"] * sf_patterns["confidence"] / sf_patterns["ease"]).round(1)

# Normalizar ICE para 0-100
max_ice = sf_patterns["ice_score"].max()
sf_patterns["ice_norm"] = (sf_patterns["ice_score"] / max_ice * 100).round(1)

print("\n=== ICE RANKING — TOP 15 ===")
ice_top = sf_patterns.nlargest(15, "ice_score")[
    ["flow","subflow","n","any_pattern","impact","confidence","ease","ice_score","ice_norm"]]
print(ice_top.to_string(index=False))

# Salvar
sf_patterns.to_csv(PROC / "subflow_patterns_ice.csv", index=False)
df.to_parquet(PROC / "conversations_patterns.parquet", index=False)
print("\nSalvo: subflow_patterns_ice.csv  |  conversations_patterns.parquet")
