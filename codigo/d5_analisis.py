"""Discontinuidad 5 (union en T): numeros del reporte.

Lee los CSV de HFSS (3 puertos), corrige el error de puerto con las lineas
de referencia de 50 y 100 ohm, compara con la T ideal y con el modelo de
Hammerstad, calcula la capacitancia en exceso de la union, separa la
potencia radiada y predice el stub abierto a partir de la T, la linea y el
extremo abierto de la discontinuidad 3. Guarda
  d5_nums.json   valores que cita el reporte
  d5_datos.npz   curvas para las figuras
Requiere d3_datos.npz (d3_analisis.py)."""
import json, math
import numpy as np
import load_d5 as L
import hammerstad as HM
from correccion import corregir_n, caja_error

C0 = 299792458.0
H_M, W1, W2, LS = 0.508e-3, 1.14e-3, 0.29e-3, 8.0e-3
DIS = ["A1_Ref50", "A2_Ref100", "B_T", "C_Divisor", "D_Stub"]
R = {d + x: L.cargar(d + x) for d in DIS for x in ["", "_SinPerd"]}
f = R["B_T"]["f"]
fh = f * 1e9
w = 2 * np.pi * fh
N = {}
db = lambda x: 20 * np.log10(np.abs(x))
vswr = lambda g: (1 + np.abs(g)) / (1 - np.abs(g))


def idx(q):
    return int(np.argmin(np.abs(f - q)))


def cruce(y, umbral, desde=0.0):
    """Primera frecuencia (interpolada) a partir de 'desde' en que y supera el umbral."""
    m = np.where((f >= desde) & (y > umbral))[0]
    if not len(m):
        return None
    k = m[0]
    if k == 0:
        return f[0]
    return float(np.interp(umbral, [y[k - 1], y[k]], [f[k - 1], f[k]]))


# ------------------------- convergencia -------------------------------
ETQ = {"A1_Ref50": "Referencia \\SI{50}{\\ohm}", "A2_Ref100": "Referencia \\SI{100}{\\ohm}",
       "B_T": "T de \\SI{50}{\\ohm}", "C_Divisor": "Divisor en T", "D_Stub": "Stub abierto"}
filas, nmax = [], 0
for d in DIS:
    for x in ["", "_SinPerd"]:
        c = L.conv(d + x)
        p, n, ds = c[-1]
        nmax = max(nmax, n)
        filas.append(r"%s%s & %d & \num{%d} & %.4f \\" % (ETQ[d], ", sin pérdidas" if x else "", p, n, ds))
N["CONVROWS5"] = "\n".join(filas)
N["NMAX5"] = "%d" % nmax
N["NDIS5"] = "%d" % len(filas)

# ------------------------- correccion ---------------------------------
CAJA = {}
for x in ["", "_SinPerd"]:
    CAJA["50" + x] = caja_error(L.a_dos(R["A1_Ref50" + x]))
    CAJA["100" + x] = caja_error(L.a_dos(R["A2_Ref100" + x]))
C = {}
for x in ["", "_SinPerd"]:
    C["B_T" + x] = corregir_n(R["B_T" + x]["S"], [CAJA["50" + x]] * 3)
    C["C_Divisor" + x] = corregir_n(R["C_Divisor" + x]["S"], [CAJA["100" + x], CAJA["100" + x], CAJA["50" + x]])
    C["D_Stub" + x] = corregir_n(R["D_Stub" + x]["S"], [CAJA["50" + x]] * 2)
res = []
for d, k in [("A1_Ref50_SinPerd", "50_SinPerd"), ("A2_Ref100_SinPerd", "100_SinPerd")]:
    res.append(np.abs(corregir_n(R[d]["S"], [CAJA[k]] * 2)[0, 0]).max())
N["RESREF5"] = "%.4f" % max(res)
i5 = idx(5)
a50, a100 = R["A1_Ref50_SinPerd"], R["A2_Ref100_SinPerd"]
N["Z50"], N["Z100"] = "%.1f" % a50["Z"][0, i5].real, "%.1f" % a100["Z"][0, i5].real
N["CP50"] = "%.0f" % (np.sqrt(a50["ee"][0, i5]) / (C0 * a50["Z"][0, i5].real) * 1e12)
N["CW100"] = "%.0f" % (np.sqrt(a100["ee"][0, i5]) / (C0 * a100["Z"][0, i5].real) * W1 * 1e15)
N["CW"] = "%.0f" % (np.sqrt(a50["ee"][0, i5]) / (C0 * a50["Z"][0, i5].real) * W1 * 1e15)    # C' * W

