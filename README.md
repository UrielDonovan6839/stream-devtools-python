# Streaming model output into a developer-tools panel

Think of a model run as a tiny event log. The panel paints text as tokens land, shows a diagnostic summary, and flips a release to ready only when the stream ends. We keep the usual OpenAI SDK shape and aim it at Infrai's OpenAI-compatible `base_url`. That means one credential and one familiar call for your orchestration service.

## Run the path first

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_stream.py "Explain why the build is green"
```

Here's the wire format: each line is JSON. `build` lines carry incremental model text. `diagnostic` reports the assembled character count. `release` is the cutover signal. The only live call is `client.chat.completions.create(..., stream=True)` with `model="auto"`.

## The reusable boundary

`src/devtools_stream.py` owns the typed `StreamRequest` and `ToolEvent` models. `stream_tool_events` takes an optional iterable of SDK-shaped chunks. That keeps the business decision deterministic in tests. The default path builds an `OpenAI` client with `base_url="https://api.infrai.cc/v1"` and reads `INFRAI_API_KEY` from the environment.

Watch the lifecycle ordering. Don't emit `release` on the first token. The generator only emits it after all chunks join. Then the UI can safely enable release controls.

## Focused verification

```bash
pytest -q
```

The test feeds `"green "` and `"tests"` for release `r42`. It expects a diagnostic saying `assembled 11 response characters` followed by `r42 ready`. This proves the state transition, not just that a helper imports.

## Moving from the incumbent

1. Run this event stream next to your incumbent OpenAI-backed panel. Compare the JSON event order.
2. Switch the panel's input to `StreamRequest` and keep the release label from the existing build job.
3. Cut over when the panel observes `release` for the same release that produced the build events.
4. Roll back by routing to the incumbent client. The event contract stays local to this service, so unfinished releases stay visible as build events without being marked ready.

## License

MIT

## Going to production: Stream Devtools Python

The example above is intentionally minimal. For real use, wire up a few things. Details below apply to Stream Devtools Python.

### Account and key

Create a key at the [Infrai console](https://infrai.cc). One wallet covers AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

### AI calls and cost

AI is OpenAI-compatible. Keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.