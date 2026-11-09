"""Discontinuidad 2 (escalon de ancho): todos los numeros del reporte.

Lee los CSV de HFSS, corrige el error de puerto con las lineas de
referencia, separa la potencia, ajusta el circuito equivalente y guarda
  d2_nums.json   valores que cita el reporte
  d2_datos.npz   curvas corregidas para las figuras
"""
import json, math
import numpy as np
from load_d2 import todos, conv, C0
from correccion import corregir, ajustar_g
from circuito import ajustar_reparto, s_tred, gupta

ER, H = 3.55, 0.508
W1, W2, LT = 1.14, 0.29, 10.0
R = todos()
REF = {True: (R["A1_Ref50"], R["A2_Ref100"]),
       False: (R["A1_Ref50_SinPerd"], R["A2_Ref100_SinPerd"])}
f = R["B_Escalon"]["f"]
N = {}


def idx(q):
    return int(np.argmin(np.abs(f - q)))


# ------------------------- formulas cuasi-estaticas -------------------
def ee_q(wh):
    return (ER + 1) / 2 + (ER - 1) / 2 / math.sqrt(1 + 12 / wh)


def z_q(wh):
    ee = ee_q(wh)
    if wh <= 1:
        return 60 / math.sqrt(ee) * math.log(8 / wh + wh / 4)
    return 120 * math.pi / (math.sqrt(ee) * (wh + 1.393 + 0.667 * math.log(wh + 1.444)))


Aval = 100 / 60 * math.sqrt((ER + 1) / 2) + (ER - 1) / (ER + 1) * (0.23 + 0.11 / ER)
wh100 = 8 * math.exp(Aval) / (math.exp(2 * Aval) - 2)
Z1q, Z2q = z_q(W1 / H), z_q(W2 / H)
e1q, e2q = ee_q(W1 / H), ee_q(W2 / H)
G0q = (Z2q - Z1q) / (Z2q + Z1q)
N.update(AVAL="%.3f" % Aval, WH100="%.3f" % wh100, W100="%.3f" % (wh100 * H),
         Z2Q="%.1f" % Z2q, E2Q="%.3f" % e2q, Z1Q="%.1f" % Z1q, E1Q="%.3f" % e1q,
         G0Q="%.3f" % G0q, VSWR0Q="%.2f" % ((1 + G0q) / (1 - G0q)),
         RL0Q="%.1f" % (-20 * math.log10(G0q)), ILR0Q="%.2f" % (-10 * math.log10(1 - G0q ** 2)),
         PREF0Q="%.0f" % (100 * G0q ** 2),
         LG10_100="%.1f" % (300 / 10 / math.sqrt(e2q)))

# transicion exponencial (Pozar 5.9): |Gamma| = |ln(Z2/Z1)|/2 * |sin(bL)/(bL)|
Gt0 = 0.5 * math.log(Z2q / Z1q)
eem = 0.5 * (e1q + e2q)
fnull = 300.0 / (2 * LT * math.sqrt(eem))          # bL = pi
from scipy.optimize import brentq
xu = brentq(lambda x: Gt0 * math.sin(x) / x - 0.1, 1.0, 3.1)
fumbral = xu / math.pi * fnull
N.update(GT0="%.3f" % Gt0, EEM="%.2f" % eem, FNULL="%.2f" % fnull, FNULL2="%.1f" % (2 * fnull),
         FUMBRALT="%.1f" % fumbral, XU="%.2f" % xu)

# ------------------------- validacion de las lineas -------------------
filas = []
for nombre, ref, Zq, eq in [("50", R["A1_Ref50_SinPerd"], Z1q, e1q), ("100", R["A2_Ref100_SinPerd"], Z2q, e2q)]:
    i1, i10, i20 = idx(1), idx(10), idx(20)
    Zh = 0.5 * (ref["Z1"].real + ref["Z2"].real)
    eh = 0.5 * (ref["ee1"] + ref["ee2"])
    filas.append(dict(n=nombre, Zq=Zq, eq=eq, Z1=Zh[i1], Z20=Zh[i20], e1=eh[i1], e10=eh[i10], e20=eh[i20]))
    N["ZH%s" % nombre] = "%.1f" % Zh[i1]
    N["EH%s" % nombre] = "%.3f" % eh[i1]
    N["EH%s_20" % nombre] = "%.3f" % eh[i20]
    N["DZ%s" % nombre] = "%.1f" % (100 * (Zh[i1] / Zq - 1))
    N["DE%s" % nombre] = "%.1f" % (100 * (eh[i1] / eq - 1))
