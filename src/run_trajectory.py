"""Analyse intra-conversation sentiment trajectory for shopping_cart."""
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sentiment import score_text

RAW = Path(__file__).parent.parent / "data" / "raw" / "abcd_v1.1.json"

with open(RAW, "r", encoding="utf-8") as f:
    raw = json.load(f)

all_convos = [c for split, convos in raw.items() for c in convos]

# For shopping_cart, collect per-turn customer sentiment
# Normalise turn position to 0-1 so conversations of different lengths are comparable
bucket_scores = {i: [] for i in range(5)}   # 5 equal-length buckets

sc_convos = [c for c in all_convos if c["scenario"]["subflow"] == "shopping_cart"]

for c in sc_convos:
    turns = c["original"]
    cust = [(i, t[1]) for i, t in enumerate(turns) if t[0] == "customer"]
    if len(cust) < 2:
        continue
    n = len(cust)
    for rank, (_, text) in enumerate(cust):
        bucket = min(int(rank / n * 5), 4)
        bucket_scores[bucket].append(score_text(text))

print("=== shopping_cart: sentimento médio por posição na conversa (0=início, 4=fim) ===")
for bucket, scores in bucket_scores.items():
    print(f"  Bucket {bucket}: mean={np.mean(scores):+.3f}  n={len(scores)}")

# Compare trajectory: with vs without try-again
print("\n=== Trajetória: com try-again vs sem ===")
for has_ta in (0, 1):
    label = "COM try-again" if has_ta else "SEM try-again"
    subset = [c for c in sc_convos
              if ("try-again" in [t["targets"][2] for t in c["delexed"]
                                  if t["targets"][1] == "take_action"]) == bool(has_ta)]
    buckets = {i: [] for i in range(5)}
    for c in subset:
        turns = c["original"]
        cust = [(i, t[1]) for i, t in enumerate(turns) if t[0] == "customer"]
        n = len(cust)
        if n < 2:
            continue
        for rank, (_, text) in enumerate(cust):
            bucket = min(int(rank / n * 5), 4)
            buckets[bucket].append(score_text(text))
    scores_by_bucket = [np.mean(buckets[i]) if buckets[i] else 0.0 for i in range(5)]
    print(f"  {label} (n={len(subset)}): {[f'{s:+.3f}' for s in scores_by_bucket]}")

# Sentiment at the exact moment of failure (turn right after "that didn't work")
print("\n=== Momento da falha: sentimento do turno após 'não funcionou' ===")
failure_phrases = ["didn't work", "did not work", "not working", "still", "same thing", "still doing"]
failure_scores = []
recovery_scores = []

for c in sc_convos:
    turns = c["original"]
    actions = [t["targets"][2] for t in c["delexed"] if t["targets"][1] == "take_action"]
    if "try-again" not in actions:
        continue
    cust_turns = [t for t in turns if t[0] == "customer"]
    for i, turn in enumerate(cust_turns):
        text = turn[1].lower()
        if any(p in text for p in failure_phrases):
            failure_scores.append(score_text(turn[1]))
            if i + 1 < len(cust_turns):
                recovery_scores.append(score_text(cust_turns[i+1][1]))

if failure_scores:
    print(f"  Turno de falha:      mean={np.mean(failure_scores):+.3f}  n={len(failure_scores)}")
if recovery_scores:
    print(f"  Turno pós-falha:     mean={np.mean(recovery_scores):+.3f}  n={len(recovery_scores)}")