# ------------------------- T de 50 ohm --------------------------------
B, B0 = C["B_T"], C["B_T_SinPerd"]
filas = []
for q in [0.1, 1, 5, 10, 15, 20]:
    i = idx(q)
    filas.append(r"%s & %.3f & %.2f & %.3f & %.3f & %.2f & %.3f & %.2f \\" % (
        ("%.1f" % q) if q < 1 else ("%.0f" % q), abs(B[0, 0, i]), vswr(B[0, 0, i]), abs(B[1, 0, i]), abs(B[2, 0, i]),
        db(B[1, 0, i] / B[2, 0, i]), abs(B[2, 2, i]), vswr(B[2, 2, i])))
N["SROWS5"] = "\n".join(filas)
i01, i20 = idx(0.1), idx(20)
N["B11_01"], N["B21_01"], N["B31_01"], N["B33_01"] = ["%.3f" % abs(B[i, j, i01]) for i, j in [(0, 0), (1, 0), (2, 0), (2, 2)]]
N["B11_20"], N["B21_20"], N["B31_20"], N["B33_20"] = ["%.3f" % abs(B[i, j, i20]) for i, j in [(0, 0), (1, 0), (2, 0), (2, 2)]]
N["VB1_01"] = "%.2f" % vswr(B[0, 0, i01])
N["VB3_20"] = "%.2f" % vswr(B[2, 2, i20])
N["S11B_01DB"] = "%.1f" % db(B[0, 0, i01])
N["PT21_20"], N["PT31_20"], N["PR11_20"] = ["%.0f" % (100 * abs(B[i, j, i20]) ** 2) for i, j in [(1, 0), (2, 0), (0, 0)]]
N["PT21_01"], N["PR11_01"] = "%.1f" % (100 * abs(B[1, 0, i01]) ** 2), "%.1f" % (100 * abs(B[0, 0, i01]) ** 2)
desb = db(B[1, 0] / B[2, 0])
N["DESB20"] = "%.2f" % desb[i20]
N["DESB10"] = "%.2f" % desb[idx(10)]
N["FDESB05"] = "%.1f" % cruce(desb, 0.5)
N["FDESB1"] = "%.1f" % cruce(desb, 1.0)
N["ANG21_20"] = "%.0f" % np.degrees(np.angle(B[1, 0, i20]))
N["ANG31_20"] = "%.0f" % np.degrees(np.angle(B[2, 0, i20]))
N["ANG11_20"] = "%.0f" % np.degrees(np.angle(B[0, 0, i20]))
# fase del tramo recto de longitud W a 20 GHz, para comparar con S21
N["FASEW20"] = "%.0f" % np.degrees(a50["g"][0, i20].imag * W1)
N["F33_20DB"] = "%.1f" % db(B[2, 2, i20])

# capacitancia en exceso vista desde la rama: Y_ent,3 - (1/Z1 + 1/Z2)
def c_exceso(S, Zr):
    y3 = (1 - S[2, 2]) / (1 + S[2, 2]) / Zr[2]
    return (y3 - 1 / Zr[0] - 1 / Zr[1]).imag / w


CE = {}
for d in ["B_T", "C_Divisor"]:
    # en la T de 50 ohm la susceptancia en exceso deja de ser proporcional a f
    # por encima de unos 5 GHz; se promedia donde si lo es
    banda = (f >= 2) & (f <= (5 if d == "B_T" else 15))
    vals = []
    for x in ["", "_SinPerd"]:
        ce = c_exceso(C[d + x], R[d + x]["Z"].real)
        CE[d + x] = ce
        vals.append(ce[banda])
    m = np.mean([v.mean() for v in vals])
    e = max(0.5 * abs(vals[0].mean() - vals[1].mean()), max(v.std() for v in vals))
    N["CE_" + d] = "%.0f" % (m * 1e15)
    N["ECE_" + d] = "%.0f" % max(e * 1e15, 1)

