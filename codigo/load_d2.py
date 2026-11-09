"""Lectura de los CSV de HFSS de la discontinuidad 2 (escalon de ancho)."""
import csv, os, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.environ.get("D2_CSV", os.path.join(AQUI, "datos", "P2_D2_Escalon_CSV"))
DES = ["A1_Ref50", "A2_Ref100", "A1_Ref50_SinPerd", "A2_Ref100_SinPerd", "B_Escalon", "B0_Escalon_SinPerd",
       "C_Transicion", "C0_Transicion_SinPerd"]
C0 = 299792458.0


def _tabla(nombre):
    p = os.path.join(D, nombre)
    if not os.path.exists(p):
        return None
    filas = list(csv.reader(open(p)))
    return np.array([[float(x) for x in r] for r in filas[1:] if r])


def cargar(d):
    t = _tabla(d + "__08_S_complejos.csv")
    if t is None:
        return None
    f = t[:, 0]
    S11 = t[:, 1] + 1j * t[:, 2]; S21 = t[:, 3] + 1j * t[:, 4]
    S12 = t[:, 5] + 1j * t[:, 6]; S22 = t[:, 7] + 1j * t[:, 8]
    z = _tabla(d + "__06_Zo_puertos.csv")
    g = _tabla(d + "__09_Gamma_puertos.csv")
    r = dict(f=f, S11=S11, S21=S21, S12=S12, S22=S22,
             Z1=z[:, 1] + 1j * z[:, 2], Z2=z[:, 3] + 1j * z[:, 4],
             g1=g[:, 1] + 1j * g[:, 2], g2=g[:, 3] + 1j * g[:, 4])
    k0 = 2 * np.pi * f * 1e9 / C0
    r["ee1"] = (r["g1"].imag / k0) ** 2
    r["ee2"] = (r["g2"].imag / k0) ** 2
    r["P1"] = 1 - abs(S11) ** 2 - abs(S21) ** 2
    r["P2"] = 1 - abs(S22) ** 2 - abs(S12) ** 2
    return r


def todos():
    return {d: cargar(d) for d in DES}


def conv(d):
    p = os.path.join(D, d + "__convergencia.txt")
    if not os.path.exists(p):
        return None
    filas = []
    for line in open(p):
        s = [x.strip() for x in line.split("|")]
        if len(s) >= 3 and s[0].isdigit():
            filas.append((int(s[0]), int(s[1]), None if s[2] == "N/A" else float(s[2])))
    return filas
