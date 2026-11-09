# -*- coding: utf-8 -*-
# =====================================================================
# Proyecto 2 - Discontinuidades en interconectores de microcinta
# Discontinuidad 1: curva de 90 grados  (version 2, modelo corregido)
#
# Cambios respecto a la version 1, segun el diagnostico de la referencia:
#   - Caja de aire mas grande: margen lateral 7 mm y altura 14h. La
#     frontera de radiacion estaba tan cerca que absorbia parte del campo
#     cercano de la linea (aparecia como "perdida" falsa).
#   - Malla mucho mas fina: Delta S = 0.005 (antes 0.02). La version 1
#     convergia con solo ~3 000 elementos; el limite estudiantil es 64 000.
#   - Gemelos sin perdidas (cobre -> PEC, tan d = 0) de cada diseno, para
#     separar la radiacion de las perdidas de cobre y dielectrico.
#
# Disenos:
#   A_Referencia, B_Curva90, C_Curva90_Chaflan            (con perdidas)
#   A0_Ref_SinPerd, B0_Curva90_SinPerd, C0_Chaflan_SinPerd (sin perdidas)
#
# Uso: Automation -> Run Script. Tarda bastante mas que la version 1.
# Compatible con IronPython 2.7 y CPython 3.
# =====================================================================
import os

try:
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
except Exception:
    pass

RESOLVER = True
EXPORTAR_CSV = True
NOMBRE_PROYECTO = "P2_D1_Curva90_v2"

# Sustrato Rogers RO4003C: h = 0.508 mm, er = 3.55, tan d = 0.0027
H_MM = 0.508      # espesor del sustrato
W_MM = 1.14       # ancho para 50 ohm (W/h = 2.24)
L1_MM = 6.0       # tramo recto entre cada puerto y la discontinuidad
MG_MM = 7.0       # margen lateral desde el borde de la traza (antes 4 mm)
HB_FAC = 14       # altura de la caja de aire = 14h (antes 8h)
MITER = 0.55      # chaflan optimo: M = 52 + 65 exp(-1.35 W/h) = 55 %
ER = "3.55"
TAND = "0.0027"