# ------------------------- modelo de Hammerstad ----------------------
Z50, e50, b50 = a50["Z"][0].real, a50["ee"][0], a50["g"][0].imag
Z100, e100, b100 = a100["Z"][0].real, a100["ee"][0], a100["g"][0].imag
HAM = {}
for d, Wm, Zm, em, bm in [("B_T", W1, Z50, e50, b50), ("C_Divisor", W2, Z100, e100, b100)]:
    p = HM.parametros(fh, H_M, 3.55, Wm, Wm, W1, Zm, Zm, Z50, em, em, e50)
    Zr = R[d + "_SinPerd"]["Z"].real
    HAM[d] = dict(S=HM.matriz_s(fh, p, [Zm, Zm, Z50], [bm, bm, b50], Zr), I=HM.ideal(Zr), p=p)
SH = HAM["B_T"]["S"]
N["H11_20"], N["H21_20"], N["H31_20"], N["H33_20"] = ["%.3f" % abs(SH[i, j, i20]) for i, j in [(0, 0), (1, 0), (2, 0), (2, 2)]]
N["HDESB20"] = "%.2f" % db(SH[1, 0, i20] / SH[2, 0, i20])
fases = []
for i, j in [(0, 0), (1, 0), (2, 0), (2, 2)]:
    dd = np.degrees(np.angle(B0[i, j] / SH[i, j]))
    fases.append(np.abs(dd[f <= 20]).max())
N["HFASEMAX"] = "%.0f" % max(fases)
N["HFASE21_20"] = "%.1f" % np.degrees(np.angle(SH[1, 0, i20]))
N["HCT10"] = "%.0f" % (HAM["B_T"]["p"]["Bt"][idx(10)] / w[idx(10)] * 1e15)
N["HCTC10"] = "%.0f" % (HAM["C_Divisor"]["p"]["Bt"][idx(10)] / w[idx(10)] * 1e15)
for d in ["B_T", "C_Divisor"]:
    S = HAM[d]["S"]; Zr = R[d + "_SinPerd"]["Z"].real
    y3 = (1 - S[2, 2]) / (1 + S[2, 2]) / Zr[2]
    ceh = (y3 - 1 / Zr[0] - 1 / Zr[1]).imag / w
    HAM[d]["CE"] = ceh
    bh = (f >= 2) & (f <= (5 if d == "B_T" else 15))
    N["HCE_" + d] = "%.0f" % (ceh[bh].mean() * 1e15)
N["CE_B_T20"] = "%.0f" % (0.5 * (CE["B_T"][i20] + CE["B_T_SinPerd"][i20]) * 1e15)
N["CE_B_T10"] = "%.0f" % (0.5 * (CE["B_T"][idx(10)] + CE["B_T_SinPerd"][idx(10)]) * 1e15)
N["RCW"] = "%.2f" % (float(N["CE_B_T"]) / float(N["CW"]))
N["HLA"] = "%.2f" % (HAM["B_T"]["p"]["La"][idx(1)] * 1e3)
N["HL2"] = "%.2f" % (HAM["B_T"]["p"]["L2"][idx(1)] * 1e3)

# ------------------------- divisor ------------------------------------
Cd, Cd0 = C["C_Divisor"], C["C_Divisor_SinPerd"]
g33 = np.abs(Cd[2, 2])
N["D33_1"], N["D33_5"], N["D33_10"], N["D33_15"], N["D33_20"] = ["%.3f" % g33[idx(q)] for q in (1, 5, 10, 15, 20)]
N["D33_20DB"] = "%.1f" % db(g33[i20])
N["FD20"] = "%.1f" % cruce(g33, 0.1)
N["D13_5"], N["D13_20"] = "%.3f" % abs(Cd[0, 2, i5]), "%.3f" % abs(Cd[0, 2, i20])
N["D13_5DB"], N["D13_20DB"] = "%.2f" % db(Cd[0, 2, i5]), "%.2f" % db(Cd[0, 2, i20])
N["D11_5"], N["D12_5"] = "%.3f" % abs(Cd[0, 0, i5]), "%.3f" % abs(Cd[0, 1, i5])
N["DANG33"] = "%.0f" % np.degrees(np.angle(Cd[2, 2, idx(10)]))
N["HD33_20"] = "%.3f" % abs(HAM["C_Divisor"]["S"][2, 2, i20])
N["DDESB20"] = "%.2f" % abs(db(Cd[0, 2, i20] / Cd[1, 2, i20]))
filas = []
for q in [0.1, 1, 5, 10, 15, 20]:
    i = idx(q)
    filas.append(r"%s & %.3f & %.2f & %.1f & %.3f & %.2f & %.3f & %.3f \\" % (
        ("%.1f" % q) if q < 1 else ("%.0f" % q), g33[i], vswr(g33[i]), db(g33[i]), abs(Cd[0, 2, i]),
        db(Cd[0, 2, i]), abs(Cd[0, 0, i]), abs(Cd[0, 1, i])))
