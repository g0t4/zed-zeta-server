#!/usr/bin/env bash

# SETUP TO TEST BACKEND disconnects (i.e. see message in its logs)

# http ollama:11434/v1/completions <<'EOF'
http ollama:8000/v1/completions <<'EOF'
{
  "prompt": "### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,10 +1,10 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n-\n+ \n \n \n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,10 +1,9 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n- \n \n \n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,9 +1,12 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n+function M.subtract(a, b)\n+    return a - b\n+end\n \n \n \n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -8,6 +8,15 @@\n     return a - b\n end\n \n+function M.multiply(a, b)\n+    return a * b\n+end\n \n+function M.divide(a, b)\n+    if b == 0 then\n+        error(\"Division by zero\")\n+    end\n+    return a / b\n+end\n \n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -1,22 +1,10 @@\n local M = {}\n \n function M.add(a, b)\n     return a + b\n end\n \n-function M.subtract(a, b)\n-    return a - b\n-end\n \n-function M.multiply(a, b)\n-    return a * b\n-end\n \n-function M.divide(a, b)\n-    if b == 0 then\n-        error(\"Division by zero\")\n-    end\n-    return a / b\n-end\n \n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited \"lua/ask-openai/prediction/tests/calc/calc.lua\":\n```diff\n@@ -7,5 +7,4 @@\n \n \n \n-\n return M\n\n```\n\n### User Excerpt:\n\n```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n\n\n<|user_cursor_is_here|>\n\nreturn M\n\n<|editable_region_end|>\n```\n\n### Response:\n",
  "max_tokens": 2048,
  "temperature": 0.0
}
EOF

#   "model": "qwen2.5-coder:1.5b",

