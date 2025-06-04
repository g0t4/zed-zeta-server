from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
from rich import print as rich_print, print_json

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions"  # vllm

app = FastAPI()

verbose_logging = False

def parse_delta(line: str) -> tuple[str, bool, str | None]:
    # print("[yellow][bold]chunk", line)
    if not line or not line.startswith("data: "):
        return "", False, None

    event_data = line[6:]
    try:
        event_data = event_data.strip()
        event = json.loads(event_data)
        choices = event.get("choices", [])
        first_choice = choices[0]
        stop_reason = first_choice.get("finish_reason")
        delta = first_choice.get("text", "")
        if stop_reason == "stop":
            return delta, True, "stop"
        return delta, False, None
    except json.JSONDecodeError:
        print("[red][bold]FAILURE parsing event_data: ", event_data)
        return "", False, None

    # vllm examples:
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"`\n","logprobs":null,"finish_reason":null,"stop_reason":null}],"usage":null}
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"","logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":null}

class StreamEditsRequest(BaseModel):
    input_events: str | None
    input_excerpt: str | None
    include_finish_reason: bool = False

@app.post("/stream_edits")
async def stream_edits(prediction_request: StreamEditsRequest, client_request: Request):

    if verbose_logging:
        print("\n\n[bold red]## Zed request body:")
        print(prediction_request)

    prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
    prompt = prompt_template.format(prediction_request.input_events, prediction_request.input_excerpt)

    if verbose_logging:
        print("\n\n[bold red]## Prompt:")
        print(prompt)

    async def request_vllm_completion_streaming():
        timeout_seconds = 30
        all_deltas = []
        # TODO! setup sync client to compare
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            request_body = {
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.0,
                "stream": True,
            }
            if verbose_logging:
                print("\n\n[bold red]## request body => zeta /v1/completions:")
                print_json(data=request_body)  # FYI print_json doesn't hard wrap lines, uses " instead of ', obvi compat w/ jq

                print("\n\n[bold red]## response zeta => deltas:")

            async with client.stream(method="POST", url=OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body) as vllm_response:
                async for chunk_of_events in vllm_response.aiter_lines():

                    # FYI vllm is showing Aborted request w/o needing to check myself for request.is_disconnected()
                    # do something special on disconnect:
                    if await client_request.is_disconnected():
                        print("Client of /stream_edits Disconnected")
                        break

                    delta, is_done, finish_reason = parse_delta(chunk_of_events)
                    if delta != "":
                        print(f"[blue]deltas: {delta}")

                    yield delta

                    if verbose_logging:
                        all_deltas.append(delta)

                    if is_done:
                        if prediction_request.include_finish_reason:
                            yield json.dumps({"finish_reason": finish_reason})
                        if verbose_logging:
                            print(f"done: {finish_reason}")
                        break

        if verbose_logging:
            print("\n\n[bold green]## All deltas:")
            print("".join(all_deltas))

    return StreamingResponse(request_vllm_completion_streaming(), media_type="text/event-stream")
