import nltk
nltk.download("vader_lexicon", quiet=True)
from nltk.sentiment.vader import SentimentIntensityAnalyzer

sid = SentimentIntensityAnalyzer()

frases = [
    "That didn't work, sorry",
    "That seemed to do the trick, thank you!",
    "still doing the same thing",
    "oh that worked. I must have entered a number or something wrong",
    "This is so frustrating, nothing is working",
    "Have a great day, goodbye!",
]

for f in frases:
    s = sid.polarity_scores(f)
    print(f'compound={s["compound"]:+.2f} | {f}')

print("VADER OK")
