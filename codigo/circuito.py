"""Circuito equivalente del escalon: L1 en serie (lado 50 ohm), C en
derivacion y L2 en serie (lado 100 ohm), ajustado a los parametros S
corregidos. k absorbe la diferencia, independiente de la frecuencia,
entre el cociente de impedancias de los puertos de HFSS y el real."""
import numpy as np
from scipy.optimize import least_squares


def s_tred(f, L1, L2, C, Z01, Z02):
    w = 2 * np.pi * f * 1e9
    one = np.ones_like(w, dtype=complex)
    a = [one, 1j * w * L1, 0 * one, one]
    def mul(p, q):
        return [p[0] * q[0] + p[1] * q[2], p[0] * q[1] + p[1] * q[3],
                p[2] * q[0] + p[3] * q[2], p[2] * q[1] + p[3] * q[3]]
    T = mul(mul(a, [one, 0 * one, 1j * w * C, one]), [one, 1j * w * L2, 0 * one, one])
    A, B, Cc, D = T
    den = A * Z02 + B + Cc * Z01 * Z02 + D * Z01
    S11 = (A * Z02 + B - Cc * Z01 * Z02 - D * Z01) / den
    S22 = (-A * Z02 + B - Cc * Z01 * Z02 + D * Z01) / den
    S21 = 2 * np.sqrt(Z01 * Z02) / den
    return S11, S21, S22


def ajustar(c, Z1, Z2, fmin=1.0, fmax=20.0):
    f = c["f"]; m = (f >= fmin) & (f <= fmax)
    def res(p):
        L1, L2, C, k = p[0] * 1e-12, p[1] * 1e-12, p[2] * 1e-15, p[3]
        S11, S21, S22 = s_tred(f[m], L1, L2, C, Z1[m], k * Z2[m])
        r = np.concatenate([S11 - c["S11"][m], S22 - c["S22"][m],
                            S21 - 0.5 * (c["S21"][m] + c["S12"][m])])
        return np.concatenate([r.real, r.imag])
    sol = least_squares(res, [15, 15, 8, 1.0])
    J = sol.jac; dof = max(1, len(sol.fun) - 4)
    s2 = np.sum(sol.fun ** 2) / dof
    try:
        cov = np.linalg.inv(J.T @ J) * s2
        err = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        err = np.full(4, np.nan)
    L1, L2, C, k = sol.x
    rms = np.sqrt(np.mean(sol.fun ** 2))
    return dict(L1=L1, L2=L2, C=C, k=k, eL1=err[0], eL2=err[1], eC=err[2], ek=err[3], rms=rms)


def gupta(W1, W2, h, er, Z1, Z2, ee1, ee2):
    """Formulas cerradas de Gupta et al. para el escalon (W1 > W2)."""
    r = W1 / W2
    C = ((10.1 * np.log10(er) + 2.33) * r - 12.6 * np.log10(er) - 3.17) * 1e-12 * np.sqrt(W1 * W2 * 1e-6)
    L = (40.5 * (r - 1) - 75 * np.log10(r) + 0.2 * (r - 1) ** 2) * 1e-9 * h * 1e-3
    c0 = 299792458.0
    Lw1, Lw2 = Z1 * np.sqrt(ee1) / c0, Z2 * np.sqrt(ee2) / c0
    return dict(C=C, L=L, L1=L * Lw1 / (Lw1 + Lw2), L2=L * Lw2 / (Lw1 + Lw2), r=r)


def ajustar_reparto(c, Z1, Z2, alfa, fmin=1.0, fmax=20.0):
    """Igual que ajustar(), pero con L1 = alfa*Ls y L2 = (1-alfa)*Ls.
    A primer orden en omega los datos solo fijan Ls = L1 + L2 y C; el
    reparto se toma proporcional a la inductancia por unidad de longitud
    de cada linea, como en Gupta et al."""
    f = c["f"]; m = (f >= fmin) & (f <= fmax)
    def res(p):
        Ls, C, k = p[0] * 1e-12, p[1] * 1e-15, p[2]
        S11, S21, S22 = s_tred(f[m], alfa * Ls, (1 - alfa) * Ls, C, Z1[m], k * Z2[m])
        r = np.concatenate([S11 - c["S11"][m], S22 - c["S22"][m],
                            S21 - 0.5 * (c["S21"][m] + c["S12"][m])])
        return np.concatenate([r.real, r.imag])
    sol = least_squares(res, [20, 8, 1.0])
    J = sol.jac; dof = max(1, len(sol.fun) - 3)
    cov = np.linalg.inv(J.T @ J) * np.sum(sol.fun ** 2) / dof
    err = np.sqrt(np.diag(cov))
    Ls, C, k = sol.x
    return dict(Ls=Ls, C=C, k=k, eLs=err[0], eC=err[1], ek=err[2],
                rms=float(np.sqrt(np.mean(sol.fun ** 2))), alfa=alfa)
