#!/usr/bin/env bash

http localhost:9000/predict_edits <<'EOF'
{
    "outline": "```lua/ask-openai/prediction/tests/calc/calc.lua\nfunction M.add\n```\n",
    "input_events": "User edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -8,4 +8,5 @@\n \n \n \n+\n return M\n\n```",
    "input_excerpt": "```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>\n```",
    "speculated_output": "<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>",
    "can_collect_data": false,
    "diagnostic_groups": []
}
EOF


# FYI should return smth like:
# {
#     "output_excerpt": "<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n\nfunction M.subtract(a, b)\n    return a - b\nend\n\nfunction M.multiply(a, b)\n    return a * b\nend\n\nfunction M.divide(a, b)\n    if b == 0 then\n        error(\"Division by zero\")\n    end\n    return a / b\nend\n\nreturn M\n\n<|editable_region_end|>\n```\n",
#     "request_id": "7914a580d7184a039ec30e23d74c8c37"
# }

