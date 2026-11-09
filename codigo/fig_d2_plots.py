"""Discontinuidad 2: figuras de resultados (requiere correr antes d2_analisis.py)."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
for p in ["/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf",
          "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-bold.otf",
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
C_REF, C_ESC, C_TRA = "#2a78d6", "#eb6834", "#1baf7a"
LW, W_IN = 1.4, 6.3

D = np.load("d2_datos.npz")
N = json.load(open("d2_nums.json"))
f = D["f"]
B, B0, C, Ct0 = "B_Escalon", "B0_Escalon_SinPerd", "C_Transicion", "C0_Transicion_SinPerd"
S = lambda d, q: D["%s_%s" % (d, q)]
RAW = lambda d, q: D["raw_%s_%s" % (d, q)]
db = lambda x: 20 * np.log10(np.abs(x))
G0Q, GT0, EEM = float(N["G0Q"]), float(N["GT0"]), float(N["EEM"])
bl = 2 * np.pi * f * 1e9 / 299792458.0 * np.sqrt(EEM) * 10e-3
Gteo = GT0 * np.abs(np.sinc(bl / np.pi))


def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre + ".pdf"))
    fig.savefig(os.path.join(OUT, nombre + ".png"), dpi=220)
    plt.close(fig)


def eje_f(ax, paso=2.5):
    ax.set_xlim(0, 20)
    ax.set_xticks(np.arange(0, 21, paso))
    ax.set_xlabel("Frecuencia (GHz)")


def etiqueta(ax, t, x=0.02, y=0.97, ha="left", va="top"):
    ax.text(x, y, t, transform=ax.transAxes, va=va, ha=ha, fontsize=8.5)


# ------------- correccion del error de puerto -------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.8))
ax = axs[0]
for k, col, lab, gk in [("A1_Ref50_SinPerd", C_REF, r"línea de 50 $\Omega$", "gfit50"),
                        ("A2_Ref100_SinPerd", "#6250d6", r"línea de 100 $\Omega$", "gfit100")]:
    ax.plot(f, np.abs(RAW(k, "S11")), color=col, lw=LW, label=lab)
    ax.plot(f, np.abs(D[gk]), color=TXT1, lw=0.8, ls=(0, (2, 1.5)))
ax.plot([], [], color=TXT1, lw=0.8, ls=(0, (2, 1.5)), label=r"modelo $g\,(e^{2j\beta L_1}-e^{-2j\beta L_1})$")
ax.set_ylabel(r"$|S_{11}|$ de la referencia")
ax.set_ylim(0, 0.03)
eje_f(ax, 5)
ax.legend(loc="upper right", fontsize=7)
etiqueta(ax, "(a)")
ax = axs[1]
ax.plot(f, np.abs(RAW(B0, "S11")), color=C_ESC, lw=0.9, alpha=0.45)
ax.plot(f, np.abs(RAW(B0, "S22")), color=C_ESC, lw=0.9, alpha=0.45, ls="--")
ax.plot(f, np.abs(S(B0, "S11")), color=C_ESC, lw=LW, label=r"$|S_{11}|$")
ax.plot(f, np.abs(S(B0, "S22")), color=C_ESC, lw=LW, ls="--", label=r"$|S_{22}|$")
ax.plot([], [], color=C_ESC, lw=0.9, alpha=0.45, label="sin corregir (tenue)")
ax.set_ylabel(r"Escalón sin pérdidas")
ax.set_ylim(0.31, 0.34)
eje_f(ax, 5)
ax.legend(loc="lower left", fontsize=7)
etiqueta(ax, "(b)", x=0.98, ha="right")
fig.tight_layout(w_pad=2.0)
guardar(fig, "fig_d2_correccion")

# ------------- |S11|, |S22| y |S21| en dB -------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 3.0), gridspec_kw=dict(width_ratios=[1.35, 1]))
ax = axs[0]
ax.plot(f, db(S(B, "S11")), color=C_ESC, lw=LW, label=r"Escalón, $|S_{11}|$")
ax.plot(f, db(S(B, "S22")), color=C_ESC, lw=1.0, ls="--", label=r"Escalón, $|S_{22}|$")
ax.plot(f, db(S(C, "S11")), color=C_TRA, lw=LW, ls="-.", label=r"Transición, $|S_{11}|$")
ax.axhline(20 * np.log10(G0Q), color=TXT2, lw=0.8, ls=":")
ax.text(19.8, 20 * np.log10(G0Q) + 1.0, r"escalón ideal $(Z_2-Z_1)/(Z_2+Z_1)$", ha="right", fontsize=6.8, color=TXT2)
ax.plot(f, db(np.maximum(Gteo, 1e-4)), color=TXT2, lw=0.7, ls=(0, (1, 1.2)))
ax.text(13.3, -44, "teoría de la\ntransición exponencial", fontsize=6.8, color=TXT2, ha="center")
ax.axhline(-20, color=TXT2, lw=0.8, ls=(0, (5, 3)))
ax.text(0.3, -19.0, r"umbral $-20$ dB", fontsize=6.8, color=TXT2)
fc = float(N["FT20"])
ax.plot([fc], [-20], marker="o", ms=5, mfc="white", mec=C_TRA, mew=1.4, zorder=5)
ax.annotate("%.2f GHz" % fc, xy=(fc, -20), xytext=(fc - 4.6, -27.5), fontsize=7.2, color=TXT1,
            arrowprops=dict(arrowstyle="-", color=TXT2, lw=0.6))
ax.set_ylim(-50, 0)
ax.set_ylabel("Reflexión (dB)")
eje_f(ax, 5)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7)
etiqueta(ax, "(a)", y=0.99)
ax = axs[1]
ax.plot(f, db(S(B, "S21")), color=C_ESC, lw=LW, label="Escalón")
ax.plot(f, db(S(C, "S21")), color=C_TRA, lw=LW, ls="-.", label="Transición")
ax.axhline(10 * np.log10(1 - G0Q ** 2), color=TXT2, lw=0.8, ls=":")
ax.text(19.6, 10 * np.log10(1 - G0Q ** 2) - 0.03, r"$10\log_{10}(1-|\Gamma_0|^2)$", ha="right", va="top",
        fontsize=6.8, color=TXT2)
ax.set_ylim(-0.7, 0.02)
ax.set_ylabel(r"$|S_{21}|$ (dB)")
eje_f(ax, 5)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7)
etiqueta(ax, "(b)", x=0.97, y=0.99, ha="right")
fig.tight_layout(w_pad=1.6)
guardar(fig, "fig_d2_S_dB")

# ------------- |Gamma| y VSWR -------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.7))
for ax, fun in zip(axs, [lambda g: g, lambda g: (1 + g) / (1 - g)]):
    ax.plot(f, fun(np.abs(S(B, "S11"))), color=C_ESC, lw=LW, label="Escalón")
    ax.plot(f, fun(np.abs(S(C, "S11"))), color=C_TRA, lw=LW, ls="-.", label="Transición gradual")
    ax.axhline(fun(G0Q), color=TXT2, lw=0.8, ls=":")
    eje_f(ax, 5)
axs[0].plot(f, Gteo, color=TXT2, lw=0.7, ls=(0, (1, 1.2)), label="teoría (exponencial)")
axs[0].set_ylabel(r"$|\Gamma|$"); axs[0].set_ylim(0, 0.36)
axs[0].text(19.8, G0Q + 0.008, r"$\Gamma_0=%.3f$" % G0Q, ha="right", fontsize=6.8, color=TXT2)
axs[1].set_ylabel("VSWR"); axs[1].set_ylim(1, 2.1)
axs[1].text(19.8, (1 + G0Q) / (1 - G0Q) + 0.02, "ideal %.2f" % ((1 + G0Q) / (1 - G0Q)), ha="right", fontsize=6.8, color=TXT2)
axs[0].legend(loc="center right", fontsize=7)
etiqueta(axs[0], "(a)", x=0.03, y=0.08, va="bottom")
etiqueta(axs[1], "(b)", x=0.03, y=0.08, va="bottom")
fig.tight_layout(w_pad=2.0)
guardar(fig, "fig_d2_Gamma_VSWR")

# ------------- carta de Smith -------------
fig, ax = plt.subplots(figsize=(3.7, 3.7))
ax.set_aspect("equal"); ax.grid(False)
for s_ in ax.spines.values():
    s_.set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
th = np.linspace(0, 2 * np.pi, 721)
gcol = "#c9c9c4"
ax.plot(np.cos(th), np.sin(th), color=TXT2, lw=0.7)
rr = np.logspace(-3, 3, 800)
for r in [0.2, 0.5, 1.0, 2.0, 5.0]:
    z = r + 1j * np.concatenate([-rr[::-1], rr])
    G = (z - 1) / (z + 1)
    ax.plot(G.real, G.imag, color=gcol, lw=0.5)
for xv in [0.2, 0.5, 1.0, 2.0, 5.0]:
    for sg in (1, -1):
        z = np.concatenate([[1j * sg * xv], rr + 1j * sg * xv])
        G = (z - 1) / (z + 1)
        ax.plot(G.real, G.imag, color=gcol, lw=0.5)
ax.plot([-1, 1], [0, 0], color=gcol, lw=0.5)
for r in [0.5, 2.0]:
    x0 = (r - 1) / (r + 1)
    ax.text(x0 + 0.01, -0.015, "%g" % r, fontsize=6.5, color=TXT2, va="top")
ax.plot(S(C, "S11").real, S(C, "S11").imag, color=C_TRA, lw=1.1, ls="-.", label=r"Transición, $S_{11}$")
ax.plot(S(B, "S11").real, S(B, "S11").imag, color=C_ESC, lw=2.2, label=r"Escalón, $S_{11}$ (ve 100 $\Omega$)")
ax.plot(S(B, "S22").real, S(B, "S22").imag, color=C_ESC, lw=2.2, ls=(0, (1.5, 1)), label=r"Escalón, $S_{22}$ (ve 50 $\Omega$)")
for fq in [1, 5, 10]:
    i = np.argmin(np.abs(f - fq))
    s = S(C, "S11")[i]
    ax.plot(s.real, s.imag, "o", ms=3.2, mfc="white", mec=C_TRA, mew=1.0, zorder=6)
    ax.annotate("%d GHz" % fq, xy=(s.real, s.imag), xytext=(s.real + 0.03, s.imag + 0.03), fontsize=6.6, color=TXT1)
ax.set_xlim(-0.55, 0.55); ax.set_ylim(-0.55, 0.55)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.0), fontsize=7, ncol=1)
ax.set_title(r"Carta de Smith (zoom $|\Gamma|\leq 0.55$), 0.1 a 20 GHz", fontsize=8.5)
guardar(fig, "fig_d2_Smith")

# ------------- fase y reactancia parasita -------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.9))
ax = axs[0]
for d, a in [(B, 1.0), (B0, 0.55)]:
    ax.plot(f, np.degrees(np.angle(S(d, "S11"))), color=C_ESC, lw=LW, alpha=a)
    ax.plot(f, np.degrees(np.angle(-S(d, "S22"))), color="#6250d6", lw=LW, alpha=a)
ax.plot(f, np.degrees(np.angle(D["S11m"])), color=TXT1, lw=0.8, ls="--")
ax.plot(f, np.degrees(np.angle(-D["S22m"])), color=TXT1, lw=0.8, ls="--")
ax.plot(f, np.degrees(np.angle(D["S11g"])), color=TXT2, lw=0.8, ls=":")
ax.text(11.0, -9.3, r"$\angle S_{11}$ (desde 50 $\Omega$)", ha="left", fontsize=7, color=C_ESC)
ax.text(19.7, 1.6, r"$\angle(-S_{22})$ (desde 100 $\Omega$)", ha="right", fontsize=7, color="#6250d6")
ax.plot([], [], color=TXT2, lw=LW, label="HFSS (tenue: sin pérdidas)")
ax.plot([], [], color=TXT1, lw=0.8, ls="--", label="circuito ajustado")
ax.plot([], [], color=TXT2, lw=0.8, ls=":", label="Gupta et al.")
ax.set_ylim(-10, 3)
ax.set_ylabel("Fase respecto al escalón ideal (°)")
eje_f(ax, 5)
ax.legend(loc="lower left", fontsize=6.8, bbox_to_anchor=(0.0, 0.08))
etiqueta(ax, "(a)", x=0.03, y=0.97)
ax = axs[1]
w = 2 * np.pi * f * 1e9
for d, a in [(B, 1.0), (B0, 0.55)]:
    s11, s22 = S(d, "S11"), S(d, "S22")
    Zi1 = D["Z1"] * (1 + s11) / (1 - s11)
    Zi2 = D["Z2"] * (1 + s22) / (1 - s22)
    ax.plot(f, Zi1.imag, color=C_ESC, lw=LW, alpha=a)
    ax.plot(f, Zi2.imag, color="#6250d6", lw=LW, alpha=a)
X1, X2 = float(N["X1"]), float(N["X2"])
ax.plot(f, w * X1 * 1e-12, color=TXT1, lw=0.8, ls="--")
ax.plot(f, w * X2 * 1e-12, color=TXT1, lw=0.8, ls="--")
ax.text(11.0, -9.3, r"$\omega(L_s-CZ_2^2)$", ha="left", fontsize=7, color=C_ESC)
ax.text(19.6, 1.0, r"$\omega(L_s-CZ_1^2)$", ha="right", fontsize=7, color="#6250d6")
ax.set_ylim(-10, 3)
ax.set_ylabel(r"Reactancia vista en el escalón ($\Omega$)")
eje_f(ax, 5)
etiqueta(ax, "(b)", x=0.03, y=0.04, va="bottom")
fig.tight_layout(w_pad=1.8)
guardar(fig, "fig_d2_fase_reactancia")

# ------------- potencia -------------
PISO = float(N["PISO2"])
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.9), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
ax.axhspan(-PISO, PISO, color="#e9e8e4", lw=0, zorder=0)
ax.plot(f, 100 * D["PradB"], color=C_ESC, lw=LW, label="Radiada, escalón")
ax.plot(f, 100 * D["PradC"], color=C_TRA, lw=LW, ls="-.", label="Radiada, transición")
ax.plot(f, 100 * D["PdisC"], color="#e87ba4", lw=LW, label="Disipada, transición")
ax.plot(f, 100 * D["PdisLin"], color=TXT2, lw=0.8, ls=":", label=r"$1-e^{-2\bar\alpha L_t}$ (atenuación de las líneas)")
ax.text(0.4, -PISO + 0.05, r"incertidumbre ($\pm$%.1f %%)" % PISO, fontsize=6.6, color=TXT2, va="bottom")
ax.set_ylabel("Potencia (%)")
ax.set_ylim(-0.6, 4)
eje_f(ax, 5)
ax.legend(loc="upper left", fontsize=6.7)
etiqueta(ax, "(a)", x=0.98, y=0.04, ha="right", va="bottom")
ax = axs[1]
ax.grid(False)
COMP = [("Reflejada", "#6250d6"), ("Radiada", "#eda100"), ("Disipada", "#e87ba4")]
filas = []
for d, d0, nom in [(B, B0, "Escalón"), (C, Ct0, "Transición")]:
    k = "B" if d == B else "C"
    for fq in [2, 10, 20]:
        i = np.argmin(np.abs(f - fq))
        refl = 100 * 0.5 * (abs(S(d, "S11")[i]) ** 2 + abs(S(d, "S22")[i]) ** 2)
        filas.append(("%s, %d GHz" % (nom, fq), [refl, max(100 * D["Prad" + k][i], 0), max(100 * D["Pdis" + k][i], 0)]))
ys = np.arange(len(filas))[::-1]
for y, (lab, vals) in zip(ys, filas):
    x0 = 0
    for (cn, col), v in zip(COMP, vals):
        ax.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=1.0)
        if v >= 1.5:
            ax.text(x0 + v / 2, y, "%.1f" % v, ha="center", va="center", fontsize=6.6,
                    color="white" if col == "#6250d6" else TXT1)
        x0 += v
    ax.text(x0 + 0.25, y, "%.1f %%" % x0, va="center", fontsize=6.8, color=TXT2)
ax.set_yticks(ys)
ax.set_yticklabels([l for l, _ in filas], fontsize=7.4)
ax.set_xlabel("Potencia que no llega al otro puerto (%)")
ax.set_xlim(0, 15.5)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True)
ax.legend(handles=[Patch(color=c, label=n) for n, c in COMP], loc="lower right", fontsize=7)
etiqueta(ax, "(b)", x=0.98, y=0.99, ha="right")
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d2_potencia")
print("ok")
