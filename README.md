# Raya-Opt

Cost-aware LLM gateway with a built-in circuit breaker.

Two modules wired together as a single pipeline (`0 → M1 → M5 → 0`):

- **M1 — Circuit Breaker**: loop detection, hard budget cap, recursive-depth cap
- **M5 — LLM Gateway**: provider abstraction (OpenAI / Anthropic / Ollama) + fallback chain

MVP only. M2 (constrained decoding), M3 (vector DB), M4 (inference engine) are out of scope for `0.1.x`.

## Install

```bash
git clone <your-private-repo> raya-opt
cd raya-opt
pip install -e ".[dev]"
```

## Quickstart

```python
from raya_opt import RayaOpt, Config, ProviderConfig

config = Config(
    providers=[
        ProviderConfig(name="llama3", type="ollama", model="llama3"),
        ProviderConfig(
            name="gpt4mini", type="openai", model="gpt-4o-mini",
            api_key="sk-...",
            cost_per_1k_input=0.00015, cost_per_1k_output=0.00060,
        ),
    ],
    fallback_chain=["llama3", "gpt4mini"],
    budget_usd=0.50,
    max_depth=5,
    loop_window=6,
    loop_threshold=3,
)

client = RayaOpt(config)
resp = client.complete([{"role": "user", "content": "Halo"}])
print(resp.content, resp.provider, resp.usage.cost_usd)
```

## Session state (multi-call budget / loop tracking)

To enforce budget and loop limits across multiple `complete()` calls (e.g. inside
an agent loop), reuse a session:

```python
state = client.new_session()
for step in range(20):
    resp = client.complete(messages, state=state)
    if resp.blocked:
        print("stopped:", resp.block_reason)
        break
```

## Config reference

| Field            | Default | Meaning                                                 |
|------------------|---------|---------------------------------------------------------|
| `budget_usd`     | 1.0     | Hard cost ceiling per session. Block before exceeding.  |
| `max_depth`      | 5       | Max `complete()` calls per session.                     |
| `loop_window`    | 6       | Sliding window of recent call hashes.                   |
| `loop_threshold` | 3       | Same hash ≥ N times in window → `LoopDetected`.         |
| `request_timeout`| 60.0    | Per-provider HTTP timeout (seconds).                    |

## Provider types

| `type`      | Required          | Notes                                |
|-------------|-------------------|--------------------------------------|
| `openai`    | `api_key`         | OpenAI-compatible endpoint           |
| `anthropic` | `api_key`         | Anthropic Messages API               |
| `ollama`    | — (local)         | Defaults to `http://localhost:11434` |

Provider cost is computed from the returned token counts and the
`cost_per_1k_input` / `cost_per_1k_output` you configure.

## Run tests

```bash
pytest -v
```

Tests use fake providers — no network or API keys needed.

## Response shape

```python
Response(
    content="...",
    provider="gpt4mini",
    model="gpt-4o-mini",
    usage=Usage(input_tokens=42, output_tokens=18, cost_usd=0.0027),
    fallback_chain=["llama3", "gpt4mini"],   # ordered attempts
    retries=1,
    blocked=False,
    block_reason=None,
)
```

## Block reasons

When a request is blocked, `resp.blocked == True` and `resp.block_reason` carries
one of:

- `LoopDetected: ...`
- `BudgetExceeded: ...`
- `MaxDepthExceeded: ...`
- `AllProvidersFailed: ...`

## License

MIT.
