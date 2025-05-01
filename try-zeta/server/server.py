import asyncio
import httpx
from flask import Flask, request, jsonify
from timing import Timer
from rich import print as rich_print, print_json

print = rich_print

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
# FYI to test this
#   export ZED_PREDICT_EDITS_URL=http://build21:PORT/predict_edits # or w/e route I use below
#   zed  # zed will use the URL for request (already confirmed this works)

#
# TODO try run quantized and/or ngram spec dec too:
#  vllm serve zed-industries/zeta --served-model-name zeta --enable-prefix-caching --enable-chunked-prefill --quantization="fp8" --speculative-model [ngram] --ngram-prompt-lookup-max 4 --ngram-prompt-lookup-min 2 --num-speculative-tokens 8
#  FYI this is mentioned in model card... IIAC this is how they're serving the actual zeta model (or at the time)
#    https://huggingface.co/zed-industries/zeta
#    do some speed tests w/ and w/o spec dec
#
#  TODO review below and touch up to work with the released HF zeta model

# FYI from zeta cask
# const CURSOR_MARKER: &'static str = "<|user_cursor_is_here|>";
# const START_OF_FILE_MARKER: &'static str = "<|start_of_file|>";
# const EDITABLE_REGION_START_MARKER: &'static str = "<|editable_region_start|>";
# const EDITABLE_REGION_END_MARKER: &'static str = "<|editable_region_end|>";
# const BUFFER_CHANGE_GROUPING_INTERVAL: Duration = Duration::from_secs(1);
# const ZED_PREDICT_DATA_COLLECTION_CHOICE: &str = "zed_predict_data_collection_choice";

app = Flask(__name__)

# PREDICTION_API_URL = os.getenv("PREDICTION_API_URL")
VLLM_COMPLETIONS_V1_URL = "http://localhost:8000/v1/completions"


@app.route('/predict_edits', methods=['POST'])
def predict_edits():
    zed_request = request.get_json()
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
        timeout_sec = 30
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            with Timer("inner"):
                vllm_request_body = {
                    # "model": "zeta", -- do not need with vllm backend
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
                print("\n\n[bold red]## request body => vllm:")
                print_json(data=vllm_request_body)  # FYI print_json doesn't hard wrap lines, uses " instead of ', obvi compat w/ jq

                response = await client.post(VLLM_COMPLETIONS_V1_URL, json=vllm_request_body)
                vllm_response_body = response.json()
                print("\n\n[bold red]## vllm => response body:")
                print_json(data=vllm_response_body)
                response.raise_for_status()
                choice_text = vllm_response_body.get("choices", [{}])[0].get("text", "")
                response_id = vllm_response_body["id"].replace("cmpl-", "")  # drop cmpl- prefix, must be valid UUID for zed to parse (not sure what it needs it for, maybe logging?)

                return {
                    "output_excerpt": choice_text,

                    # FYI PR/23997 does not set request_id so lets skip for now, was only in zeta codebase
                    "request_id": response_id,  # required, UUID
                    # here is where crates/zeta uses reuest_id:
                    #   https://github.com/zed-industries/zed/blob/17ecf94f6f/crates/zeta/src/zeta.rs#L845
                    #   not sure this is then used anywhere
                }

    try:
        with Timer("async-outer"):
            zed_prediction_response_body = asyncio.run(generate_prediction())
            print("\n\n[bold green]## Zed response body:")
            print_json(data=zed_prediction_response_body)
            return jsonify(zed_prediction_response_body)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=9000, host="0.0.0.0")
