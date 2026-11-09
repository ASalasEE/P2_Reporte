"""Discontinuidad 4: campos de HFSS a 5 GHz junto a la union de dos
sustratos (carga, corriente y voltaje a lo largo de la linea, y E y D en el
corte vertical por el eje)."""
import os
import numpy as np

D = os.path.join("datos", "P2_D4_Material_CSV", "campos")
EPS0 = 8.8541878128e-12
ER1 = 3.55
W1, L1, H = 1.14, 6.0, 0.508


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


def suavizar(x, v, ancho=0.1):
    """Media movil de ancho fijo, sin mezclar los dos lados de la union."""
    out = np.array(v, dtype=complex)
    for lado in (x < L1, x >= L1):
        xi, vi = x[lado], v[lado]
        out[lado] = [np.mean(vi[np.abs(xi - x0) <= ancho / 2]) for x0 in xi]
    return out


def superficie(nombre, er2, w2):
    """rho_s y J_s sobre la traza (planos z = h +- 0.02 mm) y q(x), I(x)."""
    xs, ys, Eb = fasor(nombre, "E_abajo")
    _, _, Ea = fasor(nombre, "E_arriba")
    _, _, Hb = fasor(nombre, "H_abajo")
    _, _, Ha = fasor(nombre, "H_arriba")
    X, Y = np.meshgrid(xs, ys)
    er = np.where(X < L1 - 1e-6, ER1, np.where(X > L1 + 1e-6, er2, np.nan))
    rho = EPS0 * (Ea[..., 2] - er * Eb[..., 2])
    dH = Ha - Hb
    Jx, Jy = -dH[..., 1], dH[..., 0]
    m = np.abs(Y) <= np.where(X < L1, W1, w2) / 2 + 1e-9
    dy = (ys[1] - ys[0]) * 1e-3
    q = np.nansum(np.where(m, rho, 0), axis=0) * dy
    I = np.nansum(np.where(m, Jx, 0), axis=0) * dy
    ok = np.abs(xs - L1) > 1e-6                     # en x = L1 el sustrato no esta definido
    xs_, q_, I_ = xs[ok], q[ok], I[ok]
    ref = (xs_ >= 4.6) & (xs_ <= 5.4)
    qs, Is = suavizar(xs_, q_), suavizar(xs_, I_)
    brazo = m & (X >= 4.6) & (X <= 5.4)
    rref = np.nanmean(np.abs(rho[brazo]))
    return dict(xs=xs, ys=ys, X=X, Y=Y, m=m, S=np.where(m, np.abs(rho) / rref, np.nan),
                x=xs_, q=qs / np.mean(np.abs(qs[ref])), I=Is / np.mean(np.abs(Is[ref])),
                q_abs=qs, I_abs=Is)


def vertical(nombre, er2):
    """|E| y |D| en el plano y = 0 y el voltaje V(x) = integral de Ez bajo la tira."""
    xs, zs, E = fasor(nombre, "E_vertical", ejes=(0, 2))
    X, Z = np.meshgrid(xs, zs)
    er = np.where(Z < H, np.where(X < L1, ER1, er2), 1.0)
    Em = np.sqrt(np.abs(E[..., 0]) ** 2 + np.abs(E[..., 2]) ** 2)
    Dm = er * Em / ER1                              # |D| / (eps0 eps_r1)
    zona = (X >= 4.85) & (X <= 5.3) & (Z >= 0.1) & (Z <= 0.4)
    ref = np.nanmean(Em[zona])
    bajo = zs < H
    dz = (zs[1] - zs[0]) * 1e-3
    V = -np.trapezoid(E[bajo, :, 2], dx=dz, axis=0)
    V = V * H / zs[bajo][-1]                       # la rejilla llega a 0.50 mm; se escala a h
    refv = (xs >= 4.85) & (xs <= 5.4)
    Vs = suavizar(xs, V)
    return dict(xs=xs, zs=zs, X=X, Z=Z, E=Em / ref, D=Dm / ref, V=Vs / np.mean(np.abs(Vs[refv])), V_abs=Vs)
