"""Discontinuidad 2: carga y corriente superficiales sobre la traza a partir
de los campos exportados de HFSS (5 GHz), y metricas para el reporte."""
import os, math
import numpy as np

D = os.path.join("datos", "P2_D2_Escalon_CSV", "campos")
EPS0, ER = 8.8541878128e-12, 3.55
W1, W2, L1, LT, H = 1.14, 0.29, 6.0, 10.0, 0.508
NPERF = 24


def leer(nombre, campo, lado, fase):
    a = np.loadtxt(os.path.join(D, "%s__%s_%s_ph%d.fld" % (nombre, campo, lado, fase)), skiprows=2)
    x, y = a[:, 0] * 1e3, a[:, 1] * 1e3
    xs, ys = np.unique(np.round(x, 6)), np.unique(np.round(y, 6))
    ix = np.searchsorted(xs, np.round(x, 6)); iy = np.searchsorted(ys, np.round(y, 6))
    V = np.full((len(ys), len(xs), 3), np.nan)
    V[iy, ix, :] = a[:, 3:6]
    return xs, ys, V


def fasor(nombre, campo, lado):
    xs, ys, A0 = leer(nombre, campo, lado, 0)
    _, _, A90 = leer(nombre, campo, lado, 90)
    return xs, ys, A0 - 1j * A90


def _z(wh):
    ee = (ER + 1) / 2 + (ER - 1) / 2 / math.sqrt(1 + 12 / wh)
    if wh <= 1:
        return 60 / math.sqrt(ee) * math.log(8 / wh + wh / 4)
    return 120 * math.pi / (math.sqrt(ee) * (wh + 1.393 + 0.667 * math.log(wh + 1.444)))


def _ancho(z):
    a, b = 0.01, 20.0
    for _ in range(80):
        m = 0.5 * (a + b)
        if _z(m) > z:
            a = m
        else:
            b = m
    return 0.5 * (a + b) * H


def ancho_traza(x, tipo):
    """Ancho de la traza en cada x (mm), igual que en el script de HFSS."""
    if tipo == "escalon":
        return np.where(x < L1, W1, W2)
    z1, z2 = _z(W1 / H), _z(W2 / H)
    xp = [L1 + LT * i / NPERF for i in range(NPERF + 1)]
    wp = [W1] + [_ancho(z1 * math.exp(i / NPERF * math.log(z2 / z1))) for i in range(1, NPERF)] + [W2]
    return np.where(x < L1, W1, np.where(x > L1 + LT, W2, np.interp(x, xp, wp)))


def cargar(nombre, tipo):
    xs, ys, Eb = fasor(nombre, "E", "abajo")
    _, _, Ea = fasor(nombre, "E", "arriba")
    _, _, Hb = fasor(nombre, "H", "abajo")
    _, _, Ha = fasor(nombre, "H", "arriba")
    rho = EPS0 * (Ea[..., 2] - ER * Eb[..., 2])
    dH = Ha - Hb
    Jx, Jy = -dH[..., 1], dH[..., 0]
    X, Y = np.meshgrid(xs, ys)
    m = np.abs(Y) <= ancho_traza(X, tipo) / 2
    dy = ys[1] - ys[0]
    q = np.nansum(np.where(m, rho, 0), axis=0) * dy * 1e-3        # C/m (por unidad de longitud)
    I = np.nansum(np.where(m, Jx, 0), axis=0) * dy * 1e-3          # A
    brazo = (xs >= xs[0] + 0.15) & (xs <= xs[0] + 0.45)
    mb = m & brazo[None, :]
    rref = np.nanmean(np.abs(rho[mb]))
    Jm = np.sqrt(np.abs(Jx) ** 2 + np.abs(Jy) ** 2)
    jref = np.nanmean(Jm[mb])
    # direccion de la corriente: parte en fase con la corriente total de cada seccion
    # (quita el retardo de la onda a lo largo de la linea)
    ph = np.exp(-1j * np.angle(I))[None, :]
    return dict(xs=xs, ys=ys, X=X, Y=Y, m=m, rho=rho, Jx=Jx, Jy=Jy, q=q, I=I,
                S=np.where(m, np.abs(rho) / rref, np.nan), JN=np.where(m, Jm / jref, np.nan),
                JXr=np.where(m, np.real(Jx * ph), 0),
                JYr=np.where(m, np.real(Jy * ph), 0),
                rref=rref, jref=jref, brazo=brazo)


def metricas_escalon(r):
    X, Y, m, xs = r["X"], r["Y"], r["m"], r["xs"]
    c = W1 / 4
    hombro = m & (X >= L1 - c) & (X < L1) & (np.abs(Y) >= W1 / 2 - c)
    angosta = m & (X >= L1) & (X <= L1 + W2)
    lejos = m & (X >= 7.5) & (X <= 7.9)
    out = dict(Chom=float(np.nanmean(r["S"][hombro])), Jhom=float(np.nanmean(r["JN"][hombro])),
               Jang=float(np.nanmean(r["JN"][angosta]) / np.nanmean(r["JN"][lejos])),
               Jlejos=float(np.nanmean(r["JN"][lejos])))
    # fraccion de la corriente de la linea ancha que va por el centro (|y| < W2/2)
    k = np.argmin(np.abs(xs - (L1 - 0.03)))
    col = m[:, k]
    jc = np.abs(r["Jx"][:, k])
    out["Icentro"] = float(np.sum(jc[col & (np.abs(r["ys"]) <= W2 / 2)]) / np.sum(jc[col]))
    k0 = np.argmin(np.abs(xs - 4.3))
    col0 = m[:, k0]; jc0 = np.abs(r["Jx"][:, k0])
    out["Icentro_lejos"] = float(np.sum(jc0[col0 & (np.abs(r["ys"]) <= W2 / 2)]) / np.sum(jc0[col0]))
    # carga en exceso: q(x) menos la extrapolacion lineal de cada linea hasta el plano del escalon
    q = r["q"]
    a = (xs >= 4.1) & (xs <= 5.2); b = (xs >= 6.9) & (xs <= 7.9)
    pa = np.polyfit(xs[a], q[a], 1); pb = np.polyfit(xs[b], q[b], 1)
    ideal = np.where(xs < L1, np.polyval(pa, xs), np.polyval(pb, xs))
    zona = (xs > 5.2) & (xs < 6.9)
    dx = (xs[1] - xs[0]) * 1e-3
    Qexc = np.sum((q - ideal)[zona]) * dx
    q1 = np.polyval(pa, L1)
    out["DL"] = float(np.real(Qexc / q1) * 1e6)          # micrometros de linea de 50 ohm
    out["q2q1"] = float(np.abs(np.polyval(pb, L1) / q1))
    out["ideal"] = ideal
    return out


def metricas_transicion(r):
    X, Y, m, xs = r["X"], r["Y"], r["m"], r["xs"]
    # maximo de la carga en los bordes a lo largo de la transicion, respecto al brazo
    zona = (xs > L1 + 0.2) & (xs < L1 + LT - 0.2)
    borde = np.nanmax(np.where(m, r["S"], np.nan), axis=0)
    ref = np.nanmean(borde[r["brazo"]])
    return dict(Cbmax=float(np.nanmax(borde[zona]) / ref), Cbfin=float(np.nanmean(borde[xs > L1 + LT + 0.2]) / ref))
