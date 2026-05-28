"""Run full sentiment analysis and print key stats for notebook 03."""
import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sentiment import score_conversation

RAW = Path(__file__).parent.parent / "data" / "raw" / "abcd_v1.1.json"
PROC = Path(__file__).parent.parent / "data" / "processed"

with open(RAW, "r", encoding="utf-8") as f:
    raw = json.load(f)

records = []
for split, convos in raw.items():
    for c in convos:
        sf = c["scenario"]["subflow"]
        fl = c["scenario"]["flow"]
        turns = c["original"]
        all_actions = [t["targets"][2] for t in c["delexed"]
                       if t["targets"][1] == "take_action"]
        last_action = all_actions[-1] if all_actions else None
        is_escalation = last_action == "notify-team" and sf != "out_of_stock_general"
        resolution = 0 if is_escalation else 1
        n_try_again = all_actions.count("try-again")
        has_friction = int(n_try_again > 0 or all_actions.count("verify-identity") > 1)

        sent = score_conversation(turns, speaker="customer")

        records.append({
            "convo_id":        c["convo_id"],
            "split":           split,
            "flow":            fl,
            "subflow":         sf,
            "n_turns":         len(turns),
            "n_try_again":     n_try_again,
            "resolution":      resolution,
            "has_friction":    has_friction,
            "sent_opening":    sent["opening"],
            "sent_closing":    sent["closing"],
            "sent_delta":      sent["delta"],
            "sent_mean":       sent["mean"],
        })

df = pd.DataFrame(records)
df.to_parquet(PROC / "conversations_sentiment.parquet", index=False)

print("=== SENTIMENTO GLOBAL ===")
print(f"  Opening médio:   {df['sent_opening'].mean():+.3f}")
print(f"  Closing médio:   {df['sent_closing'].mean():+.3f}")
print(f"  Delta médio:     {df['sent_delta'].mean():+.3f}")

print("\n=== COM vs SEM FRICÇÃO ===")
grp = df.groupby("has_friction")[["sent_opening", "sent_closing", "sent_delta", "sent_mean"]].mean()
print(grp.round(3).to_string())

print("\n=== shopping_cart e credit_card ===")
target = df[df["subflow"].isin(["shopping_cart", "credit_card"])]
grp2 = target.groupby(["subflow", "has_friction"])[
    ["sent_opening", "sent_closing", "sent_delta"]
].mean()
print(grp2.round(3).to_string())

print("\n=== DELTA POR FLOW ===")
flow_sent = df.groupby("flow")[["sent_opening", "sent_closing", "sent_delta"]].mean()
flow_sent = flow_sent.sort_values("sent_delta")
print(flow_sent.round(3).to_string())

print("\nSalvo em data/processed/conversations_sentiment.parquet")
