# -*- coding: utf-8 -*-
# =====================================================================
# Proyecto 2 - Diagnostico de la linea de referencia
#
# Seis variantes de la linea recta de 50 ohm para encontrar de donde sale
# la "perdida" de ~4 % que aparece en 1 - |S11|^2 - |S21|^2:
#
#   R2_Orig_SinPerdidas      caja original, cobre -> PEC y tan d = 0
#   R3_Orig_SinDeembed       caja original, puertos sin de-embedding
#   R4_Orig_CarasPEC         caja original, caras de los puertos en PEC
#                            (sin frontera de radiacion pegada al puerto)
#   R5_Grande_ABC            caja grande (Mg = 7 mm, Hb = 14h), caras con radiacion
#   R6_Grande_CarasPEC       caja grande y caras de los puertos en PEC
#   R7_Grande_PEC_SinPerd    como R6, sin perdidas
#
# Ademas exporta la convergencia (numero de tetraedros por pase) de cada
# diseno, para saber cuanto margen queda bajo el limite de la version
# estudiantil.
#
# Uso: Automation -> Run Script.  Tarda unos minutos.
# Compatible con IronPython 2.7 y CPython 3.
# =====================================================================
import os

try:
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
except Exception:
    pass

NOMBRE_PROYECTO = "P2_Diagnostico_Referencia"

H_MM = 0.508
W_MM = 1.14
L1_MM = 6.0
ER = "3.55"
TAND = "0.0027"

F_SOL = "20GHz"
F_INI, F_FIN, F_PASO = "0.1GHz", "20GHz", "0.05GHz"
MAX_PASES = 10
DELTA_S = 0.02

SOLUCION = "Setup1 : Sweep1"
fallas = []


# ------------------------------ Utilidades ---------------------------
def msg(texto, nivel=0):
    try:
        oDesktop.AddMessage("", "", nivel, "[P2] " + texto)
    except Exception:
        pass


def aviso(texto):
    fallas.append(texto)
    msg(texto, 1)


def intentar(descripcion, variantes, silencioso=False):
    """Prueba variantes de una llamada hasta que una funcione.
    Devuelve el indice de la variante que funciono, o -1."""
    ultimo = ""
    for i, f in enumerate(variantes):
        try:
            f()
            return i
        except Exception as e:
            ultimo = str(e)
    if silencioso:
        msg("Opcional, no se pudo: %s" % descripcion)
    else:
        aviso("No se pudo: %s (%s)" % (descripcion, ultimo))
    return -1


def mm(x):
    return "%gmm" % x


# ------------------------------- Diseno ------------------------------
def nombres_disenos(oProject):
    try:
        return [str(n) for n in oProject.GetTopDesignList()]
    except Exception:
        return []


def nuevo_diseno(oProject, nombre):
    for tipo in ["HFSS Modal Network", "DrivenModal", ""]:
        try:
            oProject.InsertDesign("HFSS", nombre, tipo, "")
            break
        except Exception:
            if nombre in nombres_disenos(oProject):
                break
    oDesign = oProject.SetActiveDesign(nombre)
    try:
        st = str(oDesign.GetSolutionType())
    except Exception:
        st = ""
    if "Modal" not in st:
        intentar("fijar solucion Modal en " + nombre, [
            lambda: oDesign.SetSolutionType("HFSS Modal Network"),
            lambda: oDesign.SetSolutionType("HFSS Modal Network", ""),
            lambda: oDesign.SetSolutionType(
                "DrivenModal", ["NAME:Options", "EnableAutoOpen:=", False])])
    return oDesign


def variable(oDesign, nombre, valor):
    intentar("variable " + nombre, [lambda: oDesign.ChangeProperty(
        ["NAME:AllTabs",
         ["NAME:LocalVariableTab",
          ["NAME:PropServers", "LocalVariables"],
          ["NAME:NewProps",
           ["NAME:" + nombre, "PropType:=", "VariableProp",
            "UserDef:=", True, "Value:=", valor]]]])])


def material_sustrato(oProject, nombre="RO4003C", tand=None):
    if tand is None:
        tand = TAND
    oDef = oProject.GetDefinitionManager()
    try:
        if oDef.DoesMaterialExist(nombre):
            return
    except Exception:
        pass
    intentar("material " + nombre, [lambda: oDef.AddMaterial(
        ["NAME:" + nombre,
         "CoordinateSystemType:=", "Cartesian",
         "BulkOrSurfaceType:=", 1,
         ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
         "permittivity:=", ER,
         "dielectric_loss_tangent:=", tand])])