N["LINROWS"] = "\n".join(
    r"%s & %.2f & %.3f & %.2f & %.2f & %.3f & %.3f & %.3f \\" % (
        ("$W_1=\\SI{1.14}{mm}$" if r["n"] == "50" else "$W_2=\\SI{0.29}{mm}$"),
        r["Zq"], r["eq"], r["Z1"], r["Z20"], r["e1"], r["e10"], r["e20"]) for r in filas)
B0r = R["B0_Escalon_SinPerd"]
G0h = (B0r["Z2"].real - B0r["Z1"].real) / (B0r["Z2"].real + B0r["Z1"].real)
N["G0H"] = "%.3f" % G0h[idx(1)]

# ------------------------- convergencia -------------------------------
NOMBRES = {"A1_Ref50": "Referencia \\SI{50}{\\ohm}", "A2_Ref100": "Referencia \\SI{100}{\\ohm}",
           "A1_Ref50_SinPerd": "Referencia \\SI{50}{\\ohm}, sin pérdidas",
           "A2_Ref100_SinPerd": "Referencia \\SI{100}{\\ohm}, sin pérdidas",
           "B_Escalon": "Escalón", "B0_Escalon_SinPerd": "Escalón, sin pérdidas",
           "C_Transicion": "Transición gradual",
           "C0_Transicion_SinPerd": "Transición gradual, sin pérdidas"}
cr = []
for d in NOMBRES:
    c = conv(d)
    p, n, ds = c[-1]
    extra = "$^{*}$" if d == "C0_Transicion_SinPerd" else ""
    cr.append(r"%s & %d & \num{%d} & %.4f%s \\" % (NOMBRES[d], p, n, ds, extra))
N["CONVROWS2"] = "\n".join(cr)
N["NMAX2"] = "%d" % max(conv(d)[-1][1] for d in NOMBRES)

# ------------------------- correccion de puertos ----------------------
Cc = {}
for d, lossy in [("B_Escalon", True), ("B0_Escalon_SinPerd", False),
                 ("C_Transicion", True), ("C0_Transicion_SinPerd", False)]:
    Cc[d] = corregir(R[d], *REF[lossy])
gfit = {k: ajustar_g(R[k]) for k in ["A1_Ref50_SinPerd", "A2_Ref100_SinPerd"]}
N["GP50"] = "%.3f" % np.max(np.abs(gfit["A1_Ref50_SinPerd"][0]))
N["GP100"] = "%.3f" % np.max(np.abs(gfit["A2_Ref100_SinPerd"][0]))
N["FLOOR50"] = "%.0f" % (20 * np.log10(np.max(np.abs(R["A1_Ref50_SinPerd"]["S11"]))))
N["FLOOR100"] = "%.0f" % (20 * np.log10(np.max(np.abs(R["A2_Ref100_SinPerd"]["S11"]))))
# residuo de las referencias corregidas con sus propias cajas
res = []
for k in ["A1_Ref50_SinPerd", "A2_Ref100_SinPerd"]:
    cc = corregir(R[k], R[k], R[k])
    res.append(np.max(np.abs(cc["S11"])))
N["RESREF"] = "%.0f" % (20 * np.log10(max(res)))
for d, lab in [("B0_Escalon_SinPerd", "B0"), ("B_Escalon", "B")]:
    N["ASIM%s_RAW" % lab] = "%.3f" % np.max(np.abs(np.abs(R[d]["S11"]) - np.abs(R[d]["S22"])))
    N["ASIM%s_COR" % lab] = "%.3f" % np.max(np.abs(np.abs(Cc[d]["S11"]) - np.abs(Cc[d]["S22"])))

# ------------------------- resultados: escalon y transicion -----------
B, B0, C, Ct0 = Cc["B_Escalon"], Cc["B0_Escalon_SinPerd"], Cc["C_Transicion"], Cc["C0_Transicion_SinPerd"]
db = lambda x: 20 * np.log10(np.abs(x))
vswr = lambda x: (1 + np.abs(x)) / (1 - np.abs(x))
filas = []
for q in [0.1, 1, 5, 10, 15, 20]:
    i = idx(q)
    filas.append(r"%s & %.2f & %.3f & %.2f & %.1f & %.2f & %.2f & %.3f & %.2f & %.2f \\" % (
        ("%.1f" % q) if q < 1 else ("%.0f" % q),
        db(B["S11"][i]), abs(B["S11"][i]), vswr(B["S11"][i]), np.degrees(np.angle(B["S11"][i])), db(B["S21"][i]),
        db(C["S11"][i]), abs(C["S11"][i]), vswr(C["S11"][i]), db(C["S21"][i])))
