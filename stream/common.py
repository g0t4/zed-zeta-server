import json

def parse_delta(line: str) -> tuple[str, bool, str | None]:
    if not line or not line.startswith("data: "):
        return "", False, None

    event_json = line[6:]
    try:
        event_json = event_json.strip()
        event = json.loads(event_json)
        choices = event.get("choices", [])
        first_choice = choices[0]
        stop_reason = first_choice.get("finish_reason")
        delta = first_choice.get("text", "")
        if stop_reason == "stop":
            return delta, True, "stop"
        return delta, False, None
    except json.JSONDecodeError:
        print("[red][bold]FAILURE parsing event_data: ", event_json)
        return "", False, None

    # vllm examples:
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"`\n","logprobs":null,"finish_reason":null,"stop_reason":null}],"usage":null}
    #  {"id":"cmpl-fd048c7865e94616a2ed2b6564c1232b","object":"text_completion","created":1747078116,"model":"zed-industries/zeta","choices":[{"index":0,"text":"","logprobs":null,"finish_reason":"stop","stop_reason":null}],"usage":null}

