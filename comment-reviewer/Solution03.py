import sys

# spaCy 3.x currently relies on pydantic.v1, which isn't compatible with Python 3.14+.
# Fail fast with a clear message instead of a long import traceback.
if sys.version_info >= (3, 14):
    raise RuntimeError(
        "This example requires Python <= 3.13 (recommended: 3.12). "
        "Your interpreter is %d.%d.%d. "
        "Create a venv with Python 3.12 and install comment-reviewer/requirements.txt."
        % (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    )

import random
import spacy
from spacy.util import minibatch
from spacy.training import Example

# Create a blank English pipeline
nlp = spacy.blank("en")

# Add text classification component
textcat = nlp.add_pipe("textcat")

# Define your labels
textcat.add_label("POSITIVE")
textcat.add_label("NOT_POSITIVE")

# Small training dataset (you should add more)
train_data = [
    ("This product is amazing, I love it!", {"cats": {"POSITIVE": 1.0, "NOT_POSITIVE": 0.0}}),
    ("Perfect quality and fast delivery.", {"cats": {"POSITIVE": 1.0, "NOT_POSITIVE": 0.0}}),
    ("Terrible item, waste of money.", {"cats": {"POSITIVE": 0.0, "NOT_POSITIVE": 1.0}}),
    ("It broke after one day. Very disappointed.", {"cats": {"POSITIVE": 0.0, "NOT_POSITIVE": 1.0}}),
]

optimizer = nlp.begin_training()

for epoch in range(10):
    random.shuffle(train_data)
    losses = {}

    batches = minibatch(train_data, size=2)
    for batch in batches:
        examples = []
        for text, annotations in batch:
            doc = nlp.make_doc(text)
            examples.append(Example.from_dict(doc, annotations))

        nlp.update(examples, sgd=optimizer, losses=losses)

    print(f"Epoch {epoch+1}, Losses: {losses}")

# Test
test_texts = [
    "This is great and works perfectly!",
    "Not good at all. Very bad quality."
]

for text in test_texts:
    doc = nlp(text)
    print(text, doc.cats)
