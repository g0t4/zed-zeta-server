if [ -d ".venv" ]; then
    echo "venv already exists, remove it to recreate it"
else
    uv venv
fi

source .venv/bin/activate

uv pip install -r requirements.txt


