import uuid
import asyncio
from vllm import AsyncLLMEngine, SamplingParams, AsyncEngineArgs
from vllm.outputs import RequestOutput
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from rich import print as rich_print

# TLDR => literally marking iron.nvim ONLY code sections
# so they don't run unless I explicitly select and send them to the REPL (ipython)
# or if I toggle this True (but that is not my intent)
# primary intent is I want uvicorn/fastapi-dev to not run this code, w/o needing to comment it out
IRON_NVIM_MARKER = False

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

if IRON_NVIM_MARKER:
    verbose_logging = True

    fake_request = {
        "input_events": "User edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -8,4 +8,5 @@\n \n \n \n+\n return M\n\n```",
        "input_excerpt": "```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>\n```",
        "include_finish_reason": True
    }
    prediction_request = ConsolidatedEditsRequest.model_validate(fake_request)

    # FYI this is working, but delta contains entire output and not just most recent token?
    async def request_and_print():
        text_thus_far = ""

        sampling_params = SamplingParams(max_tokens=2048, temperature=0.0)
        request_id = str(uuid.uuid4())
        generator = engine.generate(prediction_request.build_prompt(), sampling_params, request_id=request_id)
        output: RequestOutput
        async for output in generator:
            # print("[bold][white]output", output)
            choice_thus_far = output.outputs[0]
            # FYI compute delta b/c each iteration returns the entire response "thus far"
            text_delta = choice_thus_far.text.removeprefix(text_thus_far)
            text_thus_far = choice_thus_far.text
            print(text_delta, end="")

            if choice_thus_far.finish_reason:
                if verbose_logging:
                    print(f"done: {choice_thus_far.finish_reason}")
                break

        if verbose_logging:
            print("\n\n[bold green]## All deltas:")
            print(text_thus_far)

    # FYI IGNORE pyright complaining about no top level await, ipython supports top level awaits (in cells)
    #   FYI re-runnable in ipython repl, i.e. with iron.nvim! super useful to not reload model on every change that I wanna test!
    #   DO NOT use asyncio.run()... cannot run a second time (not easily anyways) w/ ipython repl
    await request_and_print()   # type: ignore

#%%

@app.post("/consolidated_edits")
async def consolidated_edits(prediction_request: ConsolidatedEditsRequest, client_request: Request):

    if verbose_logging:
        print("\n\n[bold red]## Zed request body:")
        print(prediction_request)

    prompt = prediction_request.build_prompt()

    if verbose_logging:
        print("\n\n[bold red]## Prompt:")
        print(prompt)

    async def request_vllm_completion_streaming():
        text_thus_far = ""

        # TODO timeout?
        sampling_params = SamplingParams(max_tokens=2048, temperature=0.0)
        request_id = str(uuid.uuid4())
        generator = engine.generate(prompt, sampling_params, request_id=request_id)

        # docs: https://docs.vllm.ai/en/stable/api/engine/async_llm_engine.html#vllm.AsyncLLMEngine.generate
        #   has good example of disconnect detection and aborting the request
        #   great article explaining both sync and async: https://medium.com/@crclq2018/explaining-the-source-code-behind-the-vllm-fast-inference-engine-91429f54d1f7
        #   btw, vllm uses FastAPI too, for /v1/completions: 
        #     https://github.com/vllm-project/vllm/blob/04a58c099/vllm/entrypoints/openai/api_server.py#L488-L506
        #     calls => https://github.com/vllm-project/vllm/blob/04a58c099/vllm/entrypoints/openai/serving_completion.py#L64
        #     stream =>
        #       https://github.com/vllm-project/vllm/blob/04a58c099/vllm/entrypoints/openai/serving_completion.py#L190-L199
        #       building response: https://github.com/vllm-project/vllm/blob/04a58c099/vllm/entrypoints/openai/serving_completion.py#L247-L277
        #     sync on cancel (IIUC abort) => https://github.com/vllm-project/vllm/blob/04a58c099/vllm/entrypoints/openai/serving_completion.py#L228
        #       TODO verify this is from engine.abort()?
        output: RequestOutput
        async for output in generator:
            # print("[bold][white]output", output)
            choice_thus_far = output.outputs[0]
            # FYI compute delta b/c each iteration returns the entire response "thus far"
            text_delta = choice_thus_far.text.removeprefix(text_thus_far)
            text_thus_far = choice_thus_far.text
            yield text_delta

            # TODO! TEST DISCONNECT
            if await client_request.is_disconnected():
                print("Client of /stream_edits Disconnected")
                await engine.abort(request_id)
                break

            if choice_thus_far.finish_reason:
                if prediction_request.include_finish_reason:
                    yield json.dumps({"finish_reason": choice_thus_far.finish_reason})
                if verbose_logging:
                    print(f"done: {choice_thus_far.finish_reason}")
                break

        if verbose_logging:
            print("\n\n[bold green]## All deltas:")
            print(text_thus_far)

    return StreamingResponse(request_vllm_completion_streaming(), media_type="text/event-stream")

#%% 

if IRON_NVIM_MARKER:
    # run web server in repl (iron.nvim) via uvicorn:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7200, reload=False)