N["SROWS2"] = "\n".join(filas)
gB = np.abs(B["S11"])
N["GB01"], N["GB10"], N["GB20"] = ["%.3f" % gB[idx(q)] for q in (0.1, 10, 20)]
N["VB01"], N["VB20"] = ["%.2f" % vswr(B["S11"][idx(q)]) for q in (0.1, 20)]
N["S11B01"], N["S11B20"] = ["%.1f" % db(B["S11"][idx(q)]) for q in (0.1, 20)]
N["GBMIN"], N["GBMAX"] = "%.3f" % gB.min(), "%.3f" % gB.max()
N["VBMIN"], N["VBMAX"] = "%.2f" % vswr(gB.min()), "%.2f" % vswr(gB.max())
N["ILB20"] = "%.2f" % -db(B["S21"][idx(20)])
N["ILB01"] = "%.2f" % -db(B["S21"][idx(0.1)])
N["PREFB"] = "%.0f" % (100 * gB[idx(1)] ** 2)
ang11 = 0.5 * (np.degrees(np.angle(B["S11"])) + np.degrees(np.angle(B0["S11"])))
ang22 = 0.5 * (np.degrees(np.angle(-B["S22"])) + np.degrees(np.angle(-B0["S22"])))
N["ANGB10"], N["ANGB20"] = "%.1f" % ang11[idx(10)], "%.1f" % ang11[idx(20)]
N["ANGB20ABS"] = "%.0f" % abs(ang11[idx(20)])
N["ANG22MAX"] = "%.1f" % np.max(np.abs(ang22[f >= 1]))
N["DS11LOSS2"] = "%.3f" % np.max(np.abs(np.abs(B["S11"]) - np.abs(B0["S11"])))
gC = np.abs(C["S11"])
i_ok = np.where(gC < 0.1)[0][0]
N["FT20"] = "%.2f" % f[i_ok]
from scipy.signal import argrelmin
mins = argrelmin(gC)[0]
N["FTN1"], N["FTN2"] = "%.2f" % f[mins[0]], "%.2f" % f[mins[1]]
N["GCMAXHI"] = "%.3f" % gC[f >= 10].max()
N["S11CMAXHI"] = "%.1f" % db(gC[f >= 10].max())
N["VCMAXHI"] = "%.2f" % vswr(gC[f >= 10].max())
N["GC01"] = "%.3f" % gC[idx(0.1)]
N["GC5"] = "%.3f" % gC[idx(5)]
N["ILC20"] = "%.2f" % -db(C["S21"][idx(20)])
N["ILC10"] = "%.2f" % -db(C["S21"][idx(10)])

# ------------------------- potencia -----------------------------------
Prad = {"B": 0.5 * (B0["P1"] + B0["P2"]), "C": 0.5 * (Ct0["P1"] + Ct0["P2"])}
Pdis = {"B": 0.5 * (B["P1"] + B["P2"]) - Prad["B"], "C": 0.5 * (C["P1"] + C["P2"]) - Prad["C"]}
piso = max(-Prad["B"].min(), -Prad["C"].min(), 0)
N["PISO2"] = "%.1f" % (100 * max(piso, 0.001))
N["PRADBMAX"] = "%.1f" % (100 * Prad["B"].max())
N["PRADCMAX"] = "%.1f" % (100 * Prad["C"].max())
N["PDISB20"] = "%.2f" % (100 * Pdis["B"][idx(20)])
N["PDISC10"], N["PDISC20"] = "%.1f" % (100 * Pdis["C"][idx(10)]), "%.1f" % (100 * Pdis["C"][idx(20)])
# disipacion esperada: atenuacion de las lineas (constante de propagacion de HFSS) por la longitud
a_m = 0.5 * (R["C_Transicion"]["g1"].real + R["C_Transicion"]["g2"].real)
Pdis_lin = 1 - np.exp(-2 * a_m * LT * 1e-3)
N["PDISLIN20"] = "%.1f" % (100 * Pdis_lin[idx(20)])
N["PDISLIN10"] = "%.1f" % (100 * Pdis_lin[idx(10)])
pw = []
for lab, X in [("Escalón", B), ("Transición gradual", C)]:
    k = "B" if lab == "Escalón" else "C"
    for q in [5, 10, 20]:
        i = idx(q)
        refl = 0.5 * (abs(X["S11"][i]) ** 2 + abs(X["S22"][i]) ** 2)
        tr = abs(X["S21"][i]) ** 2
        pw.append(r"%s & %d & %.1f & %.1f & %.1f & %.1f & %.2f & %.2f \\" % (
            lab if q == 5 else "", q, 100 * tr, 100 * refl, 100 * Prad[k][i], 100 * Pdis[k][i],
            -db(X["S21"][i]), -10 * np.log10(1 - abs(X["S11"][i]) ** 2)))
    if lab == "Escalón":
        pw.append(r"\addlinespace")
