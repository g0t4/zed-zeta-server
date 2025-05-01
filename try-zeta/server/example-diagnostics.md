

## Zed request body:
```json
{
  "outline": "```lua/ask-openai/prediction/tests/calc/calc.lua\nfunction add\n```\n",
  "input_events": "User edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,9 +1,12 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n+function M.subtract(a, b)\n+    return a - b\n+end\n \n \n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -8,6 +8,15 @@\n     return a - b\n end\n \n+function M.multiply(a, b)\n+    return a * b\n+end\n \n+function M.divide(a, b)\n+    if b == 0 then\n+        error(\"Division by zero\")\n+    end\n+    return a / b\n+end\n \n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,22 +1,10 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n-function M.subtract(a, b)\n-    return a - b\n-end\n \n-function M.multiply(a, b)\n-    return a * b\n-end\n \n-function M.divide(a, b)\n-    if b == 0 then\n-        error(\"Division by zero\")\n-    end\n-    return a / b\n-end\n \n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,5 +7,4 @@\n \n \n \n-\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,6 +1,6 @@\n local M = {}\n \n-function M.add(a, b)\n+function add(a, b)\n     return a + b\n end\n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,6 +1,6 @@\n local M = {}\n \n-function add(a, b)\n+function add(a, b, c)\n     return a + b\n end\n \n\n```",
  "input_excerpt": "```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction add(a, b, c)\n    return a + b\nend\n\n<|user_cursor_is_here|>\n\n\nreturn M\n\n<|editable_region_end|>\n```",
  "speculated_output": "<|editable_region_start|>\nlocal M = {}\n\nfunction add(a, b, c)\n    return a + b\nend\n\n<|user_cursor_is_here|>\n\n\nreturn M\n\n<|editable_region_end|>",
  "can_collect_data": false,
  "diagnostic_groups": [
    [
      "lua-language-server",
      {
        "entries": [
          {
            "range": {
              "start": 33,
              "end": 34
            },
            "diagnostic": {
              "source": "Lua Diagnostics.",
              "code": "unused-local",
              "severity": 4,
              "message": "Unused local `c`.",
              "group_id": 25,
              "is_primary": true,
              "is_disk_based": false,
              "is_unnecessary": true,
              "data": null
            }
          }
        ],
        "primary_ix": 0
      }
    ]
  ]
}
```

## Prompt:
### Instruction:
You are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting
the appropriate edits within the excerpt, taking into account the cursor location.

### User Edits:

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -1,9 +1,12 @@
 local M = {}

 function M.add(a, b)
     return a + b
 end

+function M.subtract(a, b)
+    return a - b
+end




```

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -8,6 +8,15 @@
     return a - b
 end

+function M.multiply(a, b)
+    return a * b
+end

+function M.divide(a, b)
+    if b == 0 then
+        error("Division by zero")
+    end
+    return a / b
+end

 return M

```

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -1,22 +1,10 @@
 local M = {}

 function M.add(a, b)
     return a + b
 end

-function M.subtract(a, b)
-    return a - b
-end

-function M.multiply(a, b)
-    return a * b
-end

-function M.divide(a, b)
-    if b == 0 then
-        error("Division by zero")
-    end
-    return a / b
-end

 return M

```

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -7,4 +7,5 @@



+
 return M

```

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -7,5 +7,4 @@



-
 return M

```

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -1,6 +1,6 @@
 local M = {}

-function M.add(a, b)
+function add(a, b)
     return a + b
 end


```

User edited "lua/ask-openai/prediction/tests/calc/calc.lua":
```diff
@@ -1,6 +1,6 @@
 local M = {}

-function add(a, b)
+function add(a, b, c)
     return a + b
 end


```

### User Excerpt:

```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua
<|start_of_file|>
<|editable_region_start|>
local M = {}

function add(a, b, c)
    return a + b
end

<|user_cursor_is_here|>


return M

<|editable_region_end|>
```

### Response:



## request body => vllm:
```json
{
  "prompt": "### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,9 +1,12 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n+function M.subtract(a, b)\n+    return a - b\n+end\n \n \n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -8,6 +8,15 @@\n     return a - b\n end\n \n+function M.multiply(a, b)\n+    return a * b\n+end\n \n+function M.divide(a, b)\n+    if b == 0 then\n+        error(\"Division by zero\")\n+    end\n+    return a / b\n+end\n \n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,22 +1,10 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n-function M.subtract(a, b)\n-    return a - b\n-end\n \n-function M.multiply(a, b)\n-    return a * b\n-end\n \n-function M.divide(a, b)\n-    if b == 0 then\n-        error(\"Division by zero\")\n-    end\n-    return a / b\n-end\n \n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,5 +7,4 @@\n \n \n \n-\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,6 +1,6 @@\n local M = {}\n \n-function M.add(a, b)\n+function add(a, b)\n     return a + b\n end\n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,6 +1,6 @@\n local M = {}\n \n-function add(a, b)\n+function add(a, b, c)\n     return a + b\n end\n \n\n```\n\n### User Excerpt:\n\n```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction add(a, b, c)\n    return a + b\nend\n\n<|user_cursor_is_here|>\n\n\nreturn M\n\n<|editable_region_end|>\n```\n\n### Response:\n",
  "max_tokens": 2048,
  "temperature": 0.0
}
```


## vllm => response body:
```json
{
  "id": "cmpl-3f2bddb289cd4faba96149c4bd672b04",
  "object": "text_completion",
  "created": 1745573796,
  "model": "zed-industries/zeta",
  "choices": [
    {
      "index": 0,
      "text": "<|editable_region_start|>\nlocal M = {}\n\nfunction add(a, b, c)\n    return a + b\nend\n\nfunction subtract(a, b)\n    return a - b\nend\n\nfunction multiply(a, b)\n    return a * b\nend\n\nfunction divide(a, b)\n    if b == 0 then\n        error(\"Division by zero\")\n    end\n    return a / b\nend\n\nreturn M\n\n<|editable_region_end|>\n```\n",
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null,
      "prompt_logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 635,
    "total_tokens": 735,
    "completion_tokens": 100,
    "prompt_tokens_details": null
  }
}
```


## Zed response body:
```json
{
    "output_excerpt": "<|editable_region_start|>\nlocal M = {}\n\nfunction add(a, b, c)\n    return a + b\nend\n\nfunction subtract(a, b)\n    return a - b\nend\n\nfunction multiply(a, b)\n    return a * b\nend\n\nfunction divide(a, b)\n    if b == 0 then\n error(\"Division by zero\")\n    end\n    return a / b\nend\n\nreturn M\n\n<|editable_region_end|>\n```\n",
    "request_id": "3f2bddb289cd4faba96149c4bd672b04"
}
```

