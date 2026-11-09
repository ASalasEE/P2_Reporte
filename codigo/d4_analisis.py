"""Discontinuidad 4 (cambio de material a mitad de la linea): numeros del reporte.

Lee los CSV de HFSS, corrige el error de puerto con la linea de referencia
de cada lado, compara la reflexion con la de un escalon ideal de
impedancia, separa las perdidas del cobre y del estano y calcula el efecto
de un tramo finito del segundo material. Guarda
  d4_nums.json   valores que cita el reporte
  d4_datos.npz   curvas corregidas para las figuras
"""
import json, math
import numpy as np
import load_d2 as L
from correccion import corregir
from circuito import ajustar_reparto, s_tred

L.D = "datos/P2_D4_Material_CSV"
C0 = 299792458.0
H, W1, W50B = 0.508, 1.14, 0.48
SUST = {"RO4003C": (3.55, 0.0027), "FR4": (4.4, 0.02), "RO3010": (10.2, 0.0022)}
SIG_CU, SIG_SN = 5.8e7, 8.7e6
REF = {"B1_FR4": ("A1_Ref_RO4003C", "A2_Ref_FR4"), "B2_RO3010": ("A1_Ref_RO4003C", "A3_Ref_RO3010"),
       "C_RO3010_Ancho50": ("A1_Ref_RO4003C", "A4_Ref_RO3010_W50"), "D_Estano": ("A1_Ref_RO4003C", "A5_Ref_Estano")}
REFS = ["A1_Ref_RO4003C", "A2_Ref_FR4", "A3_Ref_RO3010", "A4_Ref_RO3010_W50", "A5_Ref_Estano"]
TODOS = [d + x for d in REFS + list(REF) for x in ["", "_SinPerd"] if not (d.endswith("Estano") and x)]
R = {n: L.cargar(n) for n in TODOS}
f = R["A1_Ref_RO4003C"]["f"]
w = 2 * np.pi * f * 1e9
k0 = w / C0
N = {}
db = lambda x: 20 * np.log10(np.abs(x))
vswr = lambda g: (1 + np.abs(g)) / (1 - np.abs(g))


def idx(q):
    return int(np.argmin(np.abs(f - q)))


# ------------------------- formulas cuasiestaticas --------------------
def hj(wh, er):
    """Hammerstad y Jensen (simplificadas): Z0 y er_ef."""
    ee = (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 / wh)
    if wh <= 1:
        z = 60 / math.sqrt(ee) * math.log(8 / wh + wh / 4)
    else:
        z = 120 * math.pi / (math.sqrt(ee) * (wh + 1.393 + 0.667 * math.log(wh + 1.444)))
    return z, ee


# ------------------------- convergencia -------------------------------
ETQ = {"A1_Ref_RO4003C": "Ref. RO4003C", "A2_Ref_FR4": "Ref. FR-4", "A3_Ref_RO3010": "Ref. RO3010",
       "A4_Ref_RO3010_W50": "Ref. RO3010, $W=\\SI{0.48}{mm}$", "A5_Ref_Estano": "Ref. estaño",
       "B1_FR4": "RO4003C $\\to$ FR-4", "B2_RO3010": "RO4003C $\\to$ RO3010",
       "C_RO3010_Ancho50": "RO4003C $\\to$ RO3010 compensado", "D_Estano": "Cobre $\\to$ estaño"}
filas, nmax = [], 0
for d in REFS + list(REF):
    for x in (["", "_SinPerd"] if not d.endswith("Estano") else [""]):
        c = L.conv(d + x)
        p, n, ds = c[-1]
        nmax = max(nmax, n)
        filas.append(r"%s%s & %d & \num{%d} & %.4f \\" % (ETQ[d], ", sin pérdidas" if x else "", p, n, ds))
N["CONVROWS4"] = "\n".join(filas)
N["NMAX4"] = "%d" % nmax
N["NDIS4"] = "%d" % len(filas)

