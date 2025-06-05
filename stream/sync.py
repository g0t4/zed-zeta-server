from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
from rich import print as rich_print

from stream.common import parse_delta

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions"  # vllm

app = FastAPI()

class StreamEditsRequest(BaseModel):
    input_events: str | None
    input_excerpt: str | None
    include_finish_reason: bool = False

@app.post("/stream_edits")
async def stream_edits(client_request: Request, prediction_request: StreamEditsRequest):

    prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
    prompt = prompt_template.format(prediction_request.input_events, prediction_request.input_excerpt)

    async def request_vllm_completion_streaming():

        with httpx.Client(timeout=30) as client:
            request_body = {
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.0,
                "stream": True,
            }

            with client.stream(method="POST", url=OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body) as vllm_response:
                for line in vllm_response.iter_lines():

                    # FYI vllm is showing Aborted request w/o needing to check myself for request.is_disconnected()
                    if await client_request.is_disconnected():
                        print("[red]Client of /stream_edits Disconnected")
                        break

                    delta, is_done, finish_reason = parse_delta(line)
                    if delta != "":
                        print(f"[blue]delta: {delta}")

                    yield delta

                    if is_done:
                        if prediction_request.include_finish_reason:
                            yield json.dumps({"finish_reason": finish_reason})
                        print(f"done: {finish_reason}")
                        break

    return StreamingResponse(request_vllm_completion_streaming(), media_type="text/event-stream")
