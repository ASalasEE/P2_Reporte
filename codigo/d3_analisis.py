"""Discontinuidad 3 (gap en serie): todos los numeros del reporte.

Lee los CSV de HFSS, corrige el error de puerto con la linea de referencia,
extrae el circuito pi (Cg en serie, Cp en derivacion), separa la potencia
y guarda
  d3_nums.json   valores que cita el reporte
  d3_datos.npz   curvas corregidas para las figuras
"""
import json, math
import numpy as np
import load_d2 as L
from correccion import corregir

L.D = "datos/P2_D3_Gap_CSV"
ER, H, W = 3.55, 0.508, 1.14
GAPS = [0.1, 0.2, 0.5, 1.0, 3.0]
ET = lambda s: ("%.1f" % s).replace(".", "p")
NOMB = {s: "B%d_Gap_%s" % (i + 1, ET(s)) for i, s in enumerate(GAPS)}
C0 = 299792458.0
R = {n: L.cargar(n) for n in ["A1_Ref50", "A1_Ref50_SinPerd"] + [NOMB[s] + x for s in GAPS for x in ["", "_SinPerd"]]}
f = R["A1_Ref50"]["f"]
w = 2 * np.pi * f * 1e9
N = {}


def idx(q):
    return int(np.argmin(np.abs(f - q)))


# ------------------------- linea y formulas cerradas ------------------
wh = W / H
ee = (ER + 1) / 2 + (ER - 1) / 2 / math.sqrt(1 + 12 / wh)
Z0q = 120 * math.pi / (math.sqrt(ee) * (wh + 1.393 + 0.667 * math.log(wh + 1.444)))
Cp1 = math.sqrt(ee) / (C0 * Z0q)                       # F/m


def garg_bahl(s):
    """Garg y Bahl (en Gupta et al.): 0.5<=W/h<=2, 2.5<=er<=15, 0.1<=s/W<=1."""
    r = s / W
    mo = wh * (0.619 * math.log10(wh) - 0.3853)
    ko = 4.26 - 1.453 * math.log10(wh)
    if r <= 0.3:
        me, ke = 0.8675, 2.043 * wh ** 0.12
    else:
        me, ke = 1.565 / wh ** 0.16 - 1, 1.97 - 0.03 / wh
    Co = (ER / 9.6) ** 0.8 * r ** mo * math.exp(ko) * W * 1e-15     # pF/m * mm -> F
    Ce = 12 * (ER / 9.6) ** 0.9 * r ** me * math.exp(ke) * W * 1e-15
    return 0.5 * Co - 0.25 * Ce, 0.5 * Ce                           # Cg, Cp


dl_oc = 0.412 * H * (ee + 0.3) * (wh + 0.264) / ((ee - 0.258) * (wh + 0.8))   # Hammerstad, mm
Coc = dl_oc * 1e-3 * Cp1
N.update(DLOC="%.3f" % dl_oc, COC="%.1f" % (Coc * 1e15), CP1Q="%.0f" % (Cp1 * 1e12))

# ------------------------- convergencia -------------------------------
filas, nmax = [], 0
for nombre, lab in [("A1_Ref50", "Referencia \\SI{50}{\\ohm}"), ("A1_Ref50_SinPerd", "Referencia, sin pérdidas")] + \
        [(NOMB[s] + x, "Gap $s=\\SI{%g}{mm}$%s" % (s, ", sin pérdidas" if x else "")) for s in GAPS for x in ["", "_SinPerd"]]:
    c = L.conv(nombre)
    p, n, ds = c[-1]
    nmax = max(nmax, n)
    marca = "$^{\\dagger}$" if (p == 15 and not (c[-2][2] is not None and c[-2][2] < 0.005 and ds < 0.005)) else ""
    filas.append(r"%s & %d & \num{%d} & %.4f%s \\" % (lab, p, n, ds, marca))
N["CONVROWS3"] = "\n".join(filas)
N["NMAX3"] = "%d" % nmax
N["DSMAX3"] = "%.4f" % max(L.conv(NOMB[s] + x)[-1][2] for s in GAPS for x in ["", "_SinPerd"])

# ------------------------- correccion y circuito pi -------------------
Cc = {}
for s in GAPS:
    Cc[NOMB[s]] = corregir(R[NOMB[s]], R["A1_Ref50"], R["A1_Ref50"])
    Cc[NOMB[s] + "_SinPerd"] = corregir(R[NOMB[s] + "_SinPerd"], R["A1_Ref50_SinPerd"], R["A1_Ref50_SinPerd"])
# residuo de la referencia corregida con su propia caja (exactitud de la correccion)
cref = corregir(R["A1_Ref50_SinPerd"], R["A1_Ref50_SinPerd"], R["A1_Ref50_SinPerd"])
res = float(np.max(np.abs(cref["S11"])))
N["RESREF3"] = "%.4f" % res


