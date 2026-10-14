"""CLI entry point for the developer-tools stream example."""

import json
import sys

from src.devtools_stream import StreamRequest, stream_tool_events


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip() or "Summarize the latest build in one sentence."
    request = StreamRequest(prompt=prompt, release="local")
    for event in stream_tool_events(request):
        print(json.dumps(event.model_dump(), ensure_ascii=True))


if __name__ == "__main__":
    main()
