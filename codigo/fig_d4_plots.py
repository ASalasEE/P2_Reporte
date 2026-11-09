"""Discontinuidad 4 (cambio de material): geometria y figuras de resultados
(requiere d4_analisis.py)."""
import os, json, math
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
C_RO, C_FR, C_CO, C_SN = "#eb6834", "#2a78d6", "#1baf7a", "#8a63d2"
F_SUB1, F_SUB2, CU, SN = "#eef3e8", "#dfe9f6", "#c8793a", "#a9a9b8"
LW, W_IN = 1.4, 6.3
D = np.load("d4_datos.npz")
N = json.load(open("d4_nums.json"))
f = D["f"]
db = lambda x: 20 * np.log10(np.abs(x))
W1, W2, L1, H = 1.14, 0.48, 6.0, 0.508


def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre + ".pdf"))
    fig.savefig(os.path.join(OUT, nombre + ".png"), dpi=220)
    plt.close(fig)


# ------------------- geometria -------------------
fig = plt.figure(figsize=(W_IN, 2.9))
# (a) corte longitudinal (escala vertical x4)
ax = fig.add_axes([0.0, 0.50, 1.0, 0.48])
ev = 4.0
xm = 2 * L1
ax.add_patch(Rectangle((0, 0), L1, H * ev, fc=F_SUB1, ec="#7b9a63", lw=0.6))
ax.add_patch(Rectangle((L1, 0), L1, H * ev, fc=F_SUB2, ec="#5f7fa8", lw=0.6))
ax.plot([0, xm], [0, 0], color="#8a4f1f", lw=2.2, solid_capstyle="butt")
ax.plot([0, L1], [H * ev, H * ev], color=CU, lw=2.6, solid_capstyle="butt")
ax.plot([L1, xm], [H * ev, H * ev], color=CU, lw=2.6, solid_capstyle="butt")
ax.plot([L1, xm], [H * ev + 0.05, H * ev + 0.05], color=SN, lw=1.4, ls=(0, (2, 1.5)), solid_capstyle="butt")
for x in (0, xm):
    ax.plot([x, x], [0, 8 * H * ev * 0.55], color="#2a78d6", lw=2.4, solid_capstyle="butt")
ax.text(-0.25, 3.2, "P1", ha="right", va="center", color="#2a78d6", fontsize=8)
ax.text(xm + 0.25, 3.2, "P2", ha="left", va="center", color="#2a78d6", fontsize=8)
ax.plot([L1, L1], [-0.35, H * ev + 1.25], color=TXT2, lw=0.8, ls=(0, (3, 2)))
ax.text(L1, H * ev + 1.32, "unión ($x=L_1$): plano de referencia de ambos puertos", ha="center", va="bottom",
        fontsize=7.2, color=TXT2)
