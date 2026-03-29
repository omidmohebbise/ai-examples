from local_model_scored import load_local_model, generate_scored_result_set

tokenizer, model = load_local_model("microsoft/Phi-3-mini-4k-instruct")

result = generate_scored_result_set(
    tokenizer=tokenizer,
    model=model,
    question="Explain Java virtual threads simply"
)

print(result["best_answer"])
print(result["scored_result_set"])