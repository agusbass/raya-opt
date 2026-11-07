# Raya-Opt PoC Runner

End-to-end PoC validating 3 claims:

| # | Scenario          | Pass criterion              |
|---|-------------------|-----------------------------|
| 1 | Cost saving       | optimized chain saves ≥50%  |
| 2 | Loop protection   | breaker saves ≥85%          |
| 3 | Uptime / fallback | 100% requests served        |

## Quickstart

### A. Mock mode (no API keys, no $)

```bash
cd raya-opt
pip install -e .
python -m examples.poc.poc_runner --mock --out ./poc_out
```

Runs the full pipeline against simulated providers. Use this to:
- verify the runner works on your server
- demo the scenarios without spending
- iterate on the report format

### B. Real mode

Set env vars for whichever providers you have:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export OLLAMA_URL=http://localhost:11434     # optional, for local Llama
```

Optional charts:
```bash
pip install matplotlib
```

Run:
```bash
python -m examples.poc.poc_runner --out ./poc_out
```

## Flags

| flag                | default     | meaning                                 |
|---------------------|-------------|-----------------------------------------|
| `--mock`            | off         | use fake providers (no network)         |
| `--scenario {1,2,3,all}` | `all`  | run a single scenario                   |
| `-n N`              | all (60)    | limit prompt count                      |
| `--out DIR`         | `./poc_out` | output directory                        |

Cost-saving runs each prompt **twice** (baseline + optimized) → 60 prompts × 2 = 120 requests.
Use `-n 20` for a quick smoke run (~40 requests).

## Output

```
poc_out/
├── results_raw.csv     # per-request data
├── summary.json        # aggregates per scenario/run
├── report.md           # 1-page pass/fail
├── chart_cost.png      # (if matplotlib)
└── chart_latency.png   # (if matplotlib)
```

`results_raw.csv` columns:
`scenario, run, prompt_id, category, provider, model, retries, fallback_chain, input_tokens, output_tokens, cost_usd, latency_ms, blocked, block_reason, response_excerpt`

## Expected budget for real run (60 prompts)

| Run                       | Approx cost |
|---------------------------|-------------|
| Baseline (gpt-4o)         | $0.50-1.00  |
| Optimized (mostly Llama)  | $0.05-0.20  |
| Loop scenario             | ~$0.05      |
| Uptime scenario           | ~$0.02      |
| **Total per PoC run**     | **~$1-2**   |

## Reading the report

`report.md` includes a PASS/FAIL verdict per scenario based on the targets in the
table above. If a scenario fails, check:

- **Scenario 1 fails**: optimized chain is hitting paid providers too often. Likely
  Ollama isn't running, so every request falls through. Start `ollama serve` and
  `ollama pull llama3`.
- **Scenario 2 fails**: `loop_threshold` may be too high. Lower it in `poc_runner.py`.
- **Scenario 3 fails**: the bad provider URL is responding (firewall not blocking
  port 9). Pick a different unreachable address.
