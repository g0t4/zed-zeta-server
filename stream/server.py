from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
from rich import print as rich_print, print_json

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions" # vllm
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://localhost:1234/v1/completions"
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:11434/v1/completions"

app = FastAPI()

verbose_logging = False

def parse_delta(line: str) -> tuple[str, bool, str|None]:
    # print("[yellow][bold]chunk", line)
    # simplifications:
    # - completions endpoint only returns "data:" field
    # - with value that is either a JSON object or "[DONE]"
    #   - finish_reason comes before [DONE] so I can ignore that event
    # - I only need to know if its done, or the delta text
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
        # TODO STOP?
        return "", False, None

    # ollama examples:
    #  {"id":"cmpl-142","object":"text_completion","created":1747075759,"choices":[{"text":"```","index":0,"finish_reason":null}],"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama"}
    #  {"id":"cmpl-142","object":"text_completion","created":1747075759,"choices":[{"text":"","index":0,"finish_reason":"stop"}],"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama"}
    #
    # vllm examples:
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"`\n","logprobs":null,"finish_reason":null,"stop_reason":null}],"usage":null}
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"","logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":null}

class StreamEditsRequest(BaseModel):
    input_events: str|None
    input_excerpt: str|None
    include_finish_reason: bool = False 

# FYI! why have stream_edits:
# OpenAI SSE total chars: 23,911
# same response with /stream_edits chars: 349
# 99% reduction in size
# timing 200ms vs 400ms of user time to process, overall latency unaffected b/c of token latency
# nonetheless, no need to parse json client side, or server side if inference integrated w/ new format

@app.post("/stream_edits")
async def stream_edits(prediction_request: StreamEditsRequest): # client_request: Request
    
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
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            request_body = {

                # FYI just need simple model to test with, and use ollama for reduced startup time in testing too
                # TODO later swap back into vllm backend for real deal
                #  ollama server
                # "model": "qwen2.5-coder:1.5b",

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
                # FYI for completions:
                #   aiter_lines() => SSEs split into data: line and empty line (separate chunks)
                #   aiter_text() => SSEs are entire chunk including 2 newlines:  with data: {}\n\n
                # async for chunk in response.aiter_lines():
                async for chunk_of_events in vllm_response.aiter_lines():

                    # FYI vllm is showing Aborted request w/o needing to check myself for request.is_disconnected()
                    # don't need this as , but could check if I needed to do something special on disconnect:
                    # if await client_request.is_disconnected():
                    #     # add client_request: Request as paramter to stream_edits way above
                    #     print("Client of /stream_edits Disconnected")
                    #     break
                
                    delta, is_done, finish_reason = parse_delta(chunk_of_events)
                    # print(f"[blue]deltas: {deltas}")
                    
                    yield delta

                    if verbose_logging:
                        all_deltas.append(delta)

                    if is_done:
                        if prediction_request.include_finish_reason:
                            yield json.dumps({"finish_reason": finish_reason })
                        if verbose_logging:
                            print(f"done: {finish_reason}")
                        break

        if verbose_logging:
            print("\n\n[bold green]## All deltas:")
            print("".join(all_deltas))

    return StreamingResponse(request_vllm_completion_streaming(), media_type="text/event-stream")
