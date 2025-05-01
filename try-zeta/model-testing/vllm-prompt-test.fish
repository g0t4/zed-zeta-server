#!/usr/bin/env fish

# vllm serve zed-industries/zeta
# use sft.py to extract prompts from dataset 

curl -X POST http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d @(jq -n \
        --arg prompt "$(cat tmp-test-runs/prompt-311.txt)" \
        '{  prompt: $prompt, 
            max_tokens: 2000,
            temperature: 0.7, 
            top_p: 0.9, 
            n: 1, 
            stop: null
        }' \
        | psub) > tmp-test-runs/response-311.json

cat tmp-test-runs/response-311.json | jq ".choices[].text" -r
# FYI don't set model for vllm b/c it only serves one model.. and will fail if you mess up name so no point in setting unless you wanna check it

# TODO left off before check prompt is setup propertly (i.e. any system message too?) is this playing well with template as intended (or if no template that too)?
# any docs on prompt itself? IIAC SFT prompts are what I would use for real deal then
# anything else added to sft prompt? check notebook
