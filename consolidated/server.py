from vllm import AsyncLLMEngine, SamplingParams, AsyncEngineArgs
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from rich import print as rich_print

print = rich_print

app = FastAPI()

verbose_logging = False

class StreamingPredictionRequest(BaseModel):
    input_events: str | None
    input_excerpt: str | None
    include_finish_reason: bool = False

# FYI! why have consolidated_edits:
# TODO! does it matter?

# hf_model = "meta-llama/Llama-3.2-1B-Instruct"  # a bit faster for testing
hf_model = "zed-industries/zeta"
engine = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(model=hf_model))

#%% 

@app.post("/consolidated_edits")
async def consolidated_edits(prediction_request: StreamingPredictionRequest):  # client_request: Request

    if verbose_logging:
        print("\n\n[bold red]## Zed request body:")
        print(prediction_request)

    prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
    prompt = prompt_template.format(prediction_request.input_events, prediction_request.input_excerpt)

    if verbose_logging:
        print("\n\n[bold red]## Prompt:")
        print(prompt)

    async def request_vllm_completion_streaming():
        all_deltas = []

        # TODO timeout?
        # TODO verify if client disconnects that vllm terminates generation (USE client_request: Request above)
        sampling_params = SamplingParams(max_tokens=2048, temperature=0.0)
        async for choice in engine.generate(prompt, sampling_params, request_id="unique_id"):
            choice = choice.outputs[0]
            delta = choice.text
            yield delta
            # TODO!? disconnect check?
            # if await client_request.is_disconnected():
            #     # add client_request: Request as paramter to stream_edits way above
            #     print("Client of /stream_edits Disconnected")
            #     break

            if verbose_logging:
                all_deltas.append(delta)

            if choice.finish_reason:
                if prediction_request.include_finish_reason:
                    yield json.dumps({"finish_reason": choice.finish_reason})
                if verbose_logging:
                    print(f"done: {choice.finish_reason}")
                break

        if verbose_logging:
            print("\n\n[bold green]## All deltas:")
            print("".join(all_deltas))

    return StreamingResponse(request_vllm_completion_streaming(), media_type="text/event-stream")
