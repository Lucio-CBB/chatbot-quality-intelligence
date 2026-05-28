"""
Sentiment scoring utilities using VADER.

Limitation: VADER misclassifies some resolution phrases that contain
negative words out of context (e.g., "that worked, I entered it wrong"
scores negative due to "wrong"). Use compound scores directionally,
not as exact values.
"""
import nltk
nltk.download("vader_lexicon", quiet=True)
from nltk.sentiment.vader import SentimentIntensityAnalyzer

_sid = SentimentIntensityAnalyzer()


def score_text(text: str) -> float:
    """Return VADER compound score [-1, +1] for a single string."""
    if not text or not text.strip():
        return 0.0
    return _sid.polarity_scores(text)["compound"]


def score_conversation(turns: list, speaker: str = "customer") -> dict:
    """
    Score a conversation's sentiment trajectory for a given speaker.

    Parameters
    ----------
    turns : list of [speaker, text] pairs
    speaker : which side to score ('customer' or 'agent')

    Returns
    -------
    dict with keys:
        opening   - mean score of first 2 speaker turns
        closing   - mean score of last 2 speaker turns
        delta     - closing - opening
        all_scores - list of (turn_index, score) for every speaker turn
        mean      - mean score across all turns
    """
    speaker_turns = [(i, t[1]) for i, t in enumerate(turns) if t[0] == speaker]

    if not speaker_turns:
        return {"opening": 0.0, "closing": 0.0, "delta": 0.0, "all_scores": [], "mean": 0.0}

    scored = [(idx, score_text(text)) for idx, text in speaker_turns]
    scores = [s for _, s in scored]

    n = len(scores)
    opening = float(sum(scores[:2]) / min(2, n))
    closing = float(sum(scores[-2:]) / min(2, n))

    return {
        "opening":    opening,
        "closing":    closing,
        "delta":      closing - opening,
        "all_scores": scored,
        "mean":       float(sum(scores) / n),
    }
