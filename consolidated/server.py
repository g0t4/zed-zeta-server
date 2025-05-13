import uuid
import asyncio
from vllm import AsyncLLMEngine, SamplingParams, AsyncEngineArgs
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from rich import print as rich_print

print = rich_print

app = FastAPI()

verbose_logging = False

prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""

class ConsolidatedEditsRequest(BaseModel):
    input_events: str | None
    input_excerpt: str | None
    include_finish_reason: bool = False

    def build_prompt(self):
        prompt = prompt_template.format(self.input_events, self.input_excerpt)
        return prompt

# FYI! why have consolidated_edits:
# TODO! does it matter?

# hf_model = "meta-llama/Llama-3.2-1B-Instruct"  # a bit faster for testing
hf_model = "zed-industries/zeta"
engine = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(model=hf_model))

#%%
verbose_logging = True 

fake_request = {
    "input_events": "User edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -8,4 +8,5 @@\n \n \n \n+\n return M\n\n```",
    "input_excerpt": "```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>\n```",
    "include_finish_reason": True
}
prediction_request = ConsolidatedEditsRequest.model_validate(fake_request)

# FYI this is working, but delta contains entire output and not just most recent token?
async def request_and_print():
    text_thus_far = None

    sampling_params = SamplingParams(max_tokens=2048, temperature=0.0)
    request_id = str(uuid.uuid4())
    generator = engine.generate(prediction_request.build_prompt(), sampling_params, request_id=request_id)
    # docs: https://docs.vllm.ai/en/stable/api/engine/async_llm_engine.html#vllm.AsyncLLMEngine.generate
    #   has good example of disconnect detection and aborting the request
    async for output in generator:
        print("[bold][white]output", output)
        choice_thus_far = output.outputs[0]
        text_thus_far = choice_thus_far.text
        # print(full_text)

        if choice_thus_far.finish_reason:
            if verbose_logging:
                print(f"done: {choice_thus_far.finish_reason}")
            break

    if verbose_logging:
        print("\n\n[bold green]## All deltas:")
        print(text_thus_far)

# FYI IGNORE pyright complaining about no top level await, ipython supports top level awaits (in cells)
await request_and_print()   # type: ignore

#%%

@app.post("/consolidated_edits")
async def consolidated_edits(prediction_request: ConsolidatedEditsRequest, client_request: Request)

    if verbose_logging:
        print("\n\n[bold red]## Zed request body:")
        print(prediction_request)

    prompt = prediction_request.build_prompt()

    if verbose_logging:
        print("\n\n[bold red]## Prompt:")
        print(prompt)

    async def request_vllm_completion_streaming():
        all_deltas = []

        # TODO timeout?
        sampling_params = SamplingParams(max_tokens=2048, temperature=0.0)
        request_id = str(uuid.uuid4())
        generator = engine.generate(prompt, sampling_params, request_id=request_id)
        async for choice in generator:
            choice = choice.outputs[0]
            delta = choice.text
            yield delta

            # TODO! TEST DISCONNECT
            if await client_request.is_disconnected():
                print("Client of /stream_edits Disconnected")
                await engine.abort(request_id)
                break

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
