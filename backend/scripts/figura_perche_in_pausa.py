"""Appendix figure: every pause comes with its reason, as a waterfall.

Proposed addition · branch `modello`.

Replaces the side-by-side bars generated in notebooks/calibrazione.ipynb (section 7)
with a real waterfall: the score is built step by step from the starting point to the
total, so the reader does not have to add the contributions up in their head.

Two readings on the same picture:
  - bottom axis, log-odds: where the contributions actually add up;
  - top axis, score: what the number means. The threshold is a vertical line, so
    "to the right of the line" simply means "paused".

Same two cases, same baseline customer and the same model.spiega() used by the
counter, the contact's phone and the bank queue.

Usage (from the backend/ folder):
    python scripts/figura_perche_in_pausa.py

Writes:
    results/figures/why_paused.png
"""
from __future__ import annotations

import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from sentinel import model, profiles  # noqa: E402

INK, INK2, ACCENT, GRID = "#0b0b0b", "#52514e", "#2a78d6", "#e4e3df"
ACCENT_SCURO = "#14477f"   # the total bar: same family as ACCENT, one step darker
FIGURA = "results/figures/why_paused.png"
SEED_PERSONA = 7

CASI = [
    ("Fake police officer: CHF 40,000 cash at the counter",
     {"canale": "sportello", "importo": 40_000}),
    ("Fake grandchild: CHF 18,000 to a new foreign account",
     {"canale": "bonifico", "importo": 18_000, "beneficiario": "Foreign IBAN",
      "nuovo_beneficiario": True, "estero": True}),
]


def _logit(p: float) -> float:
    return float(np.log(p / (1 - p)))


def _pannello(ax, titolo: str, op: dict, base, soglia: float) -> None:
    motivi = model.spiega(op, base)
    score = model.punteggio(op, base)
    inizio = model.PESI["bias"]

    etichette = ["Starting point"] + [textwrap.fill(m[0][0].upper() + m[0][1:], 30) for m in motivi]
    passi = [inizio] + [m[1] for m in motivi]
    cum = np.cumsum(passi)
    totale = float(cum[-1])

    etichette.append("Score for this operation")
    y = np.arange(len(etichette))[::-1]          # first row at the top

    # the steps of the waterfall
    for i, (yi, passo) in enumerate(zip(y[:-1], passi)):
        sinistra = 0.0 if i == 0 else float(cum[i - 1])
        colore = INK2 if i == 0 else ACCENT
        ax.barh(yi, passo, left=sinistra, height=0.55, color=colore, zorder=3)
        ax.text(sinistra + passo + (0.08 if passo >= 0 else -0.08), yi, f"{passo:+.1f}",
                va="center", ha="left" if passo >= 0 else "right", color=INK, fontsize=9)
        if i < len(passi) - 1:                   # connector to the next step
            ax.plot([cum[i], cum[i]], [yi - 0.28, yi - 0.72], color=INK2, lw=0.8,
                    ls=(0, (2, 2)), zorder=2)

    # the total bar
    ax.barh(y[-1], totale, left=0.0, height=0.55,
            color=ACCENT_SCURO if totale >= _logit(soglia) else INK2, zorder=3)
    ax.text(totale + 0.10, y[-1], f"{score:.2f}", va="center", ha="left",
            color=INK, fontsize=10, fontweight="bold")
    ax.plot([cum[-2], cum[-2]], [y[-2] - 0.28, y[-1] + 0.28], color=INK2, lw=0.8,
            ls=(0, (2, 2)), zorder=2)

    ax.axvline(_logit(soglia), color=INK, lw=1.2, zorder=4)
    ax.set_yticks(y, etichette, fontsize=9)
    ax.set_ylim(-0.7, len(etichette) - 0.3)
    esito = "paused, the contact is asked" if score >= soglia else "no pause"
    ax.set_title(f"{titolo}\nscore {score:.2f}  ·  threshold {soglia:.2f}  →  {esito}",
                 loc="left", color=INK, fontsize=10)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def main() -> None:
    base = model.adatta_baseline(profiles.genera_storico("anziano", seed=SEED_PERSONA))
    soglia = model.SOGLIA
    righe = [1 + len(model.spiega(op, base)) + 1 for _, op in CASI]

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, axes = plt.subplots(len(CASI), 1, figsize=(8.6, 6.2), sharex=True,
                             gridspec_kw={"height_ratios": righe})
    for ax, (titolo, op) in zip(axes, CASI):
        _pannello(ax, titolo, op, base, soglia)

    axes[-1].set_xlim(-4.0, 3.6)
    axes[-1].set_xlabel("How the score builds up (log-odds: this is where the contributions add)")

    # second reading: the same axis, labelled as a score
    alto = axes[0].secondary_xaxis("top")
    ticks = [0.05, 0.2, 0.5, 0.8, 0.95]
    alto.set_xticks([_logit(t) for t in ticks], [f"{t:.2f}" for t in ticks], fontsize=9)
    alto.set_xlabel("Score", fontsize=9, color=INK2)
    alto.spines["top"].set_color(INK2)
    alto.tick_params(colors=INK2)

    for ax in axes:
        ax.annotate(f"threshold {soglia:.2f} \u2192 paused", xy=(_logit(soglia), -0.45),
                    xytext=(6, 0), textcoords="offset points", color=INK, fontsize=9,
                    va="center", ha="left")

    fig.tight_layout()
    os.makedirs(os.path.dirname(FIGURA), exist_ok=True)
    fig.savefig(FIGURA, dpi=200)
    plt.close(fig)
    print(f"written: {FIGURA}")


if __name__ == "__main__":
    main()
