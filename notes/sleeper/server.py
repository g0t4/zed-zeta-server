from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import asyncio
import httpx
from rich import print as rich_print

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions"
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://localhost:1234/v1/completions"
app = FastAPI()

@app.get("/test_sleeper_proxy")
async def test_proxy(client_request: Request):
    # THIS IS A SIMULATED PROXY (like /predict_edits), curl connects here, then this connects to upstream
    async def make_request():
        async with httpx.AsyncClient() as client:
            return await client.get("http://localhost:9000/test_sleeper", timeout=None)  # disable timeout for demo

    upstream_request_task = asyncio.create_task(make_request())
    while not upstream_request_task.done():
        # if/when the client disconnects, we cancel the upstream request
        # if client does not disconnect, the request eventually completes (task.done() == True) (below then returns the response to curl)
        if await client_request.is_disconnected():
            print("Client of /test_sleeper_proxy disconnected")
            upstream_request_task.cancel()
            break
    try:
        response = await upstream_request_task
        return Response(response.text, media_type="text/plain")
    except asyncio.CancelledError:
        print("Request to /test_sleeper cancelled")

@app.get("/test_sleeper")
async def test_stream(request: Request):
    # THIS IS A SIMULATED UPSTREAM, takes place of vllm
    # all of this logic has to reside in vllm for this to work end to end (gotta test it next)
    async def event_stream():
        for i in range(10):
            print("Checking if client is disconnected")
            # doesn't matter here b/c this would be intenal logic to vllm... but you can check request.is_disconnected() but it wasn't necessary to get this to terminate when proxy disconnects
            # print(await request.is_disconnected())
            # if await request.is_disconnected():
            #     print("Client disconnected")
            #     break
            print("Sending event", i)
            yield f"data: {i}\n\n"
            await asyncio.sleep(0.500)
        print("Stream finished")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