# ------------------------- lineas: Z0, er_ef, L', C', alfa ------------
i5 = idx(5)
lin = {}
filas = []
for d, mat, wd in [("A1_Ref_RO4003C", "RO4003C", W1), ("A2_Ref_FR4", "FR4", W1), ("A3_Ref_RO3010", "RO3010", W1),
                   ("A4_Ref_RO3010_W50", "RO3010", W50B), ("A5_Ref_Estano", "RO4003C", W1)]:
    r = R[d]
    Z, ee, a = r["Z1"].real, r["ee1"], r["g1"].real            # alfa en Np/m
    Lp = Z * np.sqrt(ee) / C0; Cp = np.sqrt(ee) / (C0 * Z)
    zq, eq = hj(wd / H, SUST[mat][0])
    lin[d] = dict(Z=Z, ee=ee, a=a, Lp=Lp, Cp=Cp, n=np.sqrt(ee), zq=zq, eq=eq)
    metal = "estaño" if "Estano" in d else "cobre"
    nom = {"FR4": "FR-4"}.get(mat, mat)
    filas.append(r"%s & %s & %.2f & %.1f & %.1f & %.3f & %.2f & %.0f & %.0f & %.3f \\" % (
        nom, metal, wd, zq, Z[i5], ee[i5], np.sqrt(ee[i5]), Lp[i5] * 1e9, Cp[i5] * 1e12, 8.686 * a[i5] / 100))
N["LINROWS4"] = "\n".join(filas)
A1, A2, A3, A4, A5 = (lin[d] for d in REFS)
N["LP1"], N["LP3"] = "%.0f" % (A1["Lp"][i5] * 1e9), "%.0f" % (A3["Lp"][i5] * 1e9)
N["DLP13"] = "%.1f" % (100 * abs(A3["Lp"][i5] / A1["Lp"][i5] - 1))
N["DLP12"] = "%.1f" % (100 * abs(A2["Lp"][i5] / A1["Lp"][i5] - 1))
N["CP1"], N["CP2"], N["CP3"] = ["%.0f" % (X["Cp"][i5] * 1e12) for X in (A1, A2, A3)]
N["LP4"], N["CP4"] = "%.0f" % (A4["Lp"][i5] * 1e9), "%.0f" % (A4["Cp"][i5] * 1e12)
N["RLP4"], N["RCP4"] = "%.2f" % (A4["Lp"][i5] / A1["Lp"][i5]), "%.2f" % (A4["Cp"][i5] / A1["Cp"][i5])
N["RN4"] = "%.2f" % (A4["n"][i5] / A1["n"][i5])
N["RCP13"], N["RCP12"] = "%.2f" % (A3["Cp"][i5] / A1["Cp"][i5]), "%.2f" % (A2["Cp"][i5] / A1["Cp"][i5])
N["Z1_5"], N["Z2_5"], N["Z3_5"], N["Z4_5"], N["Z5_5"] = ["%.1f" % X["Z"][i5] for X in (A1, A2, A3, A4, A5)]
N["N1"], N["N2"], N["N3"], N["N4"] = ["%.2f" % X["n"][i5] for X in (A1, A2, A3, A4)]
N["EE1"], N["EE3"] = "%.2f" % A1["ee"][i5], "%.2f" % A3["ee"][i5]
N["EE3_1"], N["EE3_20"] = "%.2f" % A3["ee"][idx(1)], "%.2f" % A3["ee"][idx(20)]
N["EE1_1"], N["EE1_20"] = "%.2f" % A1["ee"][idx(1)], "%.2f" % A1["ee"][idx(20)]
N["ZQ1"], N["ZQ2"], N["ZQ3"], N["ZQ4"] = ["%.1f" % X["zq"] for X in (A1, A2, A3, A4)]
N["EQ1"], N["EQ2"], N["EQ3"], N["EQ4"] = ["%.2f" % X["eq"] for X in (A1, A2, A3, A4)]
# filling factor q = (ee-1)/(er-1)
N["Q1"] = "%.2f" % ((A1["ee"][i5] - 1) / (3.55 - 1))
N["Q3"] = "%.2f" % ((A3["ee"][i5] - 1) / (10.2 - 1))
N["Q3_20"] = "%.2f" % ((A3["ee"][idx(20)] - 1) / (10.2 - 1))
N["Q1_20"] = "%.2f" % ((A1["ee"][idx(20)] - 1) / (3.55 - 1))
N["LG1_5"] = "%.1f" % (C0 / 5e9 / A1["n"][i5] * 1e3)
N["LG3_5"] = "%.1f" % (C0 / 5e9 / A3["n"][i5] * 1e3)
N["LG4_5"] = "%.1f" % (C0 / 5e9 / A4["n"][i5] * 1e3)

