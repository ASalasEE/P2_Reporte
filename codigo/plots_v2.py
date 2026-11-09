import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

exec(open("extract_v2.py").read())
DES_ALL = list(DES)
DES = DES_ALL[:3]

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

# Paleta categorica validada (slots 1-3) + estilo de linea como codificacion secundaria
EST = {
    "A_Referencia":      dict(color="#2a78d6", ls="-",  label="Referencia (línea recta)"),
    "B_Curva90":         dict(color="#eb6834", ls="--", label="Curva 90° sin chaflán"),
    "C_Curva90_Chaflan": dict(color="#1baf7a", ls="-.", label="Curva 90° con chaflán (55 %)"),
}
LW = 1.4
W_IN = 6.3
f = data["A_Referencia"]["f"]


def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre + ".pdf"))
    fig.savefig(os.path.join(OUT, nombre + ".png"), dpi=220)
    plt.close(fig)


def eje_f(ax):
    ax.set_xlim(0, 20)
    ax.set_xticks(np.arange(0, 21, 2.5))
    ax.set_xlabel("Frecuencia (GHz)")


def cruce(y, umbral):
    i = np.where(y > umbral)[0]
    return f[i[0]] if len(i) else None


# ---------------- Fig 1: S11 ----------------
fig, ax = plt.subplots(figsize=(W_IN, 3.0))
for d in DES:
    ax.plot(f, data[d]["s11db"], lw=LW, **EST[d])
ax.axhline(-20, color=TXT2, lw=0.8, ls=":")
ax.text(19.8, -19.2, r"umbral $-20$ dB ($|\Gamma| = 0.1$)", ha="right", va="bottom",
        fontsize=7.5, color=TXT2)
fc = cruce(data["B_Curva90"]["s11db"], -20)
ax.plot([fc], [-20], marker="o", ms=5, mfc="white", mec="#eb6834", mew=1.4, zorder=5)
ax.annotate("%.2f GHz" % fc, xy=(fc, -20), xytext=(fc + 0.6, -27),
            fontsize=7.5, color=TXT1,
            arrowprops=dict(arrowstyle="-", color=TXT2, lw=0.6))
ax.set_ylim(-60, 0)
ax.set_ylabel(r"$|S_{11}|$ (dB)")
eje_f(ax)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7.6)
guardar(fig, "fig1_S11_dB")

# ---------------- Fig 2: S21 ----------------
fig, ax = plt.subplots(figsize=(W_IN, 2.8))
for d in DES:
    ax.plot(f, data[d]["s21db"], lw=LW, **EST[d])
ax.set_ylim(-1.0, 0.05)
ax.set_ylabel(r"$|S_{21}|$ (dB)")
eje_f(ax)
ax.legend(loc="lower left")
guardar(fig, "fig2_S21_dB")

# ---------------- Fig 3: |Gamma| y VSWR (small multiples) ----------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.7))
for d in DES:
    g = np.abs(data[d]["S11"])
    axs[0].plot(f, g, lw=LW, **EST[d])
    axs[1].plot(f, (1 + g) / (1 - g), lw=LW, **EST[d])
axs[0].set_ylabel(r"$|\Gamma|$")
axs[0].set_ylim(0, 0.35)
axs[1].set_ylabel("VSWR")
axs[1].set_ylim(1, 2.05)
for ax, t in zip(axs, ["(a)", "(b)"]):
    eje_f(ax)
    ax.set_xticks(np.arange(0, 21, 5))
    ax.text(0.02, 0.97, t, transform=ax.transAxes, va="top", fontsize=8.5)
axs[0].legend(loc="upper left", bbox_to_anchor=(0.10, 1.0), fontsize=7.2)
fig.tight_layout(w_pad=2.0)
guardar(fig, "fig3_Gamma_VSWR")

# ---------------- Fig 4: carta de Smith (zoom) ----------------
fig, ax = plt.subplots(figsize=(3.6, 3.6))
ax.set_aspect("equal")
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
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
        z = rr + 1j * sg * xv
        z = np.concatenate([[1j * sg * xv], z])
        G = (z - 1) / (z + 1)
        ax.plot(G.real, G.imag, color=gcol, lw=0.5)
ax.plot([-1, 1], [0, 0], color=gcol, lw=0.5)
for r in [0.5, 2.0]:
    x0 = (r - 1) / (r + 1)
    ax.text(x0 + 0.008, -0.012, "%g" % r, fontsize=6.5, color=TXT2, va="top")
for d in DES:
    S = data[d]["S11"]
    ax.plot(S.real, S.imag, lw=LW, **EST[d])
SB = data["B_Curva90"]["S11"]
for fq in [5, 10, 15, 20]:
    i = np.argmin(np.abs(f - fq))
    ax.plot(SB[i].real, SB[i].imag, "o", ms=3.5, mfc="white", mec="#eb6834", mew=1.1, zorder=6)
    ax.annotate("%d GHz" % fq, xy=(SB[i].real, SB[i].imag),
                xytext=(SB[i].real + 0.035, SB[i].imag - 0.012), fontsize=6.8, color=TXT1)
