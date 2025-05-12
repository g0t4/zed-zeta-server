from fastapi import FastAPI, Request, Response
import asyncio
import httpx
from timing import Timer
from rich import print as rich_print, print_json

print = rich_print

OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://ollama:8000/v1/completions"
# OPENAI_COMPAT_V1_COMPLETIONS_URL = "http://localhost:1234/v1/completions"
app = FastAPI()

# based on:
# https://github.com/zed-industries/zed/blob/35fbe1ef3d/crates/collab/src/llm.rs#L439
#    RIGHT BEFORE THEY REMOVED THIS IN PR 23997
#
# also reverse engineered from dataset repo on huggingface... (see other files in this try-zeta dir)
#    https://huggingface.co/datasets/zed-industries/zeta
#    btw I don't see outline in  SFT/DPO ipynb (notebooks) in hf dataset repo!? are those old?
#      or did they just add outline and it happens to not cause trouble? and be helpful without any SFT?
#      or is there a newer model :) and train dataset :)
#
# *** to test this
#   export ZED_PREDICT_EDITS_URL=http://localhost:1234/predict_edits # or w/e route I use below
#   zed  # zed will use the URL for request (already confirmed this works)

#
# TODO try run quantized and/or ngram spec dec too:
#  vllm serve zed-industries/zeta --served-model-name zeta --enable-prefix-caching --enable-chunked-prefill --quantization="fp8" --speculative-model [ngram] --ngram-prompt-lookup-max 4 --ngram-prompt-lookup-min 2 --num-speculative-tokens 8
#  FYI this is mentioned in model card... IIAC this is how they're serving the actual zeta model (or at the time)
#    https://huggingface.co/zed-industries/zeta
#    do some speed tests w/ and w/o spec dec


@app.post("/predict_edits")
async def predict_edits(request: Request, response: Response):
    
    zed_request = await request.json()
    print("\n\n[bold red]## Zed request body:")
    print_json(data=zed_request)
    outline = zed_request.get('outline', '')
    input_events = zed_request.get('input_events', '')
    input_excerpt = zed_request.get('input_excerpt', '')
    #
    # FYI other params passed by zed:
    #
    # speculated_output: Some(values.speculated_output), # IIAC not needed b/c:
    # - IIAC speculated_output is for ngram (speculative decoding)
    #   - IIAC intended to map to OpenAI's predition.content?
    #     - https://platform.openai.com/docs/api-reference/chat/create#chat-create-prediction
    # - BUT, AFAICT vllm builds ngrams on prompt (no parameter to use as basis instead)
    #   - https://docs.vllm.ai/en/latest/features/spec_decode.html#speculating-by-matching-n-grams-in-the-prompt
    # - FYI it is very much possible that they are NOT using vllm on the backend
    #   - they show vllm on huggingface, so I assume they are... 
    #     - they even show how to use speculative decoding
    #   - or they have a custom ngram implementation with vllm 
    #
    # diagnostic_groups # TODO capture example of this
    #
    # can_collect_data
    #
    # TODO is this the right outline prefix/header for prompt?
    outline_prefix = f"### Outline for current file:\n{outline}\n" if outline else ""
    if outline:
        print("\n\n[yellow][WARN]: outline not yet supported")

    # TODO is there a header before Instruction?
    prompt_template = """### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\n{}\n\n### User Excerpt:\n\n{}\n\n### Response:\n"""
    prompt = prompt_template.format(input_events, input_excerpt)

    print("\n\n[bold red]## Prompt:")
    print(prompt)

    # TODO pass outline
    # TODO any thing else passed in current version?
    # zeta client request body builder:
    #   https://github.com/zed-industries/zed/blob/17ecf94f6f/crates/zeta/src/zeta.rs#L449-L466
    async def generate_prediction():
        timeout_seconds = 30
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            with Timer("inner"):
                request_body = {

                    # "model": "zeta", # LMStudio defaults to zeta 
                    # * for VLLM clear model or set matching value with `--served-model-name zeta`

                    "prompt": prompt,
                    "max_tokens": 2048,  # PR 23997 used 2048 # TODO what max? # can I get it to just stop on EOT?
                    # TODO should I set EOT to be the end of the template token(s)?
                    #
                    "temperature": 0.0,  # 23997 PR used 0 # TODO what value to use?
                    # "top_p": 0.9, # TODO value?
                    # "n": 1, # s/b default
                    # "stop": null # TODO what value?
                    # "rewrite_speculation": True # TODO?
                }
                print("\n\n[bold red]## request body => zeta /v1/completions:")
                print_json(data=request_body)  # FYI print_json doesn't hard wrap lines, uses " instead of ', obvi compat w/ jq

                response = await client.post(OPENAI_COMPAT_V1_COMPLETIONS_URL, json=request_body)
                response_body = response.json()
                print("\n\n[bold red]## zeta /v1/completions => response body:")
                print_json(data=response_body)
                response.raise_for_status()
                choice_text = response_body.get("choices", [{}])[0].get("text", "")
                response_id = response_body["id"].replace("cmpl-", "")  # drop cmpl- prefix, must be valid UUID for zed to parse (not sure what it needs it for, maybe logging?)

                return {
                    "output_excerpt": choice_text,

                    # FYI PR/23997 does not set request_id so lets skip for now, was only in zeta codebase
                    "request_id": response_id,  # required, UUID
                    # here is where crates/zeta uses reuest_id:
                    #   https://github.com/zed-industries/zed/blob/17ecf94f6f/crates/zeta/src/zeta.rs#L845
                    #   not sure this is then used anywhere
                }

    with Timer("async-outer"):
        task = asyncio.create_task(generate_prediction())

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

    # to simulate and test predictions client disconnect:
    #   run ./server/test-server.sh
    #   Ctrl-C half a second later (let vllm see the request first)
    #   then I get this:
    #     INFO 05-06 16:27:59 [async_llm.py:252] Added request cmpl-f1c129d7868647b488c7ef3e5bb1b73b-0.
    #     INFO 05-06 16:27:59 [async_llm.py:411] Aborted request cmpl-f1c129d7868647b488c7ef3e5bb1b73b-0.
    #     INFO 05-06 16:27:59 [async_llm.py:318] Request cmpl-f1c129d7868647b488c7ef3e5bb1b73b-0 aborted.
    # Or, better yet run this with neovim by using the predictions plugin
    #   hit i to go into insert mode
    #   hit escape to bail 
    #   you will see aborted in vllm logs! (and in predict_edits logs)






# I prefer fastapi dev ... but uvicorn can do hot reload too
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app", host="127.0.0.1", port=9000, reload=True)
