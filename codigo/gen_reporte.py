import os, re, json, math, shutil, subprocess
import numpy as np

S = ""
exec(open(S + "extract_v2.py").read())
v2 = data
f = v2["A_Referencia"]["f"]

# Diagnostico (datos v1 y variantes R)
exec(open(S + "load_diag.py").read())
fd = dd["A_Referencia"]["f"]
i10d = np.argmin(np.abs(fd - 10))

OUT = "reporte"
FIG = os.path.join(OUT, "figuras")
os.makedirs(FIG, exist_ok=True)
for n in ["fig0_geometria", "fig1_S11_dB", "fig2_S21_dB", "fig3_Gamma_VSWR",
          "fig4_Smith_S11", "fig5_parasitos_LC", "fig6_radiacion_potencia",
          "fig7_carga_corriente", "fig8_escala_lambda", "fig9_imagen_radiacion"]:
    shutil.copy("figuras/%s.pdf" % n, FIG)
for n in ["fig_d3_geometria", "fig_d3_S", "fig_d3_capacitancias", "fig_d3_potencia", "fig_d3_campos",
          "fig_d4_geometria", "fig_d4_reflexion", "fig_d4_tramo", "fig_d4_perdidas", "fig_d4_campos",
          "fig_d5_geometria", "fig_d5_T", "fig_d5_divisor", "fig_d5_stub", "fig_d5_campos",
          "fig_d5_stub_mapas", "fig_d5_stub_onda"]:
    shutil.copy("figuras/%s.pdf" % n, FIG)
for n in ["fig_d2_geometria", "fig_d2_correccion", "fig_d2_S_dB", "fig_d2_Gamma_VSWR", "fig_d2_Smith",
          "fig_d2_fase_reactancia", "fig_d2_potencia", "fig_d2_carga_corriente", "fig_d2_escala"]:
    shutil.copy("figuras/%s.pdf" % n, FIG)
UP = "capturas_hfss/"
for n in ["hfss3d_referencia", "hfss3d_curva", "hfss3d_chaflan", "hfss3d_d2_ref50", "hfss3d_d2_ref100",
          "hfss3d_d2_escalon", "hfss3d_d2_transicion", "hfss3d_d3_ref", "hfss3d_d3_0p1", "hfss3d_d3_0p2",
          "hfss3d_d3_0p5", "hfss3d_d3_1p0", "hfss3d_d3_3p0", "hfss3d_d4_ref", "hfss3d_d4_ref_w50",
          "hfss3d_d4_sustrato", "hfss3d_d4_compensado", "hfss3d_d4_estano", "hfss3d_d5_ref50",
          "hfss3d_d5_ref100", "hfss3d_d5_T", "hfss3d_d5_divisor", "hfss3d_d5_stub"]:
    shutil.copy(UP + n + ".png", os.path.join(FIG, n + ".png"))


def idx(q):
    return int(np.argmin(np.abs(f - q)))


def cruce(y, th):
    i = np.where(y > th)[0]
    return f[i[0]] if len(i) else None


def g(d, q):
    return abs(v2[d]["S11"][idx(q)])


R = {}
er, h, Z0 = 3.55, 0.508, 50.0
B = 377 * math.pi / (2 * Z0 * math.sqrt(er))
wh = 2 / math.pi * (B - 1 - math.log(2 * B - 1) + (er - 1) / (2 * er) * (math.log(B - 1) + 0.39 - 0.61 / er))
W = 1.14; u = W / h
ee = (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 * h / W)
Zp = 120 * math.pi / (math.sqrt(ee) * (u + 1.393 + 0.667 * math.log(u + 1.444)))
R.update(BVAL="%.3f" % B, WH="%.3f" % wh, WCALC="%.3f" % (wh * h), EEFF="%.3f" % ee, Z0="%.2f" % Zp,
         LG10="%.2f" % (300 / 10 / math.sqrt(ee)), LG20="%.2f" % (300 / 20 / math.sqrt(ee)),
         MVAL="%.1f" % (52 + 65 * math.exp(-1.35 * u)))
Hp = 8 * h; eperp = Hp / ((Hp - h) + h / er)
R["FC"] = "%.0f" % (300 / (2 * 5 * W * math.sqrt(eperp)))

