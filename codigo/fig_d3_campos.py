"""Discontinuidad 3 (gap): carga superficial y lineas de campo (HFSS, 5 GHz)."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from campos_d3 import superficie, vertical, lineas_de_campo, W, L1, H

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "axes.unicode_minus": True})
TXT1, TXT2 = "#0b0b0b", "#52514e"
C_DER, C_TIE, C_OUT = "#eb6834", "#2a78d6", "#b5b4ae"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
nums = json.load(open("d3_nums.json"))

casos = [("B2_Gap_0p2", 0.2), ("B4_Gap_1p0", 1.0)]
res = {}
for n, s in casos:
    r = superficie(n, s)
    v = vertical(n, s)
    lin, dst, peso, frac = lineas_de_campo(v, s)
    res[n] = dict(r=r, v=v, lin=lin, dst=dst, frac=frac)

fig = plt.figure(figsize=(6.3, 4.1))
anchos = [s + 3.0 for _, s in casos]
for k, (n, s) in enumerate(casos):
    r, v = res[n]["r"], res[n]["v"]
    y0 = 0.55 - k * 0.43
    # ---- carga (vista superior)
    ax = fig.add_axes([0.06, y0, 0.40, 0.40])
    im = ax.pcolormesh(r["X"], r["Y"], np.clip(r["R"], -2.5, 2.5), cmap="RdBu_r", vmin=-2.5, vmax=2.5,
                       shading="auto", rasterized=True)
    for xa, xb in [(L1 - 1.5, L1), (L1 + s, L1 + s + 1.5)]:
        ax.add_patch(Rectangle((xa, -W / 2), xb - xa, W, fill=False, ec=TXT2, lw=0.6))
    ax.set_xlim(L1 - 1.5, L1 + s + 1.5); ax.set_ylim(-0.7, 1.05)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.text(-0.03, 0.5, "$s=%g$ mm" % s, transform=ax.transAxes, rotation=90, va="center", ha="right", fontsize=8.6)
    ax.annotate("extremo derecho: %.0f %% de la\ncarga del izquierdo, con signo opuesto" % (100 * abs(r["ratio"])),
                xy=(L1 + s + 0.04, 0.35), xytext=(L1 + s + 1.48, 0.84), fontsize=6.6, color=TXT1, va="center", ha="right",
                arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
    if k == 0:
        ax.set_title("Carga superficial (signo incluido)", fontsize=8.6)
    # ---- lineas de campo (corte vertical por el eje)
    ax2 = fig.add_axes([0.52, y0, 0.46, 0.40])
    ax2.add_patch(Rectangle((v["xs"][0], 0), v["xs"][-1] - v["xs"][0], H, fc="#eef3e8", ec="none", zorder=0))
    for l, d in zip(res[n]["lin"], res[n]["dst"]):
        col = {"derecha": C_DER, "tierra": C_TIE}.get(d, C_OUT)
        ax2.plot(l[:, 1], l[:, 0], color=col, lw=0.55, zorder=2)
    ax2.plot([v["xs"][0], L1], [H, H], color="#8a4f1f", lw=2.6, solid_capstyle="butt", zorder=3)
    ax2.plot([L1 + s, v["xs"][-1]], [H, H], color="#8a4f1f", lw=2.6, solid_capstyle="butt", zorder=3)
    ax2.plot([v["xs"][0], v["xs"][-1]], [0, 0], color="#8a4f1f", lw=2.0, zorder=3)
    ax2.set_xlim(v["xs"][0], v["xs"][-1]); ax2.set_ylim(-0.03, 1.3)
    ax2.set_aspect("equal"); ax2.set_xticks([]); ax2.set_yticks([])
    for sp in ax2.spines.values():
        sp.set_visible(False)
    fr = res[n]["frac"]
    ax2.text(0.99, 0.97, "flujo desde los últimos 0.5 mm:\n%.0f %% a la tira derecha\n%.0f %% a tierra\n%.0f %% sale del corte" % (100 * fr["derecha"], 100 * fr["tierra"], 100 * fr["fuera"]),
             transform=ax2.transAxes, ha="right", va="top", fontsize=6.6, color=TXT1, zorder=6,
             bbox=dict(fc="white", ec="none", alpha=0.88, pad=1.5))
    if k == 0:
        ax2.set_title("Líneas de campo eléctrico (corte por el eje)", fontsize=8.6)
cax = fig.add_axes([0.12, 0.06, 0.28, 0.02])
cb = fig.colorbar(im, cax=cax, orientation="horizontal")
cb.set_label(r"$\rho_s/|\rho_s|_{\mathrm{l\acute{i}nea}}$", fontsize=7.4, labelpad=1); cb.ax.tick_params(labelsize=6.8)
h = [Line2D([], [], color=C_DER, lw=1.2), Line2D([], [], color=C_TIE, lw=1.2), Line2D([], [], color=C_OUT, lw=1.2)]
fig.legend(h, ["termina en la tira derecha ($C_g$)", "termina en tierra ($C_p$)", "sale del corte"],
           loc="lower center", bbox_to_anchor=(0.75, -0.01), ncol=3, fontsize=6.6, frameon=False, columnspacing=0.8, handlelength=1.4)
fig.savefig(os.path.join(OUT, "fig_d3_campos.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig_d3_campos.png"), dpi=220)
json.dump({n: dict(ratio=res[n]["r"]["ratio"], frac=res[n]["frac"]) for n in res}, open("d3_campos.json", "w"), indent=1)
print({n: (round(res[n]["r"]["ratio"], 3), {k: round(x, 3) for k, x in res[n]["frac"].items()}) for n in res})
