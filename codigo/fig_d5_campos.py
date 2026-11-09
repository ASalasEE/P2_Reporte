"""Discontinuidad 5: carga y corriente superficiales en la union en T (campos
de HFSS a 5 GHz): T de 50 ohm excitada desde la linea principal y divisor
excitado desde la rama."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from campos_d5 import cargar, metricas, L1

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "axes.unicode_minus": True})
TXT1, TXT2 = "#0b0b0b", "#52514e"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)

casos = [("B_T", 1.14, 1.14, "izq", "(a) T de 50 $\\Omega$, excitada desde P1"),
         ("C_Divisor", 0.29, 1.14, "rama", "(b) Divisor, excitado desde la rama (P3)")]
R = {n: cargar(n, wb, ws, ref) for n, wb, ws, ref, _ in casos}
M = {n: metricas(R[n]) for n in R}


def contorno(r):
    wb, ws = r["wb"], r["ws"]
    x0, x1 = r["xs"][0], r["xs"][-1]
    y1 = r["ys"][-1]
    return [(x0, -wb / 2), (x1, -wb / 2), (x1, wb / 2), (L1 + ws, wb / 2), (L1 + ws, y1), (L1, y1),
            (L1, wb / 2), (x0, wb / 2)]


def mapa(ax, r, campo, vmax):
    if campo == "rho":
        im = ax.pcolormesh(r["X"], r["Y"], np.clip(r["S"], 0, vmax), cmap="Oranges", vmin=0, vmax=vmax,
                           shading="auto", rasterized=True)
        ec = "#5a3a1a"
    else:
        im = ax.pcolormesh(r["X"], r["Y"], np.clip(r["JN"], 0, vmax), cmap="Blues", vmin=0, vmax=vmax,
                           shading="auto", rasterized=True)
        ec = "#1b3a66"
        if r["wb"] > 1:
            seeds = np.array([[r["xs"][0] + 0.02, y] for y in np.linspace(-0.92, 0.92, 15) * r["wb"] / 2])
        else:
            seeds = np.array([[x, r["ys"][-1] - 0.02] for x in L1 + np.linspace(0.05, 0.95, 15) * r["ws"]])
        ax.streamplot(r["xs"], r["ys"], r["JXr"], r["JYr"], color=TXT1, linewidth=0.55, arrowsize=0.55,
                      start_points=seeds, density=6, integration_direction="forward", broken_streamlines=False)
    pg = Polygon(contorno(r), closed=True, fill=False, ec=ec, lw=0.7)
    ax.add_patch(pg); im.set_clip_path(pg)
    ax.set_aspect("equal"); ax.set_xlim(r["xs"][0], r["xs"][-1]); ax.set_ylim(-r["wb"] / 2 - 0.45, r["ys"][-1])
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    return im


def nota(ax, txt, xy, xytext, ha="left"):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=6.8, color=TXT1, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))


fig = plt.figure(figsize=(6.3, 5.3))
for k, (n, wb, ws, ref, tit) in enumerate(casos):
    r, m = R[n], M[n]
    y0 = 0.50 - k * 0.44
    ax1 = fig.add_axes([0.02, y0, 0.46, 0.36]); ax2 = fig.add_axes([0.52, y0, 0.46, 0.36])
    imr = mapa(ax1, r, "rho", 2.5)
    imj = mapa(ax2, r, "J", 3.0)
    fig.text(0.02, y0 + 0.375, tit, fontsize=8.8)
    if k == 0:
        fig.text(0.25, 0.925, "Densidad de carga superficial", fontsize=8.6, ha="center")
        nota(ax1, "cuadro de unión: %.1f×" % m["Ccuadro"], (L1 + ws / 2, 0.0), (L1 + ws + 0.4, 1.3))
        fig.text(0.75, 0.925, "Densidad de corriente superficial", fontsize=8.6, ha="center")
        nota(ax2, "brazo recto: %.2f" % m["der"], (L1 + ws + 1.0, 0.0), (L1 + ws + 0.4, -0.85))
        nota(ax2, "rama: %.2f" % m["rama"], (L1 + ws / 2, r["y3"]), (L1 + ws + 0.35, r["y3"] + 0.35))
        nota(ax2, "corriente de entrada: 1", (L1 - 1.2, 0.0), (L1 - 1.45, -0.85))
        nota(ax2, "esquinas interiores:\n%.1f× el brazo" % m["Jesq"], (L1 + 0.05, wb / 2 + 0.05), (r["xs"][0] + 0.1, 1.45))
    else:
        nota(ax1, "hombros de la rama:\n%.1f× la carga de la rama" % m["Chombro"], (L1 + 0.06, wb / 2 + 0.08), (r["xs"][0] + 0.1, 1.0))
        nota(ax1, "unión: %.1f×" % m["Ccuadro"], (L1 + ws / 2, 0.0), (L1 + ws + 0.4, 0.75))
        nota(ax2, "%.2f" % m["izq"], (L1 - 1.2, 0.0), (L1 - 1.5, -0.6))
        nota(ax2, "%.2f" % m["der"], (L1 + ws + 1.2, 0.0), (L1 + ws + 1.5, -0.6), ha="right")
        nota(ax2, "entrada: 1", (L1 + ws / 2, r["y3"]), (L1 + ws + 0.35, r["y3"]))
        nota(ax2, "esquinas: %.1f×" % m["Jesq"], (L1 + ws - 0.05, wb / 2 + 0.05), (L1 + ws + 0.35, 0.75))
    for ax, im, lab in [(ax1, imr, r"$|\rho_s|/|\rho_s|_{\mathrm{brazo\ de\ entrada}}$"),
                        (ax2, imj, r"$|\mathbf{J}_s|/|\mathbf{J}_s|_{\mathrm{brazo\ de\ entrada}}$")]:
        if k == 1:
            pos = ax.get_position()
            cax = fig.add_axes([pos.x0 + 0.06, 0.03, pos.width - 0.12, 0.014])
            cb = fig.colorbar(im, cax=cax, orientation="horizontal")
            cb.set_label(lab, fontsize=7.2, labelpad=1); cb.ax.tick_params(labelsize=6.8, pad=1)
fig.savefig(os.path.join(OUT, "fig_d5_campos.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig_d5_campos.png"), dpi=220)
json.dump(M, open("d5_campos.json", "w"), indent=1)
print({n: {k: round(v, 3) for k, v in M[n].items()} for n in M})