B_, C_, A_ = "B_Curva90", "C_Curva90_Chaflan", "A_Referencia"
R["F20"] = "%.2f" % cruce(v2[B_]["s11db"], -20)
R["F30"] = "%.2f" % cruce(v2[B_]["s11db"], -30)
R["S11B20"] = "%.1f" % v2[B_]["s11db"][idx(20)]
R["GB20"] = "%.3f" % g(B_, 20)
R["VSWR20B"] = "%.2f" % ((1 + g(B_, 20)) / (1 - g(B_, 20)))
gc = np.abs(v2[C_]["S11"])
R["VSWRCMAX"] = "%.2f" % ((1 + gc.max()) / (1 - gc.max()))
R["CMAX"] = "%.1f" % v2[C_]["s11db"].max()
R["REFMAX"] = "%.1f" % v2[A_]["s11db"].max()
R["ANG5"] = "%.1f" % np.degrees(np.angle(v2[B_]["S11"][idx(5)]))
m = (f >= 3) & (f <= 12)
par = {d: (v2[d]["C"][m].mean() * 1e12, v2[d]["L"][m].mean() * 1e9, v2[d]["Zeq"][m].mean(),
           v2[d]["tau"][m].mean() * 1e12) for d in [A_, B_, C_]}
R["CA"], R["LA"] = "%.3f" % par[A_][0], "%.3f" % par[A_][1]
R["CB"], R["LB"] = "%.3f" % par[B_][0], "%.3f" % par[B_][1]
R["CC"], R["LC"] = "%.3f" % par[C_][0], "%.3f" % par[C_][1]
R["ZEQB"], R["ZEQC"] = "%.0f" % par[B_][2], "%.0f" % par[C_][2]
R["DCPCT"] = "%.0f" % (100 * (par[B_][0] - par[C_][0]) / par[B_][0])
tau = par[B_][3]
R["TAUB"] = "%.2f" % tau
R["FPRED"] = "%.1f" % (0.1 / (math.pi * tau * 1e-12) / 1e9)
lg = lambda q: 300 / q / math.sqrt(ee)
R["FRAC7"] = "%.0f" % (lg(float(R["F20"])) / (W * math.sqrt(2)))
R["FRAC20"] = "%.1f" % (lg(20) / (W * math.sqrt(2)))
R["ILB10"] = "%.2f" % -v2[B_]["s21db"][idx(10)]
R["ILB20"] = "%.2f" % -v2[B_]["s21db"][idx(20)]
R["ILC20"] = "%.2f" % -v2[C_]["s21db"][idx(20)]
R["ILRB20"] = "%.2f" % (-10 * math.log10(1 - g(B_, 20) ** 2))
R["REFLB20"] = "%.1f" % (100 * g(B_, 20) ** 2)

P0 = v2["A0_Ref_SinPerd"]["pl"]
RAD = {B_: v2["B0_Curva90_SinPerd"]["pl"] - P0, C_: v2["C0_Chaflan_SinPerd"]["pl"] - P0}
DIS = {B_: v2[B_]["pl"] - v2["B0_Curva90_SinPerd"]["pl"], C_: v2[C_]["pl"] - v2["C0_Chaflan_SinPerd"]["pl"]}
low = f < 6
piso = 100 * max(np.abs(RAD[B_][low]).max(), np.abs(RAD[C_][low]).max())
R["PISO"] = "%.1f" % piso
R["RADB20"] = "%.1f" % (100 * RAD[B_][idx(20)])
R["RADC20"] = "%.1f" % (100 * RAD[C_][idx(20)])
R["EXPO"] = "%.0f" % (math.log(RAD[B_][idx(20)] / RAD[B_][idx(10)]) / math.log(2))
mm3 = f >= 3
R["DS11LOSS"] = "%.1f" % np.max(np.abs(v2[B_]["s11db"][mm3] - v2["B0_Curva90_SinPerd"]["s11db"][mm3]))