# ------------------------- correccion de puertos ----------------------
Cc = {}
for d, (ra, rb) in REF.items():
    for x in (["", "_SinPerd"] if d != "D_Estano" else [""]):
        Cc[d + x] = corregir(R[d + x], R[ra + x], R[rb + x])
res = []
for d in REFS:
    x = "" if d.endswith("Estano") else "_SinPerd"
    cc = corregir(R[d + x], R[d + x], R[d + x])
    res.append(np.max(np.abs(cc["S11"])))
N["RESREF4"] = "%.4f" % max(res)
N["RESREF4DB"] = "%.0f" % db(max(res))

# ------------------------- reflexion frente al escalon ideal ----------
G = {}
for d in REF:
    r = R[d]
    G[d] = (r["Z2"].real - r["Z1"].real) / (r["Z2"].real + r["Z1"].real)
Gn = {"B1_FR4": (A1["n"] - A2["n"]) / (A1["n"] + A2["n"]), "B2_RO3010": (A1["n"] - A3["n"]) / (A1["n"] + A3["n"])}
N["GN2_5"], N["GN3_5"] = "%.3f" % Gn["B1_FR4"][i5], "%.3f" % Gn["B2_RO3010"][i5]
N["GZ2_5"], N["GZ3_5"] = "%.3f" % G["B1_FR4"][i5], "%.3f" % G["B2_RO3010"][i5]
for d, k in [("B1_FR4", "B1"), ("B2_RO3010", "B2"), ("C_RO3010_Ancho50", "C"), ("D_Estano", "D")]:
    c = Cc[d]
    g = np.abs(c["S11"])
    N["G%s_1" % k], N["G%s_5" % k], N["G%s_10" % k], N["G%s_20" % k] = ["%.3f" % g[idx(q)] for q in (1, 5, 10, 20)]
    N["G%sMAX" % k] = "%.3f" % g.max()
    N["G%sMIN" % k] = "%.3f" % g.min()
    N["S11%s_5" % k] = "%.1f" % db(c["S11"][i5])
    N["S11%sMAX" % k] = "%.1f" % db(g.max())
    N["V%s_5" % k] = "%.2f" % vswr(g[i5])
    N["V%sMAX" % k] = "%.2f" % vswr(g.max())
    N["V%s_20" % k] = "%.2f" % vswr(g[idx(20)])
    N["PR%s_5" % k] = "%.1f" % (100 * g[i5] ** 2)
    N["IL%s_5" % k] = "%.2f" % -db(c["S21"][i5])
    N["IL%s_20" % k] = "%.2f" % -db(c["S21"][idx(20)])
    N["ML%s_5" % k] = "%.2f" % (-10 * np.log10(1 - g[i5] ** 2))
    dev = np.abs(c["S11"] - G[d])
    N["DEV%s_10" % k] = "%.3f" % dev[f <= 10].max()
    N["DEV%s_20" % k] = "%.3f" % dev.max()
    N["ANG21%s_20" % k] = "%.1f" % np.degrees(np.angle(c["S21"][idx(20)]))
    N["ANG11%sMAX" % k] = "%.1f" % np.max(np.abs(180 - np.abs(np.degrees(np.angle(c["S11"][f >= 1])))))