# ------------------------------ Geometria ----------------------------
def atributos(nombre, material, color, transp, completo):
    a = ["NAME:Attributes", "Name:=", nombre, "Flags:=", "",
         "Color:=", color, "Transparency:=", transp,
         "PartCoordinateSystem:=", "Global", "UDMId:=", "",
         "MaterialValue:=", '"%s"' % material,
         "SurfaceMaterialValue:=", '""', "SolveInside:=", True]
    if completo:
        a += ["ShellElement:=", False, "ShellElementThickness:=", "0mm",
              "IsMaterialEditable:=", True, "UseMaterialAppearance:=", False,
              "IsLightweight:=", False]
    return a


def crear(oEditor, metodo, params, nombre, material, color, transp):
    f = getattr(oEditor, metodo)
    return intentar("crear " + nombre, [
        lambda: f(params, atributos(nombre, material, color, transp, True)),
        lambda: f(params, atributos(nombre, material, color, transp, False))])


def caja(oEditor, nombre, pos, tam, material, color, transp):
    params = ["NAME:BoxParameters",
              "XPosition:=", pos[0], "YPosition:=", pos[1], "ZPosition:=", pos[2],
              "XSize:=", tam[0], "YSize:=", tam[1], "ZSize:=", tam[2]]
    crear(oEditor, "CreateBox", params, nombre, material, color, transp)


def lamina(oEditor, nombre, puntos, color="(255 128 64)", transp=0):
    """Lamina plana cerrada definida por sus vertices (x, y, z)."""
    pts = ["NAME:PolylinePoints"]
    for p in list(puntos) + [puntos[0]]:
        pts.append(["NAME:PLPoint", "X:=", p[0], "Y:=", p[1], "Z:=", p[2]])
    seg = ["NAME:PolylineSegments"]
    for i in range(len(puntos)):
        seg.append(["NAME:PLSegment", "SegmentType:=", "Line",
                    "StartIndex:=", i, "NoOfPoints:=", 2])
    xs = ["NAME:PolylineXSection", "XSectionType:=", "None",
          "XSectionOrient:=", "Auto", "XSectionWidth:=", "0mm",
          "XSectionTopWidth:=", "0mm", "XSectionHeight:=", "0mm",
          "XSectionNumSegments:=", "0", "XSectionBendType:=", "Corner"]
    params = ["NAME:PolylineParameters", "IsPolylineCovered:=", True,
              "IsPolylineClosed:=", True, pts, seg, xs]
    crear(oEditor, "CreatePolyline", params, nombre, "vacuum", color, transp)


def rect_plano(oEditor, nombre, plano, c, r1, r2, color="(0 0 255)", transp=0.6):
    """Rectangulo en el plano X=c (r1=y, r2=z), Y=c (r1=x, r2=z) o Z=c (r1=x, r2=y)."""
    a0, a1 = r1
    b0, b1 = r2
    if plano == "X":
        pts = [(c, a0, b0), (c, a1, b0), (c, a1, b1), (c, a0, b1)]
    elif plano == "Y":
        pts = [(a0, c, b0), (a1, c, b0), (a1, c, b1), (a0, c, b1)]
    else:
        pts = [(a0, b0, c), (a1, b0, c), (a1, b1, c), (a0, b1, c)]
    lamina(oEditor, nombre, pts, color, transp)


# --------------------------- Fronteras y puertos ---------------------
def perfecto(oDesign, nombre, objetos):
    oB = oDesign.GetModule("BoundarySetup")
    intentar("Perfect E en " + nombre, [lambda: oB.AssignPerfectE(
        ["NAME:" + nombre, "Objects:=", objetos, "InfGroundPlane:=", False])])


def cond_finita(oDesign, nombre, objetos):
    oB = oDesign.GetModule("BoundarySetup")
    i = intentar("cobre en " + nombre, [
        lambda: oB.AssignFiniteCond(
            ["NAME:" + nombre, "Objects:=", objetos,
             "UseMaterial:=", True, "Material:=", "copper",
             "UseThickness:=", False, "Roughness:=", "0um",
             "InfGroundPlane:=", False, "IsTwoSided:=", False,
             "IsInternal:=", True]),
        lambda: oB.AssignPerfectE(
            ["NAME:" + nombre, "Objects:=", objetos, "InfGroundPlane:=", False])])
    if i == 1:
        aviso("%s quedo como Perfect E (sin perdidas de cobre)" % nombre)