# Diagnostico
pd = {n: 100 * dd[n]["pl"][i10d] for n in dd}
R["DEEMB10"] = "%.1f" % (pd["R3_Orig_SinDeembed"] - pd["A_Referencia"])
R["DEEMB10DB"] = "%.2f" % (-10 * math.log10(1 - (pd["R3_Orig_SinDeembed"] - pd["A_Referencia"]) / 100))
l0 = 30.0
ad = 27.3 * er / math.sqrt(ee) * (ee - 1) / (er - 1) * 0.0027 / l0
Rs = math.sqrt(math.pi * 10e9 * 4 * math.pi * 1e-7 / 5.8e7)
ac = 8.686 * Rs / (Z0 * W * 1e-3) / 1000
R["FEED10"] = "%.2f" % ((ad + ac) * 12)
i10 = idx(10)
diag = [("Inicial", r"caja de \SI{4}{mm} y $8h$, $\max|\Delta S|<0.02$", pd["A_Referencia"]),
        ("R2", "sin pérdidas (PEC, $\\tan\\delta=0$)", pd["R2_Orig_SinPerdidas"]),
        ("R3", "sin de-embedding", pd["R3_Orig_SinDeembed"]),
        ("R4", "caras de los puertos conductoras", pd["R4_Orig_CarasPEC"]),
        ("R5", r"caja de \SI{7}{mm} y $14h$", pd["R5_Grande_ABC"]),
        ("R6", "R5 + caras conductoras", pd["R6_Grande_CarasPEC"]),
        ("R7", "R6 sin pérdidas", pd["R7_Grande_PEC_SinPerd"]),
        ("Final", r"caja de \SI{7}{mm} y $14h$, $\max|\Delta S|<0.005$", 100 * v2[A_]["pl"][i10]),
        ("Final sin pérdidas", "gemelo sin pérdidas del modelo final", 100 * P0[i10])]
R["DIAGROWS"] = "\n".join(r"%s & %s & %.2f \\" % r for r in diag)

conv = json.load(open(S + "conv_v2.json"))
nombres = [(A_, "Referencia"), (B_, "Curva sin chaflán"), (C_, "Curva con chaflán"),
           ("A0_Ref_SinPerd", "Referencia sin pérdidas"), ("B0_Curva90_SinPerd", "Curva sin chaflán, sin pérdidas"),
           ("C0_Chaflan_SinPerd", "Curva con chaflán, sin pérdidas")]
R["CONVROWS"] = "\n".join(r"%s & %d & \num{%d} & %.4f \\" % (n, conv[d]["passes"], conv[d]["tets"], conv[d]["ds"])
                          for d, n in nombres)

rows = []
for q in [2, 5, 10, 15, 20]:
    i = idx(q); fila = ["%g" % q]
    for d in [A_, B_, C_]:
        gg = abs(v2[d]["S11"][i])
        fila += ["%.1f" % v2[d]["s11db"][i], "%.3f" % gg, "%.2f" % ((1 + gg) / (1 - gg)), "%.2f" % v2[d]["s21db"][i]]
    rows.append(" & ".join(fila) + r" \\")
R["SROWS"] = "\n".join(rows)

rows = []
for d, n in [(A_, "Referencia"), (B_, "Curva sin chaflán"), (C_, "Curva con chaflán")]:
    c = cruce(v2[d]["s11db"], -20)
    rows.append(r"%s & %.3f & %.3f & %.1f & %.2f & %s \\" % (n, par[d][0], par[d][1], par[d][2], par[d][3],
                                                            (r"\SI{%.2f}{GHz}" % c) if c else r"$>\SI{20}{GHz}$"))
R["LCROWS"] = "\n".join(rows)

rows = []
for d, n in [(B_, "Sin chaflán"), (C_, "Con chaflán")]:
    for q in [10, 15, 20]:
        i = idx(q)
        t21 = 100 * 10 ** (v2[d]["s21db"][i] / 10)
        refl = 100 * abs(v2[d]["S11"][i]) ** 2
        rad = 100 * RAD[d][i]; dis = 100 * DIS[d][i]
        rows.append(r"%s & %d & %.1f & %.1f & %.1f & %.1f & %.1f & %.2f & %.2f \\" % (
            n, q, t21, refl, rad, dis, 100 - t21 - refl - rad - dis, -v2[d]["s21db"][i],
            -10 * math.log10(1 - abs(v2[d]["S11"][i]) ** 2)))