def pi(c, Z1, Z2):
    Cg, Cpa, Cpb = np.zeros(len(f)), np.zeros(len(f)), np.zeros(len(f))
    for k in range(len(f)):
        S = np.array([[c["S11"][k], c["S12"][k]], [c["S21"][k], c["S22"][k]]])
        y = np.diag(1 / np.sqrt([Z1[k], Z2[k]]))
        Y = y @ (np.eye(2) - S) @ np.linalg.inv(np.eye(2) + S) @ y
        Y21 = 0.5 * (Y[1, 0] + Y[0, 1])
        Cg[k] = -Y21.imag / w[k]
        Cpa[k] = (Y[0, 0] + Y21).imag / w[k]
        Cpb[k] = (Y[1, 1] + Y21).imag / w[k]
    return Cg, Cpa, Cpb


banda = (f >= 3) & (f <= 15)
circ, curvas = {}, {}
for s in GAPS:
    vals = []
    for x in ["", "_SinPerd"]:
        n = NOMB[s] + x
        Cg, Cpa, Cpb = pi(Cc[n], R[n]["Z1"].real, R[n]["Z2"].real)
        curvas[n] = (Cg, 0.5 * (Cpa + Cpb))
        vals.append((Cg[banda].mean(), 0.5 * (Cpa + Cpb)[banda].mean(), Cg[banda].std(), (0.5 * (Cpa + Cpb))[banda].std()))
    Cg_m = np.mean([v[0] for v in vals]); Cp_m = np.mean([v[1] for v in vals])
    eCg = max(abs(vals[0][0] - vals[1][0]) / 2, max(v[2] for v in vals))
    eCp = max(abs(vals[0][1] - vals[1][1]) / 2, max(v[3] for v in vals))
    circ[s] = dict(Cg=Cg_m, Cp=Cp_m, eCg=eCg, eCp=eCp, gb=garg_bahl(s) if s <= 1.0 else None)

Z0n = 50.0
filas = []
for s in GAPS:
    c = circ[s]
    fcorte = 1 / (2 * math.pi * 2 * Z0n * c["Cg"]) / 1e9 if c["Cg"] > 0 else float("inf")
    cg = ("%.1f $\\pm$ %.1f" % (c["Cg"] * 1e15, c["eCg"] * 1e15)) if c["Cg"] * 1e15 > 1 else "$<1$"
    cp = "%.1f $\\pm$ %.1f" % (c["Cp"] * 1e15, c["eCp"] * 1e15)
    if c["gb"]:
        gb = "%.1f & %.1f" % (c["gb"][0] * 1e15, c["gb"][1] * 1e15)
    else:
        gb = "--- & %.1f$^{\\ddagger}$" % (Coc * 1e15)
    fc = ("%.0f" % fcorte) if fcorte < 1000 else "---"
    filas.append(r"%.1f & %.2f & %s & %s & %s & %s \\" % (s, s / W, cg, cp, gb, fc))
N["CIRCROWS"] = "\n".join(filas)
for s in GAPS:
    k = ET(s).upper()
    N["CG" + k] = "%.0f" % (circ[s]["Cg"] * 1e15) if circ[s]["Cg"] * 1e15 >= 1 else "%.1f" % (circ[s]["Cg"] * 1e15)
    N["CP" + k] = "%.0f" % (circ[s]["Cp"] * 1e15)
    N["CT" + k] = "%.0f" % ((circ[s]["Cp"] + circ[s]["Cg"]) * 1e15)
    if circ[s]["gb"]:
        N["CGGB" + k] = "%.0f" % (circ[s]["gb"][0] * 1e15)
        N["CPGB" + k] = "%.0f" % (circ[s]["gb"][1] * 1e15)
N["FCORTE0P1"] = "%.0f" % (1 / (2 * math.pi * 2 * Z0n * circ[0.1]["Cg"]) / 1e9)
N["FCORTE0P2"] = "%.0f" % (1 / (2 * math.pi * 2 * Z0n * circ[0.2]["Cg"]) / 1e9)
gbr = [circ[s]["Cg"] / circ[s]["gb"][0] for s in GAPS if circ[s]["gb"]]
N["RGBMIN"], N["RGBMAX"] = "%.1f" % min(gbr), "%.1f" % max(gbr)
N["DLEXT"] = "%.2f" % (circ[3.0]["Cp"] / Cp1 * 1e3)     # mm

# ------------------------- parametros S -------------------------------
db = lambda x: 20 * np.log10(np.abs(x))
filas = []
for q in [1, 5, 10, 20]:
    i = idx(q)
    fila = ["%g" % q]
    for s in GAPS:
        c = Cc[NOMB[s]]
        fila += ["%.3f" % min(abs(c["S11"][i]), 1.0), "%.1f" % db(c["S21"][i])]
    filas.append(" & ".join(fila) + r" \\")
