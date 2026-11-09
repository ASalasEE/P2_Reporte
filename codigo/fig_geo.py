import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Rectangle
for p in ["/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf"]:
    fm.fontManager.addfont(p)
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
TXT1, TXT2 = "#0b0b0b", "#52514e"
CU, SUB, PORT, REF = "#c8793a", "#eef3e8", "#2a78d6", "#52514e"
W, L1, MG = 1.14, 6.0, 7.0
Pw = 5 * W
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)

def panel(ax, tipo, titulo):
    ax.set_aspect("equal"); ax.axis("off")
    if tipo == "recta":
        xm, ymin, ymax = 2 * L1 + W, -W / 2 - MG, W / 2 + MG
        traza = [(0, -W/2), (xm, -W/2), (xm, W/2), (0, W/2)]
        p1 = ((0, -Pw/2), (0, Pw/2)); p2 = ((xm, -Pw/2), (xm, Pw/2))
        r1 = ((L1, -W), (L1, W)); r2 = ((L1 + W, -W), (L1 + W, W))
    else:
        xm, ymin, ymax = L1 + W + MG, -W / 2 - MG, W / 2 + L1
        if tipo == "curva":
            traza = [(0, -W/2), (L1+W, -W/2), (L1+W, W/2+L1), (L1, W/2+L1), (L1, W/2), (0, W/2)]
        else:
            a = 2 * 0.55 * W
            traza = [(0, -W/2), (L1+W-a, -W/2), (L1+W, -W/2+a), (L1+W, W/2+L1), (L1, W/2+L1), (L1, W/2), (0, W/2)]
        xc = L1 + W / 2
        p1 = ((0, -Pw/2), (0, Pw/2)); p2 = ((xc - Pw/2, ymax), (xc + Pw/2, ymax))
        r1 = ((L1, -W), (L1, W)); r2 = ((L1 - W/2, W/2), (L1 + 1.5*W, W/2))
    ax.add_patch(Rectangle((0, ymin), xm, ymax - ymin, fc=SUB, ec="#b9c2ae", lw=0.6))
    ax.add_patch(Polygon(traza, closed=True, fc=CU, ec="#8a4f1f", lw=0.6))
    for (x0, y0), (x1, y1) in [p1, p2]:
        ax.plot([x0, x1], [y0, y1], color=PORT, lw=2.6, solid_capstyle="butt")
    for (x0, y0), (x1, y1) in [r1, r2]:
        ax.plot([x0, x1], [y0, y1], color=REF, lw=0.9, ls=(0, (3, 2)))
    if tipo == "recta":
        ax.text(-0.3, 0, "P1", ha="right", va="center", color=PORT, fontsize=8)
        ax.text(xm + 0.3, 0, "P2", ha="left", va="center", color=PORT, fontsize=8)
        ax.annotate("", xy=(0.15, -3.6), xytext=(L1, -3.6), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
        ax.text(L1 / 2 + 0.1, -3.9, "$L_1$", ha="center", va="top", fontsize=7.5, color=TXT2)
        ax.text(L1 + W / 2, 1.25, "$W$", ha="center", va="bottom", fontsize=7.5, color=TXT2)
    else:
        ax.text(-0.3, 0, "P1", ha="right", va="center", color=PORT, fontsize=8)
        ax.text(L1 + W / 2, ymax + 0.35, "P2", ha="center", va="bottom", color=PORT, fontsize=8)
        if tipo == "chaflan":
            ax.annotate("chaflán 55 %", xy=(L1 + W - 0.25, -W/2 + 0.3), xytext=(L1 + W + 1.6, -2.6),
                        fontsize=7.2, color=TXT2, arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
    ax.set_xlim(-1.6, xm + 1.4); ax.set_ylim(ymin - 0.5, ymax + 1.4)
    ax.set_title(titulo, fontsize=8.5)

fig, axs = plt.subplots(1, 3, figsize=(6.3, 2.6), gridspec_kw=dict(width_ratios=[13.14 + 3, 14.14 + 3, 14.14 + 3]))
panel(axs[0], "recta", "(a) Referencia")
panel(axs[1], "curva", "(b) Curva de 90°")
panel(axs[2], "chaflan", "(c) Curva con chaflán")
from matplotlib.lines import Line2D
h = [Line2D([], [], color=PORT, lw=2.6), Line2D([], [], color=REF, lw=0.9, ls=(0, (3, 2))),
     Rectangle((0, 0), 1, 1, fc=CU, ec="#8a4f1f", lw=0.6), Rectangle((0, 0), 1, 1, fc=SUB, ec="#b9c2ae", lw=0.6)]
fig.legend(h, ["puerto de onda", "plano de referencia tras de-embedding", "traza de cobre", "sustrato (RO4003C)"],
           loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, 0.02))
fig.tight_layout(w_pad=0.4)
fig.savefig(os.path.join(OUT, "fig0_geometria.pdf")); fig.savefig(os.path.join(OUT, "fig0_geometria.png"), dpi=220)
print("ok")