R["POWROWS"] = "\n".join(rows)

R["RCB"], R["RCC"] = "%.2f" % (par[B_][0] / par[A_][0]), "%.2f" % (par[C_][0] / par[A_][0])
hc = json.load(open(S + "campos_nums.json"))
R["HCEXT"], R["HJEXT"] = "%.1f" % hc["curva"]["Cext"], "%.2f" % hc["curva"]["Jext"]
R["HQOUT"], R["HIIN"] = "%.0f" % (100 * hc["curva"]["Qout"]), "%.0f" % (100 * hc["curva"]["Iin"])
R["HCCH"], R["HJCH"] = "%.1f" % hc["chaflan"]["Cch"], "%.2f" % hc["chaflan"]["Jch"]
R["HIINC"] = "%.0f" % (100 * hc["chaflan"]["Iin"])
R["HQB"], R["HQC"] = "%.2f" % hc["curva"]["Qrel"], "%.2f" % hc["chaflan"]["Qrel"]
dg = W * math.sqrt(2)
R["LG2"] = "%.0f" % lg(2)
R["FRAC2"] = "%.0f" % (lg(2) / dg)
R["FASE7"] = "%.0f" % (360 * dg / lg(float(R["F20"])))
R["FASE20"] = "%.0f" % (360 * dg / lg(20))
# Discontinuidad 2 (calculada por d2_analisis.py y fig_d2_campos.py)
for k, v in json.load(open(S + "d2_nums.json", encoding="utf-8")).items():
    R["D2_" + k] = v
c2 = json.load(open(S + "d2_campos.json"))["escalon"]
R["D2_CHOM"] = "%.1f" % c2["Chom"]
R["D2_ICEN"] = "%.0f" % (100 * c2["Icentro"])
R["D2_ICENL"] = "%.0f" % (100 * c2["Icentro_lejos"])
# Discontinuidad 3 (calculada por d3_analisis.py y fig_d3_campos.py)
for k, v in json.load(open(S + "d3_nums.json", encoding="utf-8")).items():
    R["D3_" + k] = v
c3 = json.load(open(S + "d3_campos.json"))
d3 = np.load(S + "d3_datos.npz")
R["D3_RQ02"] = "%.0f" % (100 * abs(c3["B2_Gap_0p2"]["ratio"]))
R["D3_RQ10"] = "%.0f" % (100 * abs(c3["B4_Gap_1p0"]["ratio"]))
R["D3_FL02"] = "%.0f" % (100 * c3["B2_Gap_0p2"]["frac"]["derecha"])
Cl = float(R["D3_CP1Q"]) * 1e-12 * 0.5e-3                       # C' * 0.5 mm
for k, i in [("RC02", 1), ("RC10", 3)]:
    cg, cp = float(d3["Cg"][i]), float(d3["Cp"][i])
    R["D3_" + k] = "%.0f" % (100 * cg / (cg + cp + Cl)) if 100 * cg / (cg + cp + Cl) >= 10 else "%.1f" % (100 * cg / (cg + cp + Cl))
# Discontinuidad 4 (calculada por d4_analisis.py y fig_d4_campos.py)
for k, v in json.load(open(S + "d4_nums.json", encoding="utf-8")).items():
    R["D4_" + k] = v
c4 = json.load(open(S + "d4_campos.json"))
R["D4_QSALTO"], R["D4_DSALTO"], R["D4_QCSALTO"] = "%.2f" % c4["q_salto"], "%.2f" % c4["D_salto"], "%.2f" % c4["qC_salto"]
R["D4_ESALTOPCT"] = "%.1f" % (100 * abs(c4["E_salto"] - 1))
R["D4_EAIREPCT"] = "%.1f" % (100 * abs(c4["Eaire"] - 1))
R["D4_VIMAX"] = "%.0f" % math.ceil(100 * max(abs(c4["V_salto"] - 1), abs(c4["I_salto"] - 1)))
# Discontinuidad 5 (calculada por d5_analisis.py y fig_d5_campos.py)
for k, v in json.load(open(S + "d5_nums.json", encoding="utf-8")).items():
    R["D5_" + k] = v
