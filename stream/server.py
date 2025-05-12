from fastapi import FastAPI, Request, Response
import asyncio
import httpx
import json
from rich import print as rich_print, print_json

print = rich_print

# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:7100/v1/completions"
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://localhost:1234/v1/completions"
OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:11434/v1/completions"

app = FastAPI()

def parse_ss_events(data: str) -> tuple[list[dict], bool]:
    events = []

    for line in data.splitlines():
        if line.startswith("data: "):
            event_data = line[6:]
            try:
                event_data = event_data.strip()
                if event_data == "[DONE]":
                    return events, True
                event = json.loads(event_data)
                events.append(event)
            except json.JSONDecodeError:
                pass

    return events, False

@app.post("/stream_edits")
async def stream_edits(request: Request, response: Response):
    
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
                "model": "qwen2.5-coder:1.5b",

                "prompt": prompt,
                "max_tokens": 2048,

                "temperature": 0.0,

                "stream": True,
            }
            print("\n\n[bold red]## request body => zeta /v1/completions:")
            print_json(data=request_body)  # FYI print_json doesn't hard wrap lines, uses " instead of ', obvi compat w/ jq
            async with client.stream(method="POST", url=OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body) as response:
                # FYI for completions:
                #   aiter_lines() => SSEs split into data: line and empty line (separate chunks)
                #   aiter_text() => SSEs are entire chunk including 2 newlines:  with data: {}\n\n
                # async for chunk in response.aiter_lines():
                async for chunk_of_events in response.aiter_text():
                    print("[yellow][bold]chunk", chunk_of_events)
                    if chunk_of_events.strip() == "":
                        continue
                    events, is_done = parse_ss_events(chunk_of_events)
                    print(events)
                    if is_done:
                        print("done")
                        break



            # # response = await client.post(OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body)
            # response_body = response.json()
            # print("\n\n[bold red]## zeta /v1/completions => response body:")
            # print_json(data=response_body)
            # response.raise_for_status()
            # choice_text = response_body.get("choices", [{}])[0].get("text", "")
            # response_id = response_body["id"].replace("cmpl-", "")

            return {
                "output_excerpt": "TODO", # choice_text
                "request_id": "TODO", # response_id,  
            }

    task = asyncio.create_task(request_vllm_completion_streaming())

    while not task.done():
        # if/when the client disconnects, we cancel the upstream request
        # if client does not disconnect, the request eventually completes (task.done() == True) (below then returns the response to curl)
        if await request.is_disconnected():
            print("Client disconnected")
            task.cancel()
            break
    try:
        zed_prediction_response_body = await task
        print("\n\n[bold green]## Zed response body:")
        print_json(data=zed_prediction_response_body)
        return zed_prediction_response_body
    except asyncio.CancelledError:
        return "Request cancelled"
    except Exception as e:
        return {"error": str(e)}

