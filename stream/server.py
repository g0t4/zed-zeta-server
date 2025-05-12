from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx
import json
from rich import print as rich_print, print_json

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions" # vllm
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://localhost:1234/v1/completions"
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:11434/v1/completions"

app = FastAPI()

def parse_deltas_from_chunk(chunk_of_events: str) -> tuple[str, bool, str|None]:
    print("[yellow][bold]chunk", chunk_of_events)
    # simplifications:
    # - completions endpoint only returns "data:" field
    # - with value that is either a JSON object or "[DONE]"
    # - I only need to know if its done, or the delta text
    if chunk_of_events.strip() == "":
        return "", False, None

    deltas = ""

    for line in chunk_of_events.splitlines():
        if line.startswith("data: "):
            event_data = line[6:]
            try:
                event_data = event_data.strip()
                if event_data == "[DONE]":
                    # FYI should never get here b/c finish_reason should be found on the previous event
                    return deltas, True, "[DONE]"
                event = json.loads(event_data)
                choices = event.get("choices", [])
                first_choice = choices[0]
                stop_reason = first_choice.get("finish_reason")
                if stop_reason == "stop":
                    return deltas, True, "stop"
                deltas += first_choice.get("text", "")
            except json.JSONDecodeError:
                pass
    # ollama examples:
    #  {"id":"cmpl-142","object":"text_completion","created":1747075759,"choices":[{"text":"```","index":0,"finish_reason":null}],"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama"}
    #  {"id":"cmpl-142","object":"text_completion","created":1747075759,"choices":[{"text":"","index":0,"finish_reason":"stop"}],"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama"}
    #
    # vllm examples:
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"`\n","logprobs":null,"finish_reason":null,"stop_reason":null}],"usage":null}
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"","logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":null}

    return deltas, False, None

@app.post("/stream_edits")
async def stream_edits(request: Request):
    
    zed_request = await request.json()
    print("\n\n[bold red]## Zed request body:")
    print_json(data=zed_request)
    input_events = zed_request.get('input_events', '')
    input_excerpt = zed_request.get('input_excerpt', '')

    prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
    prompt = prompt_template.format(input_events, input_excerpt)

    print("\n\n[bold red]## Prompt:")
    print(prompt)

    async def request_vllm_completion_streaming():
        timeout_seconds = 30
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
            print("\n\n[bold red]## request body => zeta /v1/completions:")
            print_json(data=request_body)  # FYI print_json doesn't hard wrap lines, uses " instead of ', obvi compat w/ jq

            print("\n\n[bold red]## response zeta => deltas:") 
            async with client.stream(method="POST", url=OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body) as response:
                # FYI for completions:
                #   aiter_lines() => SSEs split into data: line and empty line (separate chunks)
                #   aiter_text() => SSEs are entire chunk including 2 newlines:  with data: {}\n\n
                # async for chunk in response.aiter_lines():
                async for chunk_of_events in response.aiter_text():
                    deltas, is_done, finish_reason = parse_deltas_from_chunk(chunk_of_events)
                    print(f"[blue]deltas: {deltas}")
                    
                    if is_done:
                        print(f"done: {finish_reason}")
                        break

                    yield deltas

            # TODO print final, full response for debugging?

    return StreamingResponse(request_vllm_completion_streaming(), media_type="text/event-stream")

    # FYI vllm is showing Aborted request w/o needing to check myself for request.is_disconnected()
    #     # if/when the client disconnects, we cancel the upstream request
    #     # if client does not disconnect, the request eventually completes (task.done() == True) (below then returns the response to curl)
    #     if await request.is_disconnected():
    #         print("Client of /stream_edits disconnected")
    #         task.cancel()
    #         break
    # try:
    #     # zed_prediction_response_body = await task
    #     # print("\n\n[bold green]## Zed response body:")
    #     # print_json(data=zed_prediction_response_body)
    #     # return zed_prediction_response_body
    #     return await task
    # except asyncio.CancelledError:
    #     return "Request to Zeta cancelled"
    # except Exception as e:
    #     return {"error": str(e)}
    #
