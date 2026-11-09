"""Discontinuidad 5: campos del stub abierto (HFSS) a 5.5, 10.8 y 16.15 GHz.
(1) carga y corriente superficiales; (2) onda estacionaria en el stub y su
descomposicion en la onda que va al extremo abierto y la que regresa."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, FancyArrowPatch
import load_d5 as L
from scipy.signal import savgol_filter
from campos_stub import superficie, voltajes, ondas, FREQS, W, L1, LS, Y0

for p in ["/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf",
          "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-italic.otf"]:
    if os.path.exists(p):
        fm.fontManager.addfont(p)
TXT1, TXT2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "axes.unicode_minus": True})
COL = {"5p5GHz": "#eb6834", "10p8GHz": "#2a78d6", "16p15GHz": "#8a63d2"}
C_A, C_B = "#1baf7a", "#eb6834"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)

ref = L.cargar("A1_Ref50")
f = ref["f"]
SUP = {t: superficie(t) for t, _ in FREQS}
VOL = {t: voltajes(t) for t, _ in FREQS}
GAM, VINC, IINC, OND, IV = {}, {}, {}, {}, {}
for t, fq in FREQS:
    k = int(np.argmin(np.abs(f - fq)))
    GAM[t] = ref["g"][0, k]
    Z0 = ref["Z"][0, k].real
    VINC[t] = np.sqrt(2 * Z0)            # 1 W incidente
    IINC[t] = VINC[t] / Z0
    OND[t] = ondas(VOL[t]["s"], VOL[t]["V"], GAM[t])
# referencias de carga y corriente: onda incidente (10.8 GHz, el stub no refleja)
s10 = SUP["10p8GHz"]
brazo = s10["m"] & (s10["X"] >= 4.1) & (s10["X"] <= 4.9) & (np.abs(s10["Y"]) <= W / 2)
RHO_INC = np.nanmean(np.abs(s10["rho"][brazo]))
J_INC = np.nanmean(np.sqrt(np.abs(s10["Jx"][brazo]) ** 2 + np.abs(s10["Jy"][brazo]) ** 2))


def contorno(r):
    x0, x1 = r["xs"][0], r["xs"][-1]
    yt = Y0 + LS
    return [(x0, -W / 2), (x1, -W / 2), (x1, W / 2), (L1 + W, W / 2), (L1 + W, yt), (L1, yt), (L1, W / 2), (x0, W / 2)]


# ======================= (1) mapas de carga y corriente ==================
fig = plt.figure(figsize=(6.3, 6.9))
titulos = {"5p5GHz": "5.5 GHz: stub $=\\lambda_g/4$", "10p8GHz": "10.8 GHz: stub $=\\lambda_g/2$",
           "16p15GHz": "16.15 GHz: stub $=3\\lambda_g/4$"}
for k, (t, fq) in enumerate(FREQS):
    r = SUP[t]
    ph = np.exp(-1j * np.angle(r["Iin"]))
    for fila, campo in enumerate(["rho", "J"]):
        ax = fig.add_axes([0.035 + k * 0.29, 0.515 - fila * 0.495, 0.27, 0.455])
        if campo == "rho":
            val = np.where(r["m"], np.abs(r["rho"]) / RHO_INC, np.nan)
            im = ax.pcolormesh(r["X"], r["Y"], np.clip(val, 0, 3), cmap="Oranges", vmin=0, vmax=3,
                               shading="auto", rasterized=True)
            ec = "#5a3a1a"
        else:
            Jm = np.sqrt(np.abs(r["Jx"]) ** 2 + np.abs(r["Jy"]) ** 2)
            val = np.where(r["m"], Jm / J_INC, np.nan)
            im = ax.pcolormesh(r["X"], r["Y"], np.clip(val, 0, 3), cmap="Blues", vmin=0, vmax=3,
                               shading="auto", rasterized=True)
            ec = "#1b3a66"
            JX = np.where(r["m"], np.real(r["Jx"] * ph), 0); JY = np.where(r["m"], np.real(r["Jy"] * ph), 0)
            seeds = np.array([[r["xs"][0] + 0.02, y] for y in np.linspace(-0.9, 0.9, 9) * W / 2])
            ax.streamplot(r["xs"], r["ys"], JX, JY, color=TXT1, linewidth=0.5, arrowsize=0.5, start_points=seeds,
                          density=6, integration_direction="forward", broken_streamlines=False)
        pg = Polygon(contorno(r), closed=True, fill=False, ec=ec, lw=0.6)
        ax.add_patch(pg); im.set_clip_path(pg)
        ax.set_aspect("equal"); ax.set_xlim(r["xs"][0], r["xs"][-1]); ax.set_ylim(-0.9, Y0 + LS + 0.2)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        if fila == 0:
            ax.set_title(titulos[t], fontsize=8.4)
        else:
            ax.text(0.5 * (r["xs"][0] + r["xs"][-1]), -0.85,
                    "corriente de salida / entrada: %.2f" % (abs(r["Iout"]) / abs(r["Iin"])),
                    ha="center", va="bottom", fontsize=6.8, color=TXT1)
        if k == 0:
            ax.text(-0.02, 0.5, "Densidad de carga" if fila == 0 else "Densidad de corriente", rotation=90,
                    transform=ax.transAxes, ha="right", va="center", fontsize=8.4)
cax1 = fig.add_axes([0.915, 0.60, 0.013, 0.30])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0, 3), cmap="Oranges"), cax=cax1)
cb.set_label(r"$|\rho_s|$ / onda incidente", fontsize=7.2, labelpad=2); cb.ax.tick_params(labelsize=6.6, pad=1)
cax2 = fig.add_axes([0.915, 0.105, 0.013, 0.30])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0, 3), cmap="Blues"), cax=cax2)
cb.set_label(r"$|\mathbf{J}_s|$ / onda incidente", fontsize=7.2, labelpad=2); cb.ax.tick_params(labelsize=6.6, pad=1)
fig.savefig(os.path.join(OUT, "fig_d5_stub_mapas.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig_d5_stub_mapas.png"), dpi=220)
plt.close(fig)

# ======================= (2) onda estacionaria ===========================
plt.rcParams.update({"axes.edgecolor": TXT2, "axes.labelcolor": TXT1, "xtick.color": TXT2, "ytick.color": TXT2,
                     "axes.linewidth": 0.6, "grid.color": GRID, "grid.linewidth": 0.5,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})
fig = plt.figure(figsize=(6.3, 5.6))
ax1 = fig.add_axes([0.08, 0.58, 0.40, 0.37]); ax2 = fig.add_axes([0.58, 0.58, 0.40, 0.37])
ax3 = fig.add_axes([0.08, 0.08, 0.40, 0.37])
dl = float(json.load(open("d5_nums.json"))["DL3"])
lab = {"5p5GHz": "5.5 GHz ($\\lambda_g/4$)", "10p8GHz": "10.8 GHz ($\\lambda_g/2$)", "16p15GHz": "16.15 GHz ($3\\lambda_g/4$)"}
for t, fq in FREQS:
    v = VOL[t]
    m = (v["s"] >= -0.3) & (v["s"] <= LS + 0.4)
    ax1.plot(v["s"][m], np.abs(v["V"][m]) / VINC[t], color=COL[t], lw=1.4, label=lab[t])
    beta = GAM[t].imag
    st = np.linspace(0, LS, 200)
    vt = np.abs(np.cos(beta * (LS + dl - st) * 1e-3))
    vmax = np.abs(v["V"][(v["s"] > LS - 1.0) & (v["s"] < LS)]).max() / VINC[t] / np.abs(np.cos(beta * dl * 1e-3))
    ax1.plot(st, vmax * vt, color=COL[t], lw=0.8, ls=(0, (3, 2)))
    # corriente a partir del voltaje: dV/ds = -j w L' I (ecuacion del telegrafista)
    k_ = int(np.argmin(np.abs(f - fq)))
    Lp = ref["Z"][0, k_].real * np.sqrt(ref["ee"][0, k_]) / 299792458.0
    w = 2 * np.pi * fq * 1e9
    # derivada con un filtro de Savitzky-Golay (ventana de 0.4 mm, cubica)
    ds = (v["s"][1] - v["s"][0]) * 1e-3
    dV = (savgol_filter(v["V"].real, 21, 3, deriv=1, delta=ds) +
          1j * savgol_filter(v["V"].imag, 21, 3, deriv=1, delta=ds))
    Iv = -dV / (1j * w * Lp)
    mm_ = (v["s"] >= 0.05) & (v["s"] <= LS - 0.3)
    ax2.plot(v["s"][mm_], np.abs(Iv[mm_]) / IINC[t], color=COL[t], lw=1.4)
    IV[t] = Iv
    it = np.abs(np.sin(beta * (LS + dl - st) * 1e-3))
    ax2.plot(st, vmax * it, color=COL[t], lw=0.8, ls=(0, (3, 2)))
for ax in (ax1, ax2):
    ax.axvline(0, color=TXT2, lw=0.6, ls=":"); ax.axvline(LS, color=TXT2, lw=0.6, ls=":")
    ax.set_xlim(-0.3, LS + 0.4); ax.grid(True)
    ax.set_xlabel("distancia desde la unión, $s$ (mm)")
ax1.text(0.1, 2.48, "unión", fontsize=6.8, color=TXT2); ax1.text(LS - 0.1, 0.08, "extremo\nabierto", fontsize=6.8, color=TXT2, ha="right", va="bottom")
ax1.set_ylim(0, 2.6); ax2.set_ylim(0, 2.6)
ax1.set_ylabel(r"$|V(s)|\,/\,V_{\mathrm{inc}}$"); ax2.set_ylabel(r"$|I(s)|\,/\,I_{\mathrm{inc}}$")
ax1.set_title("(a) Voltaje a lo largo del stub", fontsize=8.6, loc="left")
ax2.set_title(r"(b) Corriente a lo largo del stub, $I=-\frac{1}{j\omega L'}\,\frac{dV}{ds}$", fontsize=8.6, loc="left")
ax1.plot([], [], color=TXT2, lw=0.8, ls=(0, (3, 2)), label="línea con extremo abierto")
h_, l_ = ax1.get_legend_handles_labels()
fig.legend(h_, l_, fontsize=6.8, loc="lower left", bbox_to_anchor=(0.555, 0.035), ncol=1)
# (c) instantaneas a 5.5 GHz
t = "5p5GHz"; v = VOL[t]
m = (v["s"] >= -0.3) & (v["s"] <= LS + 0.4)
env = np.abs(v["V"][m]) / VINC[t]
ax3.fill_between(v["s"][m], -env, env, color="#fbe2d5", lw=0)
for k, wt in enumerate(np.arange(0, 180, 22.5)):
    y = np.real(v["V"][m] * np.exp(1j * np.radians(wt))) / VINC[t]
    ax3.plot(v["s"][m], y, color=C_B, lw=0.7, alpha=0.35 + 0.08 * k)
ax3.axvline(0, color=TXT2, lw=0.6, ls=":"); ax3.axvline(LS, color=TXT2, lw=0.6, ls=":")
ax3.axhline(0, color=TXT2, lw=0.5)
ax3.annotate("nodo: el voltaje\nen la unión es\nsiempre casi cero", xy=(0, 0), xytext=(0.6, -2.0), fontsize=6.8,
             arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax3.set_xlim(-0.3, LS + 0.4); ax3.set_ylim(-2.6, 2.6); ax3.grid(True)
ax3.set_xlabel("distancia desde la unión, $s$ (mm)"); ax3.set_ylabel(r"$v(s,t)\,/\,V_{\mathrm{inc}}$")
ax3.set_title("(c) Voltaje en ocho instantes, 5.5 GHz", fontsize=8.6, loc="left")
# (d) fasores en la union (suma cabeza con cola)
NUM = {}
for j, (t, titulo) in enumerate([("5p5GHz", "5.5 GHz: se cancelan"), ("10p8GHz", "10.8 GHz: se suman")]):
    A, B, aj, err = OND[t]
    ax = fig.add_axes([0.56 + j * 0.22, 0.24, 0.19, 0.17])
    a, b = A / VINC[t], B / VINC[t]
    rot = np.exp(-1j * np.angle(a))
    a, b = a * rot, b * rot
    off = 0.18j if abs(a + b) < 0.5 * abs(a) else 0.0
    def flecha(z0, z1, col, lw):
        ax.add_patch(FancyArrowPatch((z0.real, z0.imag), (z1.real, z1.imag), arrowstyle="-|>", mutation_scale=8,
                                     color=col, lw=lw, shrinkA=0, shrinkB=0))
    flecha(0, a, C_A, 1.6)
    flecha(a + off, a + b + off, C_B, 1.6)
    if abs(a + b) > 0.05:
        flecha(-0.11j, a + b - 0.11j, TXT1, 1.8)
    else:
        ax.plot([(a + b).real], [(a + b).imag], "o", color=TXT1, ms=3.5)
    ax.text(0.06, -0.38, "$|A|=%.2f$" % abs(a), ha="left", fontsize=6.6, color=C_A)
    ax.text((a + b / 2 + off).real, 0.33, "$|B|=%.2f$" % abs(b), ha="center", fontsize=6.6, color=C_B)
    ax.text(0.06, -0.62, "$|A+B|=%.2f$" % abs(a + b), ha="left", fontsize=6.6, color=TXT1)
    ax.set_xlim(-0.25, 2.4); ax.set_ylim(-0.66, 0.5)
    ax.set_aspect("equal"); ax.axhline(0, color=GRID, lw=0.5, zorder=0); ax.axvline(0, color=GRID, lw=0.5, zorder=0)
    ax.set_xticks([]); ax.set_yticks([])
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    ax.set_title(titulo, fontsize=7.8)
    NUM[t] = dict(A=float(abs(A) / VINC[t]), B=float(abs(B) / VINC[t]), ratio=float(abs(B / A)),
                  ang=float(np.degrees(np.angle(B / A))), suma=float(abs(A + B) / abs(A)), err=float(err))
fig.text(0.56, 0.455, "(d) Fasores de voltaje en la unión ($s=0$)", fontsize=8.6)
fig.text(0.56, 0.205, "$A$: onda hacia el extremo abierto\n$B$: onda que regresa (en $V_{\\mathrm{inc}}$)",
         fontsize=6.8, color=TXT2, va="top")
fig.savefig(os.path.join(OUT, "fig_d5_stub_onda.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig_d5_stub_onda.png"), dpi=220)
plt.close(fig)

# ======================= numeros para el reporte ========================
out = {}
for t, fq in FREQS:
    v, sp = VOL[t], SUP[t]
    i0 = int(np.argmin(np.abs(v["s"] - 0))); ie = int(np.argmin(np.abs(v["s"] - LS)))
    j0 = int(np.argmin(np.abs(sp["s"] - 0.1))); je = int(np.argmin(np.abs(sp["s"] - (LS - 0.1))))
    zona = (v["s"] > 0.3) & (v["s"] < LS - 0.3)
    out[t] = dict(V0=float(abs(v["V"][i0]) / VINC[t]), Vend=float(abs(v["V"][ie]) / VINC[t]),
                  I0=float(abs(IV[t][int(np.argmin(np.abs(v["s"] - 0.1)))]) / IINC[t]),
                  Iout_in=float(abs(sp["Iout"]) / abs(sp["Iin"])),
                  smin=float(v["s"][zona][np.argmin(np.abs(v["V"][zona]))]),
                  simin=float(v["s"][zona][np.argmin(np.abs(IV[t][zona]))]), **NUM.get(t, {}))
    if t == "16p15GHz":
        A, B, aj, err = OND[t]
        out[t].update(ang=float(np.degrees(np.angle(B / A))), suma=float(abs(A + B) / abs(A)))
    lg = 299792458 / (fq * 1e9) / np.sqrt(np.interp(fq, f, ref["ee"][0])) * 1e3
    out[t]["lg"] = float(lg)
json.dump(out, open("d5_stub.json", "w"), indent=1)
for t in out:
    print(t, {k: round(v, 3) for k, v in out[t].items()})
