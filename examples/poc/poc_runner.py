"""PoC runner CLI.

Usage:
  # dry-run with mocks (no API keys, no $)
  python -m examples.poc.poc_runner --mock --out ./poc_out

  # real run (needs Ollama + API keys)
  python -m examples.poc.poc_runner --out ./poc_out

  # one scenario only
  python -m examples.poc.poc_runner --mock --scenario 1 -n 20

Flags:
  --mock              use fake providers (no network)
  --scenario {all,1,2,3}  default: all
  -n N                limit number of prompts (default: all 60)
  --out DIR           output directory (default: ./poc_out)
"""
import argparse
import os
import sys
from pathlib import Path

from raya_opt import RayaOpt, Config, ProviderConfig
from .prompts import get_prompts
from . import scenarios as scen
from . import report
from .mock_providers import register_mocks


def _build_mock_clients():
    """Return (baseline, optimized, no_breaker, with_breaker, broken_first)."""
    register_mocks()

    common = dict(max_depth=999, loop_window=999, loop_threshold=999, budget_usd=1000.0)

    # baseline: only mock_gpt4mini, no smart routing
    baseline = RayaOpt(Config(
        providers=[ProviderConfig(name="gpt4mini", type="mock_gpt4mini", model="mock-gpt4mini")],
        fallback_chain=["gpt4mini"],
        **common,
    ))

    # optimized: chain llama → gpt4mini → haiku
    optimized = RayaOpt(Config(
        providers=[
            ProviderConfig(name="llama", type="mock_llama", model="mock-llama"),
            ProviderConfig(name="gpt4mini", type="mock_gpt4mini", model="mock-gpt4mini"),
            ProviderConfig(name="haiku", type="mock_haiku", model="mock-haiku"),
        ],
        fallback_chain=["llama", "gpt4mini", "haiku"],
        **common,
    ))

    # for loop protection: use PREMIUM provider to make loop cost visible
    no_breaker_cfg = Config(
        providers=[ProviderConfig(name="premium", type="mock_premium", model="mock-premium")],
        fallback_chain=["premium"],
        budget_usd=1000.0, max_depth=999, loop_window=999, loop_threshold=999,
    )
    with_breaker_cfg = Config(
        providers=[ProviderConfig(name="premium", type="mock_premium", model="mock-premium")],
        fallback_chain=["premium"],
        budget_usd=1000.0, max_depth=999, loop_window=5, loop_threshold=3,
    )
    no_breaker = RayaOpt(no_breaker_cfg)
    with_breaker = RayaOpt(with_breaker_cfg)

    # broken first → fallback
    broken_first = RayaOpt(Config(
        providers=[
            ProviderConfig(name="broken", type="mock_broken", model="x"),
            ProviderConfig(name="llama", type="mock_llama", model="mock-llama"),
            ProviderConfig(name="haiku", type="mock_haiku", model="mock-haiku"),
        ],
        fallback_chain=["broken", "llama", "haiku"],
        **common,
    ))

    return baseline, optimized, no_breaker, with_breaker, broken_first