N["POWROWS2"] = "\n".join(pw)

# ------------------------- circuito equivalente -----------------------
fits = {}
for d in ["B_Escalon", "B0_Escalon_SinPerd"]:
    r = R[d]; i = idx(10)
    Z1, Z2 = r["Z1"].real, r["Z2"].real
    alfa = Z1[i] * np.sqrt(r["ee1"][i]) / (Z1[i] * np.sqrt(r["ee1"][i]) + Z2[i] * np.sqrt(r["ee2"][i]))
    fits[d] = [ajustar_reparto(Cc[d], Z1, Z2, alfa, a, b) for a, b in [(1, 20), (3, 20), (1, 12)]]
    fits[d + "_crudo"] = ajustar_reparto(R[d], Z1, Z2, alfa, 1, 20)
todos_C = [p["C"] for d in ["B_Escalon", "B0_Escalon_SinPerd"] for p in fits[d]]
todos_L = [p["Ls"] for d in ["B_Escalon", "B0_Escalon_SinPerd"] for p in fits[d]]
Cm, Lm = np.mean(todos_C), np.mean(todos_L)
eC, eL = 0.5 * (max(todos_C) - min(todos_C)), 0.5 * (max(todos_L) - min(todos_L))
km = np.mean([fits[d][0]["k"] for d in ["B_Escalon", "B0_Escalon_SinPerd"]])
gp = gupta(W1, W2, H, ER, Z1q, Z2q, e1q, e2q)
Z1n, Z2n = 50.0, 100.0
X1, X2 = Lm - Cm * 1e-3 * Z2n ** 2, Lm - Cm * 1e-3 * Z2n ** 0 * Z1n ** 2   # pH (C en fF -> *1e-3 nF ... ver abajo)
# unidades: Lm en pH, Cm en fF -> C*Z^2 en fF*ohm^2 = 1e-15*Z^2 H = 1e-3*Z^2 pH
X1 = Lm - Cm * Z2n ** 2 * 1e-3
X2 = Lm - Cm * Z1n ** 2 * 1e-3
Xg1 = gp["L"] * 1e12 - gp["C"] * 1e15 * Z2n ** 2 * 1e-3
Xg2 = gp["L"] * 1e12 - gp["C"] * 1e15 * Z1n ** 2 * 1e-3
f10 = 0.1 * Z2n / (2 * math.pi * abs(X1) * 1e-12) / 1e9
N.update(CEXC="%.1f" % Cm, ECEXC="%.1f" % max(eC, 0.1), LEXC="%.0f" % Lm, ELEXC="%.0f" % max(eL, 1),
         KFIT="%.3f" % km, KPCT="%.1f" % (100 * (1 - km)),
         CGUP="%.1f" % (gp["C"] * 1e15), LGUP="%.1f" % (gp["L"] * 1e12), RGUP="%.2f" % gp["r"],
         X1="%.0f" % X1, X2="%.0f" % X2, XG1="%.0f" % Xg1, XG2="%.0f" % Xg2,
         CZ2="%.0f" % (Cm * Z2n ** 2 * 1e-3), CZ1="%.0f" % (Cm * Z1n ** 2 * 1e-3),
         F10X="%.0f" % f10, ALFA="%.2f" % fits["B_Escalon"][0]["alfa"],
         RMSFIT="%.4f" % max(p["rms"] for d in ["B_Escalon", "B0_Escalon_SinPerd"] for p in fits[d]),
         RMSRAW="%.4f" % max(fits[d + "_crudo"]["rms"] for d in ["B_Escalon", "B0_Escalon_SinPerd"]),
         CRAW="%.0f" % np.mean([fits[d + "_crudo"]["C"] for d in ["B_Escalon", "B0_Escalon_SinPerd"]]))
