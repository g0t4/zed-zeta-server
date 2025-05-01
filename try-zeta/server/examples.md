## first captures on start zed

These appear to be a mistake? ... nonetheless they serve as a good example of some edge cases to watch for, i.e. untitled where s/b filename.
These ran before I made any changes to anything so these were not triggered by me, literally show on zed start.

```json
{
    "outline": "```untitled\n```\n",
    "input_events": "",
    "input_excerpt": "```untitled\n<|start_of_file|>\n<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>\n```",
    "speculated_output": "<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>",
    "can_collect_data": false,
    "diagnostic_groups": null   #
}
{
    "outline": "```untitled\n```\n",
    "input_events": "",
    "input_excerpt": "```untitled\n<|start_of_file|>\n<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>\n```",
    "speculated_output": "<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>",
    "can_collect_data": false,
    "diagnostic_groups": null
}
```

## request after I made a change in calc.lua

```json
{
    'outline': '```lua/ask-openai/prediction/tests/calc/calc.lua\nfunction M.add\n```\n',
    'input_events': 'User edited "lua/ask-openai/prediction/tests/calc/calc.lua":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited "lua/ask-openai/prediction/tests/calc/calc.lua":\n```diff\n@@ -8,4 +8,5 @@\n \n \n \n+\n return M\n\n```',
    'input_excerpt': '```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>\n```',
    'speculated_output': '<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>',
    'can_collect_data': False,
    'diagnostic_groups': []
}
```

## vllm calc.lua response example

```json

// vllm prompt log:
'### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\nUser edited "lua/ask-openai/prediction/tests/calc/calc.lua":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited "lua/ask-openai/prediction/tests/calc/calc.lua":\n```diff\n@@ -8,4 +8,5 @@\n \n \n \n+\n return M\n\n```\n\n### User Excerpt:\n\n```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>\n```\n\n### Response:\n'

// vllm response:
{
    'id': 'cmpl-1e2dd241cbba4f2e8b8ccfa26af7636b',
    'object': 'text_completion',
    'created': 1745566545,
    'model': 'zed-industries/zeta',
    'choices': [
        {
            'index': 0,
            'text': '<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n\nfunction M.subtract(a, b)\n    return a - b\nend\n\nfunction M.multiply(a, b)\n    return a * b\nend\n\nfunction M.divide(a, b)\n    if b == 0 then\n        error("Division by zero")\n    end\n    return a / b\nend\n\nreturn M\n\n<|editable_region_end|>\n```\n',
            'logprobs': None,
            'finish_reason': 'stop',
            'stop_reason': None,
            'prompt_logprobs': None
        }
    ],
    'usage': {'prompt_tokens': 209, 'total_tokens': 311, 'completion_tokens': 102, 'prompt_tokens_details': None}
}
```
