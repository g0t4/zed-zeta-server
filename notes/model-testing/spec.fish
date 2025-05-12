#!/usr/bin/env fish

# FYI! change to cu128 compiled nightlies for torch
z vllm-latest
# TODO pull latest and build to see if that fixes quantization


# zed model card says to use:
#   https://huggingface.co/zed-industries/zeta
#
vllm serve zed-industries/zeta \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --quantization="fp8" \
    --speculative-model [ngram] \
    --ngram-prompt-lookup-max 4 \
    --ngram-prompt-lookup-min 2 \
    --num-speculative-tokens 8
#  but the ngram params don't exist on vllm serve? or do I need a custom build?
# or did vllm change how this works?
# FYI I found these args used in vllm repo:
#   https://github.com/vllm-project/vllm/blob/1ef53cce9/benchmarks/README.md#L148-L152
#     --speculative-model [ngram] \
#     --ngram-prompt-lookup-max 4 \
#     --ngram-prompt-lookup-min 2 \
#     --num-speculative-tokens 8
#  * so are they just undocumented or changed?

# vllm docs spec dec ngram:
#   https://docs.vllm.ai/en/latest/features/spec_decode.html#speculating-by-matching-n-grams-in-the-prompt
vllm serve --help
# shows:
# --speculative-config SPECULATIVE_CONFIG
#   The configurations for speculative decoding. Should be a JSON string. (default: None)
vllm serve zed-industries/zeta \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --speculative-config '{"method": "ngram", "num_speculative_tokens": 5, "prompt_lookup_max": 4, "prompt_lookup_min": 2 }' 
    # --quantization="fp8" \
# cool! timings on ./server/test.sh:
#   ~ 1.2s w/o spec dec
#   ~ 770ms w/ spec dec
#      yup in Zed it feels much faster too!

# TODO! FIGURE OUT quantization! that should boost speeds even more so!
# --quantization="fp8"    ... adding this causes runtime errors, need to dig into stack trace as there's no useful message AFAICT


# * btw these work w/o spec dec (but --quantization="fp8" fails... is it not possible on 50 series?)
vllm serve zed-industries/zeta \
    --enable-prefix-caching \
    --enable-chunked-prefill \

# * spec dec that I have working too:

vllm serve zed-industries/zeta \
    --speculative-config '{"method": "ngram", "num_speculative_tokens": 5, "prompt_lookup_max": 4, "prompt_lookup_min": 2 }' 

vllm serve zed-industries/zeta \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --speculative-config '{"method": "ngram", "num_speculative_tokens": 5, "prompt_lookup_max": 4, "prompt_lookup_min": 2 }' 

# w/o spec dec:

vllm serve zed-industries/zeta

