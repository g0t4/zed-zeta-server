#!/usr/bin/env fish

# rm -rf .venv
uv venv
source .venv/bin/activate.fish
uv pip install ipykernel rich yapf
uv pip install httpx flask # for server.py
uv pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
uv pip install xformers --no-deps
# TODO install xformers from source so its built for cu128 torch 
# Unsloth: Failed to patch Gemma3ForConditionalGeneration.
# WARNING[XFORMERS]: xFormers can't load C++/CUDA extensions. xFormers was built for:
#     PyTorch 2.6.0+cu124 with CUDA 1204 (you have 2.8.0.dev20250424+cu128)
#     Python  3.11.11 (you have 3.11.11)
#   Please reinstall xformers (see https://github.com/facebookresearch/xformers#installing-xformers)
#   Memory-efficient attention, SwiGLU, sparse and more won't be available.
#   Set XFORMERS_MORE_DETAILS=1 for more details

# unsolth needs these deps (don't install its deps from prod package, it will replace cu128 torch):
#   FYI run imports and/or use unsloth to find what is needed for my case:
#   then dry run installs:
#      uv pip install bitsandbytes --dry-run
uv pip install bitsandbytes --no-deps 
uv pip install unsloth_zoo # many deps, look benign w/ --dry-run so let it install them (diff pip list to see if it changes in future)
# 
uv pip install --upgrade --no-cache-dir --no-deps git+https://github.com/unslothai/unsloth.git
# FYI confirmed no deps installed if just use repo alone (even if remove the --no-deps flag)
# FYI drop --no-cache-dir to speed up uv pip install... but then not using latest (necessarily)

#%% 
