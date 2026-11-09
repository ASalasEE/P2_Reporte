"""Discontinuidad 3 (gap): geometria y figuras de resultados (requiere d3_analisis.py)."""
import os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

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
# secuencial de un solo tono (azul) para las cinco separaciones, de oscuro (acoplado) a claro (abierto)
COLS = ["#0d3b7a", "#1f5fae", "#2a78d6", "#6fa6e6", "#a9c9f0"]
C_CG, C_CP = "#eb6834", "#2a78d6"
LW, W_IN = 1.4, 6.3
D = np.load("d3_datos.npz")
N = json.load(open("d3_nums.json"))
f = D["f"]; GAPS = list(D["gaps"])
ET = lambda s: ("%.1f" % s).replace(".", "p")
NOMB = {s: "B%d_Gap_%s" % (i + 1, ET(s)) for i, s in enumerate(GAPS)}
db = lambda x: 20 * np.log10(np.abs(x))
W, L1, Pw = 1.14, 6.0, 5 * 1.14


def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre + ".pdf"))
    fig.savefig(os.path.join(OUT, nombre + ".png"), dpi=220)
    plt.close(fig)


# ------------------- geometria -------------------
fig = plt.figure(figsize=(6.3, 2.35))
ax = fig.add_axes([0.0, 0.42, 1.0, 0.56])
s = 0.5
xm = 2 * L1 + s
ax.add_patch(Rectangle((0, -3.3), xm, 6.6, fc="#eef3e8", ec="none"))
for xa, xb in [(0, L1), (L1 + s, xm)]:
    ax.add_patch(Rectangle((xa, -W / 2), xb - xa, W, fc="#c8793a", ec="#8a4f1f", lw=0.6))
for x in (0, xm):
    ax.plot([x, x], [-Pw / 2, Pw / 2], color="#2a78d6", lw=2.6, solid_capstyle="butt")
for x in (L1, L1 + s):
    ax.plot([x, x], [-1.1, 1.1], color=TXT2, lw=0.9, ls=(0, (3, 2)))
ax.text(-0.3, 0, "P1", ha="right", va="center", color="#2a78d6", fontsize=8)
ax.text(xm + 0.3, 0, "P2", ha="left", va="center", color="#2a78d6", fontsize=8)
for x0, x1, t in [(0, L1, "$L_1$"), (L1 + s, xm, "$L_1$")]:
    ax.annotate("", xy=(x0, -2.0), xytext=(x1, -2.0), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
    ax.text(0.5 * (x0 + x1), -2.35, t, ha="center", va="top", fontsize=7.5, color=TXT2)
ax.annotate("$s$", xy=(L1 + s / 2, 0.62), xytext=(L1 + s / 2, 1.9), ha="center", fontsize=8, color=TXT1,
            arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax.text(L1 / 2, 0.75, r"$W=1.14$ mm (50 $\Omega$)", ha="center", va="bottom", fontsize=7.4, color=TXT2)
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.4, xm + 1.4); ax.set_ylim(-3.5, 3.5)
ax.set_title("(a) Estructura (ejemplo con $s=0.5$ mm; sustrato recortado)", fontsize=8.5)
# region del gap de los cinco disenos, en fila y a la misma escala
axz = fig.add_axes([0.02, 0.0, 0.96, 0.30])
x = 0.0
hh = W
for s_ in GAPS:
    axz.add_patch(Rectangle((x, -hh / 2), 0.9, hh, fc="#c8793a", ec="#8a4f1f", lw=0.5))
    axz.add_patch(Rectangle((x + 0.9 + s_, -hh / 2), 0.9, hh, fc="#c8793a", ec="#8a4f1f", lw=0.5))
    axz.text(x + 0.9 + s_ / 2, hh / 2 + 0.2, "$s=%g$ mm" % s_, ha="center", va="bottom", fontsize=7.4, color=TXT1)
    x += 1.8 + s_ + 0.9
axz.set_xlim(-0.2, x - 0.7); axz.set_ylim(-hh / 2 - 0.1, hh / 2 + 0.75)
axz.set_aspect("equal"); axz.axis("off")
fig.text(0.5, 0.375, "(b) Región del gap de los cinco diseños (vista superior, misma escala)", ha="center", fontsize=8.5)
guardar(fig, "fig_d3_geometria")

# ------------------- |S21| (log f) y fase de S11 -------------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 3.0), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
for s_, col in zip(GAPS, COLS):
    ax.semilogx(f, db(D["%s_S21" % NOMB[s_]]), color=col, lw=LW, label="$s=%g$ mm" % s_)
ff = np.array([1, 10])
ax.semilogx(ff, -33.3 + 20 * np.log10(ff), color=TXT2, lw=0.8, ls=":")
ax.text(1.6, -24, "20 dB/década", fontsize=7, color=TXT2, rotation=27)
ax.axhline(-10, color=TXT2, lw=0.7, ls=(0, (5, 3)))
ax.text(0.5, -9.2, r"$-10$ dB (10 % transmitido)", fontsize=6.8, color=TXT2)
ax.set_xlim(0.1, 20); ax.set_ylim(-90, 0)
ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 5, 10, 20]); ax.set_xticklabels(["0.1", "0.2", "0.5", "1", "2", "5", "10", "20"])
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$|S_{21}|$ (dB)")
ax.legend(loc="lower right", fontsize=7)
ax.text(0.02, 0.04, "(a)", transform=ax.transAxes, va="bottom")
ax = axs[1]
for s_, col in zip(GAPS, COLS):
    ax.plot(f, np.degrees(np.angle(D["%s_S11" % NOMB[s_]])), color=col, lw=LW)
