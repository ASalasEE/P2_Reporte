"""Discontinuidad 5: campos del stub abierto (HFSS) a 5.5, 10.8 y 16.15 GHz.

Carga y corriente superficiales sobre el stub y la union, voltaje a lo largo
del stub y de la linea principal (integral de Ez bajo la tira) y
descomposicion del voltaje del stub en la onda que va hacia el extremo
abierto y la que regresa. Todo se normaliza a la onda incidente: con 1 W
en P1, V_inc = sqrt(2 P Z0)."""
import os
import numpy as np

D = os.path.join("datos", "P2_D5_Stub_Campos")
EPS0, ER, H = 8.8541878128e-12, 3.55, 0.508
W, L1, LS = 1.14, 6.0, 8.0
Y0 = W / 2                       # base del stub (plano de referencia de la rama)
FREQS = [("5p5GHz", 5.5), ("10p8GHz", 10.8), ("16p15GHz", 16.15)]


def _leer(archivo, ejes):
    a = np.loadtxt(os.path.join(D, archivo), skiprows=2)
    c1, c2 = a[:, ejes[0]] * 1e3, a[:, ejes[1]] * 1e3
    u1, u2 = np.unique(np.round(c1, 6)), np.unique(np.round(c2, 6))
    i1 = np.searchsorted(u1, np.round(c1, 6)); i2 = np.searchsorted(u2, np.round(c2, 6))
    V = np.full((len(u2), len(u1), 3), np.nan)
    V[i2, i1, :] = a[:, 3:6]
    return u1, u2, V


def fasor(tag, etiqueta, ejes=(0, 1)):
    u1, u2, A0 = _leer("Stub_%s__%s_ph0.fld" % (tag, etiqueta), ejes)
    _, _, A90 = _leer("Stub_%s__%s_ph90.fld" % (tag, etiqueta), ejes)
    return u1, u2, A0 - 1j * A90


def mascara(X, Y):
    principal = np.abs(Y) <= W / 2 + 1e-9
    stub = (X >= L1 - 1e-9) & (X <= L1 + W + 1e-9) & (Y >= 0) & (Y <= Y0 + LS + 1e-9)
    return principal | stub


def superficie(tag):
    xs, ys, Eb = fasor(tag, "E_abajo")
    _, _, Ea = fasor(tag, "E_arriba")
    _, _, Hb = fasor(tag, "H_abajo")
    _, _, Ha = fasor(tag, "H_arriba")
    rho = EPS0 * (Ea[..., 2] - ER * Eb[..., 2])
    dH = Ha - Hb
    Jx, Jy = -dH[..., 1], dH[..., 0]
    X, Y = np.meshgrid(xs, ys)
    m = mascara(X, Y)
    dx = (xs[1] - xs[0]) * 1e-3
    # a lo largo del stub: carga y corriente totales en cada seccion
    en_stub = (xs >= L1 - 1e-9) & (xs <= L1 + W + 1e-9)
    s = ys - Y0
    q = np.nansum(np.where(m[:, en_stub], rho[:, en_stub], 0), axis=1) * dx
    I = np.nansum(np.where(m[:, en_stub], Jy[:, en_stub], 0), axis=1) * dx
    # corriente de la linea principal a cada lado
    def sec_x(x0):
        k = np.argmin(np.abs(xs - x0))
        col = m[:, k] & (np.abs(ys) <= W / 2 + 1e-9)
        return np.nansum(Jx[col, k]) * dx
    return dict(xs=xs, ys=ys, X=X, Y=Y, m=m, rho=rho, Jx=Jx, Jy=Jy, s=s, q=q, I=I,
                Iin=sec_x(L1 - 1.5), Iout=sec_x(L1 + W + 1.5))


def voltajes(tag):
    ys, zs, E = fasor(tag, "E_vert_stub", ejes=(1, 2))
    bajo = zs < H
    dz = (zs[1] - zs[0]) * 1e-3
    Vs = -np.trapezoid(E[bajo, :, 2], dx=dz, axis=0) * H / zs[bajo][-1]
    xs, zl, El = fasor(tag, "E_vert_linea", ejes=(0, 2))
    bajo = zl < H
    Vl = -np.trapezoid(El[bajo, :, 2], dx=dz, axis=0) * H / zl[bajo][-1]
    return dict(s=ys - Y0, V=Vs, x=xs, Vl=Vl)


def ondas(s, V, gamma, s0=0.4, s1=7.4):
    """Ajusta V(s) = A e^{-gamma s} + B e^{+gamma s} (s en mm) entre s0 y s1:
    A es la onda que va hacia el extremo abierto y B la que regresa."""
    m = (s >= s0) & (s <= s1)
    sm = s[m] * 1e-3
    M = np.vstack([np.exp(-gamma * sm), np.exp(gamma * sm)]).T
    (A, B), *_ = np.linalg.lstsq(M, V[m], rcond=None)
    ajuste = A * np.exp(-gamma * s * 1e-3) + B * np.exp(gamma * s * 1e-3)
    err = np.sqrt(np.mean(np.abs(ajuste[m] - V[m]) ** 2)) / np.max(np.abs(V[m]))
    return A, B, ajuste, err
