"""Aggregate results → CSV, summary, charts, markdown report."""
import csv
import json
import statistics
from pathlib import Path
from typing import Dict, List

from .scenarios import ResultRow


def write_csv(rows: List[ResultRow], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].to_dict().keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r.to_dict())


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def aggregate(rows: List[ResultRow]) -> Dict:
    """Per-scenario, per-run aggregates."""
    out: Dict = {}
    runs: Dict[tuple, List[ResultRow]] = {}
    for r in rows:
        runs.setdefault((r.scenario, r.run), []).append(r)

    for (scn, run), rs in runs.items():
        succeeded = [r for r in rs if not r.blocked]
        blocked = [r for r in rs if r.blocked]
        lat = [r.latency_ms for r in succeeded]
        cost = [r.cost_usd for r in succeeded]

        out.setdefault(scn, {})[run] = {
            "total_requests": len(rs),
            "succeeded": len(succeeded),
            "blocked": len(blocked),
            "block_reasons": list({r.block_reason for r in blocked if r.block_reason}),
            "total_cost_usd": round(sum(cost), 6),
            "avg_cost_per_req": round(sum(cost) / max(1, len(succeeded)), 6),
            "latency_ms": {
                "p50": round(_percentile(lat, 50), 2),
                "p95": round(_percentile(lat, 95), 2),
                "p99": round(_percentile(lat, 99), 2),
                "max": round(max(lat) if lat else 0, 2),
            },
            "providers_used": dict(_count_providers(succeeded)),
        }
    return out


def _count_providers(rows: List[ResultRow]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r.provider] = counts.get(r.provider, 0) + 1
    return counts


def write_summary_json(summary: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def render_markdown_report(summary: Dict, path: Path) -> None:
    lines = ["# Raya-Opt PoC Report", ""]

    # Scenario 1
    if "cost_saving" in summary:
        cs = summary["cost_saving"]
        b = cs.get("baseline", {})
        o = cs.get("optimized", {})
        bcost = b.get("total_cost_usd", 0)
        ocost = o.get("total_cost_usd", 0)
        saving_pct = (1 - ocost / bcost) * 100 if bcost > 0 else 0
        lines += [
            "## Scenario 1 — Cost Saving",
            "",
            f"| metric            | baseline | optimized |",
            f"|-------------------|----------|-----------|",
            f"| requests          | {b.get('total_requests',0)} | {o.get('total_requests',0)} |",
            f"| total cost (USD)  | ${bcost:.4f} | ${ocost:.4f} |",
            f"| avg cost/req      | ${b.get('avg_cost_per_req',0):.6f} | ${o.get('avg_cost_per_req',0):.6f} |",
            f"| latency p95 (ms)  | {b.get('latency_ms',{}).get('p95',0)} | {o.get('latency_ms',{}).get('p95',0)} |",
            "",
            f"**Saving: {saving_pct:.1f}%** "
            f"(target ≥50% → {'PASS ✓' if saving_pct >= 50 else 'FAIL ✗'})",
            "",
            f"Providers used (optimized): {o.get('providers_used', {})}",
            "",
        ]

    # Scenario 2
    if "loop_protection" in summary:
        lp = summary["loop_protection"]
        no = lp.get("no_breaker", {})
        wi = lp.get("with_breaker", {})
        nocost = no.get("total_cost_usd", 0)
        wicost = wi.get("total_cost_usd", 0)
        loop_saving = (1 - wicost / nocost) * 100 if nocost > 0 else 0
        lines += [
            "## Scenario 2 — Loop Protection",
            "",
            f"| metric            | no breaker | with breaker |",
            f"|-------------------|------------|--------------|",
            f"| requests sent     | {no.get('total_requests',0)} | {wi.get('total_requests',0)} |",
            f"| succeeded         | {no.get('succeeded',0)} | {wi.get('succeeded',0)} |",
            f"| blocked           | {no.get('blocked',0)} | {wi.get('blocked',0)} |",
            f"| total cost (USD)  | ${nocost:.4f} | ${wicost:.4f} |",
            "",
            f"**Saving: {loop_saving:.1f}%** "
            f"(target ≥85% → {'PASS ✓' if loop_saving >= 85 else 'FAIL ✗'})",
            "",
            f"Block reasons: {wi.get('block_reasons', [])}",
            "",
        ]

    # Scenario 3
    if "uptime" in summary:
        ut = summary["uptime"].get("fallback_test", {})
        total = ut.get("total_requests", 0)
        ok = ut.get("succeeded", 0)
        rate = (ok / total) * 100 if total > 0 else 0
        lines += [
            "## Scenario 3 — Uptime / Fallback",
            "",
            f"| metric            | value |",
            f"|-------------------|-------|",
            f"| requests          | {total} |",
            f"| served            | {ok} |",
            f"| success rate      | {rate:.1f}% |",
            f"| providers used    | {ut.get('providers_used', {})} |",
            "",
            f"**Target 100% success → {'PASS ✓' if rate >= 100 else 'FAIL ✗'}**",
            "",
        ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def render_charts(rows: List[ResultRow], outdir: Path) -> bool:
    """Render bar/hist charts if matplotlib is installed. Returns False if skipped."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    outdir.mkdir(parents=True, exist_ok=True)
    summary = aggregate(rows)

    # cost comparison
    if "cost_saving" in summary:
        cs = summary["cost_saving"]
        runs = list(cs.keys())
        costs = [cs[r]["total_cost_usd"] for r in runs]
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(runs, costs, color=["#cc4444", "#44aa44"])
        ax.set_title("Scenario 1 — Total Cost (USD)")
        ax.set_ylabel("USD")
        for b, c in zip(bars, costs):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                    f"${c:.4f}", ha="center", va="bottom")
        fig.tight_layout()
        fig.savefig(outdir / "chart_cost.png", dpi=120)
        plt.close(fig)

    # latency distribution (optimized run only)
    opt_rows = [r for r in rows if r.scenario == "cost_saving" and r.run == "optimized" and not r.blocked]
    if opt_rows:
        lat = [r.latency_ms for r in opt_rows]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(lat, bins=20, color="#4488cc", edgecolor="white")
        ax.set_title("Scenario 1 — Latency Distribution (optimized)")
        ax.set_xlabel("ms")
        ax.set_ylabel("count")
        fig.tight_layout()
        fig.savefig(outdir / "chart_latency.png", dpi=120)
        plt.close(fig)

    return True