# tabla de parametros S
filas = []
for q in [0.1, 1, 5, 10, 15, 20]:
    i = idx(q)
    fila = [("%.1f" % q) if q < 1 else ("%.0f" % q)]
    for d in ["B1_FR4", "B2_RO3010", "D_Estano"]:
        c = Cc[d]
        s21 = db(c["S21"][i])
        fila += ["%.3f" % abs(c["S11"][i]), "%.2f" % vswr(c["S11"][i]), "%.2f" % (s21 if abs(s21) >= 0.005 else 0.0)]
    filas.append(" & ".join(fila) + r" \\")
N["SROWS4"] = "\n".join(filas)
gB2 = np.abs(Cc["B2_RO3010"]["S11"])
N["GB2REL"] = "%.0f" % (100 * (gB2[idx(20)] / gB2[idx(1)] - 1))
N["PRB2MIN"], N["PRB2MAX"] = "%.1f" % (100 * gB2.min() ** 2), "%.1f" % (100 * gB2.max() ** 2)

# ------------------------- potencia -----------------------------------
bal = {}
for d in ["B1_FR4", "B2_RO3010", "C_RO3010_Ancho50"]:
    c0 = Cc[d + "_SinPerd"]
    bal[d] = 0.5 * (c0["P1"] + c0["P2"])
N["BALMAX4"] = "%.1f" % (100 * max(np.abs(bal[d]).max() for d in bal))
cD = Cc["D_Estano"]
N["BALD"] = "%.1f" % (100 * np.abs(0.5 * (cD["P1"] + cD["P2"])).max())

# ------------------------- perdidas: cobre frente a estano ------------
# alfa_d con er_ef de HFSS; alfa_c = alfa - alfa_d (misma linea, mismo dielectrico)
er, td = SUST["RO4003C"]
ad = k0 * er * (A1["ee"] - 1) * td / (2 * np.sqrt(A1["ee"]) * (er - 1))
acu = A1["a"] - ad
asn = A5["a"] - ad
rat = asn / acu
rs = math.sqrt(SIG_CU / SIG_SN)
fr = (rat - 1) / (rs - 1)                 # fraccion de la perdida de conductor que esta en la tira
filas = []
for q in [1, 5, 10, 20]:
    i = idx(q)
    filas.append(r"%d & %.3f & %.3f & %.3f & %.3f & %.2f & %.2f \\" % (
        q, 8.686 * ad[i] / 100, 8.686 * acu[i] / 100, 8.686 * asn[i] / 100, 8.686 * (asn[i] - acu[i]) / 100,
        rat[i], 8.686 * (asn[i] - acu[i]) * 0.1))
