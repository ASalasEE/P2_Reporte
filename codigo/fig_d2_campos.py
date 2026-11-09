"""Discontinuidad 2: carga y corriente superficiales (campos de HFSS a 5 GHz)
en el escalon y en la transicion gradual."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from campos_d2 import cargar, metricas_escalon, metricas_transicion, ancho_traza, W1, W2, L1, LT

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "axes.unicode_minus": True})
TXT1, TXT2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
C_ESC, C_TRA = "#eb6834", "#1baf7a"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)

rb = cargar("B_Escalon", "escalon")
rc = cargar("C_Transicion", "transicion")
mb = metricas_escalon(rb)
mb_ideal = mb.pop("ideal")
mc = metricas_transicion(rc)


def contorno(tipo, x0, x1):
    xs = np.linspace(x0, x1, 600)
    w = ancho_traza(xs, tipo)
    if tipo == "escalon":
        pts = [(x0, -W1 / 2), (L1, -W1 / 2), (L1, -W2 / 2), (x1, -W2 / 2),
               (x1, W2 / 2), (L1, W2 / 2), (L1, W1 / 2), (x0, W1 / 2)]
    else:
        pts = list(zip(xs, -w / 2)) + list(zip(xs[::-1], w[::-1] / 2))
    return pts


def mapa(ax, r, tipo, campo, x0, x1):
    if campo == "rho":
        im = ax.pcolormesh(r["X"], r["Y"], np.clip(r["S"], 0, 2.5), cmap="Oranges", vmin=0, vmax=2.5,
                           shading="auto", rasterized=True)
        ec = "#5a3a1a"
    else:
        im = ax.pcolormesh(r["X"], r["Y"], np.clip(r["JN"], 0, 4.0), cmap="Blues", vmin=0, vmax=4.0,
                           shading="auto", rasterized=True)
        ec = "#1b3a66"
        seeds = np.array([[x0 + 0.02, y] for y in np.linspace(-0.85, 0.85, 9) * W1 / 2])
        ax.streamplot(r["xs"], r["ys"], r["JXr"], r["JYr"], color=TXT1, linewidth=0.55, arrowsize=0.55,
                      start_points=seeds, density=4, broken_streamlines=False)
    pg = Polygon(contorno(tipo, x0, x1), closed=True, fill=False, ec=ec, lw=0.7)
    ax.add_patch(pg); im.set_clip_path(pg)
    ax.set_aspect("equal"); ax.set_xlim(x0, x1)
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    return im


def nota(ax, txt, xy, xytext, ha="left", va="center"):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=7.0, color=TXT1, ha=ha, va=va,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))


fig = plt.figure(figsize=(6.3, 7.3))
# ---- (a) escalon
xa0, xa1 = 4.0, 8.0
ax1 = fig.add_axes([0.05, 0.715, 0.445, 0.24]); ax2 = fig.add_axes([0.535, 0.715, 0.445, 0.24])
im_r = mapa(ax1, rb, "escalon", "rho", xa0, xa1)
im_j = mapa(ax2, rb, "escalon", "J", xa0, xa1)
for ax in (ax1, ax2):
    ax.set_ylim(-1.12, 1.15)
ax1.set_title("Densidad de carga superficial", fontsize=8.6)
ax2.set_title("Densidad de corriente superficial", fontsize=8.6)
nota(ax1, "hombros: %.1f×\nla carga de la\nlínea ancha" % mb["Chom"], (L1 - 0.04, W1 / 2 - 0.04), (6.45, 0.98))
nota(ax1, "línea angosta:\nmenos carga\njunto al escalón", (6.12, -0.1), (6.45, -0.8))
nota(ax2, "el %.0f %% de la\ncorriente ya va\npor el centro" % (100 * mb["Icentro"]), (L1 - 0.06, 0.0), (6.45, 0.9))
nota(ax2, "lejos del escalón: %.0f %%" % (100 * mb["Icentro_lejos"]), (4.35, 0.06), (4.1, -0.95))
ax1.text(-0.03, 0.5, "(a) Escalón", transform=ax1.transAxes, rotation=90, va="center", ha="right", fontsize=8.6)
for rect, im, lab in [([0.11, 0.69, 0.33, 0.011], im_r, r"$|\rho_s|/|\rho_{s}|_{\mathrm{l\acute{i}nea\ ancha}}$"),
                      ([0.595, 0.69, 0.33, 0.011], im_j, r"$|\mathbf{J}_s|/|\mathbf{J}_{s}|_{\mathrm{l\acute{i}nea\ ancha}}$")]:
    cax = fig.add_axes(rect)
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_label(lab, fontsize=7.4, labelpad=1); cb.ax.tick_params(labelsize=6.8, pad=1)
# ---- (b) transicion
xb0, xb1 = 5.0, 17.0
ax3 = fig.add_axes([0.05, 0.495, 0.93, 0.085]); ax4 = fig.add_axes([0.05, 0.395, 0.93, 0.085])
mapa(ax3, rc, "transicion", "rho", xb0, xb1)
mapa(ax4, rc, "transicion", "J", xb0, xb1)
for ax in (ax3, ax4):
    ax.set_ylim(-0.7, 0.7)
ax3.text(-0.01, 0.5, r"$|\rho_s|$", transform=ax3.transAxes, va="center", ha="right", fontsize=8)
ax4.text(-0.01, 0.5, r"$|\mathbf{J}_s|$", transform=ax4.transAxes, va="center", ha="right", fontsize=8)
ax3.set_title("(b) Transición gradual de 10 mm (mismas escalas de color)", fontsize=8.6, pad=3)
# ---- (c) perfiles a lo largo de la linea
ax5 = fig.add_axes([0.085, 0.06, 0.39, 0.25]); ax6 = fig.add_axes([0.59, 0.06, 0.39, 0.25])
xs = rb["xs"]; ref = np.mean(np.abs(rb["q"][rb["brazo"]]))
ax5.plot(xs - L1, np.abs(rb["q"]) / ref, color=C_ESC, lw=1.3, label="HFSS")
ax5.plot(xs - L1, np.abs(mb_ideal) / ref, color=TXT2, lw=0.9, ls="--", label="escalón ideal")
ax5.annotate("carga en exceso\n(hombros)", xy=(-0.03, 1.55), xytext=(0.35, 1.5), fontsize=7, color=TXT1,
             va="center", arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax5.annotate("déficit en la\nlínea angosta", xy=(0.06, 0.33), xytext=(0.5, 0.18), fontsize=7, color=TXT1,
             va="center", arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax5.set_xlim(-2, 2); ax5.set_ylim(0, 1.8)
ax5.set_ylabel(r"$|q(x)|\,/\,|q|_{\mathrm{l\acute{i}nea\ ancha}}$")
ax5.set_title("(c) Carga por unidad de longitud", fontsize=8.6, loc="left")
ax5.legend(fontsize=7, frameon=False, loc="upper left")
for r, col, lab in [(rb, C_ESC, "Escalón"), (rc, C_TRA, "Transición gradual")]:
    jx = np.abs(r["Jx"])
    cen = np.sum(np.where(r["m"] & (np.abs(r["Y"]) <= W2 / 2), jx, 0), axis=0)
    tot = np.sum(np.where(r["m"], jx, 0), axis=0)
    ax6.plot(r["xs"] - L1, 100 * cen / tot, color=col, lw=1.3, label=lab)
ax6.set_xlim(-2, 11.2); ax6.set_ylim(0, 105)
ax6.set_ylabel(r"corriente por $|y|<W_2/2$ (%)")
ax6.set_title("(d) Corriente por la franja central", fontsize=8.6, loc="left")
ax6.legend(fontsize=7, frameon=False, loc="lower right")
for ax in (ax5, ax6):
    ax.axvline(0, color=TXT2, lw=0.6, ls=":")
    ax.grid(True, color=GRID, lw=0.5)
    for s_ in ["top", "right"]:
        ax.spines[s_].set_visible(False)
    ax.set_xlabel(r"$x-L_1$ (mm)")
ax6.axvline(LT, color=TXT2, lw=0.6, ls=":")
fig.savefig(os.path.join(OUT, "fig_d2_carga_corriente.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig_d2_carga_corriente.png"), dpi=220)
json.dump(dict(escalon=mb, transicion=mc), open("d2_campos.json", "w"), indent=1)
print(mb, mc)