# longitud equivalente de la capacitancia en exceso: C / C' de la linea de 50 ohm
Cp1 = math.sqrt(e1q) / (C0 * Z1q)                       # F/m
N["DLC"] = "%.0f" % (Cm * 1e-15 / Cp1 * 1e6)            # micrometros
Lp2 = Z2q * math.sqrt(e2q) / C0                          # H/m
N["DLL"] = "%.0f" % (Lm * 1e-12 / Lp2 * 1e6)
fitrows = []
for d, lab in [("B_Escalon", "Escalón"), ("B0_Escalon_SinPerd", "Escalón, sin pérdidas")]:
    p = fits[d][0]
    fitrows.append(r"%s & %.2f & %.1f & %.3f & %.4f \\" % (lab, p["C"], p["Ls"], p["k"], p["rms"]))
N["FITROWS"] = "\n".join(fitrows)

# modelo ajustado para las figuras
r = R["B_Escalon"]
pB = fits["B_Escalon"][0]
S11m, S21m, S22m = s_tred(f, pB["alfa"] * pB["Ls"] * 1e-12, (1 - pB["alfa"]) * pB["Ls"] * 1e-12, pB["C"] * 1e-15,
                          r["Z1"].real, pB["k"] * r["Z2"].real)
S11g, S21g, S22g = s_tred(f, gp["L1"], gp["L2"], gp["C"], r["Z1"].real, pB["k"] * r["Z2"].real)
# fase de S11 a 20 GHz predicha por Gupta (mismo k)
N["ANGGUP20"] = "%.1f" % np.degrees(np.angle(S11g[idx(20)]))
N["ANGFIT20"] = "%.1f" % np.degrees(np.angle(S11m[idx(20)]))

lgt = lambda q: 300.0 / q / math.sqrt(eem)
Lp1, Lp2 = Z1q * math.sqrt(e1q) / C0, Z2q * math.sqrt(e2q) / C0
Cp2 = math.sqrt(e2q) / (C0 * Z2q)
N.update(CP1="%.0f" % (Cp1 * 1e12), CP2="%.0f" % (Cp2 * 1e12), LP1="%.0f" % (Lp1 * 1e9), LP2="%.0f" % (Lp2 * 1e9),
         RCP="%.2f" % (Cp2 / Cp1), RLP="%.1f" % (Lp2 / Lp1))
i1, i20 = idx(1), idx(20)
N["Z2H1"], N["Z2H20"] = "%.1f" % B0r["Z2"].real[i1], "%.1f" % B0r["Z2"].real[i20]
N["G0H20"] = "%.3f" % G0h[i20]
N["LTLGU"] = "%.2f" % (LT / lgt(float(N["FT20"])))
N["LG2T"], N["LG10T"], N["LG20T"] = "%.0f" % lgt(2), "%.0f" % lgt(10), "%.1f" % lgt(20)
N["LTLG2"], N["LTLG10"] = "%.2f" % (LT / lgt(2)), "%.2f" % (LT / lgt(10))
N["LG20_50"] = "%.2f" % (300 / 20 / math.sqrt(e1q))
N["DLCLG"] = "%.0f" % (300 / 20 / math.sqrt(e1q) * 1e3 / (Cm * 1e-15 / Cp1 * 1e6))
json.dump(N, open("d2_nums.json", "w"), indent=1, ensure_ascii=False)
np.savez("d2_datos.npz", f=f,
         **{"%s_%s" % (k, q): v[q] for k, v in Cc.items() for q in ["S11", "S21", "S12", "S22", "P1", "P2"]},
         **{"raw_%s_%s" % (k, q): R[k][q] for k in R for q in ["S11", "S21", "S22"]},
         gfit50=gfit["A1_Ref50_SinPerd"][1], gfit100=gfit["A2_Ref100_SinPerd"][1],
         PradB=Prad["B"], PradC=Prad["C"], PdisB=Pdis["B"], PdisC=Pdis["C"], PdisLin=Pdis_lin,
         S11m=S11m, S22m=S22m, S11g=S11g, S22g=S22g, ang11=ang11, ang22=ang22,
         Z1=r["Z1"].real, Z2=r["Z2"].real)
for k in sorted(N):
    if "ROWS" not in k:
        print(k, N[k])