N["DROWS5"] = "\n".join(filas)

# ------------------------- potencia -----------------------------------
def perdida(S, j):
    return 1 - np.sum(np.abs(S[:, j]) ** 2, axis=0)


Prad = {"B1": perdida(B0, 0), "B3": perdida(B0, 2), "C3": perdida(Cd0, 2),
        "D": 0.5 * (perdida(C["D_Stub_SinPerd"], 0) + perdida(C["D_Stub_SinPerd"], 1))}
Pdis = {"B1": perdida(B, 0) - Prad["B1"], "B3": perdida(B, 2) - Prad["B3"], "C3": perdida(Cd, 2) - Prad["C3"],
        "D": 0.5 * (perdida(C["D_Stub"], 0) + perdida(C["D_Stub"], 1)) - Prad["D"]}
piso = max(-min(v[f <= 8].min() for v in Prad.values()), 0.001)
N["PISO5"] = "%.1f" % (100 * piso)
for k in Prad:
    N["PRAD%s_10" % k] = "%.1f" % (100 * Prad[k][idx(10)])
    N["PRAD%s_20" % k] = "%.1f" % (100 * Prad[k][i20])
    N["PDIS%s_20" % k] = "%.1f" % (100 * Pdis[k][i20])
filas = []
for lab, k, S, j in [("T, desde P1", "B1", B, 0), ("T, desde P3", "B3", B, 2), ("Divisor, desde P3", "C3", Cd, 2)]:
    for q in [5, 10, 20]:
        i = idx(q)
        sal = [kk for kk in range(3) if kk != j]
        filas.append(r"%s & %d & %.1f & %.1f & %.1f & %.1f & %.1f \\" % (
            lab if q == 5 else "", q, 100 * abs(S[j, j, i]) ** 2, 100 * abs(S[sal[0], j, i]) ** 2,
            100 * abs(S[sal[1], j, i]) ** 2, 100 * Prad[k][i], 100 * Pdis[k][i]))
    if k != "C3":
        filas.append(r"\addlinespace")
N["POWROWS5"] = "\n".join(filas)

# ------------------------- stub abierto -------------------------------
SD, SD0 = C["D_Stub"], C["D_Stub_SinPerd"]
s21 = np.abs(SD[1, 0])
k1 = int(np.argmin(np.where(f < 10, s21, 9)))
k2 = int(np.argmin(np.where(f > 10, s21, 9)))
N["FN1"], N["FN2"] = "%.2f" % f[k1], "%.2f" % f[k2]
N["DN1"], N["DN2"] = "%.0f" % db(s21[k1]), "%.0f" % db(s21[k2])
N["DN1_0"] = "%.0f" % db(np.abs(SD0[1, 0])[k1])
N["RN21"] = "%.2f" % (f[k2] / f[k1])
N["G11N1"] = "%.3f" % abs(SD[0, 0, k1])
bw = f[(f < 10) & (s21 < 10 ** (-10 / 20))]
N["BW10A"], N["BW10B"] = "%.2f" % bw.min(), "%.2f" % bw.max()
bw3 = f[(f < 10) & (s21 < 10 ** (-3 / 20))]
N["BW3A"], N["BW3B"] = "%.2f" % bw3.min(), "%.2f" % bw3.max()
N["FS20"] = "%.2f" % cruce(np.abs(SD[0, 0]), 0.1)
N["S21D_1"] = "%.2f" % db(SD[1, 0, idx(1)])
N["S11D_1"] = "%.3f" % abs(SD[0, 0, idx(1)])
# prediccion: T + linea de 8 mm + extremo abierto (gap de 3 mm de la discontinuidad 3)
D3 = np.load("d3_datos.npz")
PRED = {}
for x in ["", "_SinPerd"]:
    g = R["A1_Ref50" + x]["g"][0]
    ee = R["A1_Ref50" + x]["ee"][0]
    wh = W1 / H_M
    dl = 0.412 * H_M * (ee + 0.3) * (wh + 0.264) / ((ee - 0.258) * (wh + 0.8))
    for lab, G0 in [("d3", D3["B5_Gap_3p0%s_S11" % x]), ("ham", np.exp(-2j * g.imag * dl))]:
        SB = C["B_T" + x]
        GL = G0 * np.exp(-2 * g * LS)
        PRED[lab + x] = (SB[0, 0] + SB[0, 2] * GL * SB[2, 0] / (1 - SB[2, 2] * GL),
                         SB[1, 0] + SB[1, 2] * GL * SB[2, 0] / (1 - SB[2, 2] * GL))
    N["DLHAM" + x.replace("_SinPerd", "0")] = "%.3f" % (dl.mean() * 1e3)
