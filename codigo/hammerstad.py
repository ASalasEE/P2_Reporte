"""Modelo de la union en T de Hammerstad (1981), en la forma en que lo
implementa el simulador Qucs (mstee.cpp): susceptancia en derivacion B_T en
el nodo central, transformadores T_a y T_b en los brazos principales y tramos
de linea La, Lb, L2 (que pueden ser negativos) que desplazan los planos de
referencia hasta los bordes del cuadro de union.

Entradas por frecuencia: impedancia y er_ef de cada brazo (a, b principales;
2 la rama), espesor h y anchos (en metros)."""
import numpy as np

ZF0 = 376.730313
C0 = 299792458.0


def parametros(f, h, er, Wa, Wb, W2, Za, Zb, Z2, ea, eb, e2):
    Da = ZF0 / Za * h / np.sqrt(ea)
    Db = ZF0 / Zb * h / np.sqrt(eb)
    D2 = ZF0 / Z2 * h / np.sqrt(e2)
    fpa = 0.4e6 * Za / h
    fpb = 0.4e6 * Zb / h
    lda = C0 / np.sqrt(ea) / f
    ldb = C0 / np.sqrt(eb) / f
    da = 0.055 * D2 * Za / Z2 * (1 - 2 * Za / Z2 * (f / fpa) ** 2)
    db = 0.055 * D2 * Zb / Z2 * (1 - 2 * Zb / Z2 * (f / fpb) ** 2)
    La = 0.5 * W2 - da
    Lb = 0.5 * W2 - db
    r = np.sqrt(Za * Zb) / Z2
    q = f ** 2 / fpa / fpb
    d2 = np.sqrt(Da * Db) * (0.5 - r * (0.05 + 0.7 * np.exp(-1.6 * r) + 0.25 * r * q - 0.17 * np.log(r)))
    L2 = 0.5 * max(Wa, Wb) - d2
    Ta2 = np.maximum(1 - np.pi * (f / fpa) ** 2 * ((Za / Z2) ** 2 / 12 + (0.5 - d2 / Da) ** 2), 1e-30)
    Tb2 = np.maximum(1 - np.pi * (f / fpb) ** 2 * ((Zb / Z2) ** 2 / 12 + (0.5 - d2 / Db) ** 2), 1e-30)
    Bt = (5.5 * (er + 2) / er * 0.5 * (da * Da / (Ta2 * lda) + db * Db / (Tb2 * ldb)) / (D2 * Z2) *
          (1 + 0.9 * np.log(r) + 4.5 * r * q - 4.4 * np.exp(-1.3 * r) - 20 * (Z2 / ZF0) ** 2))
    return dict(La=La, Lb=Lb, L2=L2, Ta2=Ta2, Tb2=Tb2, Bt=Bt, da=da, db=db, d2=d2)


def matriz_s(f, p, Zl, beta, Zr):
    """S de tres puertos (a, b, 2) referida a las impedancias Zr de los
    puertos. Zl[k] y beta[k] son la impedancia y la constante de fase de la
    linea de cada brazo (para los tramos La, Lb, L2)."""
    n = len(f)
    S = np.zeros((3, 3, n), complex)
    for k in range(n):
        T = [np.sqrt(p["Ta2"][k]), np.sqrt(p["Tb2"][k]), 1.0]
        u = np.array([1 / T[0], 1 / T[1], 1 / T[2]])
        Zc = np.outer(u, u) / (1j * p["Bt"][k])                    # nodo central con B_T
        L = [p["La"][k], p["Lb"][k], p["L2"][k]]
        A = np.diag([np.cos(beta[i][k] * L[i]) for i in range(3)])
        B = np.diag([1j * Zl[i][k] * np.sin(beta[i][k] * L[i]) for i in range(3)])
        C = np.diag([1j * np.sin(beta[i][k] * L[i]) / Zl[i][k] for i in range(3)])
        Z = (A @ Zc + B) @ np.linalg.inv(C @ Zc + A)
        zr = np.diag(1 / np.sqrt([Zr[i][k] for i in range(3)]))
        z = zr @ Z @ zr
        S[:, :, k] = (z - np.eye(3)) @ np.linalg.inv(z + np.eye(3))
    return S


def ideal(Zr):
    """T sin parasitos: tres lineas unidas en un punto."""
    n = Zr.shape[1]
    S = np.zeros((3, 3, n), complex)
    for k in range(n):
        y = 1 / Zr[:, k]
        for i in range(3):
            for j in range(3):
                S[i, j, k] = (2 * np.sqrt(y[i] * y[j]) / y.sum()) - (1.0 if i == j else 0.0)
    return S