Z1 = D["Z1"]
wv = 2 * np.pi * f * 1e9
ax.plot(f, -2 * np.degrees(np.arctan(wv * float(D["Coc"]) * Z1)), color=TXT2, lw=0.8, ls=":")
ax.text(19.5, -2 * np.degrees(np.arctan(wv[-1] * float(D["Coc"]) * Z1[-1])) + 2.5, "extremo abierto\n(Hammerstad)",
        ha="right", va="bottom", fontsize=6.8, color=TXT2)
ax.axhline(0, color=TXT2, lw=0.6)
ax.text(0.3, 2, "circuito abierto ideal", fontsize=6.8, color=TXT2)
ax.set_xlim(0, 20); ax.set_xticks(np.arange(0, 21, 5)); ax.set_ylim(-32, 5)
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$\angle S_{11}$ (°)")
ax.text(0.03, 0.04, "(b)", transform=ax.transAxes, va="bottom")
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d3_S")

# ------------------- capacitancias -------------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.9), gridspec_kw=dict(width_ratios=[1.2, 1]))
ax = axs[0]
sv = np.array(GAPS)
Cg, Cp, eCg, eCp = D["Cg"] * 1e15, D["Cp"] * 1e15, D["eCg"] * 1e15, D["eCp"] * 1e15
mcg = Cg > 1
ax.errorbar(sv[mcg], Cg[mcg], yerr=eCg[mcg], color=C_CG, marker="o", ms=4.5, lw=LW, capsize=2.5, label=r"$C_g$ HFSS")
ax.errorbar(sv, Cp, yerr=eCp, color=C_CP, marker="s", ms=4.5, lw=LW, capsize=2.5, label=r"$C_p$ HFSS")
ax.plot(sv, Cg * mcg + Cp * 1, color=TXT2, marker="^", ms=4, lw=0.9, ls="--", label=r"$C_g+C_p$")
sg = np.logspace(np.log10(0.114), np.log10(1.14), 60)
# formulas cerradas (misma rutina que en d3_analisis.py, sin volver a leer los CSV)
wh, ER = 1.14 / 0.508, 3.55
def gb(s):
    r = s / 1.14
    mo = wh * (0.619 * math.log10(wh) - 0.3853); ko = 4.26 - 1.453 * math.log10(wh)
    me, ke = ((0.8675, 2.043 * wh ** 0.12) if r <= 0.3 else (1.565 / wh ** 0.16 - 1, 1.97 - 0.03 / wh))
    Co = (ER / 9.6) ** 0.8 * r ** mo * math.exp(ko) * 1.14
    Ce = 12 * (ER / 9.6) ** 0.9 * r ** me * math.exp(ke) * 1.14
    return 0.5 * Co - 0.25 * Ce, 0.5 * Ce
