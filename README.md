## Running server

```bash
# create venv
python -m venv venv
uv venv

# activate venv
source venv/bin/activate

# install deps
pip install -r requirements.txt
uv pip install -r requirements.txt

# run server
ipython3 server/server.py

```


## Predictions Backend Architecture


```mermaid
---
config:
  theme: mc
  look: neo
---
sequenceDiagram
    participant ZedIDE as Zed IDE
    participant API as Predict API<br> /predict_edits
    participant Zeta as vllm serve zeta<br> /v1/comletions
    ZedIDE->>API: JSON (input_excerpt, events...)
    API->>Zeta: Prompt 
    Zeta-->>API: Completion Response
    API-->>ZedIDE: JSON (output_excerpt)
```
