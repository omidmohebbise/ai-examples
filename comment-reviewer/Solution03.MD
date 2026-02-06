# Solution03 — spaCy custom sentiment classifier (TextCategorizer)

This solution shows how to build a **very small** sentiment-style classifier using **spaCy**.

It uses spaCy’s **TextCategorizer** component (`textcat`) to assign labels like:

- `POSITIVE`
- `NOT_POSITIVE`

> Note: This is a toy example with a tiny training set. It’s meant to show the workflow, not to achieve good accuracy.

---

## What is spaCy?

**spaCy** is a popular Python library for production-ready NLP (Natural Language Processing). It provides:

- Fast tokenization and linguistic features
- Pre-trained pipelines for many languages (depending on installed model)
- Trainable components (NER, text classification, etc.)
- A consistent training and inference API (`nlp(text)`)

In spaCy, an NLP “pipeline” is an object called `nlp` (technically a `Language` instance). It runs a sequence of components (tokenizer, tagger, text classifier, etc.) when you call:

```python
doc = nlp("some text")
```

The output is a `Doc` object containing tokens and any predictions produced by pipeline components.

---

## What `Solution03.py` is doing (step-by-step)

### 1) Version guard

At the top, the script checks the Python version:

- spaCy 3.x currently depends on **`pydantic.v1`**
- **Pydantic v1 doesn’t work on Python 3.14+**

So the script fails early with a clear error message on Python 3.14+.

### 2) Imports

The script imports:

- `spacy` — the NLP framework
- `minibatch` — helper to create small training batches
- `Example` — spaCy’s training wrapper that pairs *(Doc, annotations)*

### 3) Create a blank pipeline

```python
nlp = spacy.blank("en")
```

This creates an **English** pipeline with only the tokenizer (no pre-trained model).

### 4) Add a text classification component

```python
textcat = nlp.add_pipe("textcat")
```

This adds spaCy’s **TextCategorizer** component. It will populate:

```python
doc.cats
```

with probabilities/scores for each label.

### 5) Register labels

```python
textcat.add_label("POSITIVE")
textcat.add_label("NOT_POSITIVE")
```

spaCy needs to know the full label set up front so it can create the correct output layer.

### 6) Prepare training data

The training set is a list of tuples:

```python
(text, {"cats": {"POSITIVE": 1.0, "NOT_POSITIVE": 0.0}})
```

This is the standard spaCy format for text classification:

- `text` is the raw text
- `cats` is a dictionary of label → 0.0/1.0

In this example:

- Positive sentences are labeled `POSITIVE: 1.0`
- Negative sentences are labeled `NOT_POSITIVE: 1.0`

### 7) Initialize the model

```python
optimizer = nlp.begin_training()
```

This initializes weights for trainable components (like `textcat`) and returns an optimizer.

### 8) Training loop

The script trains for 10 epochs:

- Shuffle training data each epoch
- Split into small minibatches (size=2)
- For each training example:
  - create a `Doc` with `nlp.make_doc(text)` (tokenization only)
  - wrap it into `Example.from_dict(doc, annotations)`
- Update model weights with:

```python
nlp.update(examples, sgd=optimizer, losses=losses)
```

`losses` will collect per-component training loss values.

### 9) Inference / testing

Finally, it runs on a couple test strings:

```python
for text in test_texts:
    doc = nlp(text)
    print(text, doc.cats)
```

`doc.cats` contains the predicted scores.

---

## Expected output

You should see:

- 10 epochs of training with a `textcat` loss that usually decreases
- Then 2 lines printing the text plus a dictionary of predicted label scores

Example (approximate):

- `{'POSITIVE': 0.84, 'NOT_POSITIVE': 0.16}`

---

## Limitations / next steps

This script is intentionally small, but for a more realistic classifier you’d typically:

- Use **much more training data**
- Use a stronger architecture (e.g. `textcat` vs `textcat_multilabel` depending on your use case)
- Add a train/dev split and evaluate accuracy
- Save and load the trained pipeline:

```python
nlp.to_disk("./sentiment_model")
# later...
# nlp = spacy.load("./sentiment_model")
```

- Consider using a transformer pipeline (spaCy + `spacy-transformers`) or Hugging Face for higher accuracy