ax.text(0.0, -0.40, "región capacitiva", ha="center", fontsize=7.5, color=TXT2, style="italic")
ax.text(0.0, 0.37, "región inductiva", ha="center", fontsize=7.5, color=TXT2, style="italic")
ax.set_xlim(-0.45, 0.45); ax.set_ylim(-0.45, 0.45)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=7.2, ncol=1)
ax.set_title(r"$S_{11}$ en la carta de Smith (zoom $|\Gamma| \leq 0.45$)", fontsize=8.5)
guardar(fig, "fig4_Smith_S11")

# ---------------- Fig 5: parasitos extraidos ----------------
m = f >= 2.0
fig, axs = plt.subplots(1, 3, figsize=(W_IN, 2.5))
for d in DES:
    x = data[d]
    axs[0].plot(f[m], x["C"][m] * 1e12, lw=LW, **EST[d])
    axs[1].plot(f[m], x["L"][m] * 1e9, lw=LW, **EST[d])
    axs[2].plot(f[m], x["Zeq"][m], lw=LW, **EST[d])
axs[0].set_ylabel(r"$C$ en paralelo (pF)"); axs[0].set_ylim(0, 0.2)
axs[1].set_ylabel(r"$L$ en serie por rama (nH)"); axs[1].set_ylim(0, 0.3)
axs[2].set_ylabel(r"$Z_{eq}=\sqrt{2L/C}$ ($\Omega$)"); axs[2].set_ylim(20, 72)
axs[2].axhline(50, color=TXT2, lw=0.8, ls=":")
for ax, t in zip(axs, ["(a)", "(b)", "(c)"]):
    ax.set_xlim(2, 20); ax.set_xticks([2, 5, 10, 15, 20])
    ax.set_xlabel("Frecuencia (GHz)")
    ax.text(0.03, 0.04 if t == "(c)" else 0.97, t, transform=ax.transAxes,
            va="bottom" if t == "(c)" else "top", fontsize=8.5)
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3, fontsize=7.5)
fig.tight_layout(w_pad=1.6)
guardar(fig, "fig5_parasitos_LC")

# ---------------- Fig 6: radiacion y destino de la potencia ----------------
P0 = data["A0_Ref_SinPerd"]["pl"]
RAD = {"B_Curva90": data["B0_Curva90_SinPerd"]["pl"] - P0,
       "C_Curva90_Chaflan": data["C0_Chaflan_SinPerd"]["pl"] - P0}
DIS = {"B_Curva90": data["B_Curva90"]["pl"] - data["B0_Curva90_SinPerd"]["pl"],
       "C_Curva90_Chaflan": data["C_Curva90_Chaflan"]["pl"] - data["C0_Chaflan_SinPerd"]["pl"]}
mlow = f < 6
PISO = 100 * max(np.abs(RAD["B_Curva90"][mlow]).max(), np.abs(RAD["C_Curva90_Chaflan"][mlow]).max())

fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.9), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
ax.axhspan(-PISO, PISO, color="#e9e8e4", lw=0, zorder=0)
ax.text(19.6, -0.36, r"incertidumbre numérica ($\pm$%.1f %%)" % PISO, fontsize=6.8, color=TXT2, ha="right", va="center")
for d in ["B_Curva90", "C_Curva90_Chaflan"]:
    ax.plot(f, 100 * RAD[d], lw=LW, **EST[d])
ax.set_ylabel("Potencia radiada por la esquina (%)")
ax.set_ylim(-0.5, 6)
eje_f(ax)
ax.set_xticks(np.arange(0, 21, 5))
ax.legend(loc="upper left", fontsize=7.2, bbox_to_anchor=(0.0, 0.93))
ax.text(0.02, 0.98, "(a)", transform=ax.transAxes, va="top", fontsize=8.5)

ax = axs[1]
ax.grid(False)
COMP = [("Reflejada", "#6250d6"), ("Radiada", "#eda100"), ("Disipada", "#e87ba4")]
filas6 = []
for d, nom in [("B_Curva90", "Sin chaflán"), ("C_Curva90_Chaflan", "Con chaflán")]:
    for fq in [10, 15, 20]:
        i = np.argmin(np.abs(f - fq))
        refl = 100 * abs(data[d]["S11"][i]) ** 2
        rad_ = max(100 * RAD[d][i], 0)
        dis_ = max(100 * DIS[d][i], 0)
        filas6.append(("%s, %d GHz" % (nom, fq), [refl, rad_, dis_]))
ys = np.arange(len(filas6))[::-1]
for y, (lab, vals) in zip(ys, filas6):
    x0 = 0
    for (cn, col), v in zip(COMP, vals):
        ax.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=1.2)
        if v >= 1.6:
            ax.text(x0 + v / 2, y, "%.1f" % v, ha="center", va="center", fontsize=6.6,
                    color="white" if col == "#6250d6" else TXT1)
        x0 += v
    ax.text(x0 + 0.3, y, "%.1f %%" % x0, va="center", fontsize=6.8, color=TXT2)
