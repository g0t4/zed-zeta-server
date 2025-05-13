#!/usr/bin/env fish

cd "$HOME/repos/github/g0t4/zed-zeta-server" || exit

# * new .venv
rm -rf .venv # wipe out venv to be safe
uv venv
source .venv/bin/activate.fish

# * vllm deps:
uv pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
uv pip install -r ~/repos/github/vllm-project/vllm-latest/requirements/build.txt

export MAX_JOBS=(nproc)
uv pip install -e "$HOME/repos/github/vllm-project/vllm-latest" --no-build-isolation

# * zed-zeta-server deps:
uv pip install -r requirements.txt

# * this was in notes for vllm itself, its build.. not sure I need this here?
# uv pip install transformers # no direct torch deps


# FYI! validated all of this works! one caveat (can load in ipython ok...)
#   but, there is a pathing issue if try to run `python consolidate/server.py` on vllm module not found...
#   but it loads fine in ipython repl (w/ and w/o iron.nvim)