def radiacion(oDesign, objetos):
    oB = oDesign.GetModule("BoundarySetup")
    intentar("frontera de radiacion", [
        lambda: oB.AssignRadiation(["NAME:Rad1", "Objects:=", objetos,
                                    "IsFssReference:=", False,
                                    "IsForPML:=", False]),
        lambda: oB.AssignRadiation(["NAME:Rad1", "Objects:=", objetos])])


def puerto(oDesign, nombre, objeto, ini, fin, deembed=True):
    """Wave port de 1 modo, renormalizado a 50 ohm y con de-embedding
    de L1 (el plano de referencia queda en el borde de la discontinuidad)."""
    oB = oDesign.GetModule("BoundarySetup")

    def args(deemb, linea):
        modo = ["NAME:Mode1", "ModeNum:=", 1]
        if linea:
            modo += ["UseIntLine:=", True,
                     ["NAME:IntLine", "Start:=", ini, "End:=", fin]]
        else:
            modo += ["UseIntLine:=", False]
        modo += ["AlignmentGroup:=", 0, "CharImp:=", "Zpi", "RenormImp:=", "50ohm"]
        a = ["NAME:" + nombre, "Objects:=", [objeto], "NumModes:=", 1,
             "UseLineModeAlignment:=", False]
        if deemb:
            a += ["DoDeembed:=", True, "DeembedDist:=", deemb]
        else:
            a += ["DoDeembed:=", False]
        a += ["RenormalizeAllTerminals:=", True, ["NAME:Modes", modo],
              "ShowReporterFilter:=", False, "ReporterFilter:=", [True],
              "UseAnalyticAlignment:=", False]
        return a

    if not deembed:
        intentar("puerto " + nombre, [
            lambda: oB.AssignWavePort(args(None, True)),
            lambda: oB.AssignWavePort(args(None, False))])
        return
    i = intentar("puerto " + nombre, [
        lambda: oB.AssignWavePort(args("L1", True)),
        lambda: oB.AssignWavePort(args(mm(L1_MM), True)),
        lambda: oB.AssignWavePort(args(None, True)),
        lambda: oB.AssignWavePort(args(None, False)),
        lambda: oB.AssignWavePort(["NAME:" + nombre, "Objects:=", [objeto],
                                   "NumModes:=", 1])])
    if i >= 2:
        aviso("Puerto %s creado sin de-embedding; activalo a mano con "
              "distancia L1 (propiedades del puerto)" % nombre)


# ------------------------- Analisis y graficas -----------------------
def analisis(oDesign):
    oA = oDesign.GetModule("AnalysisSetup")
    intentar("Setup1", [
        lambda: oA.InsertSetup("HfssDriven", [
            "NAME:Setup1", "SolveType:=", "Single", "Frequency:=", F_SOL,
            "MaxDeltaS:=", DELTA_S, "UseMatrixConv:=", False,
            "MaximumPasses:=", MAX_PASES, "MinimumPasses:=", 2,
            "MinimumConvergedPasses:=", 2, "PercentRefinement:=", 25,
            "IsEnabled:=", True, "BasisOrder:=", 1,
            "DoLambdaRefine:=", True, "DoMaterialLambda:=", True,
            "SetLambdaTarget:=", False, "Target:=", 0.3333,
            "UseMaxTetIncrease:=", False, "PortAccuracy:=", 2,
            "UseABCOnPort:=", False, "SetPortMinMaxTri:=", False,
            "UseDomains:=", False, "UseIterativeSolver:=", False,
            "SaveRadFieldsOnly:=", False, "SaveAnyFields:=", True]),
        lambda: oA.InsertSetup("HfssDriven", [
            "NAME:Setup1", "Frequency:=", F_SOL, "MaxDeltaS:=", DELTA_S,
            "MaximumPasses:=", MAX_PASES, "MinimumPasses:=", 2,
            "MinimumConvergedPasses:=", 2, "PercentRefinement:=", 25,
            "IsEnabled:=", True])])
    intentar("barrido de frecuencia", [
        lambda: oA.InsertFrequencySweep("Setup1", [
            "NAME:Sweep1", "IsEnabled:=", True, "RangeType:=", "LinearStep",
            "RangeStart:=", F_INI, "RangeEnd:=", F_FIN, "RangeStep:=", F_PASO,
            "Type:=", "Interpolating", "SaveFields:=", False,
            "SaveRadFields:=", False, "InterpTolerance:=", 0.5,
            "InterpMaxSolns:=", 250, "InterpMinSolns:=", 0,
            "InterpMinSubranges:=", 1, "InterpUseS:=", True,
            "InterpUsePortImped:=", False, "InterpUsePropConst:=", True,
            "UseDerivativeConvergence:=", False, "InterpDerivTolerance:=", 0.2,
            "UseFullBasis:=", True, "EnforcePassivity:=", True,
            "PassivityErrorTolerance:=", 0.0001]),
        lambda: oA.InsertFrequencySweep("Setup1", [
            "NAME:Sweep1", "IsEnabled:=", True, "RangeType:=", "LinearStep",
            "RangeStart:=", F_INI, "RangeEnd:=", F_FIN, "RangeStep:=", F_PASO,
            "Type:=", "Interpolating"])])