N["ALFAROWS"] = "\n".join(filas)
N["EXT1"], N["EXT20"] = ["%.2f" % (8.686 * (asn[idx(q)] - acu[idx(q)]) * 0.1) for q in (1, 20)]
banda = (f >= 1) & (f <= 20)
N["RATMIN"], N["RATMAX"] = "%.2f" % rat[banda].min(), "%.2f" % rat[banda].max()
N["RAT5"] = "%.2f" % rat[i5]
N["RS"] = "%.2f" % rs
N["FRTIRA"] = "%.0f" % (100 * np.mean(fr[banda]))
N["DA5PCT"] = "%.0f" % (100 * (A5["a"][i5] / A1["a"][i5] - 1))
N["AD5"], N["ACU5"], N["ASN5"] = ["%.3f" % (8.686 * v[i5] / 100) for v in (ad, acu, asn)]
# exponente de la ley alfa_c ~ f^p entre 1 y 20 GHz
p_cu = np.polyfit(np.log(f[banda]), np.log(acu[banda]), 1)[0]
p_sn = np.polyfit(np.log(f[banda]), np.log(asn[banda]), 1)[0]
N["PCU"], N["PSN"] = "%.2f" % p_cu, "%.2f" % p_sn
# reflexion esperada en la union Cu -> Sn: |Gamma| = d(alfa_c)/(sqrt2 beta)
beta1 = np.imag(R["A1_Ref_RO4003C"]["g1"])
gsn = (asn - acu) / (math.sqrt(2) * beta1)
N["GSN01"], N["GSN1"], N["GSN20"] = "%.4f" % gsn[idx(0.1)], "%.4f" % gsn[idx(1)], "%.4f" % gsn[idx(20)]
N["ILDMAX"] = "%.2f" % max(0.01, np.abs(db(cD["S21"])).max())
N["DBRES1"] = "%.0f" % (20 * np.log10(max(res) / gsn[idx(1)]))
N["DBRES20"] = "%.0f" % (20 * np.log10(max(res) / gsn[idx(20)]))
N["GDMAX_HI"] = "%.3f" % np.abs(cD["S11"][f >= 1]).max()
# profundidad de penetracion
dsk = lambda fq, s: 1 / math.sqrt(math.pi * fq * 4e-7 * math.pi * s) * 1e6
N["DSN01"], N["DSN1"], N["DSN20"] = "%.0f" % dsk(0.1e9, SIG_SN), "%.1f" % dsk(1e9, SIG_SN), "%.1f" % dsk(20e9, SIG_SN)
N["DCU1"] = "%.1f" % dsk(1e9, SIG_CU)
# FR-4: el tramo despues de la union pierde mas por el dielectrico
N["AFR5"], N["ARO5"] = "%.3f" % (8.686 * A2["a"][i5] / 100), "%.3f" % (8.686 * A1["a"][i5] / 100)
N["RFR5"] = "%.1f" % (A2["a"][i5] / A1["a"][i5])
N["AFR20"], N["ARO20"] = "%.2f" % (8.686 * A2["a"][idx(20)] / 100), "%.2f" % (8.686 * A1["a"][idx(20)] / 100)
N["A3_5"], N["A4_5"] = "%.3f" % (8.686 * A3["a"][i5] / 100), "%.3f" % (8.686 * A4["a"][i5] / 100)

# ------------------------- tramo finito del segundo material ----------
from correccion import s2t, t2s, mult


def tramo(d, dref, ell):
    """Union d, tramo de longitud ell (mm) de la linea dref y la union inversa."""
    c = Cc[d]
    g = R[dref]["g1"]
    TJ = s2t(c["S11"], c["S21"], c["S12"], c["S22"])
    TL = np.array([[np.exp(-g * ell * 1e-3), 0 * g], [0 * g, np.exp(g * ell * 1e-3)]])
    TR = s2t(c["S22"], c["S12"], c["S21"], c["S11"])
    S11, S21, S12, S22 = t2s(mult(mult(TJ, TL), TR))
    return S11, S21


LONG = [6.0, 12.0, 24.0]
fin = {}
filas = []
for ell in LONG:
    S11, S21 = tramo("B2_RO3010", "A3_Ref_RO3010", ell)
    fin["B2_%g" % ell] = (S11, S21)
    g = np.abs(S11)
    k = np.where(g > 0.1)[0][0]
    fs = np.interp(0.1, [g[k - 1], g[k]], [f[k - 1], f[k]])          # primer cruce de 0.1
    fq = C0 / (4 * ell * 1e-3 * A3["n"][i5]) / 1e9                     # tramo = lambda_g/4
    lg = C0 / (fs * 1e9) / np.sqrt(np.interp(fs, f, A3["ee"])) * 1e3
    filas.append(r"%g & %.2f & %.1f & $\lambda_g/%.0f$ & %.3f \\" % (ell, fs, fq, lg / ell, g.max()))
    N["FS%g" % ell] = "%.2f" % fs
    N["FQ%g" % ell] = "%.1f" % fq
    N["LGF%g" % ell] = "%.0f" % (lg / ell)
    N["GPK%g" % ell] = "%.2f" % g.max()
