"""Discontinuidad 4 (cambio de sustrato): E, D, carga, corriente y voltaje
junto a la union, a partir de los campos de HFSS a 5 GHz."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
from campos_d4 import superficie, vertical, W1, L1, H

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "axes.unicode_minus": True})
TXT1, TXT2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
C_V, C_I, C_Q = "#2a78d6", "#1baf7a", "#eb6834"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
N4 = json.load(open("d4_nums.json"))

sB = superficie("B2_RO3010", 10.2, W1)
vB = vertical("B2_RO3010", 10.2)
sC = superficie("C_RO3010_Ancho50", 10.2, 0.48)

fig = plt.figure(figsize=(6.3, 6.9))
# ---- (a) corte vertical: |E| y |D|
for k, (campo, tit) in enumerate([("E", r"$|\mathbf{E}|$: continuo a través de la unión"),
                                  ("D", r"$|\mathbf{D}|=\varepsilon|\mathbf{E}|$: salta en el sustrato")]):
    ax = fig.add_axes([0.04 + k * 0.49, 0.735, 0.45, 0.235])
    im = ax.pcolormesh(vB["X"], vB["Z"], np.clip(vB[campo], 0, 3.2), cmap="YlOrBr", vmin=0, vmax=3.2,
                       shading="auto", rasterized=True)
    ax.plot([vB["xs"][0], vB["xs"][-1]], [H, H], color="#3b2a1a", lw=2.0, solid_capstyle="butt")
    ax.plot([L1, L1], [0, H], color="white", lw=0.8, ls=(0, (3, 2)))
    ax.set_xlim(vB["xs"][0], vB["xs"][-1]); ax.set_ylim(0, 1.3)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(tit, fontsize=8.4)
    ax.text(L1 - 0.6, 0.18, "RO4003C", ha="center", fontsize=7, color=TXT1)
    ax.text(L1 + 0.6, 0.18, "RO3010", ha="center", fontsize=7, color="white" if campo == "D" else TXT1)
    ax.text(L1 + 1.15, H + 0.06, "tira", ha="right", va="bottom", fontsize=7, color=TXT1)
cax = fig.add_axes([0.30, 0.705, 0.40, 0.011])
cb = fig.colorbar(im, cax=cax, orientation="horizontal")
cb.set_label(r"$|\mathbf{E}|$ y $|\mathbf{D}|/\varepsilon_{r1}\varepsilon_0$, normalizados al valor bajo la tira en RO4003C", fontsize=7.2, labelpad=1)
cb.ax.tick_params(labelsize=6.8, pad=1)
fig.text(0.005, 0.85, "(a)", fontsize=8.6)
# ---- (b) carga superficial, vista superior
for k, (s, tit) in enumerate([(sB, "Cambio de sustrato (mismo ancho)"), (sC, "Sustrato con ancho compensado")]):
    ax = fig.add_axes([0.04 + k * 0.49, 0.41, 0.45, 0.19])
    im2 = ax.pcolormesh(s["X"], s["Y"], np.clip(s["S"], 0, 4), cmap="Oranges", vmin=0, vmax=4,
                        shading="auto", rasterized=True)
    w2 = W1 if k == 0 else 0.48
    for xa, xb, w in [(4.5, L1, W1), (L1, 7.5, w2)]:
        ax.add_patch(Rectangle((xa, -w / 2), xb - xa, w, fill=False, ec="#5a3a1a", lw=0.6))
    ax.plot([L1, L1], [-1, 1], color=TXT2, lw=0.6, ls=(0, (3, 2)))
    ax.set_xlim(4.5, 7.5); ax.set_ylim(-1.0, 1.0); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(tit, fontsize=8.4)
    ax.text(4.6, -0.95, "RO4003C", fontsize=6.8, color=TXT2, va="bottom")
    ax.text(7.4, -0.95, "RO3010", fontsize=6.8, color=TXT2, va="bottom", ha="right")
cax = fig.add_axes([0.30, 0.385, 0.40, 0.011])
cb = fig.colorbar(im2, cax=cax, orientation="horizontal")
cb.set_label(r"$|\rho_s|/|\rho_s|_{\mathrm{RO4003C}}$", fontsize=7.2, labelpad=1)
cb.ax.tick_params(labelsize=6.8, pad=1)
fig.text(0.005, 0.50, "(b)", fontsize=8.6)
# ---- (c) perfiles a lo largo de la linea (cambio de sustrato)
ax = fig.add_axes([0.10, 0.06, 0.86, 0.23])
ax.plot(sB["x"] - L1, np.abs(sB["q"]), color=C_Q, lw=1.4, label=r"carga por unidad de longitud $|q(x)|$")
ax.plot(vB["xs"] - L1, np.abs(vB["V"]), color=C_V, lw=1.4, label=r"voltaje $|V(x)|=|\int E_z\,dz|$")
ax.plot(sB["x"] - L1, np.abs(sB["I"]), color=C_I, lw=1.4, label=r"corriente $|I(x)|$")
rc = float(N4["RCP13"])
ax.axhline(rc, color=C_Q, lw=0.8, ls="--")
ax.text(-1.17, rc + 0.07, r"$C'_{\mathrm{RO3010}}/C'_{\mathrm{RO4003C}}=%s$ (puertos de HFSS)" % N4["RCP13"],
        fontsize=7, color=C_Q, va="bottom")
ax.axvline(0, color=TXT2, lw=0.6, ls=":")
ax.set_xlim(-1.2, 1.2); ax.set_ylim(0, 3.3)
ax.set_xlabel(r"$x-L_1$ (mm)"); ax.set_ylabel("normalizado al lado RO4003C")
ax.grid(True, color=GRID, lw=0.5)
for s_ in ["top", "right"]:
    ax.spines[s_].set_visible(False)
ax.legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(0.0, 0.55))
ax.set_title("(c) Cambio de sustrato: magnitudes a lo largo de la línea", fontsize=8.6, loc="left")
fig.savefig(os.path.join(OUT, "fig_d4_campos.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig_d4_campos.png"), dpi=220)


def lado(x, v, a, b):
    return float(np.mean(np.abs(v[(x >= a) & (x <= b)])))


met = dict(
    q_salto=lado(sB["x"], sB["q"], 6.3, 7.2) / lado(sB["x"], sB["q"], 4.8, 5.7),
    V_salto=lado(vB["xs"], vB["V"], 6.05, 6.3) / lado(vB["xs"], vB["V"], 5.7, 5.95),
    I_salto=lado(sB["x"], sB["I"], 6.05, 6.3) / lado(sB["x"], sB["I"], 5.7, 5.95),
    D_salto=float(np.nanmean(vB["D"][(vB["X"] > 6.2) & (vB["X"] < 6.6) & (vB["Z"] > 0.1) & (vB["Z"] < 0.4)]) /
                  np.nanmean(vB["D"][(vB["X"] > 5.4) & (vB["X"] < 5.8) & (vB["Z"] > 0.1) & (vB["Z"] < 0.4)])),
    E_salto=float(np.nanmean(vB["E"][(vB["X"] > 6.02) & (vB["X"] < 6.12) & (vB["Z"] > 0.1) & (vB["Z"] < 0.4)]) /
                  np.nanmean(vB["E"][(vB["X"] > 5.88) & (vB["X"] < 5.98) & (vB["Z"] > 0.1) & (vB["Z"] < 0.4)])),
    Eaire=float(np.nanmean(vB["E"][(vB["X"] > 6.02) & (vB["X"] < 6.12) & (vB["Z"] > 0.6) & (vB["Z"] < 0.9)]) /
                np.nanmean(vB["E"][(vB["X"] > 5.88) & (vB["X"] < 5.98) & (vB["Z"] > 0.6) & (vB["Z"] < 0.9)])),
    qC_salto=lado(sC["x"], sC["q"], 6.3, 7.2) / lado(sC["x"], sC["q"], 4.8, 5.7),
)
json.dump(met, open("d4_campos.json", "w"), indent=1)
print({k: round(v, 3) for k, v in met.items()})
