"""Discontinuidad 5 (union en T): geometria y figuras de resultados
(requiere d5_analisis.py)."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Polygon

OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
for p in ["/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf",
          "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-italic.otf"]:
    if os.path.exists(p):
        fm.fontManager.addfont(p)
TXT1, TXT2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
plt.rcParams.update({
    "font.family": "Latin Modern Roman", "mathtext.fontset": "cm",
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.edgecolor": TXT2, "axes.labelcolor": TXT1, "xtick.color": TXT2,
    "ytick.color": TXT2, "text.color": TXT1, "axes.linewidth": 0.6,
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.grid": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "legend.frameon": False, "axes.unicode_minus": True,
})
C11, C21, C31, C33 = "#eb6834", "#2a78d6", "#1baf7a", "#8a63d2"
CU, SUB = "#c8793a", "#eef3e8"
LW, W_IN = 1.4, 6.3
D = np.load("d5_datos.npz")
N = json.load(open("d5_nums.json"))
f = D["f"]
db = lambda x: 20 * np.log10(np.abs(x))
W1, W2, L1, LS = 1.14, 0.29, 6.0, 8.0


def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre + ".pdf"))
    fig.savefig(os.path.join(OUT, nombre + ".png"), dpi=220)
    plt.close(fig)


# ------------------- geometria -------------------
fig = plt.figure(figsize=(W_IN, 2.75))
casos = [("(a) T de 50 $\\Omega$", W1, W1, L1, True), ("(b) Divisor en T", W2, W1, L1, True),
         ("(c) Stub abierto", W1, W1, LS, False)]
for k, (tit, wb, ws, lr, puerto3) in enumerate(casos):
    ax = fig.add_axes([0.0 + k * 0.335, 0.1, 0.32, 0.82])
    xm = 2 * L1 + ws
    ytop = wb / 2 + lr
    ax.add_patch(Rectangle((0, -3.2), xm, ytop + 3.2 + (0 if puerto3 else 1.2), fc=SUB, ec="none"))
    pts = [(0, -wb / 2), (xm, -wb / 2), (xm, wb / 2), (L1 + ws, wb / 2), (L1 + ws, ytop), (L1, ytop), (L1, wb / 2), (0, wb / 2)]
    ax.add_patch(Polygon(pts, closed=True, fc=CU, ec="#8a4f1f", lw=0.5))
    for x in (0, xm):
        ax.plot([x, x], [-2.85, 2.85], color="#2a78d6", lw=2.4, solid_capstyle="butt")
    ax.text(-0.25, -2.5, "P1", ha="right", va="center", color="#2a78d6", fontsize=7.6)
    ax.text(xm + 0.25, -2.5, "P2", ha="left", va="center", color="#2a78d6", fontsize=7.6)
    if puerto3:
        ax.plot([L1 + ws / 2 - 2.85, L1 + ws / 2 + 2.85], [ytop, ytop], color="#2a78d6", lw=2.4, solid_capstyle="butt")
        ax.text(L1 + ws / 2 + 3.0, ytop, "P3", ha="left", va="center", color="#2a78d6", fontsize=7.6)
    else:
        ax.text(L1 + ws + 0.3, ytop - 0.3, "abierto", ha="left", va="top", fontsize=7, color=TXT2)
    # planos de referencia
    for xx in (L1, L1 + ws):
        ax.plot([xx, xx], [-1.6, -wb / 2], color=TXT2, lw=0.7, ls=(0, (2, 1.5)))
    if puerto3:
        ax.plot([L1 - 1.0, L1], [wb / 2, wb / 2], color=TXT2, lw=0.7, ls=(0, (2, 1.5)))
    ax.annotate("", xy=(0, -1.9), xytext=(L1, -1.9), arrowprops=dict(arrowstyle="<->", lw=0.5, color=TXT2))
    ax.text(L1 / 2, -2.05, "$L_1$", ha="center", va="top", fontsize=7, color=TXT2)
    ax.text(L1 + ws + 0.25, wb / 2 + lr / 2, ("$L_1$" if puerto3 else "8 mm"), ha="left", va="center", fontsize=7, color=TXT2)
    lab = "1.14 mm" if wb > 1 else "0.29 mm\n(100 $\\Omega$)"
    ax.text(xm - 0.2, wb / 2 + 0.25, lab, ha="right", va="bottom", fontsize=6.6, color=TXT2)
    ax.set_xlim(-1.2, xm + 1.2); ax.set_ylim(-3.3, 9.0)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(tit, fontsize=8.5)
fig.text(0.5, 0.06, "Líneas punteadas: planos de referencia (bordes del cuadro de unión). Sustrato recortado.",
         ha="center", fontsize=7.2, color=TXT2)
guardar(fig, "fig_d5_geometria")

# ------------------- T de 50 ohm -------------------
SB, SB0 = D["B_T_S"], D["B_T_SinPerd_S"]
SH, SI = D["ham_B_T"], D["ideal_B_T"]
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 3.2), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
for (i, j), col, lab in [((0, 0), C11, "$|S_{11}|$"), ((1, 0), C21, "$|S_{21}|$ (brazo recto)"),
                         ((2, 0), C31, "$|S_{31}|$ (rama)"), ((2, 2), C33, "$|S_{33}|$")]:
    ax.plot(f, np.abs(SB[i, j]), color=col, lw=LW, label=lab)
    ax.plot(f, np.abs(SH[i, j]), color=col, lw=0.9, ls=":")
ax.axhline(1 / 3, color=TXT2, lw=0.8, ls="--"); ax.axhline(2 / 3, color=TXT2, lw=0.8, ls="--")
ax.text(0.3, 1 / 3 - 0.025, "ideal: 1/3", fontsize=6.8, color=TXT2, va="top")
ax.text(0.3, 2 / 3 + 0.015, "ideal: 2/3", fontsize=6.8, color=TXT2, va="bottom")
ax.plot([], [], color=TXT2, lw=0.9, ls=":", label="Hammerstad")
ax.set_xlim(0, 20); ax.set_ylim(0.2, 0.8); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel("Magnitud")
ax.legend(loc="center left", fontsize=6.8, bbox_to_anchor=(0.0, 0.5))
ax.text(0.97, 0.96, "(a)", transform=ax.transAxes, ha="right", va="top")
ax = axs[1]
pr = {"refl": np.abs(SB[0, 0]) ** 2, "rec": np.abs(SB[1, 0]) ** 2, "rama": np.abs(SB[2, 0]) ** 2}
ax.plot(f, 100 * pr["rec"], color=C21, lw=LW, label="al brazo recto")
ax.plot(f, 100 * pr["rama"], color=C31, lw=LW, label="a la rama")
ax.plot(f, 100 * pr["refl"], color=C11, lw=LW, label="reflejada")
ax.plot(f, 100 * D["Prad_B1"], color=TXT2, lw=1.0, label="radiada (sin pérdidas)")
piso = 100 * float(D["piso"])
ax.fill_between(f, -piso, piso, color="#e9e9e5", lw=0, zorder=0)
ax.axhline(100 * 4 / 9, color=TXT2, lw=0.7, ls="--")
ax.text(0.3, 100 * 4 / 9 + 1.0, "ideal: 4/9", fontsize=6.8, color=TXT2)
ax.set_xlim(0, 20); ax.set_ylim(-2, 60); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel("Potencia incidente por P1 (%)")
ax.legend(loc="center right", fontsize=6.8, bbox_to_anchor=(1.0, 0.33))
ax.text(0.03, 0.96, "(b)", transform=ax.transAxes, va="top")
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d5_T")

# ------------------- divisor y capacitancia en exceso -------------------
SC = D["C_Divisor_S"]
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.9), gridspec_kw=dict(width_ratios=[1.1, 1]))
ax = axs[0]
ax.plot(f, db(SC[2, 2]), color=C33, lw=LW, label="HFSS")
ax.plot(f, db(D["ham_C_Divisor"][2, 2]), color=C33, lw=0.9, ls=":", label="Hammerstad")
ax.axhline(-20, color=TXT2, lw=0.7, ls=(0, (5, 3)))
ax.text(0.3, -19.2, "$-20$ dB", fontsize=6.8, color=TXT2)
ax.set_xlim(0, 20); ax.set_ylim(-60, -10); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$|S_{33}|$ (dB), entrada por la rama")
ax.legend(loc="lower right", fontsize=6.8)
ax.text(0.03, 0.96, "(a)", transform=ax.transAxes, va="top")
ax = axs[1]
m = f >= 1
for d, col, lab in [("B_T", C11, "T de 50 $\\Omega$"), ("C_Divisor", C33, "divisor")]:
    ax.plot(f[m], D["CE_" + d][m] * 1e15, color=col, lw=LW, label=lab + " (HFSS)")
    ax.plot(f[m], D["CE_" + d + "_SinPerd"][m] * 1e15, color=col, lw=0.8, ls=(0, (4, 2)))
    ax.plot(f[m], D["hamCE_" + d][m] * 1e15, color=col, lw=0.9, ls=":")
ax.axhline(float(N["CW"]), color=TXT2, lw=0.7, ls="--")
ax.text(19.8, float(N["CW"]) + 2, r"$C'W$ de la línea de 50 $\Omega$", fontsize=6.6, color=TXT2, ha="right")
ax.plot([], [], color=TXT2, lw=0.8, ls=(0, (4, 2)), label="gemelo sin pérdidas")
ax.plot([], [], color=TXT2, lw=0.9, ls=":", label="Hammerstad")
ax.set_xlim(0, 20); ax.set_ylim(0, 140); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel("Capacitancia en exceso (fF)")
ax.legend(loc="upper right", fontsize=6.4, ncol=1, bbox_to_anchor=(1.0, 0.86))
ax.text(0.03, 0.96, "(b)", transform=ax.transAxes, ha="left", va="top")
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d5_divisor")

# ------------------- stub abierto -------------------
SD, SD0 = D["D_Stub_S"], D["D_Stub_SinPerd_S"]
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 3.0), gridspec_kw=dict(width_ratios=[1.3, 1]))
ax = axs[0]
ax.plot(f, db(SD[1, 0]), color=C21, lw=LW, label="$|S_{21}|$ HFSS")
ax.plot(f, db(D["pred21_d3"]), color=C21, lw=0.9, ls="--", label="$|S_{21}|$ predicho")
ax.plot(f, db(SD[0, 0]), color=C11, lw=LW, label="$|S_{11}|$ HFSS")
ax.plot(f, db(D["pred11_d3"]), color=C11, lw=0.9, ls="--", label="$|S_{11}|$ predicho")
for fq, lab in [(float(N["FN1"]), r"$\lambda_g/4$"), (float(N["FN2"]), r"$3\lambda_g/4$")]:
    ax.axvline(fq, color=TXT2, lw=0.6, ls=":")
    ax.text(fq + 0.2, -42, lab, fontsize=7.2, color=TXT2)
ax.set_xlim(0, 20); ax.set_ylim(-45, 2); ax.set_xticks(np.arange(0, 21, 2))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel("dB")
ax.legend(loc="lower right", fontsize=6.6, bbox_to_anchor=(1.0, 0.08))
ax.text(0.02, 0.04, "(a)", transform=ax.transAxes, va="bottom")
ax = axs[1]
ax.plot(f, 100 * D["Prad_D"], color=TXT1, lw=LW, label="stub (sin pérdidas)")
ax.plot(f, 100 * D["Prad_B1"], color=C21, lw=1.0, label="T de 50 $\\Omega$, desde P1")
ax.fill_between(f, -piso, piso, color="#e9e9e5", lw=0, zorder=0)
for fq in (float(N["FN1"]), float(N["FN2"])):
    ax.axvline(fq, color=TXT2, lw=0.6, ls=":")
ax.set_xlim(0, 20); ax.set_ylim(-1.5, 8); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel("Potencia radiada (%)")
ax.legend(loc="upper left", fontsize=6.8)
ax.text(0.97, 0.04, "(b)", transform=ax.transAxes, ha="right", va="bottom")
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d5_stub")
print("ok")