def variables_salida(oDesign):
    oV = oDesign.GetModule("OutputVariable")
    hechas = []
    for nombre, expr in [
            ("Gamma_mag", "mag(S(1,1))"),
            ("VSWR_P1", "(1+mag(S(1,1)))/(1-mag(S(1,1)))"),
            ("RL_dB", "-dB(S(1,1))"),
            ("IL_dB", "-dB(S(2,1))"),
            # potencia que ni se refleja ni se transmite: radiacion + perdidas
            ("P_perdida", "1-mag(S(1,1))^2-mag(S(2,1))^2")]:
        ok = intentar("variable de salida " + nombre, [
            lambda: oV.CreateOutputVariable(nombre, expr, SOLUCION,
                                            "Modal Solution Data", []),
            lambda: oV.CreateOutputVariable(nombre, expr, SOLUCION,
                                            "Modal Solution Data",
                                            ["Domain:=", "Sweep"])])
        if ok >= 0:
            hechas.append(nombre)
    return hechas


def graficas(oDesign, nombres_var, salidas):
    oR = oDesign.GetModule("ReportSetup")
    fam = ["Freq:=", ["All"]]
    for v in nombres_var:
        fam += [v + ":=", ["Nominal"]]

    def reporte(nombre, tipo, alternativas, silencioso=False):
        variantes = []
        for exprs in alternativas:
            if tipo == "Smith Chart":
                tr = ["Polar Component:=", exprs]
            else:
                tr = ["X Component:=", "Freq", "Y Component:=", exprs]
            variantes += [
                lambda tr=tr: oR.CreateReport(nombre, "Modal Solution Data", tipo,
                                              SOLUCION, ["Domain:=", "Sweep"], fam, tr),
                lambda tr=tr: oR.CreateReport(nombre, "Modal Solution Data", tipo,
                                              SOLUCION, ["Domain:=", "Sweep"], fam, tr, []),
                lambda tr=tr: oR.CreateReport(nombre, "Modal Solution Data", tipo,
                                              SOLUCION, [], ["Freq:=", ["All"]], tr)]
        intentar("grafica " + nombre, variantes, silencioso)

    reporte("01_S11_S21_dB", "Rectangular Plot", [["dB(S(1,1))", "dB(S(2,1))"]])
    g = [["Gamma_mag"]] if "Gamma_mag" in salidas else []
    reporte("02_Gamma_mag", "Rectangular Plot", g + [["mag(S(1,1))"]])
    v = [["VSWR_P1"]] if "VSWR_P1" in salidas else []
    reporte("03_VSWR", "Rectangular Plot", v + [["VSWR(1)"]])
    reporte("04_Smith_S11", "Smith Chart", [["S(1,1)"]])
    reporte("05_Fase_deg", "Rectangular Plot",
            [["ang_deg(S(1,1))", "ang_deg(S(2,1))"]])
    reporte("06_Zo_puerto", "Rectangular Plot",
            [["re(Zo(1))", "im(Zo(1))"], ["mag(Zo(1))"]], silencioso=True)
    p = [["P_perdida"]] if "P_perdida" in salidas else []
    reporte("07_Balance_potencia", "Rectangular Plot",
            p + [["1-mag(S(1,1))^2-mag(S(2,1))^2"]], silencioso=True)