F_SOL = "20GHz"
F_INI, F_FIN, F_PASO = "0.1GHz", "20GHz", "0.05GHz"
MAX_PASES = 15    # con 30 % por pase se queda por debajo de ~50 000 elementos
MIN_PASES = 3
DELTA_S = 0.005

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
            "MaximumPasses:=", MAX_PASES, "MinimumPasses:=", MIN_PASES,
            "MinimumConvergedPasses:=", 2, "PercentRefinement:=", 30,
            "IsEnabled:=", True, "BasisOrder:=", 1,
            "DoLambdaRefine:=", True, "DoMaterialLambda:=", True,
            "SetLambdaTarget:=", False, "Target:=", 0.3333,
            "UseMaxTetIncrease:=", False, "PortAccuracy:=", 2,
            "UseABCOnPort:=", False, "SetPortMinMaxTri:=", False,
            "UseDomains:=", False, "UseIterativeSolver:=", False,
            "SaveRadFieldsOnly:=", False, "SaveAnyFields:=", True]),
        lambda: oA.InsertSetup("HfssDriven", [
            "NAME:Setup1", "Frequency:=", F_SOL, "MaxDeltaS:=", DELTA_S,
            "MaximumPasses:=", MAX_PASES, "MinimumPasses:=", MIN_PASES,
            "MinimumConvergedPasses:=", 2, "PercentRefinement:=", 30,
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


# ------------------------- Construccion de disenos -------------------
def construir(oProject, nombre, tipo, perdidas=True):
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
    variable(oDesign, "Mg", mm(MG_MM))
    variable(oDesign, "Hb", "%g*h" % HB_FAC)  # altura de la caja de aire
    variable(oDesign, "Hp", "8*h")            # altura del puerto
    variable(oDesign, "Pw", "5*W")            # ancho del puerto: sin modos de caja < 25 GHz
    if tipo == "chaflan":
        variable(oDesign, "Mt", "%g" % MITER)
        nombres_var.append("Mt")

    YMIN = "-W/2-Mg"
    if tipo == "recta":
        XMAX, YMAX = "2*L1+W", "W/2+Mg"
    else:
        XMAX, YMAX = "L1+W+Mg", "W/2+L1"
    ANCHO_Y = "(%s)-(%s)" % (YMAX, YMIN)
    mat = "RO4003C" if perdidas else "RO4003C_SinPerdidas"

    # Volumenes
    caja(oEditor, "Sustrato", ("0mm", YMIN, "0mm"), (XMAX, ANCHO_Y, "h"),
         mat, "(0 128 0)", 0.6)
    caja(oEditor, "Aire", ("0mm", YMIN, "h"), (XMAX, ANCHO_Y, "Hb-h"),
         "vacuum", "(128 255 255)", 0.9)

    # Traza superior
    if tipo == "recta":
        traza = [("0mm", "-W/2", "h"), ("2*L1+W", "-W/2", "h"),
                 ("2*L1+W", "W/2", "h"), ("0mm", "W/2", "h")]
    elif tipo == "curva":
        traza = [("0mm", "-W/2", "h"), ("L1+W", "-W/2", "h"),
                 ("L1+W", "W/2+L1", "h"), ("L1", "W/2+L1", "h"),
                 ("L1", "W/2", "h"), ("0mm", "W/2", "h")]
    else:
        traza = [("0mm", "-W/2", "h"), ("L1+W-2*Mt*W", "-W/2", "h"),
                 ("L1+W", "-W/2+2*Mt*W", "h"), ("L1+W", "W/2+L1", "h"),
                 ("L1", "W/2+L1", "h"), ("L1", "W/2", "h"), ("0mm", "W/2", "h")]
    lamina(oEditor, "Traza", traza, "(255 128 64)", 0)
    rect_plano(oEditor, "Tierra", "Z", "0mm", ("0mm", XMAX), (YMIN, YMAX),
               "(255 200 120)", 0.3)

    # Puertos (altura Hp) y laminas de radiacion (resto de las caras)
    G = "(200 200 200)"
    ZB, ZP, ZS = ("0mm", "Hb"), ("0mm", "Hp"), ("Hp", "Hb")
    rad = ["Rad_Arriba", "Rad_Ymin"]
    rect_plano(oEditor, "Rad_Arriba", "Z", "Hb", ("0mm", XMAX), (YMIN, YMAX), G, 0.9)
    rect_plano(oEditor, "Rad_Ymin", "Y", YMIN, ("0mm", XMAX), ZB, G, 0.9)
    rect_plano(oEditor, "P1", "X", "0mm", ("-Pw/2", "Pw/2"), ZP)
    rect_plano(oEditor, "Rad_X0a", "X", "0mm", ("Pw/2", YMAX), ZB, G, 0.9)
    rect_plano(oEditor, "Rad_X0b", "X", "0mm", (YMIN, "-Pw/2"), ZB, G, 0.9)
    rect_plano(oEditor, "Rad_X0c", "X", "0mm", ("-Pw/2", "Pw/2"), ZS, G, 0.9)
    rad += ["Rad_X0a", "Rad_X0b", "Rad_X0c"]
    if tipo == "recta":
        rect_plano(oEditor, "P2", "X", XMAX, ("-Pw/2", "Pw/2"), ZP)
        rect_plano(oEditor, "Rad_XLa", "X", XMAX, ("Pw/2", YMAX), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_XLb", "X", XMAX, (YMIN, "-Pw/2"), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_XLc", "X", XMAX, ("-Pw/2", "Pw/2"), ZS, G, 0.9)
        rect_plano(oEditor, "Rad_Ymax", "Y", YMAX, ("0mm", XMAX), ZB, G, 0.9)
        rad += ["Rad_XLa", "Rad_XLb", "Rad_XLc", "Rad_Ymax"]
        x2, y2 = 2 * L1_MM + W_MM, 0.0
    else:
        X2A, X2B = "L1+W/2-Pw/2", "L1+W/2+Pw/2"
        rect_plano(oEditor, "P2", "Y", YMAX, (X2A, X2B), ZP)
        rect_plano(oEditor, "Rad_Ymax_a", "Y", YMAX, ("0mm", X2A), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_Ymax_b", "Y", YMAX, (X2B, XMAX), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_Ymax_c", "Y", YMAX, (X2A, X2B), ZS, G, 0.9)
        rect_plano(oEditor, "Rad_Xmax", "X", XMAX, (YMIN, YMAX), ZB, G, 0.9)
        rad += ["Rad_Ymax_a", "Rad_Ymax_b", "Rad_Ymax_c", "Rad_Xmax"]
        x2, y2 = L1_MM + W_MM / 2.0, W_MM / 2.0 + L1_MM

    # Fronteras
    if perdidas:
        cond_finita(oDesign, "Cu_Traza", ["Traza"])
        cond_finita(oDesign, "Cu_Tierra", ["Tierra"])
    else:
        perfecto(oDesign, "PEC_Traza", ["Traza"])
        perfecto(oDesign, "PEC_Tierra", ["Tierra"])
    radiacion(oDesign, rad)

    # Puertos (linea de integracion de tierra a la traza)
    puerto(oDesign, "1", "P1", ["0mm", "0mm", "0mm"], ["0mm", "0mm", mm(H_MM)])
    puerto(oDesign, "2", "P2", [mm(x2), mm(y2), "0mm"], [mm(x2), mm(y2), mm(H_MM)])

    analisis(oDesign)
    salidas = variables_salida(oDesign)
    graficas(oDesign, nombres_var, salidas)

    try:
        msg("%s: validacion = %s (1 = correcto)" % (nombre, oDesign.ValidateDesign()))
    except Exception:
        pass
    try:
        oEditor.FitAll()
    except Exception:
        pass
    return oDesign


def exportar_convergencia(oDesign, nombre, carpeta):
    ruta = os.path.join(carpeta, "%s__convergencia.txt" % nombre)
    v_ind = "h='%gmm',W='%gmm',L1='%gmm',Mg='%gmm'" % (H_MM, W_MM, L1_MM, MG_MM)
    intentar("convergencia de " + nombre, [
        lambda: oDesign.ExportConvergence("Setup1", "", ruta),
        lambda: oDesign.ExportConvergence("Setup1", v_ind, ruta),
        lambda: oDesign.ExportConvergence("Setup1", "", ruta, True)], silencioso=True)


# -------------------------------- Main -------------------------------
#          nombre                 tipo       perdidas
DISENOS = [("A_Referencia",       "recta",   True),
           ("B_Curva90",          "curva",   True),
           ("C_Curva90_Chaflan",  "chaflan", True),
           ("A0_Ref_SinPerd",     "recta",   False),
           ("B0_Curva90_SinPerd", "curva",   False),
           ("C0_Chaflan_SinPerd", "chaflan", False)]

try:
    oDesktop.RestoreWindow()
except Exception:
    pass

oProject = oDesktop.NewProject()
material_sustrato(oProject, "RO4003C", TAND)
material_sustrato(oProject, "RO4003C_SinPerdidas", "0")
for d in DISENOS:
    construir(oProject, *d)

# Guardar en Documentos\Ansoft\Proyecto2_Microcinta
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

if RESOLVER:
    for d in DISENOS:
        nombre = d[0]
        msg("Resolviendo %s (puede tardar varios minutos) ..." % nombre)
        oDesign = oProject.SetActiveDesign(nombre)
        intentar("resolver " + nombre, [lambda: oDesign.AnalyzeAll()])
        intentar("guardar resultados", [lambda: oProject.Save()], silencioso=True)

    if EXPORTAR_CSV:
        csv_dir = os.path.join(os.path.dirname(ruta),
                               os.path.splitext(os.path.basename(ruta))[0] + "_CSV")
        if not os.path.isdir(csv_dir):
            os.makedirs(csv_dir)
        for d in DISENOS:
            nombre = d[0]
            oDesign = oProject.SetActiveDesign(nombre)
            oR = oDesign.GetModule("ReportSetup")
            try:
                reportes = [str(r) for r in oR.GetAllReportNames()]
            except Exception:
                reportes = ["01_S11_S21_dB", "02_Gamma_mag", "03_VSWR",
                            "04_Smith_S11", "05_Fase_deg", "06_Zo_puerto",
                            "07_Balance_potencia"]
            for r in reportes:
                archivo = os.path.join(csv_dir, "%s__%s.csv" % (nombre, r))
                intentar("exportar %s/%s" % (nombre, r),
                         [lambda: oR.ExportToFile(r, archivo)], silencioso=True)
            exportar_convergencia(oDesign, nombre, csv_dir)
        msg("CSV exportados en: " + csv_dir)

if fallas:
    msg("Terminado con %d aviso(s). Revisa los mensajes [P2] anteriores." % len(fallas), 1)
else:
    msg("Terminado sin errores.")
