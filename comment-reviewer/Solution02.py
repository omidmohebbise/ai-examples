# pip install transformers torch
from transformers import pipeline

classifier = pipeline("sentiment-analysis")  # downloads a default model

def is_positive(text: str) -> tuple[bool, float, str]:
    r = classifier(text)[0]
    label = r["label"]          # e.g., "POSITIVE" / "NEGATIVE"
    score = float(r["score"])   # 0..1
    return (label.upper() == "POSITIVE"), score, label

print(is_positive("I love this product, totally worth it!"))
print(is_positive("It broke after two days."))
