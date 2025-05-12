# based on: sft.ipynb

import subprocess

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

#%% 

from unsloth import FastLanguageModel
import torch
import os

hf_token = os.environ.get('HF_TOKEN')
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')

# TODO if I wanna run SFT... need to install xformers built for cu128

max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = False # Use 4bit quantization to reduce memory usage. Can be False.
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen2.5-Coder-7B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
#%% 

# FYI for now skipping unsloth usage b/c I just wanna build prompts to test vllm serve zeta

#%% 

# FYI! I had to collapse prompt into a single line string b/c iron.nvim doesn't detect these! ugh it filters them out as if comments... TODO fix that!
# alpaca_prompt = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n\n{}\n"""
# FYI for my purposes, I don't want to include response (obviously... I am testing the already fine tuned model :)...  so I lopped off output/response
test_prompt = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""

#%% 

EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
original_start_marker = "<|editable_region_start|>"
original_end_marker = "<|editable_region_end|>"

def format_example(events, input, output):
    is_312 = "let new_edits = <|user_cursor_is_here|>" in input
    if is_312:
        print("## 312 found")
        print("events:", events)
        print("input:", input)
        print("output:", output)
    prompt = test_prompt.format(events, input, output)
    if is_312:
        print("prompt:", prompt)
    return prompt

def formatting_prompts_func(examples):
    events       = examples["events"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for events, input, output in zip(events, inputs, outputs):
        output_start_index = output.find(original_start_marker)
        output_focused_region = output[output_start_index:]
        output = output_focused_region

        # Must add EOS_TOKEN, otherwise your generation will go on forever!
        text = format_example(events, input, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }
pass

def filter_long_sequences(examples):
    tokenized = tokenizer(examples["text"])
    return len(tokenized['input_ids']) <= 1500

from datasets import load_dataset

# Pinned commit: 5920488, num_steps = 60, ratio = 2e-4, batch=8, rank=256, alpha=256
revision = "5920488"
dataset = load_dataset("zed-industries/zeta", token = hf_token, revision = revision)
dataset = dataset.map(formatting_prompts_func, batched = True,)
train_dataset = dataset["train"].filter(filter_long_sequences)
eval_dataset = dataset["eval"]

print("train len", len(train_dataset))
print("eval len", len(eval_dataset))

#%% 
# * right now I am just extracting examples to manually test vllm serve myself (so dont need to load model above... just being lazy with generating prompt and EOS token was only reason I left that stuff in for loading tokenizer)
import json
from rich import print as rich_print
print = rich_print

_311 = train_dataset[311] 

with open('tmp-test-runs/full-311.json', 'w') as f:
    f.write(json.dumps(_311))
with open('tmp-test-runs/prompt-311.txt', 'w') as f:
    f.write(_311["text"])

print(_311)