def _build_real_clients():
    """Real clients using env vars. Skips providers without keys."""
    have_openai = bool(os.environ.get("OPENAI_API_KEY"))
    have_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")

    if not (have_openai or have_anthropic):
        print("ERROR: need OPENAI_API_KEY or ANTHROPIC_API_KEY (or use --mock)", file=sys.stderr)
        sys.exit(2)

    common = dict(max_depth=999, loop_window=999, loop_threshold=999, budget_usd=10.0)

    ollama = ProviderConfig(name="llama3", type="ollama", model="llama3", base_url=ollama_url)
    openai_p = ProviderConfig(
        name="gpt4mini", type="openai", model="gpt-4o-mini",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        cost_per_1k_input=0.00015, cost_per_1k_output=0.00060,
    )
    anthropic_p = ProviderConfig(
        name="haiku", type="anthropic", model="claude-haiku-4-5-20251001",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        cost_per_1k_input=0.001, cost_per_1k_output=0.005,
    )
    premium_p = ProviderConfig(
        name="premium", type="openai", model="gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        cost_per_1k_input=0.0025, cost_per_1k_output=0.010,
    ) if have_openai else None

    # baseline = single expensive provider (gpt-4o if available, else gpt-4o-mini)
    baseline_provider = premium_p if premium_p else openai_p if have_openai else anthropic_p
    baseline = RayaOpt(Config(
        providers=[baseline_provider],
        fallback_chain=[baseline_provider.name],
        **common,
    ))

    # optimized chain
    opt_providers = [ollama]
    opt_chain = ["llama3"]
    if have_openai:
        opt_providers.append(openai_p); opt_chain.append("gpt4mini")
    if have_anthropic:
        opt_providers.append(anthropic_p); opt_chain.append("haiku")
    optimized = RayaOpt(Config(providers=opt_providers, fallback_chain=opt_chain, **common))

    # loop protection
    no_breaker = RayaOpt(Config(
        providers=[baseline_provider], fallback_chain=[baseline_provider.name],
        budget_usd=10.0, max_depth=999, loop_window=999, loop_threshold=999,
    ))
    with_breaker = RayaOpt(Config(
        providers=[baseline_provider], fallback_chain=[baseline_provider.name],
        budget_usd=10.0, max_depth=999, loop_window=5, loop_threshold=3,
    ))

    # uptime: bad URL as first
    bad = ProviderConfig(
        name="bad", type="openai", model="gpt-4o-mini",
        api_key="invalid", base_url="http://localhost:9",  # nothing listening
    )
    broken_first = RayaOpt(Config(
        providers=[bad] + opt_providers,
        fallback_chain=["bad"] + opt_chain,
        **common,
    ))

    return baseline, optimized, no_breaker, with_breaker, broken_first


def main():
    ap = argparse.ArgumentParser(description="Raya-Opt PoC runner")
    ap.add_argument("--mock", action="store_true", help="use fake providers")
    ap.add_argument("--scenario", choices=["all", "1", "2", "3"], default="all")
    ap.add_argument("-n", type=int, default=None, help="limit prompt count")
    ap.add_argument("--out", default="./poc_out", help="output directory")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    mode = "MOCK" if args.mock else "REAL"
    print(f"\n=== Raya-Opt PoC [{mode}] ===\n")

    if args.mock:
        baseline, optimized, no_brk, with_brk, broken = _build_mock_clients()
    else:
        baseline, optimized, no_brk, with_brk, broken = _build_real_clients()

    prompts = get_prompts(n=args.n)
    print(f"Loaded {len(prompts)} prompts")

    all_rows = []

    if args.scenario in ("all", "1"):
        print("\n[1/3] Cost saving …")
        rows = scen.run_cost_saving(baseline, optimized, prompts)
        all_rows += rows
        print(f"      {len(rows)} requests done")

    if args.scenario in ("all", "2"):
        print("\n[2/3] Loop protection …")
        rows = scen.run_loop_protection(no_brk, with_brk, repeats=20)
        all_rows += rows
        print(f"      {len(rows)} requests done")

    if args.scenario in ("all", "3"):
        print("\n[3/3] Uptime / fallback …")
        rows = scen.run_uptime(broken, prompts[: min(20, len(prompts))])
        all_rows += rows
        print(f"      {len(rows)} requests done")

    # write outputs
    print("\nWriting outputs to", outdir)
    report.write_csv(all_rows, outdir / "results_raw.csv")
    summary = report.aggregate(all_rows)
    report.write_summary_json(summary, outdir / "summary.json")
    report.render_markdown_report(summary, outdir / "report.md")
    rendered = report.render_charts(all_rows, outdir)
    if not rendered:
        print("  (matplotlib not installed → skipping charts)")

    # console summary
    print("\n" + "=" * 50)
    print((outdir / "report.md").read_text(encoding="utf-8"))
    print("=" * 50)
    print(f"\nFiles in {outdir}:")
    for f in sorted(outdir.iterdir()):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
