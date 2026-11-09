"""Figura de la discusion 6.3: par de corrientes tira-imagen y radiacion en la curva."""
import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

try:
    fm.fontManager.addfont("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf")
except Exception:
    pass
plt.rcParams.update({"font.family": "Latin Modern Roman", "mathtext.fontset": "cm", "font.size": 8.5,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
TXT1, TXT2 = "#0b0b0b", "#52514e"
CU, IMG = "#eb6834", "#2a78d6"
OUT = "figuras"
os.makedirs(OUT, exist_ok=True)
Wn = 1.14 / 0.508   # ancho normalizado a h

# ---------------- campo de la tira y su imagen (2D, h = 1) ----------------
def B_tira(X, Y, y0, signo, n=41):
    bx = np.zeros_like(X); by = np.zeros_like(X)
    for xc in np.linspace(-Wn / 2, Wn / 2, n):
        dx, dy = X - xc, Y - y0
        r2 = dx ** 2 + dy ** 2 + 1e-6
        bx += signo * (-dy) / r2 / n
        by += signo * dx / r2 / n
    return bx, by

x = np.linspace(-6, 6, 400); y = np.linspace(-4.5, 5.5, 400)
X, Y = np.meshgrid(x, y)
b1x, b1y = B_tira(X, Y, 1.0, +1)
b2x, b2y = B_tira(X, Y, -1.0, -1)
BX, BY = b1x + b2x, b1y + b2y
BM = np.sqrt(BX ** 2 + BY ** 2)

fig = plt.figure(figsize=(6.3, 6.0))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], width_ratios=[1.25, 1], hspace=0.32, wspace=0.28)

ax = fig.add_subplot(gs[0, 0])
ax.add_patch(Rectangle((-6, -4.5), 12, 4.5, fc="#eef2f8", ec="none", zorder=0))
ax.pcolormesh(X, Y, np.log10(BM), cmap="Greys", vmin=-2.5, vmax=0.6, shading="auto", alpha=0.55,
              rasterized=True, zorder=1)