N["SROWS3"] = "\n".join(filas)
c1 = Cc[NOMB[0.1]]
s21 = db(c1["S21"])
i10 = np.where(s21 > -10)[0]
N["F10DB"] = "%.1f" % f[i10[0]] if len(i10) else "---"
N["S21G1_1"], N["S21G1_20"] = "%.1f" % s21[idx(1)], "%.1f" % s21[idx(20)]
N["S21G5_1"], N["S21G5_20"] = "%.0f" % db(Cc[NOMB[3.0]]["S21"][idx(1)]), "%.0f" % db(Cc[NOMB[3.0]]["S21"][idx(20)])
N["S21G2_20"] = "%.1f" % db(Cc[NOMB[0.2]]["S21"][idx(20)])
N["S21G4_20"] = "%.1f" % db(Cc[NOMB[1.0]]["S21"][idx(20)])
# pendiente entre 1 y 10 GHz (dB por decada)
pend = [(db(Cc[NOMB[s]]["S21"][idx(10)]) - db(Cc[NOMB[s]]["S21"][idx(1)])) for s in [0.1, 0.2, 0.5, 1.0]]
N["PENDMIN"], N["PENDMAX"] = "%.0f" % min(pend), "%.0f" % max(pend)
N["G1_20"] = "%.3f" % abs(c1["S11"][idx(20)])
N["VSWRG1_20"] = "%.1f" % ((1 + abs(c1["S11"][idx(20)])) / (1 - abs(c1["S11"][idx(20)])))
N["PR1_20"] = "%.0f" % (100 * abs(c1["S11"][idx(20)]) ** 2)
N["GMIN3"] = "%.3f" % min(abs(Cc[NOMB[s]]["S11"][f <= 20]).min() for s in GAPS)
N["PT1_20"] = "%.0f" % (100 * abs(c1["S21"][idx(20)]) ** 2)
N["ANG5_10"] = "%.0f" % np.degrees(np.angle(Cc[NOMB[3.0]]["S11"][idx(10)]))

# ------------------------- potencia -----------------------------------
Prad = {s: 0.5 * (Cc[NOMB[s] + "_SinPerd"]["P1"] + Cc[NOMB[s] + "_SinPerd"]["P2"]) for s in GAPS}
Pdis = {s: 0.5 * (Cc[NOMB[s]]["P1"] + Cc[NOMB[s]]["P2"]) - Prad[s] for s in GAPS}
piso = 2 * res                      # error de |S11|^2 por el residuo de la correccion
N["PISO3"] = "%.0f" % (100 * piso) if piso >= 0.01 else "%.1f" % (100 * piso)
N["PRAD5"] = "%.1f" % np.mean([Prad[s][idx(5)] * 100 for s in GAPS])
N["PRAD10"] = "%.1f" % np.mean([Prad[s][idx(10)] * 100 for s in GAPS])
N["PRAD20MIN"] = "%.1f" % min(Prad[s][idx(20)] * 100 for s in GAPS)
N["PRAD20MAX"] = "%.1f" % max(Prad[s][idx(20)] * 100 for s in GAPS)
N["PDISMAX3"] = "%.1f" % max(Pdis[s][f <= 20].max() * 100 for s in GAPS)
pr1 = np.mean([Prad[s] for s in GAPS], axis=0)
N["F1PCT"] = "%.0f" % f[np.where(pr1 > 0.01)[0][0]]
filas = []
for s in [0.1, 1.0, 3.0]:
    c = Cc[NOMB[s]]
    for q in [5, 10, 20]:
        i = idx(q)
        filas.append(r"%s & %d & %.1f & %.2f & %.1f & %.1f \\" % (
            ("$s=\\SI{%g}{mm}$" % s) if q == 5 else "", q, 100 * abs(c["S11"][i]) ** 2,
            100 * abs(c["S21"][i]) ** 2, 100 * Prad[s][i], 100 * Pdis[s][i]))
    if s != 3.0:
        filas.append(r"\addlinespace")
N["POWROWS3"] = "\n".join(filas)

json.dump(N, open("d3_nums.json", "w"), indent=1, ensure_ascii=False)
np.savez("d3_datos.npz", f=f, gaps=np.array(GAPS),
         **{"%s_%s" % (k, q): v[q] for k, v in Cc.items() for q in ["S11", "S21", "S12", "S22"]},
         **{"Prad_%s" % ET(s): Prad[s] for s in GAPS}, **{"Pdis_%s" % ET(s): Pdis[s] for s in GAPS},
         **{"Cg_%s" % k: v[0] for k, v in curvas.items()}, **{"Cp_%s" % k: v[1] for k, v in curvas.items()},
         Cg=np.array([circ[s]["Cg"] for s in GAPS]), Cp=np.array([circ[s]["Cp"] for s in GAPS]),
         eCg=np.array([circ[s]["eCg"] for s in GAPS]), eCp=np.array([circ[s]["eCp"] for s in GAPS]),
         Z1=R[NOMB[0.1]]["Z1"].real, Coc=Coc, piso=piso)
for k in sorted(N):
    if "ROWS" not in k:
        print(k, N[k])
print(N["CIRCROWS"]); print(N["SROWS3"]); print(N["POWROWS3"]); print(N["CONVROWS3"])