# ------------------------- Construccion de variantes -----------------
def construir_ref(oProject, nombre, mg, hb_fac, caras, perdidas, deembed):
    """Linea recta de 50 ohm.
    mg: margen lateral (mm); hb_fac: altura de la caja en multiplos de h;
    caras: 'abc' (radiacion junto al puerto) o 'pec' (pared conductora);
    perdidas: cobre + tan d reales, o PEC + tan d = 0; deembed: L1 o nada."""
    msg("Construyendo %s ..." % nombre)
    oDesign = nuevo_diseno(oProject, nombre)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    intentar("unidades mm", [lambda: oEditor.SetModelUnits(
        ["NAME:Units Parameter", "Units:=", "mm", "Rescale:=", False])],
        silencioso=True)

    nombres_var = ["h", "W", "L1", "Mg", "Hb", "Hp", "Pw"]
    variable(oDesign, "h", mm(H_MM))
    variable(oDesign, "W", mm(W_MM))
    variable(oDesign, "L1", mm(L1_MM))
    variable(oDesign, "Mg", mm(mg))
    variable(oDesign, "Hb", "%g*h" % hb_fac)   # altura de la caja de aire
    variable(oDesign, "Hp", "8*h")             # altura del puerto (fija)
    variable(oDesign, "Pw", "5*W")             # ancho del puerto (fijo)

    XMAX, YMIN, YMAX = "2*L1+W", "-W/2-Mg", "W/2+Mg"
    ANCHO_Y = "(%s)-(%s)" % (YMAX, YMIN)
    mat = "RO4003C" if perdidas else "RO4003C_SinPerdidas"

    caja(oEditor, "Sustrato", ("0mm", YMIN, "0mm"), (XMAX, ANCHO_Y, "h"),
         mat, "(0 128 0)", 0.6)
    caja(oEditor, "Aire", ("0mm", YMIN, "h"), (XMAX, ANCHO_Y, "Hb-h"),
         "vacuum", "(128 255 255)", 0.9)
    lamina(oEditor, "Traza", [("0mm", "-W/2", "h"), (XMAX, "-W/2", "h"),
                              (XMAX, "W/2", "h"), ("0mm", "W/2", "h")])
    rect_plano(oEditor, "Tierra", "Z", "0mm", ("0mm", XMAX), (YMIN, YMAX),
               "(255 200 120)", 0.3)

    G = "(200 200 200)"
    ZB = ("0mm", "Hb")
    rad = ["Rad_Arriba", "Rad_Ymin", "Rad_Ymax"]
    rect_plano(oEditor, "Rad_Arriba", "Z", "Hb", ("0mm", XMAX), (YMIN, YMAX), G, 0.9)
    rect_plano(oEditor, "Rad_Ymin", "Y", YMIN, ("0mm", XMAX), ZB, G, 0.9)
    rect_plano(oEditor, "Rad_Ymax", "Y", YMAX, ("0mm", XMAX), ZB, G, 0.9)
    rect_plano(oEditor, "P1", "X", "0mm", ("-Pw/2", "Pw/2"), ("0mm", "Hp"))
    rect_plano(oEditor, "P2", "X", XMAX, ("-Pw/2", "Pw/2"), ("0mm", "Hp"))
    if caras == "abc":
        for xc, suf in [("0mm", "X0"), (XMAX, "XL")]:
            rect_plano(oEditor, "Rad_%sa" % suf, "X", xc, ("Pw/2", YMAX), ZB, G, 0.9)
            rect_plano(oEditor, "Rad_%sb" % suf, "X", xc, (YMIN, "-Pw/2"), ZB, G, 0.9)
            rad += ["Rad_%sa" % suf, "Rad_%sb" % suf]
            if hb_fac > 8:
                rect_plano(oEditor, "Rad_%sc" % suf, "X", xc, ("-Pw/2", "Pw/2"),
                           ("Hp", "Hb"), G, 0.9)
                rad.append("Rad_%sc" % suf)

    if perdidas:
        cond_finita(oDesign, "Cu_Traza", ["Traza"])
        cond_finita(oDesign, "Cu_Tierra", ["Tierra"])
    else:
        perfecto(oDesign, "PEC_Traza", ["Traza"])
        perfecto(oDesign, "PEC_Tierra", ["Tierra"])
    radiacion(oDesign, rad)

    x2 = 2 * L1_MM + W_MM
    puerto(oDesign, "1", "P1", ["0mm", "0mm", "0mm"], ["0mm", "0mm", mm(H_MM)], deembed)
    puerto(oDesign, "2", "P2", [mm(x2), "0mm", "0mm"], [mm(x2), "0mm", mm(H_MM)], deembed)

    analisis(oDesign)
    salidas = variables_salida(oDesign)
    graficas(oDesign, nombres_var, salidas)
    try:
        msg("%s: validacion = %s" % (nombre, oDesign.ValidateDesign()))
    except Exception:
        pass
    try:
        oEditor.FitAll()
    except Exception:
        pass
    return oDesign


