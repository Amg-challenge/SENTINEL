"""Threshold frontier: what the bank buys for what it spends.

Proposed addition · branch `modello`.

The report already shows four thresholds in a table. This script sweeps the pause
threshold over a grid and draws the trade-off curve: fraud money protected against
cost to serve. It answers the question a jury actually asks - *why 0.50 and not
0.40 or 0.60?* - by showing that the threshold is a point chosen on a frontier,
not a magic number.

Same books as scripts/simula_portafoglio.py and notebooks/calibrazione.ipynb, so
the numbers reconcile with results/simulation_report.md.

Usage (from the backend/ folder):
    python scripts/frontiera_soglia.py            # full run
    python scripts/frontiera_soglia.py --rapido   # fewer books, for a quick check

Writes:
    results/threshold_frontier.csv
    results/figures/threshold_frontier.png
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sentinel import economics, model, profiles  # noqa: E402

PREVALENZA_REALE = 0.01
PREVALENZA_SIM = 0.30
N_CLIENTI = 300
SEEDS_LOAD = (100, 101, 102)
SEEDS_DET = (0, 1, 2, 3, 4, 5)
PREZZO_ANNO = 30.0            # CHF per protected client per year (v6)
GRIGLIA = np.round(np.arange(0.20, 0.92, 0.02), 2)
CSV = "results/threshold_frontier.csv"
FIGURA = "results/figures/threshold_frontier.png"


def _libri(seeds: tuple[int, ...], prob_frode: float) -> pd.DataFrame:
    pezzi = []
    for s in seeds:
        port = profiles.genera_portafoglio(n_clienti=N_CLIENTI, prob_frode=prob_frode, seed=s)
        port["cliente"] = port["cliente"] + s * 10_000
        pezzi.append(economics.punteggia_portafoglio(port))
    return pd.concat(pezzi, ignore_index=True)


def calcola(seeds_load=SEEDS_LOAD, seeds_det=SEEDS_DET) -> pd.DataFrame:
    print("  · building the books (the slow part)", flush=True)
    reale = _libri(seeds_load, PREVALENZA_REALE)
    sim = _libri(seeds_det, PREVALENZA_SIM)
    righe = []
    for soglia in GRIGLIA:
        carico = economics.stima_alert(reale, float(soglia), seed=0)
        det = economics.importo_protetto(sim, float(soglia))
        righe.append({
            "threshold": float(soglia),
            "alerts/client/year": carico["alert_per_cliente_anno"],
            "to the bank": carico["quota_banca"],
            "cost to serve CHF": carico["cost_to_serve"],
            "fraud episodes caught": det["episodi_intercettati"],
            "fraud money protected": det["importo_protetto"],
        })
        print(f"    soglia {soglia:.2f}  CHF {carico['cost_to_serve']:.2f}  "
              f"protetto {100*det['importo_protetto']:.0f}%", flush=True)
    df = pd.DataFrame(righe)
    os.makedirs("results", exist_ok=True)
    df.to_csv(CSV, index=False)
    return df


def figura(df: pd.DataFrame) -> None:
    """Trade-off curve: money protected against cost to serve, threshold along the line."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, ink2, accent, grid = "#0b0b0b", "#52514e", "#2a78d6", "#e4e3df"
    d = df.sort_values("threshold", ascending=False)   # parametric curve: follow the threshold
    x = d["cost to serve CHF"].to_numpy(float)
    y = 100 * d["fraud money protected"].to_numpy(float)

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": ink2, "xtick.color": ink2, "ytick.color": ink2})
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot(x, y, color=accent, lw=2, zorder=2, solid_capstyle="round")
    ax.scatter(x, y, s=16, color=accent, alpha=0.5, zorder=3)

    # the operating point chosen by the group
    scelto = df.loc[(df["threshold"] - model.SOGLIA).abs().idxmin()]
    sx, sy = float(scelto["cost to serve CHF"]), 100 * float(scelto["fraud money protected"])
    ax.scatter([sx], [sy], s=130, color=accent, edgecolor="white", linewidth=2, zorder=5)
    ax.annotate(f"chosen: threshold {scelto['threshold']:.2f}\n"
                f"CHF {sx:.2f} · {sy:.0f}% of fraud money protected\n"
                f"{scelto['alerts/client/year']:.1f} alerts per client per year",
                xy=(sx, sy), xycoords="data", xytext=(0.30, 0.46), textcoords="axes fraction",
                color=ink, fontsize=9, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=ink2, lw=1))

    # a few thresholds along the curve, to read the direction
    for t in (0.30, 0.40, 0.60, 0.70, 0.80):
        r = df.loc[(df["threshold"] - t).abs().idxmin()]
        ax.annotate(f"{r['threshold']:.2f}",
                    (float(r["cost to serve CHF"]), 100 * float(r["fraud money protected"])),
                    xytext=(0, 9), textcoords="offset points", ha="center",
                    color=ink2, fontsize=8.5)

    ax.set_xlabel("Cost to serve per protected client per year (CHF)")
    ax.set_ylabel("Fraud money protected (%)")
    ax.set_title(f"What the bank buys for what it spends "
                 f"(price: CHF {PREZZO_ANNO:.0f} per client per year)",
                 loc="left", color=ink, fontsize=11)
    # the flat tail: the punchline about diminishing returns
    basso = df.loc[(df["threshold"] - 0.30).abs().idxmin()]
    bx, by = float(basso["cost to serve CHF"]), 100 * float(basso["fraud money protected"])
    ax.annotate(f"past the knee the curve flattens: CHF {bx:.0f} per client,\n"
                f"almost three times the cost, buys only +{by - sy:.0f} points",
                xy=(bx, by), xycoords="data", xytext=(0.62, 0.17), textcoords="axes fraction",
                color=ink2, fontsize=9, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=ink2, lw=1))

    ax.grid(color=grid, lw=0.8)
    ax.set_axisbelow(True)
    ax.margins(x=0.10)
    ax.set_ylim(max(0.0, float(np.nanmin(y)) - 8), 103)
    fig.tight_layout()
    os.makedirs(os.path.dirname(FIGURA), exist_ok=True)
    fig.savefig(FIGURA, dpi=200)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true", help="fewer books, for a quick check")
    ap.add_argument("--figura-only", action="store_true",
                    help="redraw the figure from results/threshold_frontier.csv")
    a = ap.parse_args()
    if a.figura_only:
        figura(pd.read_csv(CSV))
        print(f"\nredrawn: {FIGURA}")
        return
    if a.rapido:
        df = calcola(seeds_load=(100,), seeds_det=(0, 1))
    else:
        df = calcola()
    figura(df)
    print(f"\nwritten: {CSV} and {FIGURA}")


if __name__ == "__main__":
    main()