ax.set_yticks(ys)
ax.set_yticklabels([l for l, _ in filas6], fontsize=7.4)
ax.set_xlabel("Potencia incidente que no llega al puerto 2 (%)")
ax.set_xlim(0, 22)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=n) for n, c in COMP], loc="lower right",
          fontsize=7, ncol=1)
ax.text(0.98, 0.98, "(b)", transform=ax.transAxes, va="top", ha="right", fontsize=8.5)
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig6_radiacion_potencia")

# ---------------- Tabla LaTeX ----------------
filas = []
for fq in [2, 5, 10, 15, 20]:
    i = np.argmin(np.abs(f - fq))
    fila = ["%g" % fq]
    for d in DES:
        g = abs(data[d]["S11"][i])
        fila += ["%.1f" % data[d]["s11db"][i], "%.3f" % g, "%.2f" % ((1 + g) / (1 - g)),
                 "%.2f" % data[d]["s21db"][i]]
    filas.append(" & ".join(fila) + r" \\")
mm = (f >= 3) & (f <= 12)
par = {d: (data[d]["C"][mm].mean() * 1e12, data[d]["L"][mm].mean() * 1e9,
           data[d]["Zeq"][mm].mean()) for d in DES}
cr = {d: cruce(data[d]["s11db"], -20) for d in DES}
tex = r"""%% Requiere \usepackage{booktabs} y \usepackage{siunitx} (opcional)
\begin{table}[htbp]
\centering
\caption{Resultados de HFSS para la curva de \ang{90} (planos de referencia en los bordes de la esquina).}
\label{tab:curva90}
\small
\setlength{\tabcolsep}{3.2pt}
\begin{tabular}{c cccc cccc cccc}
\toprule
 & \multicolumn{4}{c}{Referencia} & \multicolumn{4}{c}{Curva sin chaflán} & \multicolumn{4}{c}{Curva con chaflán} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-9}\cmidrule(lr){10-13}
$f$ (GHz) & $S_{11}$ & $|\Gamma|$ & VSWR & $S_{21}$ & $S_{11}$ & $|\Gamma|$ & VSWR & $S_{21}$ & $S_{11}$ & $|\Gamma|$ & VSWR & $S_{21}$ \\
 & (dB) & & & (dB) & (dB) & & & (dB) & (dB) & & & (dB) \\
\midrule
""" + "\n".join(filas) + r"""
\bottomrule
\end{tabular}
\end{table}

\begin{table}[htbp]
\centering
\caption{Circuito equivalente en T extraído de HFSS (promedio de 3 a 12 GHz).}
\label{tab:curva90_LC}
\small
\begin{tabular}{lcccc}
\toprule
Diseño & $C$ (pF) & $L$ por rama (nH) & $Z_{eq}=\sqrt{2L/C}$ ($\Omega$) & $|S_{11}|=-20$ dB en \\
\midrule
""" + "\n".join([
    r"%s & %.3f & %.3f & %.1f & %s \\" % (n, par[d][0], par[d][1], par[d][2],
                                           ("%.2f GHz" % cr[d]) if cr[d] else r"$>20$ GHz")
    for n, d in [("Referencia", "A_Referencia"), ("Curva sin chaflán", "B_Curva90"),
                 ("Curva con chaflán", "C_Curva90_Chaflan")]]) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
filas_dec = []
for d, nom in [("B_Curva90", "Sin chaflán"), ("C_Curva90_Chaflan", "Con chaflán")]:
    for fq in [10, 15, 20]:
        i = np.argmin(np.abs(f - fq))
        t21 = 100 * 10 ** (data[d]["s21db"][i] / 10)
        refl = 100 * abs(data[d]["S11"][i]) ** 2
        resto = 100 - t21 - refl - 100 * RAD[d][i] - 100 * DIS[d][i]
        filas_dec.append(r"%s & %d & %.1f & %.1f & %.1f & %.1f & %.1f & %.2f & %.2f \\" % (
            nom, fq, t21, refl, 100 * RAD[d][i], 100 * DIS[d][i], resto, -data[d]["s21db"][i],
            -10 * np.log10(1 - abs(data[d]["S11"][i]) ** 2)))
tex += r"""
\begin{table}[htbp]
\centering
\caption{Destino de la potencia incidente (\%%). Radiada $= P_{X0}-P_{A0}$ y disipada $= P_{X}-P_{X0}$, con $P = 1-|S_{11}|^2-|S_{21}|^2$ y $X0$ el gemelo sin pérdidas; incertidumbre de la radiada $\pm$%.1f\,\%%. El residuo es el error numérico común a todos los diseños (pérdida aparente de la referencia sin pérdidas).}
\label{tab:curva90_potencia}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lcccccccc}
\toprule
Diseño & $f$ (GHz) & Transmitida & Reflejada & Radiada & Disipada & Residuo & IL (dB) & IL refl. (dB) \\
\midrule
""" % PISO + "\n".join(filas_dec) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
open(os.path.join(OUT, "tablas_curva90.tex"), "w", encoding="utf-8").write(tex)
print("ok", sorted(os.listdir(OUT)))
