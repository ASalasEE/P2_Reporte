"""Discontinuidad 2: vista superior del escalon y de la transicion gradual."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Rectangle
from matplotlib.lines import Line2D
from campos_d2 import ancho_traza

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
TXT2 = "#52514e"
CU, SUB, PORT, REF = "#c8793a", "#eef3e8", "#2a78d6", "#52514e"
W1, W2, L1, LT = 1.14, 0.29, 6.0, 10.0
Pw = 5 * W1
YV = 3.3                      # semialto de la vista (el sustrato completo mide +-7.57 mm)
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)


def cota(ax, x0, x1, y, txt, dy=-0.35):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
    ax.text(0.5 * (x0 + x1), y + dy, txt, ha="center", va="top" if dy < 0 else "bottom", fontsize=7.5, color=TXT2)


def panel(ax, tipo, titulo):
    ax.set_aspect("equal"); ax.axis("off")
    xm = 2 * L1 + (LT if tipo == "transicion" else 0)
    ax.add_patch(Rectangle((0, -YV), xm, 2 * YV, fc=SUB, ec="none"))
    for yy in (-YV, YV):
        ax.plot([0, xm], [yy, yy], color="#b9c2ae", lw=0.6, ls=(0, (1, 1.5)))
    xs = np.linspace(0, xm, 800)
    w = ancho_traza(xs, "escalon" if tipo == "escalon" else "transicion")
    if tipo == "escalon":
        pts = [(0, -W1 / 2), (L1, -W1 / 2), (L1, -W2 / 2), (xm, -W2 / 2), (xm, W2 / 2), (L1, W2 / 2), (L1, W1 / 2), (0, W1 / 2)]
    else:
        pts = list(zip(xs, -w / 2)) + list(zip(xs[::-1], w[::-1] / 2))
    ax.add_patch(Polygon(pts, closed=True, fc=CU, ec="#8a4f1f", lw=0.6))
    for x in (0, xm):
        ax.plot([x, x], [-Pw / 2, Pw / 2], color=PORT, lw=2.6, solid_capstyle="butt")
    planos = [L1] if tipo == "escalon" else [L1, L1 + LT]
    for x in planos:
        ax.plot([x, x], [-1.1, 1.1], color=REF, lw=0.9, ls=(0, (3, 2)))
    ax.text(-0.3, 0, "P1", ha="right", va="center", color=PORT, fontsize=8)
    ax.text(xm + 0.3, 0, "P2", ha="left", va="center", color=PORT, fontsize=8)
    cota(ax, 0, L1, -2.0, "$L_1$")
    if tipo == "escalon":
        cota(ax, L1, xm, -2.0, "$L_1$")
        ax.text(L1 / 2, 0.75, r"$W_1$ (50 $\Omega$)", ha="center", va="bottom", fontsize=7.4, color=TXT2)
        ax.text(L1 + L1 / 2, 0.45, r"$W_2$ (100 $\Omega$)", ha="center", va="bottom", fontsize=7.4, color=TXT2)
    else:
        cota(ax, L1, L1 + LT, -2.0, "$L_t=10$ mm")
        cota(ax, L1 + LT, xm, -2.0, "$L_1$")
        ax.text(L1 + LT / 2, 1.45, r"$\ln Z$ varía linealmente con $x$", ha="center", va="bottom", fontsize=7.2, color=TXT2)
    ax.set_xlim(-1.4, xm + 1.4); ax.set_ylim(-YV - 0.2, YV + 0.2)
    ax.set_title(titulo, fontsize=8.5)


fig, axs = plt.subplots(1, 2, figsize=(6.3, 1.6), gridspec_kw=dict(width_ratios=[12 + 2.8, 22 + 2.8]))
panel(axs[0], "escalon", "(a) Escalón abrupto")
panel(axs[1], "transicion", "(b) Transición gradual (exponencial)")
h = [Line2D([], [], color=PORT, lw=2.6), Line2D([], [], color=REF, lw=0.9, ls=(0, (3, 2)))]
fig.legend(h, ["puerto de onda", "plano de referencia tras el de-embedding"], loc="lower center",
           bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=7.4, frameon=False)
fig.savefig(os.path.join(OUT, "fig_d2_geometria.pdf"))
fig.savefig(os.path.join(OUT, "fig_d2_geometria.png"), dpi=220)
print("ok")