N["FINROWS"] = "\n".join(filas)
N["GPKT"] = "%.2f" % (2 * gB2[i5] / (1 + gB2[i5] ** 2))
for ell in [6.0]:
    S11, S21 = tramo("B1_FR4", "A2_Ref_FR4", ell)
    fin["B1_%g" % ell] = (S11, S21)
    N["GPKFR"] = "%.3f" % np.abs(S11).max()
    S11c, S21c = tramo("C_RO3010_Ancho50", "A4_Ref_RO3010_W50", ell)
    fin["C_%g" % ell] = (S11c, S21c)
    N["GPKC"] = "%.3f" % np.abs(S11c).max()

# ------------------------- union compensada (ancho ajustado) ----------
d = "C_RO3010_Ancho50"
r = R[d]
alfa = A1["Lp"][i5] / (A1["Lp"][i5] + A4["Lp"][i5])
fits = []
for x in ["", "_SinPerd"]:
    for a, b in [(1, 20), (3, 20), (1, 12)]:
        fits.append(ajustar_reparto(Cc[d + x], R[d + x]["Z1"].real, R[d + x]["Z2"].real, alfa, a, b))
Cs = [p["C"] for p in fits]; Ls = [p["Ls"] for p in fits]
N["CCOMP"], N["ECCOMP"] = "%.0f" % np.mean(Cs), "%.0f" % max(0.5 * (max(Cs) - min(Cs)), 1)
N["LCOMP"], N["ELCOMP"] = "%.0f" % np.mean(Ls), "%.0f" % max(0.5 * (max(Ls) - min(Ls)), 1)
N["ALFA4"] = "%.2f" % alfa
N["RMS4"] = "%.4f" % max(p["rms"] for p in fits)
gC = np.abs(Cc[d]["S11"])
N["FC20DB"] = "%.0f" % (20 * np.log10(gC[f <= 20].max()))
N["GCLOW"] = "%.3f" % gC[f <= 2].max()
N["RED"] = "%.0f" % (gB2[i5] / gC[i5])
N["DLY20"] = "%.1f" % abs(np.degrees(np.angle(Cc[d]["S21"][idx(20)])))
pC = fits[0]
S11m, S21m, S22m = s_tred(f, alfa * pC["Ls"] * 1e-12, (1 - alfa) * pC["Ls"] * 1e-12, pC["C"] * 1e-15,
                          r["Z1"].real, pC["k"] * r["Z2"].real)
N["KC"] = "%.3f" % pC["k"]

json.dump(N, open("d4_nums.json", "w"), indent=1, ensure_ascii=False)
np.savez("d4_datos.npz", f=f,
         **{"%s_%s" % (k, q): v[q] for k, v in Cc.items() for q in ["S11", "S21", "S12", "S22"]},
         **{"G_%s" % k: v for k, v in G.items()},
         **{"crudo_%s" % k: R[k]["S11"] for k in REF},
         **{"fin_%s" % k: v[0] for k, v in fin.items()}, **{"fin21_%s" % k: v[1] for k, v in fin.items()},
         **{"a_%s" % k: lin[k]["a"] for k in lin}, **{"ee_%s" % k: lin[k]["ee"] for k in lin},
         **{"Z_%s" % k: lin[k]["Z"] for k in lin},
         ad=ad, acu=acu, asn=asn, gsn=gsn, S11m_C=S11m, S21m_C=S21m)
for k in sorted(N):
    if "ROWS" not in k:
        print(k, N[k])
for k in ["LINROWS4", "SROWS4", "ALFAROWS", "FINROWS", "CONVROWS4"]:
    print(N[k])
