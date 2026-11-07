"""Quickstart for Raya-Opt.

Requires:
  - Ollama running locally with `llama3` pulled  (optional)
  - OPENAI_API_KEY or ANTHROPIC_API_KEY in env    (optional)
"""
import os
import logging
from raya_opt import RayaOpt, Config, ProviderConfig

logging.basicConfig(level=logging.INFO)

providers = [
    ProviderConfig(
        name="llama3_local",
        type="ollama",
        model="llama3",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
    ),
]

if os.environ.get("OPENAI_API_KEY"):
    providers.append(
        ProviderConfig(
            name="gpt4mini",
            type="openai",
            model="gpt-4o-mini",
            api_key=os.environ["OPENAI_API_KEY"],
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.00060,
        )
    )

if os.environ.get("ANTHROPIC_API_KEY"):
    providers.append(
        ProviderConfig(
            name="claude_haiku",
            type="anthropic",
            model="claude-haiku-4-5-20251001",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.005,
        )
    )

config = Config(
    providers=providers,
    fallback_chain=[p.name for p in providers],
    budget_usd=0.50,
    max_depth=5,
    loop_window=6,
    loop_threshold=3,
)

client = RayaOpt(config)

resp = client.complete([
    {"role": "user", "content": "Sebutkan 3 manfaat sayur bayam dalam 1 kalimat."}
])

print("provider :", resp.provider)
print("model    :", resp.model)
print("retries  :", resp.retries)
print("chain    :", resp.fallback_chain)
print("tokens   :", resp.usage.input_tokens, "+", resp.usage.output_tokens)
print("cost     : $", round(resp.usage.cost_usd, 6))
print("blocked  :", resp.blocked)
print("reply    :", resp.content)
