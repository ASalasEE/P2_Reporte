"""Figura 9: carga y corriente superficial en la esquina a partir de los campos de HFSS (5 GHz)."""
import os, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
S_ = ""
exec(open(S_ + "campos_hfss.py").read())
TXT1, TXT2 = "#0b0b0b", "#52514e"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)

res, num = {}, {}
for nombre, tipo in [("B_Curva90", "curva"), ("C_Curva90_Chaflan", "chaflan")]:
    res[tipo] = cargar(nombre, tipo)
    num[tipo] = metricas(res[tipo], tipo)
json.dump(num, open(S_ + "campos_nums.json", "w"), indent=1)

La = 10 * W
cont = {"curva": [(-La, 0), (W, 0), (W, W + La), (0, W + La), (0, W), (-La, W)],
        "chaflan": [(-La, 0), (W - AC, 0), (W, AC), (W, W + La), (0, W + La), (0, W), (-La, W)]}
fig, axs = plt.subplots(2, 2, figsize=(6.3, 5.9))
xl, yl = (-1.6 * W, 1.45 * W), (-0.75 * W, 2.6 * W)
for ax in axs.ravel():
    ax.set_aspect("equal"); ax.set_xlim(*xl); ax.set_ylim(*yl)
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)


def nota(ax, txt, xy, xytext, ha="left", va="center"):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=7.2, color=TXT1, ha=ha, va=va,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))


ims = []
for r_, t in enumerate(["curva", "chaflan"]):
    R = res[t]
    ax = axs[r_, 0]
    im = ax.pcolormesh(R["X"], R["Y"], np.clip(R["S"], 0, 2.5), cmap="Oranges", vmin=0, vmax=2.5,
                       shading="auto", rasterized=True)
    pg = Polygon(cont[t], closed=True, fill=False, ec="#5a3a1a", lw=0.7)
    ax.add_patch(pg); im.set_clip_path(pg); ims.append(im)
    ax = axs[r_, 1]
    im2 = ax.pcolormesh(R["X"], R["Y"], np.clip(R["JN"], 0, 2.0), cmap="Blues", vmin=0, vmax=2.0,
                        shading="auto", rasterized=True)
    seeds = np.array([[-1.5 * W, y] for y in np.linspace(0.1 * W, 0.9 * W, 9)])
    ax.streamplot(R["xl"], R["yl"], R["JXr"], R["JYr"], color=TXT1, linewidth=0.6, arrowsize=0.6,
                  start_points=seeds, density=3, broken_streamlines=False)
    pg2 = Polygon(cont[t], closed=True, fill=False, ec="#1b3a66", lw=0.7)
    ax.add_patch(pg2); im2.set_clip_path(pg2); ims.append(im2)

nb, nc = num["curva"], num["chaflan"]
nota(axs[0, 0], "esquina exterior:\n%.1f× la carga del\ntramo recto" % nb["Cext"], (W - 0.05, 0.05), (W + 0.05, -0.30 * W), ha="right", va="top")
nota(axs[0, 0], "esquina interior:\n%.1f×" % nb["Cint"], (0.04, W - 0.04), (-1.45 * W, 1.75 * W))
nota(axs[0, 1], "el %.0f %% de la\ncorriente pasa\npor la mitad\ninterior" % (100 * nb["Iin"]), (0.25 * W, 0.75 * W), (-1.5 * W, 1.85 * W))
nota(axs[0, 1], "esquina exterior: %.2f×\n(casi sin corriente)" % nb["Jext"], (0.93 * W, 0.07 * W), (W + 0.05, -0.30 * W), ha="right", va="top")
xm, ym = W - AC / 2, AC / 2
nota(axs[1, 0], "borde del chaflán:\n%.1f×" % nc["Cch"], (xm + 0.03, ym - 0.03), (W + 0.05, -0.30 * W), ha="right", va="top")
nota(axs[1, 0], "esquina interior:\n%.1f×" % nc["Cint"], (0.04, W - 0.04), (-1.45 * W, 1.75 * W))
nota(axs[1, 1], "el %.0f %% de la\ncorriente pasa\npor la mitad\ninterior" % (100 * nc["Iin"]), (0.2 * W, 0.8 * W), (-1.5 * W, 1.85 * W))
nota(axs[1, 1], "junto al chaflán: %.2f×\n(todo el metal\nconduce corriente)" % nc["Jch"], (xm - 0.02, ym + 0.02), (W + 0.05, -0.30 * W), ha="right", va="top")

axs[0, 0].set_title("Densidad de carga superficial", fontsize=8.6)
axs[0, 1].set_title("Densidad de corriente superficial", fontsize=8.6)
axs[0, 0].text(-0.06, 0.5, "(a) Sin chaflán", transform=axs[0, 0].transAxes, rotation=90, va="center", ha="right", fontsize=8.6)
axs[1, 0].text(-0.06, 0.5, "(b) Con chaflán", transform=axs[1, 0].transAxes, rotation=90, va="center", ha="right", fontsize=8.6)
fig.tight_layout(h_pad=0.6, w_pad=0.4)
cb = fig.colorbar(ims[0], ax=axs[:, 0], orientation="horizontal", fraction=0.035, pad=0.03, shrink=0.75)
cb.set_label(r"$|\rho_s|/|\rho_{s}|_{\mathrm{tramo\ recto}}$", fontsize=7.6); cb.ax.tick_params(labelsize=7)
cb2 = fig.colorbar(ims[1], ax=axs[:, 1], orientation="horizontal", fraction=0.035, pad=0.03, shrink=0.75)
cb2.set_label(r"$|\mathbf{J}_s|/|\mathbf{J}_{s}|_{\mathrm{tramo\ recto}}$", fontsize=7.6); cb2.ax.tick_params(labelsize=7)
fig.savefig(os.path.join(OUT, "fig7_carga_corriente.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig7_carga_corriente.png"), dpi=220)
print(json.dumps(num, indent=1))