ax.text(L1 / 2, H * ev / 2, r"RO4003C ($\varepsilon_r=3.55$)", ha="center", va="center", fontsize=7.6)
ax.text(1.5 * L1, H * ev / 2, r"FR-4 (4.4) o RO3010 (10.2)", ha="center", va="center", fontsize=7.6)
ax.text(1.5 * L1, H * ev + 0.22, "tira de cobre (o de estaño en el caso D)", ha="center", va="bottom", fontsize=7, color=TXT2)
ax.text(L1 / 2, H * ev + 0.22, "tira de cobre", ha="center", va="bottom", fontsize=7, color=TXT2)
ax.text(L1 / 2, -0.12, "tierra", ha="center", va="top", fontsize=7, color=TXT2)
ax.annotate("", xy=(xm + 0.9, 0), xytext=(xm + 0.9, H * ev), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
ax.text(xm + 1.05, H * ev / 2, "$h=0.508$ mm\n(escala vertical ×4)", ha="left", va="center", fontsize=7, color=TXT2)
ax.annotate("", xy=(0, -0.7), xytext=(L1, -0.7), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
ax.annotate("", xy=(L1, -0.7), xytext=(xm, -0.7), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2))
ax.text(L1 / 2, -0.8, "$L_1=6$ mm", ha="center", va="top", fontsize=7, color=TXT2)
ax.text(1.5 * L1, -0.8, "$L_1=6$ mm", ha="center", va="top", fontsize=7, color=TXT2)
ax.set_xlim(-1.0, xm + 3.7); ax.set_ylim(-1.5, H * ev + 1.8)
ax.axis("off")
ax.set_title("(a) Corte longitudinal por el eje de la línea", fontsize=8.5, loc="left")
# (b) vistas superiores de la zona de la union
casos = [("(b) Cambio de sustrato", W1, CU, F_SUB2), ("(c) Sustrato con ancho compensado", W2, CU, F_SUB2),
         ("(d) Cambio de metal", W1, SN, F_SUB1)]
for k, (tit, w2, met2, sub2) in enumerate(casos):
    axb = fig.add_axes([0.02 + k * 0.33, 0.0, 0.30, 0.38])
    x0, x1 = L1 - 2.5, L1 + 2.5
    axb.add_patch(Rectangle((x0, -1.6), L1 - x0, 3.2, fc=F_SUB1, ec="none"))
    axb.add_patch(Rectangle((L1, -1.6), x1 - L1, 3.2, fc=sub2, ec="none"))
    axb.add_patch(Rectangle((x0, -W1 / 2), L1 - x0, W1, fc=CU, ec="#8a4f1f", lw=0.5))
    axb.add_patch(Rectangle((L1, -w2 / 2), x1 - L1, w2, fc=met2, ec="#55556a" if met2 == SN else "#8a4f1f", lw=0.5))
    axb.plot([L1, L1], [-1.6, 1.6], color=TXT2, lw=0.7, ls=(0, (3, 2)))
    lab2 = {0: "1.14 mm", 1: "0.48 mm", 2: "1.14 mm"}[k]
    axb.text(L1 - 1.25, W1 / 2 + 0.12, "1.14 mm", ha="center", va="bottom", fontsize=6.8, color=TXT2)
    axb.text(L1 + 1.25, w2 / 2 + 0.12, lab2, ha="center", va="bottom", fontsize=6.8, color=TXT2)
    izq, der = "RO4003C", {0: "FR-4 / RO3010", 1: "RO3010", 2: "RO4003C"}[k]
    axb.text(L1 - 1.25, -1.45, izq, ha="center", va="bottom", fontsize=6.6, color=TXT2)
    axb.text(L1 + 1.25, -1.45, der, ha="center", va="bottom", fontsize=6.6, color=TXT2)
    if k == 2:
        axb.text(L1 - 1.25, 0, "Cu", ha="center", va="center", fontsize=7, color="white")
        axb.text(L1 + 1.25, 0, "Sn", ha="center", va="center", fontsize=7, color=TXT1)
    axb.set_xlim(x0, x1); axb.set_ylim(-1.6, 1.6); axb.set_aspect("equal"); axb.axis("off")
    axb.set_title(tit, fontsize=8, pad=2)
guardar(fig, "fig_d4_geometria")

# ------------------- reflexion -------------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 3.3), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
ax.plot(f, db(D["B2_RO3010_S11"]), color=C_RO, lw=LW, label="RO4003C → RO3010")
ax.plot(f, db(D["G_B2_RO3010"]), color=C_RO, lw=0.9, ls="--")
ax.plot(f, db(D["B1_FR4_S11"]), color=C_FR, lw=LW, label="RO4003C → FR-4")
ax.plot(f, db(D["G_B1_FR4"]), color=C_FR, lw=0.9, ls="--")
ax.plot(f, db(D["C_RO3010_Ancho50_S11"]), color=C_CO, lw=LW, label="RO3010 con ancho compensado")
ax.plot(f, db(D["D_Estano_S11"]), color=C_SN, lw=LW, label="cobre → estaño")
ax.plot(f, db(D["gsn"]), color=C_SN, lw=0.9, ls=":", label=r"estaño, teoría: $\Delta\alpha_c/(\sqrt{2}\,\beta)$")
piso = float(N["RESREF4"])
ax.axhspan(-80, db(piso), color="#f1f1ee", lw=0, zorder=0)
ax.text(19.7, db(piso) - 0.8, "resolución de la corrección", ha="right", va="top", fontsize=6.8, color=TXT2)
ax.axhline(-20, color=TXT2, lw=0.7, ls=(0, (5, 3)))
ax.text(0.3, -19.2, "$-20$ dB", fontsize=6.8, color=TXT2)
ax.plot([], [], color=TXT2, lw=0.9, ls="--", label=r"escalón ideal $(Z_2-Z_1)/(Z_2+Z_1)$")
ax.set_xlim(0, 20); ax.set_ylim(-70, 0); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$|S_{11}|$ (dB)")
h_a, l_a = ax.get_legend_handles_labels()
ax.text(0.02, 0.96, "(a)", transform=ax.transAxes, va="top")
ax = axs[1]
for d, col, lab in [("B2_RO3010", C_RO, "RO3010"), ("B1_FR4", C_FR, "FR-4")]:
    for x, ls in [("", "-"), ("_SinPerd", (0, (1.5, 1.2)))]:
        ax.plot(f, np.abs(D["%s%s_S11" % (d, x)] - D["G_%s" % d]), color=col, lw=LW if x == "" else 1.0, ls=ls,
                label=lab if x == "" else None)
ax.axhline(piso, color=TXT2, lw=0.7, ls=(0, (5, 3)))
ax.text(0.3, piso + 0.0006, "resolución de la corrección", fontsize=6.8, color=TXT2, va="bottom")
ax.plot([], [], color=TXT2, lw=1.0, ls=(0, (1.5, 1.2)), label="gemelo sin pérdidas")
ax.set_xlim(0, 20); ax.set_ylim(0, 0.03); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$|S_{11}-\Gamma_{\mathrm{ideal}}|$")
ax.legend(loc="upper left", fontsize=7, bbox_to_anchor=(0.06, 0.93))
ax.text(0.02, 0.96, "(b)", transform=ax.transAxes, va="top")
fig.tight_layout(w_pad=1.5, rect=(0, 0.12, 1, 1))
fig.legend(h_a, l_a, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 0.0), columnspacing=1.2,
           handlelength=1.8)
