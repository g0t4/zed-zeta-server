from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
from rich import print as rich_print

from stream.common import parse_delta

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions"  # vllm

app = FastAPI()

class EditPrediction(BaseModel):
    input_excerpt: str
    input_events: str = ""

    def prompt(self):
        template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
        return template.format(self.input_events, self.input_excerpt)

    def request_body(self):
        return {
            "prompt": self.prompt(),
            "max_tokens": 2048,
            "temperature": 0.0,
            "stream": True,
        }

@app.post("/stream_edits")
async def stream_edits(ide_request: Request, prediction: EditPrediction):

    async def get_vllm_completion_streaming():

        async with httpx.AsyncClient(timeout=30) as client:
            request_body = prediction.request_body()

            async with client.stream(method="POST", url=OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body) as vllm_response:
                async for line in vllm_response.aiter_lines():

                    delta, is_done, finish_reason = parse_delta(line)
                    if delta:
                        print(f"[blue]delta: {delta}")
                        yield delta

                    if is_done:
                        print(f"done: {finish_reason}")
                        break

    return StreamingResponse(get_vllm_completion_streaming(), media_type="text/event-stream")