ax.streamplot(x, y, BX, BY, color="#3a3a38", linewidth=0.55, density=1.1, arrowsize=0.5, zorder=2)
ax.axhline(0, color=TXT2, lw=1.0, zorder=3)
ax.add_patch(Rectangle((-Wn / 2, 0.93), Wn, 0.14, fc=CU, ec="none", zorder=4))
ax.add_patch(Rectangle((-Wn / 2, -1.07), Wn, 0.14, fc=IMG, ec="none", zorder=4))
ax.text(Wn / 2 + 0.25, 1.0, "$+I$ (tira)", va="center", fontsize=7.6, color=TXT1, zorder=5,
        bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
ax.text(Wn / 2 + 0.25, -1.0, "$-I$ (imagen)", va="center", fontsize=7.6, color=TXT1, zorder=5,
        bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
ax.text(-5.8, 0.18, "plano de tierra", fontsize=7.2, color=TXT2, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
ax.text(-5.8, -4.3, "región imagen (sustituye al plano de tierra)", fontsize=6.8, color=TXT2, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
ax.set_xlim(-6, 6); ax.set_ylim(-4.5, 5.5)
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("(a) Campo magnético en sección transversal", fontsize=8.5)

# ---------------- decaimiento con la distancia ----------------
ax = fig.add_subplot(gs[0, 1])
r = np.logspace(0.3, 2, 200)
sola = np.array([np.hypot(*B_tira(np.array([0.0]), np.array([1 + ri]), 1.0, +1)) for ri in r]).ravel()
bxp, byp = [], []
for ri in r:
    a1 = B_tira(np.array([0.0]), np.array([1 + ri]), 1.0, +1)
    a2 = B_tira(np.array([0.0]), np.array([1 + ri]), -1.0, -1)
    bxp.append(a1[0] + a2[0]); byp.append(a1[1] + a2[1])
par = np.hypot(np.array(bxp), np.array(byp)).ravel()
ax.loglog(r, sola / sola[0], color=CU, lw=1.4, label="tira sola ($\\propto 1/r$)")
ax.loglog(r, par / sola[0], color=IMG, lw=1.4, ls="--", label="tira + imagen ($\\propto 2h/r^2$)")
ax.set_xlabel("distancia sobre la tira, $r/h$")
ax.set_ylabel("$|B|$ normalizado")
ax.grid(True, which="major", color="#dcdcd8", lw=0.5)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.legend(fontsize=7, frameon=False, loc="lower left")
ax.set_title("(b) Cancelación lejos de la línea", fontsize=8.5)

# ---------------- esquema de la curva (proyeccion oblicua dibujada a mano) ----------------
ax = fig.add_subplot(gs[1, :])
ang = np.radians(38); k = 0.62
def P(x, y, z):
    return x + k * y * np.cos(ang), z + k * y * np.sin(ang)
L, zt = 6.0, 1.15
def linea(pts, **kw):
    uv = np.array([P(*q) for q in pts]); ax.plot(uv[:, 0], uv[:, 1], **kw)
def flecha(p0, p1, color, lw=1.3):
    ax.annotate("", xy=P(*p1), xytext=P(*p0), arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                                               mutation_scale=9, shrinkA=0, shrinkB=0))
# imagen (debajo del plano)
linea([(0, 0, -zt), (L, 0, -zt), (L, L, -zt)], color=IMG, lw=1.8, ls=(0, (4, 2)))
for xi in [0.9, 2.7, 4.5]:
    flecha((xi + 1.0, 0, -zt), (xi, 0, -zt), IMG, 1.1)
for yi in [1.2, 3.0, 4.8]:
    flecha((L, yi + 1.0, -zt), (L, yi, -zt), IMG, 1.1)
# plano de tierra
gp = np.array([P(*q) for q in [(-1.0, -4.2, 0), (L + 5.0, -4.2, 0), (L + 5.0, L + 1.2, 0), (-1.0, L + 1.2, 0)]])
ax.fill(gp[:, 0], gp[:, 1], fc="#d9d9d4", ec="#a9a9a2", lw=0.7, alpha=0.55, zorder=2)
# tira (encima del plano)
uv = np.array([P(*q) for q in [(0, 0, zt), (L, 0, zt), (L, L, zt)]])
ax.plot(uv[:, 0], uv[:, 1], color=CU, lw=3.4, solid_capstyle="round", zorder=4)
for xi in [0.9, 2.7, 4.5]:
    flecha((xi, 0, zt + 0.35), (xi + 1.0, 0, zt + 0.35), CU)
for yi in [1.2, 3.0, 4.8]:
    flecha((L, yi, zt + 0.35), (L, yi + 1.0, zt + 0.35), CU)
# conectores verticales que indican la separacion 2h
for (xq, yq) in [(1.5, 0)]:
    u0, v0 = P(xq, yq, zt); u1, v1 = P(xq, yq, -zt)
    ax.annotate("", xy=(u1, v1), xytext=(u0, v0), arrowprops=dict(arrowstyle="<->", lw=0.6, color=TXT2), zorder=5)
    ax.text(u0 - 0.25, (v0 + v1) / 2, "$2h$", fontsize=7.6, color=TXT2, ha="right", va="center", zorder=5)
# frentes de onda desde la esquina exterior (hacia afuera de la L y hacia arriba)
uc, vc = P(L, 0, zt)
for rad, al in [(1.2, 0.95), (2.0, 0.7), (2.8, 0.45)]:
    t = np.linspace(np.radians(62), np.radians(150), 60)
    ax.plot(uc + rad * np.cos(t), vc + 0.1 + rad * np.sin(t), color="#6250d6", lw=1.3, alpha=al, zorder=6)
ax.text(uc - 2.9, vc + 2.75, "radiación", fontsize=8, color="#6250d6", zorder=6, ha="right")
ax.text(0.0, -0.02, "tramos rectos: $I$ (tira) y $-I$ (imagen) van juntas y sus campos se cancelan lejos de la línea",
        transform=ax.transAxes, fontsize=7.4, color=TXT1, va="top", zorder=6)
ax.annotate("esquina: la corriente gira $90^\\circ$ y la\ncancelación deja de ser completa",
            xy=(uc + 0.05, vc - 0.05), xytext=(0.70, 0.62), textcoords="axes fraction",
            fontsize=7.4, color=TXT1, va="top", ha="left", zorder=6,
            arrowprops=dict(arrowstyle="-", lw=0.6, color=TXT2))
ax.text(*P(-0.5, 0, zt + 0.25), "$I$", fontsize=8.5, color=CU, ha="right", zorder=6)
ax.text(*P(-0.5, 0, -zt - 0.1), "$-I$", fontsize=8.5, color=IMG, ha="right", va="top", zorder=6)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("(c) Tira, imagen y radiación en la curva (alturas exageradas)", fontsize=8.5, pad=14)

fig.savefig(os.path.join(OUT, "fig9_imagen_radiacion.pdf"), dpi=300)
fig.savefig(os.path.join(OUT, "fig9_imagen_radiacion.png"), dpi=220)
print("ok")
