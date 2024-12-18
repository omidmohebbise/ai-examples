from transformers import pipeline

# Load a pre-trained text-generation model (GPT-2)
generator = pipeline("text-generation", model="gpt2")

# Generate text from a simple prompt
prompt = "I am going to GYM"
result = generator(prompt, max_length=50, num_return_sequences=1)

# Print the output
print("AI Response:")
print(result[0]["generated_text"])
