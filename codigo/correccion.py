"""Correccion del error de puerto con las lineas de referencia (2x-thru).

Cada referencia A_k es una linea recta de impedancia k con los planos de
referencia de-embebidos hasta el centro (linea de longitud cero). Lo que
HFSS da para ella es solo el error numerico de los puertos:
  - un pequeno desacople g entre el modo 2D del puerto y la linea en la
    malla 3D, que aparece como S11_A = g (e^{2j b L1} - e^{-2j b L1})
  - un error de fase y de potencia en la transmision, S21_A != 1.
Con eso se arma una caja de error por lado y se quita de cada diseno.
"""
import numpy as np
from load_d2 import C0

L1 = 6.0e-3


def ajustar_g(r, orden=3):
    """g(f) como polinomio complejo en f, por minimos cuadrados."""
    f = r["f"]; b = r["g1"].imag
    base = np.exp(2j * b * L1) - np.exp(-2j * b * L1)
    x = f / 20.0
    A = np.vstack([base * x ** n for n in range(orden + 1)]).T
    yv = 0.5 * (r["S11"] + r["S22"])
    coef, *_ = np.linalg.lstsq(A, yv, rcond=None)
    g = sum(coef[n] * x ** n for n in range(orden + 1))
    return g, A @ coef


def caja_error(r):
    """Caja de error (puerto externo = 1, lado interno = 2)."""
    g, _ = ajustar_g(r)
    b = r["g1"].imag
    E11 = g * np.exp(2j * b * L1)
    E22 = -g * np.exp(-2j * b * L1)
    S21 = 0.5 * (r["S21"] + r["S12"])
    E21 = np.sqrt(S21 * (1 - E22 ** 2))
    # rama continua cercana a +1
    E21 = np.where(np.real(E21) < 0, -E21, E21)
    return E11, E21, E22


def s2t(S11, S21, S12, S22):
    return np.array([[S12 * S21 - S11 * S22, S11], [-S22, np.ones_like(S11)]]) / S21


def t2s(T):
    T11, T12, T21, T22 = T[0, 0], T[0, 1], T[1, 0], T[1, 1]
    return T12 / T22, (T11 * T22 - T12 * T21) / T22, 1 / T22, -T21 / T22


def inv2(T):
    det = T[0, 0] * T[1, 1] - T[0, 1] * T[1, 0]
    return np.array([[T[1, 1], -T[0, 1]], [-T[1, 0], T[0, 0]]]) / det


def mult(A, B):
    return np.einsum("ijf,jkf->ikf", A, B)


def corregir(r, ref1, ref2):
    """Quita las cajas de error de los puertos 1 (ref1) y 2 (ref2)."""
    a11, a21, a22 = caja_error(ref1)
    b11, b21, b22 = caja_error(ref2)
    TA = s2t(a11, a21, a21, a22)
    TB = s2t(b22, b21, b21, b11)          # caja del puerto 2, vista desde dentro
    TM = s2t(r["S11"], r["S21"], r["S12"], r["S22"])
    TS = mult(mult(inv2(TA), TM), inv2(TB))
    S11, S21, S12, S22 = t2s(TS)
    out = dict(r)
    out.update(S11=S11, S21=S21, S12=S12, S22=S22,
               P1=1 - abs(S11) ** 2 - abs(S21) ** 2, P2=1 - abs(S22) ** 2 - abs(S12) ** 2)
    return out


def corregir_n(S, cajas):
    """Correccion de N puertos: S[i, j, f] medida y una caja de error por
    puerto, (E11 externa, E21, E22 interna). Con D00, D01=D10 y D11
    diagonales, S_m = D00 + D01 S (I - D11 S)^-1 D10, de donde
    X = D01^-1 (S_m - D00) D10^-1 y S = (I + X D11)^-1 X."""
    n, _, nf = S.shape
    out = np.zeros_like(S)
    for k in range(nf):
        e00 = np.array([c[0][k] for c in cajas]); e01 = np.array([c[1][k] for c in cajas])
        e11 = np.array([c[2][k] for c in cajas])
        X = (S[:, :, k] - np.diag(e00)) / np.outer(e01, e01)
        out[:, :, k] = np.linalg.solve(np.eye(n) + X @ np.diag(e11), X)
    return out
