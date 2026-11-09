"""Discontinuidad 2: longitud de la transicion frente a la longitud de onda guiada."""
import os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
TXT1, TXT2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "axes.unicode_minus": True,
                     "axes.edgecolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2, "axes.linewidth": 0.6})
C_ESC, C_TRA, WAVE, BAND = "#eb6834", "#1baf7a", "#2a78d6", "#d6efe4"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
D = np.load("d2_datos.npz")
N = json.load(open("d2_nums.json"))
f = D["f"]
EEM, GT0, LT, L1 = float(N["EEM"]), float(N["GT0"]), 10.0, 6.0
lg = 300.0 / (f * math.sqrt(EEM))            # mm
u = LT / lg                                  # longitud electrica de la transicion
gC = np.abs(D["C_Transicion_S11"]); gB = np.abs(D["B_Escalon_S11"])
x = np.linspace(1e-3, 1.25, 600)
teo = GT0 * np.abs(np.sin(2 * np.pi * x) / (2 * np.pi * x))

fig = plt.figure(figsize=(6.3, 2.9))
gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.15], hspace=0.6, wspace=0.28)
ax = fig.add_subplot(gs[:, 0])
ax.plot(u, gB, color=C_ESC, lw=1.4, label=r"Escalón ($L_t=0$)")
ax.plot(u, gC, color=C_TRA, lw=1.4, ls="-.", label="Transición, HFSS")
ax.plot(x, teo, color=TXT2, lw=0.8, ls=":", label="Transición, teoría")
ax.axhline(0.1, color=TXT2, lw=0.7, ls=(0, (5, 3)))
ax.text(1.22, 0.108, r"$|\Gamma|=0.1$", ha="right", fontsize=7, color=TXT2)
for v, t in [(0.5, r"$L_t=\lambda_g/2$"), (1.0, r"$L_t=\lambda_g$")]:
    ax.axvline(v, color=TXT2, lw=0.6, ls=":")
    ax.text(v + 0.015, 0.355, t, fontsize=7, color=TXT2, va="top")
ax.set_xlim(0, 1.25); ax.set_ylim(0, 0.37)
ax.set_xlabel(r"Longitud eléctrica de la transición, $L_t/\lambda_g$")
ax.set_ylabel(r"$|\Gamma|$")
ax.grid(True, color=GRID, lw=0.5)
for s_ in ["top", "right"]:
    ax.spines[s_].set_visible(False)
ax.legend(fontsize=7, frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.62))
ax.text(0.02, 0.98, "(a)", transform=ax.transAxes, va="top", fontsize=8.5)
# ---- (b) onda a lo largo de la estructura a 2 y 10 GHz
s = np.linspace(0, 2 * L1 + LT, 1200)
for k, fq in enumerate([2, 10]):
    a = fig.add_subplot(gs[k, 1])
    l = 300.0 / fq / math.sqrt(EEM)
    a.axvspan(L1, L1 + LT, color=BAND, lw=0, zorder=0)
    a.axhline(0, color="#d5d5cf", lw=0.6, zorder=1)
    y = np.cos(2 * np.pi * s / l)
    a.plot(s, y, color=WAVE, lw=1.3, zorder=3)
    mk = (s >= L1) & (s <= L1 + LT)
    a.plot(s[mk], y[mk], color=TXT1, lw=2.0, zorder=4)
    a.set_xlim(0, 2 * L1 + LT); a.set_ylim(-1.3, 1.3); a.set_yticks([])
    for s_ in ["top", "right", "left"]:
        a.spines[s_].set_visible(False)
    a.set_title(r"%d GHz: $\lambda_g=%.0f$ mm, $L_t=%.2f\,\lambda_g$" % (fq, l, LT / l), fontsize=8, pad=3)
    if k == 1:
        a.set_xlabel("posición a lo largo de la línea (mm)")
    else:
        a.set_xticklabels([])
        a.text(L1 + LT / 2, 1.05, "transición", ha="center", fontsize=7, color=TXT2)
fig.text(0.535, 0.97, "(b)", fontsize=8.5, va="top")
fig.savefig(os.path.join(OUT, "fig_d2_escala.pdf"))
fig.savefig(os.path.join(OUT, "fig_d2_escala.png"), dpi=220)
print("ok")