def exportar_convergencia(oDesign, nombre, carpeta, mg, hb_fac):
    ruta = os.path.join(carpeta, "%s__convergencia.txt" % nombre)
    v_ind = "h='%gmm',W='%gmm',L1='%gmm',Mg='%gmm'" % (H_MM, W_MM, L1_MM, mg)
    v_ind2 = "h=%gmm,W=%gmm,L1=%gmm,Mg=%gmm" % (H_MM, W_MM, L1_MM, mg)
    v_all = v_ind + ",Hb='%g*h',Hp='8*h',Pw='5*W'" % hb_fac
    i = intentar("convergencia de " + nombre, [
        lambda: oDesign.ExportConvergence("Setup1", "", ruta),
        lambda: oDesign.ExportConvergence("Setup1", v_ind, ruta),
        lambda: oDesign.ExportConvergence("Setup1", v_ind2, ruta),
        lambda: oDesign.ExportConvergence("Setup1", v_all, ruta),
        lambda: oDesign.ExportConvergence("Setup1", "", ruta, True)], silencioso=True)
    rp = os.path.join(carpeta, "%s__perfil.txt" % nombre)
    intentar("perfil de " + nombre, [
        lambda: oDesign.ExportProfile("Setup1", "", rp),
        lambda: oDesign.ExportProfile("Setup1", "", rp, True),
        lambda: oDesign.ExportProfile("Setup1", v_ind, rp)], silencioso=True)


# -------------------------------- Main -------------------------------
#            nombre                  Mg   Hb/h  caras  perdidas deembed
VARIANTES = [("R2_Orig_SinPerdidas",   4.0,  8,  "abc", False, True),
             ("R3_Orig_SinDeembed",    4.0,  8,  "abc", True,  False),
             ("R4_Orig_CarasPEC",      4.0,  8,  "pec", True,  True),
             ("R5_Grande_ABC",         7.0, 14,  "abc", True,  True),
             ("R6_Grande_CarasPEC",    7.0, 14,  "pec", True,  True),
             ("R7_Grande_PEC_SinPerd", 7.0, 14,  "pec", False, True)]

try:
    oDesktop.RestoreWindow()
except Exception:
    pass

oProject = oDesktop.NewProject()
material_sustrato(oProject, "RO4003C", TAND)
material_sustrato(oProject, "RO4003C_SinPerdidas", "0")
for v in VARIANTES:
    construir_ref(oProject, *v)

try:
    base = str(oDesktop.GetProjectDirectory())
except Exception:
    base = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
carpeta = os.path.join(base, "Proyecto2_Microcinta")
if not os.path.isdir(carpeta):
    os.makedirs(carpeta)
ruta = os.path.join(carpeta, NOMBRE_PROYECTO + ".aedt")
n = 2
while os.path.exists(ruta):
    ruta = os.path.join(carpeta, "%s_v%d.aedt" % (NOMBRE_PROYECTO, n))
    n += 1
intentar("guardar proyecto", [lambda: oProject.SaveAs(ruta, True)])
msg("Proyecto guardado en: " + ruta)

csv_dir = os.path.join(os.path.dirname(ruta),
                       os.path.splitext(os.path.basename(ruta))[0] + "_CSV")
if not os.path.isdir(csv_dir):
    os.makedirs(csv_dir)

for v in VARIANTES:
    nombre = v[0]
    msg("Resolviendo %s ..." % nombre)
    oDesign = oProject.SetActiveDesign(nombre)
    intentar("resolver " + nombre, [lambda: oDesign.AnalyzeAll()])
intentar("guardar resultados", [lambda: oProject.Save()])

for v in VARIANTES:
    nombre = v[0]
    oDesign = oProject.SetActiveDesign(nombre)
    oR = oDesign.GetModule("ReportSetup")
    for r in ["01_S11_S21_dB", "05_Fase_deg", "07_Balance_potencia"]:
        archivo = os.path.join(csv_dir, "%s__%s.csv" % (nombre, r))
        intentar("exportar %s/%s" % (nombre, r),
                 [lambda: oR.ExportToFile(r, archivo)], silencioso=True)
    exportar_convergencia(oDesign, nombre, csv_dir, v[1], v[2])
msg("CSV exportados en: " + csv_dir)

if fallas:
    msg("Terminado con %d aviso(s). Revisa los mensajes [P2] anteriores." % len(fallas), 1)
else:
    msg("Terminado sin errores.")