guardar(fig, "fig_d4_reflexion")

# ------------------- tramo finito del segundo material -------------------
fig, ax = plt.subplots(figsize=(W_IN, 3.0))
for ell, col in zip([6, 12, 24], ["#f0a07a", C_RO, "#9c3a10"]):
    ax.plot(f, np.abs(D["fin_B2_%g" % ell]), color=col, lw=LW, label="RO3010, $\\ell=%g$ mm" % ell)
ax.plot(f, np.abs(D["fin_B1_6"]), color=C_FR, lw=1.1, label="FR-4, $\\ell=6$ mm")
ax.plot(f, np.abs(D["fin_C_6"]), color=C_CO, lw=1.1, label="RO3010 compensado, $\\ell=6$ mm")
ax.axhline(0.1, color=TXT2, lw=0.7, ls=(0, (5, 3)))
ax.text(19.8, 0.108, r"$|S_{11}|=0.1$ ($-20$ dB)", ha="right", fontsize=6.8, color=TXT2,
        bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
ax.axhline(float(N["GPKT"]), color=TXT2, lw=0.6, ls=":")
ax.text(19.8, 0.535, r"línea punteada: $2|\Gamma|/(1+|\Gamma|^2)$", ha="right", fontsize=6.8, color=TXT2)
fq = float(N["FQ6"])
yq = float(np.interp(fq, f, np.abs(D["fin_B2_6"])))
ax.annotate(r"$\ell=\lambda_g/4$ con $\ell=6$ mm", xy=(fq, yq), xytext=(fq - 0.6, 0.545), fontsize=7, color=TXT1, ha="right",
            arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax.set_xlim(0, 20); ax.set_ylim(0, 0.6); ax.set_xticks(np.arange(0, 21, 2))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$|S_{11}|$ a la entrada")
fig.tight_layout(rect=(0, 0.1, 1, 1))
h_, l_ = ax.get_legend_handles_labels()
fig.legend(h_, l_, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 0.0), columnspacing=1.2)
guardar(fig, "fig_d4_tramo")

# ------------------- perdidas: cobre y estano -------------------
fig, axs = plt.subplots(1, 2, figsize=(W_IN, 2.8), gridspec_kw=dict(width_ratios=[1.15, 1]))
ax = axs[0]
k = 8.686 / 100
ax.plot(f, k * D["a_A1_Ref_RO4003C"], color=CU, lw=LW, label="tira de cobre")
ax.plot(f, k * D["a_A5_Ref_Estano"], color=C_SN, lw=LW, label="tira de estaño")
ax.plot(f, k * D["ad"], color=TXT2, lw=0.9, ls="--", label=r"$\alpha_d$ (dieléctrico)")
ax.plot(f, k * D["acu"], color=CU, lw=0.9, ls=":", label=r"$\alpha_c$ cobre")
ax.plot(f, k * D["asn"], color=C_SN, lw=0.9, ls=":", label=r"$\alpha_c$ estaño")
ax.set_xlim(0, 20); ax.set_ylim(0, 0.17); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$\alpha$ (dB/cm)")
ax.legend(loc="upper left", fontsize=6.8)
ax.text(0.97, 0.04, "(a) sobre RO4003C", transform=ax.transAxes, ha="right", va="bottom", fontsize=8)
ax = axs[1]
m = f >= 0.5
ax.plot(f[m], D["asn"][m] / D["acu"][m], color=C_SN, lw=LW, label="HFSS")
rs = float(N["RS"])
ax.axhline(rs, color=TXT2, lw=0.8, ls="--")
ax.text(19.8, rs + 0.04, r"toda la pérdida en la tira: $\sqrt{\sigma_{Cu}/\sigma_{Sn}}=%s$" % N["RS"], ha="right",
        fontsize=6.8, color=TXT2)
ax.axhline(1, color=TXT2, lw=0.8, ls="--")
ax.text(19.8, 1.04, "toda la pérdida en la tierra", ha="right", fontsize=6.8, color=TXT2)
ax.set_xlim(0, 20); ax.set_ylim(0.8, 2.9); ax.set_xticks(np.arange(0, 21, 5))
ax.set_xlabel("Frecuencia (GHz)"); ax.set_ylabel(r"$\alpha_{c,\mathrm{Sn}}/\alpha_{c,\mathrm{Cu}}$")
ax.text(0.97, 0.30, "(b) la tira lleva el %s %%\nde la pérdida de conductor" % N["FRTIRA"], transform=ax.transAxes,
        ha="right", va="bottom", fontsize=7.2)
fig.tight_layout(w_pad=1.5)
guardar(fig, "fig_d4_perdidas")
print("ok")