gbv = np.array([gb(x) for x in sg])
ax.plot(sg, gbv[:, 0], color=C_CG, lw=0.9, ls=":")
ax.plot(sg, gbv[:, 1], color=C_CP, lw=0.9, ls=":")
ax.plot([], [], color=TXT2, lw=0.9, ls=":", label="Garg y Bahl ($0.1\\leq s/W\\leq 1$)")
ax.axhline(float(D["Coc"]) * 1e15, color=C_CP, lw=0.7, ls=(0, (5, 3)))
ax.text(0.105, float(D["Coc"]) * 1e15 + 1.0, "extremo abierto (Hammerstad)", fontsize=6.8, color=C_CP)
ax.set_xscale("log"); ax.set_xlim(0.09, 3.5); ax.set_ylim(0, 45)
ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 3]); ax.set_xticklabels(["0.1", "0.2", "0.5", "1", "2", "3"])
ax.set_xlabel("Separación $s$ (mm)"); ax.set_ylabel("Capacitancia (fF)")
ax.legend(loc="upper right", fontsize=6.8)
ax.text(0.02, 0.97, "(a)", transform=ax.transAxes, va="top")
ax = axs[1]
m = f >= 2
for s_, col in zip(GAPS[:4], COLS[:4]):
    ax.plot(f[m], D["Cg_%s" % NOMB[s_]][m] * 1e15, color=col, lw=LW, label="$s=%g$ mm" % s_)
    ax.plot(f[m], D["Cp_%s" % NOMB[s_]][m] * 1e15, color=col, lw=1.0, ls="--")
ax.axvspan(3, 15, color="#f0efeb", lw=0, zorder=0)
ax.text(9, 41.5, "banda promediada", ha="center", fontsize=6.8, color=TXT2)
ax.set_xlim(2, 20); ax.set_ylim(0, 45); ax.set_xticks([2, 5, 10, 15, 20])
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$C_g$ (continua), $C_p$ (discontinua) (fF)")
ax.legend(loc="lower center", fontsize=6.6, bbox_to_anchor=(0.5, 1.0), ncol=2)
ax.text(0.97, 0.97, "(b)", transform=ax.transAxes, va="top", ha="right")
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d3_capacitancias")

# ------------------- potencia -------------------
PISO = float(D["piso"]) * 100
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.9), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
ax.axhspan(-PISO, PISO, color="#e9e8e4", lw=0, zorder=0)
for s_, col in zip(GAPS, COLS):
    ax.plot(f, 100 * D["Prad_%s" % ET(s_)], color=col, lw=LW, label="$s=%g$ mm" % s_)
ax.text(19.6, -PISO + 0.08, r"incertidumbre ($\pm$%.1f %%)" % PISO, fontsize=6.6, color=TXT2, ha="right", va="bottom")
ax.set_xlim(0, 20); ax.set_xticks(np.arange(0, 21, 5)); ax.set_ylim(-1, 6)
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel("Potencia radiada (%)")
ax.legend(loc="upper left", fontsize=6.8)
ax.text(0.55, 0.97, "(a)", transform=ax.transAxes, va="top")
ax = axs[1]
ax.grid(False)
COMP = [("Transmitida", "#1baf7a"), ("Radiada", "#eda100"), ("Disipada", "#e87ba4")]
filas = []
for s_ in [0.1, 1.0, 3.0]:
    for q in [5, 10, 20]:
        i = int(np.argmin(np.abs(f - q)))
        n = NOMB[s_]
        filas.append(("$s=%g$ mm, %d GHz" % (s_, q),
                      [100 * abs(D["%s_S21" % n][i]) ** 2, max(100 * D["Prad_%s" % ET(s_)][i], 0),
                       max(100 * D["Pdis_%s" % ET(s_)][i], 0)]))
ys = np.arange(len(filas))[::-1]
for y, (lab, vals) in zip(ys, filas):
    x0 = 0
    for (cn, col), v in zip(COMP, vals):
        ax.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=1.0)
        if v >= 1.8:
            ax.text(x0 + v / 2, y, "%.1f" % v, ha="center", va="center", fontsize=6.4, color=TXT1)
        x0 += v
    ax.text(x0 + 0.3, y, "%.1f %%" % x0, va="center", fontsize=6.6, color=TXT2)
ax.set_yticks(ys); ax.set_yticklabels([l for l, _ in filas], fontsize=7)
ax.set_xlabel("Potencia que no se refleja (%)")
ax.set_xlim(0, 24)
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0); ax.xaxis.grid(True)
ax.legend(handles=[Patch(color=c, label=n) for n, c in COMP], loc="lower right", fontsize=6.8)
ax.text(0.98, 0.99, "(b)", transform=ax.transAxes, va="top", ha="right")
fig.tight_layout(w_pad=1.2)
guardar(fig, "fig_d3_potencia")
print("ok")
