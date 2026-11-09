"""Discontinuidad 5 (union en T): carga y corriente superficiales junto a la
union a partir de los campos de HFSS a 5 GHz, y corriente que pasa por cada
brazo."""
import os
import numpy as np

D = os.path.join("datos", "P2_D5_T_CSV", "campos")
EPS0, ER = 8.8541878128e-12, 3.55
L1 = 6.0


def _leer(archivo):
    a = np.loadtxt(os.path.join(D, archivo), skiprows=2)
    x, y = a[:, 0] * 1e3, a[:, 1] * 1e3
    xs, ys = np.unique(np.round(x, 6)), np.unique(np.round(y, 6))
    ix = np.searchsorted(xs, np.round(x, 6)); iy = np.searchsorted(ys, np.round(y, 6))
    V = np.full((len(ys), len(xs), 3), np.nan)
    V[iy, ix, :] = a[:, 3:6]
    return xs, ys, V


def fasor(nombre, etiqueta):
    xs, ys, A0 = _leer("%s__%s_ph0.fld" % (nombre, etiqueta))
    _, _, A90 = _leer("%s__%s_ph90.fld" % (nombre, etiqueta))
    return xs, ys, A0 - 1j * A90


def mascara(X, Y, wb, ws):
    """Puntos sobre la traza: linea principal de ancho wb y rama de ancho ws."""
    principal = np.abs(Y) <= wb / 2 + 1e-9
    rama = (X >= L1 - 1e-9) & (X <= L1 + ws + 1e-9) & (Y >= 0)
    return principal | rama


def cargar(nombre, wb, ws, referencia):
    xs, ys, Eb = fasor(nombre, "E_abajo")
    _, _, Ea = fasor(nombre, "E_arriba")
    _, _, Hb = fasor(nombre, "H_abajo")
    _, _, Ha = fasor(nombre, "H_arriba")
    rho = EPS0 * (Ea[..., 2] - ER * Eb[..., 2])
    dH = Ha - Hb
    Jx, Jy = -dH[..., 1], dH[..., 0]
    X, Y = np.meshgrid(xs, ys)
    m = mascara(X, Y, wb, ws)
    dx = (xs[1] - xs[0]) * 1e-3
    # corrientes por secciones transversales de cada brazo (A)
    def sec_x(x0):
        k = np.argmin(np.abs(xs - x0))
        col = m[:, k] & (np.abs(ys) <= wb / 2 + 1e-9)
        return np.nansum(Jx[col, k]) * dx
    def sec_y(y0):
        k = np.argmin(np.abs(ys - y0))
        fil = m[k, :]
        return np.nansum(Jy[k, fil]) * dx
    x1, x2 = L1 - 1.2, L1 + ws + 1.2
    y3 = wb / 2 + 1.2
    I = {"izq": sec_x(x1), "der": sec_x(x2), "rama": sec_y(y3)}
    # referencia: brazo de entrada, lejos de la union
    if referencia == "izq":
        brazo = m & (X >= L1 - 1.45) & (X <= L1 - 1.05)
        Iref = I["izq"]
    else:
        brazo = m & (Y >= wb / 2 + 1.0) & (Y <= wb / 2 + 1.4)
        Iref = I["rama"]
    rref = np.nanmean(np.abs(rho[brazo]))
    Jm = np.sqrt(np.abs(Jx) ** 2 + np.abs(Jy) ** 2)
    jref = np.nanmean(Jm[brazo])
    ph = np.exp(-1j * np.angle(Iref))
    if referencia == "rama":
        ph = -ph            # que la corriente de la rama apunte hacia la union
    return dict(xs=xs, ys=ys, X=X, Y=Y, m=m, wb=wb, ws=ws,
                S=np.where(m, np.abs(rho) / rref, np.nan), JN=np.where(m, Jm / jref, np.nan),
                JXr=np.where(m, np.real(Jx * ph), 0), JYr=np.where(m, np.real(Jy * ph), 0),
                I=I, Iref=Iref, x1=x1, x2=x2, y3=y3, rho=rho, Jm=Jm)


def metricas(r):
    """Fracciones de corriente y concentraciones en la union."""
    I = r["I"]
    out = {k: float(abs(v / r["Iref"])) for k, v in I.items()}
    X, Y, m, wb, ws = r["X"], r["Y"], r["m"], r["wb"], r["ws"]
    c = 0.15
    # esquinas interiores de la rama (donde la corriente dobla)
    esq = m & (((np.abs(X - L1) <= c) | (np.abs(X - (L1 + ws)) <= c)) & (np.abs(Y - wb / 2) <= c))
    out["Jesq"] = float(np.nanmean(r["JN"][esq]))
    # borde opuesto a la rama, bajo la union
    opuesto = m & (X >= L1) & (X <= L1 + ws) & (Y <= -wb / 2 + c)
    out["Copuesto"] = float(np.nanmean(r["S"][opuesto]))
    out["Jopuesto"] = float(np.nanmean(r["JN"][opuesto]))
    # hombros: extremo de la rama que sobresale de la linea principal (divisor)
    hombro = m & (Y >= wb / 2) & (Y <= wb / 2 + c) & ((X <= L1 + c) | (X >= L1 + ws - c))
    out["Chombro"] = float(np.nanmean(r["S"][hombro]))
    cuadro = m & (X >= L1) & (X <= L1 + ws) & (np.abs(Y) <= wb / 2)
    out["Ccuadro"] = float(np.nanmean(r["S"][cuadro]))
    return out
