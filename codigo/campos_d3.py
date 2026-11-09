"""Discontinuidad 3 (gap): carga y corriente sobre la traza y lineas de campo
en el plano vertical que pasa por el eje, a partir de los campos de HFSS."""
import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator

D = os.path.join("datos", "P2_D3_Gap_CSV", "campos")
EPS0, ER = 8.8541878128e-12, 3.55
W, L1, H = 1.14, 6.0, 0.508


def _leer(archivo, ejes):
    a = np.loadtxt(os.path.join(D, archivo), skiprows=2)
    c1, c2 = a[:, ejes[0]] * 1e3, a[:, ejes[1]] * 1e3
    u1, u2 = np.unique(np.round(c1, 6)), np.unique(np.round(c2, 6))
    i1 = np.searchsorted(u1, np.round(c1, 6)); i2 = np.searchsorted(u2, np.round(c2, 6))
    V = np.full((len(u2), len(u1), 3), np.nan)
    V[i2, i1, :] = a[:, 3:6]
    return u1, u2, V


def fasor(nombre, etiqueta, ejes=(0, 1)):
    u1, u2, A0 = _leer("%s__%s_ph0.fld" % (nombre, etiqueta), ejes)
    _, _, A90 = _leer("%s__%s_ph90.fld" % (nombre, etiqueta), ejes)
    return u1, u2, A0 - 1j * A90


def superficie(nombre, s):
    """rho_s y J_s sobre la traza (planos z = h +- 0.02 mm)."""
    xs, ys, Eb = fasor(nombre, "E_abajo")
    _, _, Ea = fasor(nombre, "E_arriba")
    _, _, Hb = fasor(nombre, "H_abajo")
    _, _, Ha = fasor(nombre, "H_arriba")
    rho = EPS0 * (Ea[..., 2] - ER * Eb[..., 2])
    dH = Ha - Hb
    Jx, Jy = -dH[..., 1], dH[..., 0]
    X, Y = np.meshgrid(xs, ys)
    izq = (X <= L1) & (np.abs(Y) <= W / 2)
    der = (X >= L1 + s) & (np.abs(Y) <= W / 2)
    m = izq | der
    # referencia: carga de la linea izquierda a 1 mm del extremo
    brazo = izq & (X >= L1 - 1.4) & (X <= L1 - 1.1)
    ref = np.nanmean(rho[brazo])
    ph = np.exp(-1j * np.angle(ref))
    dA = (xs[1] - xs[0]) * (ys[1] - ys[0]) * 1e-6
    ell = 0.5
    QL = np.nansum(rho[izq & (X >= L1 - ell)]) * dA
    QR = np.nansum(rho[der & (X <= L1 + s + ell)]) * dA
    return dict(xs=xs, ys=ys, X=X, Y=Y, m=m, izq=izq, der=der,
                R=np.where(m, np.real(rho * ph) / abs(ref), np.nan),
                JN=np.where(m, np.sqrt(np.abs(Jx) ** 2 + np.abs(Jy) ** 2), np.nan),
                QL=QL, QR=QR, ratio=float(np.real(QR / QL)), ell=ell)


def vertical(nombre, s):
    """E en el plano y = 0, en la fase en que la carga del extremo es maxima."""
    xs, zs, E = fasor(nombre, "E_vertical", ejes=(0, 2))
    k = np.nanargmax(np.abs(E[..., 2]).ravel())
    ph = np.exp(-1j * np.angle(E[..., 2].ravel()[k]))
    Ex, Ez = np.real(E[..., 0] * ph), np.real(E[..., 2] * ph)
    return dict(xs=xs, zs=zs, Ex=Ex, Ez=Ez, mag=np.sqrt(np.abs(E[..., 0]) ** 2 + np.abs(E[..., 2]) ** 2))


def lineas_de_campo(v, s, ell=0.5, n=60, paso=0.004, nmax=6000):
    """Traza lineas de E desde la superficie del ultimo tramo ell de la tira
    izquierda (arriba y abajo) y las clasifica por su destino. Cada linea
    se pesa con el flujo de D que sale de su punto de partida."""
    fx = RegularGridInterpolator((v["zs"], v["xs"]), v["Ex"], bounds_error=False, fill_value=np.nan)
    fz = RegularGridInterpolator((v["zs"], v["xs"]), v["Ez"], bounds_error=False, fill_value=np.nan)
    x0, x1 = v["xs"][0], v["xs"][-1]
    z1 = v["zs"][-1]
    lineas, peso, destino = [], [], []
    xs0 = np.linspace(L1 - ell, L1 - 0.005, n)
    for lado, zst, eps in [("arriba", H + 0.012, 1.0), ("abajo", H - 0.012, ER)]:
        for xa in xs0:
            p = np.array([zst, xa])
            e0 = np.array([fz(p)[0], fx(p)[0]])
            if not np.all(np.isfinite(e0)):
                continue
            sg = np.sign(e0[0]) if lado == "arriba" else -np.sign(e0[0])
            w = eps * abs(e0[0])
            camino = [p.copy()]
            fin = "fuera"
            for _ in range(nmax):
                e = np.array([fz(p)[0], fx(p)[0]])
                if not np.all(np.isfinite(e)) or np.hypot(*e) == 0:
                    break
                d = sg * e / np.hypot(*e)
                p = p + paso * d
                camino.append(p.copy())
                z, x = p
                if z <= 0.004:
                    fin = "tierra"; break
                if abs(z - H) < 0.006 and x >= L1 + s:
                    fin = "derecha"; break
                if abs(z - H) < 0.006 and x <= L1 and len(camino) > 20:
                    fin = "izquierda"; break
                if x <= x0 or x >= x1 or z >= z1:
                    fin = "fuera"; break
            lineas.append(np.array(camino)); peso.append(w); destino.append(fin)
    peso = np.array(peso)
    frac = {k: float(peso[np.array(destino) == k].sum() / peso.sum()) for k in ["derecha", "tierra", "fuera", "izquierda"]}
    return lineas, destino, peso, frac
