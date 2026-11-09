"""Lectura de los CSV de HFSS de la discontinuidad 5 (union en T), de N puertos.
El orden de las columnas se toma del encabezado de cada CSV."""
import csv, os, re
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "datos", "P2_D5_T_CSV")
C0 = 299792458.0


def _tabla(nombre):
    p = os.path.join(D, nombre)
    if not os.path.exists(p):
        return None, None
    filas = list(csv.reader(open(p)))
    return filas[0], np.array([[float(x) for x in r] for r in filas[1:] if r])


def cargar(d):
    """Devuelve f, S[i, j, f] (indices desde 0), Z[i, f], gamma[i, f] y er_ef[i, f]."""
    enc, t = _tabla(d + "__08_S_complejos.csv")
    f = t[:, 0]
    idx = {}
    for k, h in enumerate(enc):
        m = re.match(r"\s*(re|im)\(S\((\d+),(\d+)\)\)", h)
        if m:
            idx[(m.group(1), int(m.group(2)), int(m.group(3)))] = k
    n = max(i for _, i, _ in idx)
    S = np.zeros((n, n, len(f)), complex)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            S[i - 1, j - 1] = t[:, idx[("re", i, j)]] + 1j * t[:, idx[("im", i, j)]]

    def pares(archivo, clave):
        enc2, t2 = _tabla(d + archivo)
        out = np.zeros((n, len(f)), complex)
        for i in range(1, n + 1):
            kr = [k for k, h in enumerate(enc2) if re.match(r"\s*re\(%s\(%d(:1)?\)\)" % (clave, i), h)][0]
            ki = [k for k, h in enumerate(enc2) if re.match(r"\s*im\(%s\(%d(:1)?\)\)" % (clave, i), h)][0]
            out[i - 1] = t2[:, kr] + 1j * t2[:, ki]
        return out
    Z = pares("__06_Zo_puertos.csv", "Zo")
    g = pares("__09_Gamma_puertos.csv", "Gamma")
    k0 = 2 * np.pi * f * 1e9 / C0
    return dict(f=f, S=S, n=n, Z=Z, g=g, ee=(g.imag / k0) ** 2)


def a_dos(r):
    """Formato del cargador de dos puertos (para reutilizar correccion.py)."""
    S = r["S"]
    return dict(f=r["f"], S11=S[0, 0], S21=S[1, 0], S12=S[0, 1], S22=S[1, 1],
                Z1=r["Z"][0], Z2=r["Z"][1], g1=r["g"][0], g2=r["g"][1], ee1=r["ee"][0], ee2=r["ee"][1])


def conv(d):
    p = os.path.join(D, d + "__convergencia.txt")
    filas = []
    for line in open(p):
        s = [x.strip() for x in line.split("|")]
        if len(s) >= 3 and s[0].isdigit():
            filas.append((int(s[0]), int(s[1]), None if s[2] == "N/A" else float(s[2])))
    return filas