c5 = json.load(open(S + "d5_campos.json"))
R["D5_IDER"], R["D5_IRAMA"] = "%.2f" % c5["B_T"]["der"], "%.2f" % c5["B_T"]["rama"]
R["D5_CCUADRO"], R["D5_JESQ"] = "%.2f" % c5["B_T"]["Ccuadro"], "%.1f" % c5["B_T"]["Jesq"]
R["D5_CCUADROC"], R["D5_JESQC"] = "%.1f" % c5["C_Divisor"]["Ccuadro"], "%.1f" % c5["C_Divisor"]["Jesq"]
cs = json.load(open(S + "d5_stub.json"))
sa, sb, sc = cs["5p5GHz"], cs["10p8GHz"], cs["16p15GHz"]
R["D5S_IOUTA"], R["D5S_IOUTB"], R["D5S_IOUTC"] = "%.1f" % (100 * sa["Iout_in"]), "%.2f" % sb["Iout_in"], "%.0f" % (100 * sc["Iout_in"])
R["D5S_SIMINC"], R["D5S_SMINB"], R["D5S_SMINC"] = "%.1f" % sc["simin"], "%.1f" % sb["smin"], "%.2f" % sc["smin"]
R["D5S_LEF"] = "%.2f" % (8 + float(R["D5_DL3"]))
R["D5S_VENDA"], R["D5S_V0A"], R["D5S_V0C"] = "%.1f" % sa["Vend"], "%.3f" % sa["V0"], "%.2f" % sc["V0"]
R["D5S_ERRA"] = "%.1f" % (100 * sa["err"])
R["D5S_AA"], R["D5S_BA"], R["D5S_SUMA"] = "%.2f" % sa["A"], "%.2f" % sa["B"], "%.2f" % sa["suma"]
R["D5S_ANGA"], R["D5S_ANGB"], R["D5S_ANGC"] = "%.0f" % abs(sa["ang"]), "%.0f" % abs(sb["ang"]), "%.0f" % abs(sc["ang"])
R["D5S_SUMB"], R["D5S_I0B"] = "%.2f" % sb["suma"], "%.2f" % sb["I0"]
R["D5S_LG2C"] = "%.2f" % (sc["lg"] / 2)
NOMBRE = "Reporte_P2_Discontinuidades"
GUIA = "Guia_explicacion_P2"
tpl = open(S + "reporte_tpl.tex", encoding="utf-8").read()
for k, v in R.items():
    tpl = tpl.replace("<<%s>>" % k, v)
left = re.findall(r"<<[A-Za-z0-9_]+>>", tpl)
assert not left, left
tex = os.path.join(OUT, NOMBRE + ".tex")
open(tex, "w", encoding="utf-8").write(tpl)
for k in sorted(R):
    if "ROWS" not in k:
        print(k, R[k])

R["TETSMAX"] = "%d" % max(max(c["tets"] for c in conv.values()), int(R["D2_NMAX2"]))
R["TETSMAX1"] = "%d" % max(c["tets"] for c in conv.values())
R["TETSMAX"] = "%d" % max(int(R["TETSMAX"]), int(R["D3_NMAX3"]), int(R["D4_NMAX4"]), int(R["D5_NMAX5"]))
for _ in range(2):
    subprocess.run(["pdflatex", "-interaction=nonstopmode", NOMBRE + ".tex"], cwd=OUT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
aux = open(os.path.join(OUT, NOMBRE + ".aux"), encoding="utf-8", errors="ignore").read()
for lab, num in re.findall(r"\\newlabel\{((?:fig|tab|sec):[a-z0-9]+)\}\{\{([\d.]+)\}", aux):
    R["FIG:" + lab] = num
gt = open(S + "guia_tpl.tex", encoding="utf-8").read()
for k, v in R.items():
    gt = gt.replace("<<%s>>" % k, v)
left = re.findall(r"<<[A-Za-z0-9:_]+>>", gt)
assert not left, left
open(os.path.join(OUT, GUIA + ".tex"), "w", encoding="utf-8").write(gt)
for _ in range(2):
    subprocess.run(["pdflatex", "-interaction=nonstopmode", GUIA + ".tex"], cwd=OUT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("figuras:", {k: v for k, v in R.items() if k.startswith("FIG:")})