p21 = np.abs(PRED["d3"][1])
N["FP1"], N["FP2"] = "%.2f" % f[int(np.argmin(np.where(f < 10, p21, 9)))], "%.2f" % f[int(np.argmin(np.where(f > 10, p21, 9)))]
ph = np.abs(PRED["ham"][1])
N["FPH1"], N["FPH2"] = "%.2f" % f[int(np.argmin(np.where(f < 10, ph, 9)))], "%.2f" % f[int(np.argmin(np.where(f > 10, ph, 9)))]
N["EFP1"] = "%.1f" % (100 * abs(float(N["FP1"]) / f[k1] - 1))
N["EFP2"] = "%.1f" % (100 * abs(float(N["FP2"]) / f[k2] - 1))
N["DPRED"] = "%.2f" % np.abs(np.abs(PRED["d3"][1]) - s21).max()
# estimacion de cuarto de onda con la extension del extremo abierto
dl3 = float(np.mean(-np.angle(D3["B5_Gap_3p0_S11"])[(f >= 2) & (f <= 15)] /
                    (2 * R["A1_Ref50"]["g"][0].imag[(f >= 2) & (f <= 15)])))
N["DL3"] = "%.2f" % (dl3 * 1e3)
nq = np.sqrt(e50)
fq = C0 / (4 * (LS + dl3) * nq) / 1e9
kq = int(np.argmin(np.abs(fq - f)))
N["FQ"] = "%.2f" % fq[kq]
N["LGQ"] = "%.1f" % (C0 / (f[k1] * 1e9 * np.sqrt(e50[k1])) * 1e3)
cp50 = float(np.sqrt(a50["ee"][0, i5]) / (C0 * a50["Z"][0, i5].real))
cst = cp50 * (LS + dl3)
N["CSTUB"] = "%.2f" % (cst * 1e12)
N["FS20T"] = "%.2f" % (0.2 / math.sqrt(0.99) / (2 * math.pi * cst * 50.0) / 1e9)
N["PRADD_N1"] = "%.1f" % (100 * Prad["D"][k1])
N["PRADD_N2"] = "%.1f" % (100 * Prad["D"][k2])
N["PRADD_MAX"] = "%.1f" % (100 * Prad["D"][f <= 20].max())
N["FRADD_MAX"] = "%.1f" % f[np.argmax(Prad["D"][f <= 20])]

json.dump(N, open("d5_nums.json", "w"), indent=1, ensure_ascii=False)
np.savez("d5_datos.npz", f=f,
         **{"%s_S" % k: v for k, v in C.items()},
         **{"ham_%s" % k: v["S"] for k, v in HAM.items()}, **{"ideal_%s" % k: v["I"] for k, v in HAM.items()},
         **{"CE_%s" % k: v for k, v in CE.items()},
         **{"Bt_%s" % k: v["p"]["Bt"] for k, v in HAM.items()}, **{"hamCE_%s" % k: v["CE"] for k, v in HAM.items()},
         **{"Prad_%s" % k: v for k, v in Prad.items()}, **{"Pdis_%s" % k: v for k, v in Pdis.items()},
         **{"pred11_%s" % k: v[0] for k, v in PRED.items()}, **{"pred21_%s" % k: v[1] for k, v in PRED.items()},
         piso=piso, resref=max(res))
for k in sorted(N):
    if "ROWS" not in k:
        print(k, N[k])
for k in ["SROWS5", "DROWS5", "POWROWS5", "CONVROWS5"]:
    print(N[k])
