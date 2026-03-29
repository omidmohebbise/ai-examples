from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# =========================
# CONFIG
# =========================

# MODEL_SOURCE = "openai/gpt-oss-20b"
# MODEL_DIR = Path("./models/gpt-oss-20b")

MODEL_SOURCE = "microsoft/Phi-3-mini-4k-instruct"
MODEL_DIR = Path("./models/Phi-3-mini-4k-instruct")

NUM_CANDIDATES = 4
MAX_NEW_TOKENS = 500 #180
TEMPERATURE = 0.8
TOP_P = 0.95


# =========================
# DATA STRUCTURE
# =========================

@dataclass
class CandidateResult:
    rank: int
    text: str
    total_logprob: float
    avg_logprob: float
    token_count: int
    perplexity: float


# =========================
# DOWNLOAD / LOAD
# =========================

def ensure_model_downloaded(model_source: str, model_dir: Path) -> None:
    """
    Download the model and tokenizer once into the local folder if missing.
    """
    model_dir.mkdir(parents=True, exist_ok=True)

    config_file = model_dir / "config.json"
    tokenizer_file = model_dir / "tokenizer_config.json"

    if config_file.exists() and tokenizer_file.exists():
        print(f"Model already exists at: {model_dir}")
        return

    print("Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_source)
    tokenizer.save_pretrained(model_dir)

    print("Downloading model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_source,
        torch_dtype="auto",
    )
    model.save_pretrained(model_dir)

    print(f"Model saved to: {model_dir}")


def load_local_model(model_dir: Path):
    """
    Load tokenizer + model strictly from local disk.
    """
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_dir),
        local_files_only=True,
    )

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        torch_dtype="auto",
        device_map="auto",
        local_files_only=True,
    )

    model.eval()
    return tokenizer, model


# =========================
# PROMPT
# =========================

def build_prompt(question: str) -> str:
    """
    Prompt format for chat/instruct-style GPT OSS models.
    """
    return f"""<|system|>
You are a helpful assistant.
<|user|>
{question}
<|assistant|>
"""


# =========================
# GENERATION + SCORING
# =========================

def generate_scored_result_set(
        tokenizer,
        model,
        question: str,
        num_candidates: int = NUM_CANDIDATES,
        max_new_tokens: int = MAX_NEW_TOKENS,
        temperature: float = TEMPERATURE,
        top_p: float = TOP_P,
) -> Dict[str, Any]:
    """
    Ask a question and return:
      - best_answer
      - scored_result_set
    """
    prompt = build_prompt(question)

    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    prompt_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            num_return_sequences=num_candidates,
            return_dict_in_generate=True,
            output_scores=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    sequences = outputs.sequences
    step_scores = outputs.scores

    results: List[CandidateResult] = []

    for seq_idx in range(sequences.shape[0]):
        full_sequence = sequences[seq_idx]
        generated_ids = full_sequence[prompt_len:]

        text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

        token_logprobs = []

        for step_idx, token_id in enumerate(generated_ids):
            if step_idx >= len(step_scores):
                break

            logits = step_scores[step_idx][seq_idx]
            log_probs = torch.log_softmax(logits, dim=-1)
            token_logprob = log_probs[token_id].item()
            token_logprobs.append(token_logprob)

        token_count = len(token_logprobs)
        total_logprob = sum(token_logprobs) if token_logprobs else float("-inf")
        avg_logprob = total_logprob / token_count if token_count > 0 else float("-inf")
        perplexity = math.exp(-avg_logprob) if token_count > 0 else float("inf")

        results.append(
            CandidateResult(
                rank=0,
                text=text,
                total_logprob=total_logprob,
                avg_logprob=avg_logprob,
                token_count=token_count,
                perplexity=perplexity,
            )
        )

    results.sort(key=lambda x: x.avg_logprob, reverse=True)

    for i, item in enumerate(results, start=1):
        item.rank = i

    return {
        "question": question,
        "best_answer": results[0].text if results else "",
        "scored_result_set": [asdict(r) for r in results],
    }


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    ensure_model_downloaded(MODEL_SOURCE, MODEL_DIR)

    print(f"Loading model locally from: {MODEL_DIR}")
    tokenizer, model = load_local_model(MODEL_DIR)

    question = "What is the difference between concurrency and parallelism in Python?"
    result = generate_scored_result_set(tokenizer, model, question)

    print("\n" + "=" * 100)
    print("BEST ANSWER")
    print("=" * 100)
    print(result["best_answer"])

    print("\n" + "=" * 100)
    print("SCORED RESULT SET")
    print("=" * 100)
    for item in result["scored_result_set"]:
        print(item)