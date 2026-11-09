"""Discusion 6.2: la estructura fija y la onda guiada encogiendose con la frecuencia."""
import os, math, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
TXT1, TXT2 = "#0b0b0b", "#52514e"
CU, WAVE, BAND = "#c8793a", "#2a78d6", "#f2d7c4"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
W, L1 = 1.14, 6.0
ee = 2.781
diag = W * math.sqrt(2)
Ltot = 2 * L1 + W            # longitud del eje entre puertos
s_c = L1 + W / 2             # posicion de la esquina sobre el eje

fig = plt.figure(figsize=(6.3, 3.9))
gs = fig.add_gridspec(3, 2, width_ratios=[0.8, 2.2], hspace=0.55, wspace=0.12)

# ---------------- vista superior fija de la curva ----------------
ax = fig.add_subplot(gs[:, 0])
tr = [(0, -W / 2), (L1 + W, -W / 2), (L1 + W, W / 2 + L1), (L1, W / 2 + L1), (L1, W / 2), (0, W / 2)]
ax.add_patch(Polygon(tr, closed=True, fc=CU, ec="#8a4f1f", lw=0.6))
ax.add_patch(Rectangle((L1, -W / 2), W, W, fc=BAND, ec="#8a4f1f", lw=0.6, zorder=3))
ax.plot([0, s_c, s_c], [0, 0, s_c], color="white", lw=0.8, ls=(0, (3, 2)), zorder=4)
ax.annotate("", xy=(4.0, 0), xytext=(1.0, 0), zorder=5,
            arrowprops=dict(arrowstyle="-|>", color="white", lw=0.9, mutation_scale=8))
ax.text(2.5, -1.2, "$s$", ha="center", fontsize=9, color=TXT1)
ax.text(-0.3, 0, "P1", ha="right", va="center", fontsize=8, color=WAVE)
ax.text(s_c, s_c + 0.5, "P2", ha="center", va="bottom", fontsize=8, color=WAVE)
ax.annotate("esquina", xy=(L1 + W, -W / 2), xytext=(L1 + W + 0.4, -2.6), fontsize=7.6, color=TXT1,
            arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax.annotate("", xy=(0, -3.6), xytext=(1.0 * 5, -3.6),
            arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
ax.text(2.5, -4.0, "5 mm", ha="center", va="top", fontsize=7.4, color=TXT2)
ax.set_aspect("equal"); ax.axis("off")
ax.set_xlim(-1.2, L1 + W + 2.4); ax.set_ylim(-4.8, L1 + W + 0.8)
ax.set_title("Curva de 90°", fontsize=8.6)

# ---------------- la onda a lo largo del eje, misma escala ----------------
s = np.linspace(0, Ltot, 1500)
for k, fq in enumerate([2, 7, 20]):
    ax = fig.add_subplot(gs[k, 1])
    lg = 300.0 / fq / math.sqrt(ee)
    y = np.cos(2 * math.pi * s / lg)
    ax.axvspan(s_c - diag / 2, s_c + diag / 2, color=BAND, lw=0, zorder=0)
    ax.axhline(0, color="#d5d5cf", lw=0.6, zorder=1)
    ax.plot(s, y, color=WAVE, lw=1.5, zorder=3)
    mc = (s >= s_c - diag / 2) & (s <= s_c + diag / 2)
    ax.plot(s[mc], y[mc], color="#0b0b0b", lw=2.4, zorder=4)
    if lg < Ltot:
        s0 = 0.0
        ax.annotate("", xy=(s0, 1.38), xytext=(s0 + lg, 1.38),
                    arrowprops=dict(arrowstyle="<->", lw=0.7, color=TXT2), annotation_clip=False)
        ax.text(s0 + lg / 2, 1.5, "$\\lambda_g$ = %.1f mm" % lg, ha="center", va="bottom", fontsize=7.4, color=TXT2)
    elif lg / 2 < Ltot:
        ax.annotate("", xy=(0, 1.38), xytext=(lg / 2, 1.38),
                    arrowprops=dict(arrowstyle="<->", lw=0.7, color=TXT2), annotation_clip=False)
        ax.text(lg / 4, 1.5, "$\\lambda_g/2$ = %.1f mm" % (lg / 2), ha="center", va="bottom", fontsize=7.4, color=TXT2)
    else:
        ax.text(0.2, -1.15, "$\\lambda_g$ = %.0f mm, mucho mayor que la línea completa" % lg, ha="left", va="bottom",
                fontsize=7.4, color=TXT2)
    rel = lg / diag
    ax.text(Ltot + 0.35, 0.0, "%d GHz\nesquina $=\\lambda_g/%s$\n$\\Delta\\phi\\approx %.0f^\\circ$" %
            (fq, ("%.0f" % rel) if rel >= 10 else ("%.1f" % rel), 360 * diag / lg),
            ha="left", va="center", fontsize=7.6, color=TXT1)
    ax.set_xlim(0, Ltot); ax.set_ylim(-1.25, 1.25)
    ax.set_yticks([])
    for sp_ in ["top", "right", "left"]:
        ax.spines[sp_].set_visible(False)
    if k < 2:
        ax.set_xticklabels([])
    else:
        ax.set_xlabel("posición a lo largo de la línea, $s$ (mm)")
    if k == 0:
        ax.set_title("Onda guiada a lo largo de la línea", fontsize=8.6, pad=14)

fig.savefig(os.path.join(OUT, "fig8_escala_lambda.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig8_escala_lambda.png"), dpi=220)
print("ok")
