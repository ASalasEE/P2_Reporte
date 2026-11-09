# -*- coding: utf-8 -*-
# =====================================================================
# Proyecto 2 - Discontinuidades en interconectores de microcinta
# Discontinuidad 5: union en T
#
# Sobre el mismo RO4003C de las discontinuidades anteriores se construyen:
#   B_T        T de tres brazos de 50 ohm (W = 1.14 mm), tres puertos:
#              P1 y P2 en los extremos de la linea principal, P3 en la rama
#   C_Divisor  divisor en T: rama de entrada de 50 ohm (P3) y linea
#              principal de 100 ohm (W = 0.29 mm, P1 y P2); 100 || 100 = 50
#   D_Stub     la misma T de 50 ohm, pero con la rama abierta (sin puerto)
#              y de 8 mm de largo: un stub en circuito abierto
# mas las lineas de referencia de 50 y 100 ohm para corregir los puertos,
# y el gemelo sin perdidas de cada estructura. Los planos de referencia
# quedan en los bordes del cuadro de union (de-embedding de L1).
#
# Al terminar exporta los CSV y, para B_T (excitada desde P1) y C_Divisor
# (excitada desde la rama, P3), los campos a 5 GHz junto a la union.
# Todo queda en P2_D5_T_CSV.zip. Si un diseno excede el limite de malla,
# se vuelve a resolver solo. Si AEDT se cierra a la mitad, correr
# P2_D5_Reanudar.py (el mismo script con MODO = "reanudar").
#
# Uso: Automation -> Run Script.  Compatible con IronPython 2.7 y CPython 3.
# =====================================================================
import math
import os

try:
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
except Exception:
    pass

RESOLVER = True
EXPORTAR_CSV = True
EXPORTAR_CAMPOS = True
NOMBRE_PROYECTO = "P2_D5_T"

H_MM = 0.508
W1_MM = 1.14      # 50 ohm
W2_MM = 0.29      # 100 ohm (la misma linea de la discontinuidad 2)
L1_MM = 6.0       # largo de cada brazo hasta el borde del cuadro de union
LS_MM = 8.0       # largo del stub abierto
MG_MM = 7.0
HB_FAC = 14
SUSTRATOS = {"RO4003C": (3.55, 0.0027)}
ER = "3.55"
TAND = "0.0027"

F_SOL = "20GHz"
F_INI, F_FIN, F_PASO = "0.1GHz", "20GHz", "0.05GHz"
MAX_PASES = 15
MIN_PASES = 3
DELTA_S = 0.005

SOLUCION = "Setup1 : Sweep1"
F_CAMPOS = "5GHz"
BARRIDO_CAMPOS = "Campos5GHz"
DZ_CAMPOS = 0.02
LIMITES = {}
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


def puerto(oDesign, nombre, objeto, ini, fin):
    """Wave port de 1 modo SIN renormalizar (referido a la impedancia de su
    propia linea) y con de-embedding de L1 hasta el plano de referencia."""
    oB = oDesign.GetModule("BoundarySetup")

    def args(deemb, linea):
        modo = ["NAME:Mode1", "ModeNum:=", 1]
        if linea:
            modo += ["UseIntLine:=", True,
                     ["NAME:IntLine", "Start:=", ini, "End:=", fin]]
        else:
            modo += ["UseIntLine:=", False]
        modo += ["AlignmentGroup:=", 0, "CharImp:=", "Zpi"]
        a = ["NAME:" + nombre, "Objects:=", [objeto], "NumModes:=", 1,
             "UseLineModeAlignment:=", False]
        if deemb:
            a += ["DoDeembed:=", True, "DeembedDist:=", deemb]
        else:
            a += ["DoDeembed:=", False]
        a += ["RenormalizeAllTerminals:=", False, ["NAME:Modes", modo],
              "ShowReporterFilter:=", False, "ReporterFilter:=", [True],
              "UseAnalyticAlignment:=", False]
        return a

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
    if i == 4:
        aviso("Puerto %s quedo con la configuracion por defecto; revisa que "
              "no este renormalizado a 50 ohm" % nombre)


# ------------------------- Analisis y graficas -----------------------
def args_setup(max_pases, min_conv, completo=True):
    if not completo:
        return ["NAME:Setup1", "Frequency:=", F_SOL, "MaxDeltaS:=", DELTA_S,
                "MaximumPasses:=", max_pases, "MinimumPasses:=", MIN_PASES,
                "MinimumConvergedPasses:=", min_conv, "PercentRefinement:=", 30,
                "IsEnabled:=", True]
    return ["NAME:Setup1", "SolveType:=", "Single", "Frequency:=", F_SOL,
            "MaxDeltaS:=", DELTA_S, "UseMatrixConv:=", False,
            "MaximumPasses:=", max_pases, "MinimumPasses:=", MIN_PASES,
            "MinimumConvergedPasses:=", min_conv, "PercentRefinement:=", 30,
            "IsEnabled:=", True, "BasisOrder:=", 1,
            "DoLambdaRefine:=", True, "DoMaterialLambda:=", True,
            "SetLambdaTarget:=", False, "Target:=", 0.3333,
            "UseMaxTetIncrease:=", False, "PortAccuracy:=", 2,
            "UseABCOnPort:=", False, "SetPortMinMaxTri:=", False,
            "UseDomains:=", False, "UseIterativeSolver:=", False,
            "SaveRadFieldsOnly:=", False, "SaveAnyFields:=", True]


def limites(nombre):
    """(pases maximos, pases convergidos) de cada diseno."""
    return LIMITES.get(nombre, (MAX_PASES, 2))


def analisis(oDesign, nombre, campos=False):
    oA = oDesign.GetModule("AnalysisSetup")
    mp, mc = limites(nombre)
    intentar("Setup1", [
        lambda: oA.InsertSetup("HfssDriven", args_setup(mp, mc)),
        lambda: oA.InsertSetup("HfssDriven", args_setup(mp, mc, False))])
    intentar("barrido de frecuencia", [
        lambda: oA.InsertFrequencySweep("Setup1", [
            "NAME:Sweep1", "IsEnabled:=", True, "RangeType:=", "LinearStep",
            "RangeStart:=", F_INI, "RangeEnd:=", F_FIN, "RangeStep:=", F_PASO,
            "Type:=", "Interpolating", "SaveFields:=", False,
            "SaveRadFields:=", False, "InterpTolerance:=", 0.5,
            "InterpMaxSolns:=", 250, "InterpMinSolns:=", 0,
            "InterpMinSubranges:=", 1, "InterpUseS:=", True,
            "InterpUsePortImped:=", True, "InterpUsePropConst:=", True,
            "UseDerivativeConvergence:=", False, "InterpDerivTolerance:=", 0.2,
            "UseFullBasis:=", True, "EnforcePassivity:=", True,
            "PassivityErrorTolerance:=", 0.0001]),
        lambda: oA.InsertFrequencySweep("Setup1", [
            "NAME:Sweep1", "IsEnabled:=", True, "RangeType:=", "LinearStep",
            "RangeStart:=", F_INI, "RangeEnd:=", F_FIN, "RangeStep:=", F_PASO,
            "Type:=", "Interpolating"])])
    if campos:
        # un solo punto con campos guardados, para exportar E y H despues
        intentar("punto de frecuencia con campos", [
            lambda: oA.InsertFrequencySweep("Setup1", [
                "NAME:" + BARRIDO_CAMPOS, "IsEnabled:=", True,
                "RangeType:=", "SinglePoints",
                "RangeStart:=", F_CAMPOS, "RangeEnd:=", F_CAMPOS,
                "SaveSingleField:=", True, "Type:=", "Discrete",
                "SaveFields:=", True, "SaveRadFields:=", False,
                "SMatrixOnlySolveMode:=", "Auto"]),
            lambda: oA.InsertFrequencySweep("Setup1", [
                "NAME:" + BARRIDO_CAMPOS, "IsEnabled:=", True,
                "RangeType:=", "LinearCount",
                "RangeStart:=", F_CAMPOS, "RangeEnd:=", F_CAMPOS, "RangeCount:=", 1,
                "Type:=", "Discrete", "SaveFields:=", True,
                "SaveRadFields:=", False])])


# ------------------------- Graficas de N puertos ---------------------
PUERTOS = {}      # numero de puertos de cada diseno


def variables_salida(oDesign, n):
    oV = oDesign.GetModule("OutputVariable")
    hechas = []
    defs = []
    for i in range(1, n + 1):
        defs.append(("VSWR_P%d" % i, "(1+mag(S(%d,%d)))/(1-mag(S(%d,%d)))" % (i, i, i, i)))
    for i in range(1, n + 1):
        # potencia que entra por el puerto i y no sale por ningun puerto
        suma = "-".join("mag(S(%d,%d))^2" % (j, i) for j in range(1, n + 1))
        defs.append(("P_perdida%d" % i, "1-" + suma))
    for nombre, expr in defs:
        ok = intentar("variable de salida " + nombre, [
            lambda: oV.CreateOutputVariable(nombre, expr, SOLUCION,
                                            "Modal Solution Data", []),
            lambda: oV.CreateOutputVariable(nombre, expr, SOLUCION,
                                            "Modal Solution Data",
                                            ["Domain:=", "Sweep"])], silencioso=True)
        if ok >= 0:
            hechas.append(nombre)
    return hechas


def graficas(oDesign, nombres_var, n):
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

    P = range(1, n + 1)
    reporte("01_S_dB", "Rectangular Plot",
            [["dB(S(%d,1))" % i for i in P] + ["dB(S(%d,%d))" % (i, i) for i in P if i > 1]])
    reporte("02_Gamma_mag", "Rectangular Plot", [["mag(S(%d,%d))" % (i, i) for i in P]])
    reporte("03_VSWR", "Rectangular Plot", [["VSWR_P%d" % i for i in P], ["VSWR(%d)" % i for i in P]])
    reporte("04_Smith", "Smith Chart", [["S(%d,%d)" % (i, i) for i in P], ["S(1,1)"]])
    reporte("05_Fase_deg", "Rectangular Plot",
            [["ang_deg(S(%d,1))" % i for i in P] + ["ang_deg(S(%d,%d))" % (i, i) for i in P if i > 1]])
    reporte("06_Zo_puertos", "Rectangular Plot",
            [sum([["re(Zo(%d))" % i, "im(Zo(%d))" % i] for i in P], []),
             ["mag(Zo(%d))" % i for i in P]])
    reporte("07_Balance_potencia", "Rectangular Plot",
            [["P_perdida%d" % i for i in P],
             ["1-" + "-".join("mag(S(%d,%d))^2" % (j, i) for j in P) for i in P]], silencioso=True)
    # todos los S(i,j) en forma compleja; el orden lo da el encabezado del CSV
    reporte("08_S_complejos", "Rectangular Plot",
            [sum([["re(S(%d,%d))" % (i, j), "im(S(%d,%d))" % (i, j)] for j in P for i in P], [])])
    reporte("09_Gamma_puertos", "Rectangular Plot",
            [sum([["re(Gamma(%d))" % i, "im(Gamma(%d))" % i] for i in P], []),
             sum([["re(Gamma(%d:1))" % i, "im(Gamma(%d:1))" % i] for i in P], [])],
            silencioso=True)


VARIABLES = ["h", "Wb", "Ws", "L1", "Ls", "Mg", "Hb", "Hp", "Pw"]


def preparar_reportes(oDesign, nombre):
    """Crea las graficas solo cuando ya hay solucion (y solo si faltan).
    Asi la interfaz no redibuja decenas de graficas mientras resuelve."""
    n = PUERTOS.get(nombre, 2)
    oR = oDesign.GetModule("ReportSetup")
    try:
        existentes = [str(r) for r in oR.GetAllReportNames()]
    except Exception:
        existentes = []
    if "08_S_complejos" not in existentes:
        variables_salida(oDesign, n)
        graficas(oDesign, VARIABLES, n)


def cerrar_ventanas():
    intentar("cerrar ventanas", [lambda: oDesktop.CloseAllWindows()], silencioso=True)


# ------------------------- Construccion de disenos -------------------
#  tipo "linea": linea recta de ancho wb (referencia, 2 puertos)
#  tipo "T":     linea principal de ancho wb y rama de ancho ws y largo L1, 3 puertos
#  tipo "stub":  la misma T con la rama abierta de largo Ls, 2 puertos
def construir(oProject, nombre, tipo, wb, ws, perdidas=True):
    msg("Construyendo %s ..." % nombre)
    oDesign = nuevo_diseno(oProject, nombre)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    intentar("unidades mm", [lambda: oEditor.SetModelUnits(
        ["NAME:Units Parameter", "Units:=", "mm", "Rescale:=", False])],
        silencioso=True)

    variable(oDesign, "h", mm(H_MM))
    variable(oDesign, "Wb", mm(wb))
    variable(oDesign, "Ws", mm(ws))
    variable(oDesign, "L1", mm(L1_MM))
    variable(oDesign, "Ls", mm(LS_MM))
    variable(oDesign, "Mg", mm(MG_MM))
    variable(oDesign, "Hb", "%g*h" % HB_FAC)
    variable(oDesign, "Hp", "8*h")
    variable(oDesign, "Pw", mm(5 * W1_MM))
    suf = "" if perdidas else "_SinPerdidas"

    if tipo == "linea":
        XMAX, xmax = "2*L1", 2 * L1_MM
        YMAX = "%s/2+Mg" % mm(W1_MM)
        rama = None
    else:
        XMAX, xmax = "2*L1+Ws", 2 * L1_MM + ws
        largo = "L1" if tipo == "T" else "Ls"
        rama = largo
        YMAX = "Wb/2+L1" if tipo == "T" else "Wb/2+Ls+Mg"
    YMIN = "-%s/2-Mg" % mm(W1_MM)
    ANCHO_Y = "(%s)-(%s)" % (YMAX, YMIN)
    XC = "L1+Ws/2"                                   # eje de la rama

    caja(oEditor, "Sustrato", ("0mm", YMIN, "0mm"), (XMAX, ANCHO_Y, "h"), "RO4003C" + suf, "(0 128 0)", 0.6)
    caja(oEditor, "Aire", ("0mm", YMIN, "h"), (XMAX, ANCHO_Y, "Hb-h"), "vacuum", "(128 255 255)", 0.9)

    # Traza: un solo poligono (linea recta o T)
    if rama is None:
        pts = [("0mm", "-Wb/2", "h"), (XMAX, "-Wb/2", "h"), (XMAX, "Wb/2", "h"), ("0mm", "Wb/2", "h")]
    else:
        tope = "Wb/2+%s" % rama
        pts = [("0mm", "-Wb/2", "h"), (XMAX, "-Wb/2", "h"), (XMAX, "Wb/2", "h"),
               ("L1+Ws", "Wb/2", "h"), ("L1+Ws", tope, "h"), ("L1", tope, "h"),
               ("L1", "Wb/2", "h"), ("0mm", "Wb/2", "h")]
    lamina(oEditor, "Traza", pts, "(255 128 64)", 0)
    rect_plano(oEditor, "Tierra", "Z", "0mm", ("0mm", XMAX), (YMIN, YMAX), "(255 200 120)", 0.3)

    # Puertos y laminas de radiacion
    G = "(200 200 200)"
    ZB, ZP, ZS = ("0mm", "Hb"), ("0mm", "Hp"), ("Hp", "Hb")
    rect_plano(oEditor, "Rad_Arriba", "Z", "Hb", ("0mm", XMAX), (YMIN, YMAX), G, 0.9)
    rect_plano(oEditor, "Rad_Ymin", "Y", YMIN, ("0mm", XMAX), ZB, G, 0.9)
    rad = ["Rad_Arriba", "Rad_Ymin"]
    for k, x in [("1", "0mm"), ("2", XMAX)]:
        rect_plano(oEditor, "P" + k, "X", x, ("-Pw/2", "Pw/2"), ZP)
        rect_plano(oEditor, "Rad_X%sa" % k, "X", x, ("Pw/2", YMAX), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_X%sb" % k, "X", x, (YMIN, "-Pw/2"), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_X%sc" % k, "X", x, ("-Pw/2", "Pw/2"), ZS, G, 0.9)
        rad += ["Rad_X%sa" % k, "Rad_X%sb" % k, "Rad_X%sc" % k]
    if tipo == "T":
        rect_plano(oEditor, "P3", "Y", YMAX, ("%s-Pw/2" % XC, "%s+Pw/2" % XC), ZP)
        rect_plano(oEditor, "Rad_Y3a", "Y", YMAX, ("0mm", "%s-Pw/2" % XC), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_Y3b", "Y", YMAX, ("%s+Pw/2" % XC, XMAX), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_Y3c", "Y", YMAX, ("%s-Pw/2" % XC, "%s+Pw/2" % XC), ZS, G, 0.9)
        rad += ["Rad_Y3a", "Rad_Y3b", "Rad_Y3c"]
    else:
        rect_plano(oEditor, "Rad_Ymax", "Y", YMAX, ("0mm", XMAX), ZB, G, 0.9)
        rad += ["Rad_Ymax"]

    # Fronteras
    if perdidas:
        cond_finita(oDesign, "Cu_Traza", ["Traza"])
        cond_finita(oDesign, "Cu_Tierra", ["Tierra"])
    else:
        perfecto(oDesign, "PEC_Traza", ["Traza"])
        perfecto(oDesign, "PEC_Tierra", ["Tierra"])
    radiacion(oDesign, rad)

    puerto(oDesign, "1", "P1", ["0mm", "0mm", "0mm"], ["0mm", "0mm", mm(H_MM)])
    puerto(oDesign, "2", "P2", [mm(xmax), "0mm", "0mm"], [mm(xmax), "0mm", mm(H_MM)])
    n = 2
    if tipo == "T":
        xc = L1_MM + ws / 2
        yp = wb / 2 + L1_MM
        puerto(oDesign, "3", "P3", [mm(xc), mm(yp), "0mm"], [mm(xc), mm(yp), mm(H_MM)])
        n = 3
    PUERTOS[nombre] = n

    analisis(oDesign, nombre, campos=(nombre in CAMPOS))
    try:
        msg("%s: validacion = %s (1 = correcto)" % (nombre, oDesign.ValidateDesign()))
    except Exception:
        pass
    try:
        oEditor.FitAll()
    except Exception:
        pass
    return oDesign


# ------------------- Campos junto a la union (5 GHz) -----------------
#   densidad de carga:     rho_s = D_z(arriba) - D_z(abajo)
#   densidad de corriente: J_s   = z x (H(arriba) - H(abajo))
# Cada campo se exporta en fase 0 y 90 grados para reconstruir el fasor.
def fuentes(oDesign, activo, n):
    """Excita solo el puerto 'activo' (1 W) para graficar los campos."""
    oS = oDesign.GetModule("Solutions")
    lista = [["Name:=", "%d:1" % k, "Magnitude:=", "1W" if k == activo else "0W", "Phase:=", "0deg"]
             for k in range(1, n + 1)]
    nombres = ["NAME:Names"] + [str(k) for k in range(1, n + 1)]
    return intentar("excitar el puerto %d" % activo, [
        lambda: oS.EditSources([["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False]] + lista),
        lambda: oS.EditSources(lista),
        lambda: oS.EditSources("ScatteredFields", nombres, ["NAME:Modes"] + [1] * n,
                               ["NAME:Magnitudes"] + [1 if k == activo else 0 for k in range(1, n + 1)],
                               ["NAME:Phases"] + ["0deg"] * n, ["NAME:Terminated"], ["NAME:Impedances"])],
        silencioso=True)


def exportar_campos(oDesign, nombre, activo, salida):
    n = PUERTOS.get(nombre, 3)
    k = fuentes(oDesign, activo, n)
    fuente = ("P%d" % activo) if k >= 0 else "por defecto (P1)"
    oF = oDesign.GetModule("FieldsReporter")
    wb, ws = DIM[nombre]
    var = ["h:=", mm(H_MM), "L1:=", mm(L1_MM), "Mg:=", mm(MG_MM)]
    sol = "Setup1 : " + BARRIDO_CAMPOS
    opciones = ["NAME:ExportOption", "IncludePtInOutput:=", True, "RefCSName:=", "Global",
                "PtInSI:=", True, "FieldInRefCS:=", True]
    x0, x1 = L1_MM - 1.5, L1_MM + ws + 1.5
    y0, y1 = -1.0, wb / 2 + 1.6
    tareas = []
    for campo in ["E", "H"]:
        for etiqueta_z, z in [("abajo", H_MM - DZ_CAMPOS), ("arriba", H_MM + DZ_CAMPOS)]:
            tareas.append(("%s_%s" % (campo, etiqueta_z), campo,
                           [mm(x0), mm(y0), mm(z)], [mm(x1), mm(y1), mm(z)], [mm(0.02)] * 3))
    for etiq, campo, ini, fin, pasos in tareas:
        for fase in [0, 90]:
            archivo = os.path.join(salida, "%s__%s_ph%d.fld" % (nombre, etiq, fase))
            intr = ["Freq:=", F_CAMPOS, "Phase:=", "%ddeg" % fase]

            def ex(variacion, conopciones=True, campo=campo, fase=fase,
                   archivo=archivo, ini=ini, fin=fin, pasos=pasos):
                oF.CalcStack("clear")
                oF.EnterQty(campo)
                oF.EnterScalar(fase)
                oF.CalcOp("AtPhase")
                extra = opciones if conopciones else True
                oF.ExportOnGrid(archivo, ini, fin, pasos, sol, variacion, extra,
                                "Cartesian", ["0mm", "0mm", "0mm"], False)

            intentar("campo %s %s fase %d" % (nombre, etiq, fase), [
                lambda: ex(var + intr),
                lambda: ex(intr),
                lambda: ex(var + intr, False),
                lambda: ex(intr, False)])
    try:
        open(os.path.join(salida, "info_%s.txt" % nombre), "w").write(
            "freq=%s fuente=%s dz=%g x=[%g,%g] y=[%g,%g] paso=0.02 h=%g Wb=%g Ws=%g L1=%g\n" % (
                F_CAMPOS, fuente, DZ_CAMPOS, x0, x1, y0, y1, H_MM, wb, ws, L1_MM))
    except Exception:
        pass
    fuentes(oDesign, 1, n)          # deja la excitacion por defecto


# ---------------------------- Materiales -----------------------------
def material(oProject, nombre, er, tand):
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
         "permittivity:=", "%g" % er,
         "dielectric_loss_tangent:=", "%g" % tand])])


def crear_materiales(oProject):
    for nombre, (er, tand) in SUSTRATOS.items():
        material(oProject, nombre, er, tand)
        material(oProject, nombre + "_SinPerdidas", er, 0)



def exportar_convergencia(oDesign, nombre, carpeta):
    ruta = os.path.join(carpeta, "%s__convergencia.txt" % nombre)
    intentar("convergencia de " + nombre, [
        lambda: oDesign.ExportConvergence("Setup1", "", ruta),
        lambda: oDesign.ExportConvergence("Setup1", "", ruta, True)], silencioso=True)
    return ruta


def ultimo_pase(ruta):
    """Ultimo pase adaptativo que aparece en el archivo de convergencia."""
    ultimo = 0
    try:
        for linea in open(ruta):
            partes = [p.strip() for p in linea.split("|")]
            if len(partes) >= 3 and partes[0].isdigit() and partes[1].isdigit():
                ultimo = int(partes[0])
    except Exception:
        pass
    return ultimo


def tiene_solucion(oDesign, carpeta, nombre):
    """Prueba exportar los parametros S; si no hay datos, no se crea el archivo."""
    prueba = os.path.join(carpeta, "%s__prueba.csv" % nombre)
    try:
        if os.path.exists(prueba):
            os.remove(prueba)
    except Exception:
        pass
    oR = oDesign.GetModule("ReportSetup")
    intentar("prueba de " + nombre, [lambda: oR.ExportToFile("08_S_complejos", prueba)], silencioso=True)
    ok = os.path.exists(prueba) and os.path.getsize(prueba) > 0
    try:
        if os.path.exists(prueba):
            os.remove(prueba)
    except Exception:
        pass
    return ok


def resolver(oProject, nombre, carpeta):
    """Resuelve un diseno. Si se queda sin solucion (por ejemplo, porque un
    pase excede el limite de malla de la version estudiantil), lo resuelve
    otra vez deteniendose en el ultimo pase que si se completo."""
    msg("Resolviendo %s (puede tardar varios minutos) ..." % nombre)
    cerrar_ventanas()
    oDesign = oProject.SetActiveDesign(nombre)
    intentar("resolver " + nombre, [lambda: oDesign.AnalyzeAll()], silencioso=True)
    preparar_reportes(oDesign, nombre)
    if tiene_solucion(oDesign, carpeta, nombre):
        return True
    p = ultimo_pase(exportar_convergencia(oDesign, nombre, carpeta))
    if p < MIN_PASES:
        aviso("%s no tiene solucion y no se pudo recuperar" % nombre)
        return False
    msg("%s: sin solucion; se resuelve otra vez hasta el pase %d" % (nombre, p), 1)
    oA = oDesign.GetModule("AnalysisSetup")
    intentar("ajustar pases de " + nombre, [
        lambda: oA.EditSetup("Setup1", args_setup(p, 1)),
        lambda: oA.EditSetup("Setup1", args_setup(p, 1, False))])
    intentar("resolver otra vez " + nombre, [lambda: oDesign.AnalyzeAll()])
    ok = tiene_solucion(oDesign, carpeta, nombre)
    if not ok:
        aviso("%s sigue sin solucion" % nombre)
    cerrar_ventanas()
    return ok


def exportar_csv(oProject, nombre, carpeta):
    oDesign = oProject.SetActiveDesign(nombre)
    preparar_reportes(oDesign, nombre)
    oR = oDesign.GetModule("ReportSetup")
    try:
        reportes = [str(r) for r in oR.GetAllReportNames()]
    except Exception:
        reportes = ["01_S_dB", "02_Gamma_mag", "03_VSWR", "04_Smith",
                    "05_Fase_deg", "06_Zo_puertos", "07_Balance_potencia",
                    "08_S_complejos", "09_Gamma_puertos"]
    for r in reportes:
        archivo = os.path.join(carpeta, "%s__%s.csv" % (nombre, r))
        intentar("exportar %s/%s" % (nombre, r),
                 [lambda: oR.ExportToFile(r, archivo)], silencioso=True)
    exportar_convergencia(oDesign, nombre, carpeta)



def comprimir(carpeta, destino, disenos=None):
    """Comprime la carpeta de resultados en un .zip para enviarla. Con
    'disenos' solo incluye los archivos de esos disenos."""
    try:
        import zipfile
    except Exception:
        return None
    base = os.path.dirname(carpeta)
    for modo in ["ZIP_DEFLATED", "ZIP_STORED"]:
        try:
            z = zipfile.ZipFile(destino, "w", getattr(zipfile, modo))
            for raiz, _dirs, archivos in os.walk(carpeta):
                for a in archivos:
                    if disenos and not [d for d in disenos if a.startswith(d + "__")]:
                        continue
                    ruta = os.path.join(raiz, a)
                    z.write(ruta, os.path.relpath(ruta, base))
            z.close()
            return destino
        except Exception:
            continue
    return None


def carpeta_proyectos():
    try:
        base = str(oDesktop.GetProjectDirectory())
    except Exception:
        base = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    carpeta = os.path.join(base, "Proyecto2_Microcinta")
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    return carpeta


def abrir_existente(carpeta):
    """Abre la version mas reciente del proyecto (P2_D5_T, _v2, _v3...)."""
    candidatos = [NOMBRE_PROYECTO] + ["%s_v%d" % (NOMBRE_PROYECTO, n) for n in range(2, 30)]
    existentes = [c for c in candidatos if os.path.exists(os.path.join(carpeta, c + ".aedt"))]
    if not existentes:
        msg("No encontre %s en %s." % (NOMBRE_PROYECTO, carpeta), 2)
        return None, os.path.join(carpeta, NOMBRE_PROYECTO + ".aedt")
    nombre = existentes[-1]
    ruta = os.path.join(carpeta, nombre + ".aedt")
    try:
        abiertos = [str(p) for p in oDesktop.GetProjectList()]
    except Exception:
        abiertos = []
    msg("Reanudando el proyecto " + nombre)
    if nombre in abiertos:
        return oDesktop.SetActiveProject(nombre), ruta
    candado = ruta + ".lock"
    if os.path.exists(candado):      # quedo de la corrida que se cerro
        try:
            os.remove(candado)
        except Exception:
            pass
    auto = ruta + ".auto"             # autoguardado: AEDT preguntaria si recuperarlo
    if os.path.exists(auto):
        try:
            if os.path.exists(auto + ".bak"):
                os.remove(auto + ".bak")
            os.rename(auto, auto + ".bak")
        except Exception:
            pass
    return oDesktop.OpenProject(ruta), ruta


# -------------------------------- Main -------------------------------
W1, W2 = W1_MM, W2_MM
#  nombre          tipo     ancho principal  ancho rama   gemelo sin perdidas
DISENOS = []
DIM = {}
for _n, _tipo, _wb, _ws in [
        ("A1_Ref50",   "linea", W1, W1),
        ("A2_Ref100",  "linea", W2, W2),
        ("B_T",        "T",     W1, W1),
        ("C_Divisor",  "T",     W2, W1),
        ("D_Stub",     "stub",  W1, W1)]:
    for _x, _p in [("", True), ("_SinPerd", False)]:
        DISENOS.append((_n + _x, _tipo, _wb, _ws, _p))
        DIM[_n + _x] = (_wb, _ws)
        PUERTOS[_n + _x] = 3 if _tipo == "T" else 2
# campos a 5 GHz: diseno -> puerto excitado
CAMPOS = {"B_T": 1, "C_Divisor": 3}

# MODO = "completo": crea el proyecto con todos los disenos y los resuelve.
# MODO = "reanudar": abre la version mas reciente de P2_D5_T y solo resuelve
#   y exporta los disenos que todavia no tengan CSV (si la corrida se interrumpio).
MODO = "completo"


def main():
    try:
        oDesktop.RestoreWindow()
    except Exception:
        pass
    carpeta = carpeta_proyectos()

    if MODO == "reanudar":
        oProject, ruta = abrir_existente(carpeta)
        if oProject is None:
            return
    else:
        oProject = oDesktop.NewProject()
        crear_materiales(oProject)
        for nombre, tipo, wb, ws, perdidas in DISENOS:
            construir(oProject, nombre, tipo, wb, ws, perdidas)
        ruta = os.path.join(carpeta, NOMBRE_PROYECTO + ".aedt")
        n = 2
        while os.path.exists(ruta):
            ruta = os.path.join(carpeta, "%s_v%d.aedt" % (NOMBRE_PROYECTO, n))
            n += 1
        intentar("guardar proyecto", [lambda: oProject.SaveAs(ruta, True)])
        msg("Proyecto guardado en: " + ruta)
    if not RESOLVER:
        return

    csv_dir = os.path.join(os.path.dirname(ruta),
                           os.path.splitext(os.path.basename(ruta))[0] + "_CSV")
    if not os.path.isdir(csv_dir):
        os.makedirs(csv_dir)
    for nombre, tipo, wb, ws, perdidas in DISENOS:
        if MODO == "reanudar" and os.path.exists(os.path.join(csv_dir, "%s__08_S_complejos.csv" % nombre)):
            continue
        if resolver(oProject, nombre, csv_dir) and EXPORTAR_CSV:
            exportar_csv(oProject, nombre, csv_dir)
        intentar("guardar resultados", [lambda: oProject.Save()], silencioso=True)
    msg("CSV exportados en: " + csv_dir)

    if EXPORTAR_CAMPOS:
        salida = os.path.join(csv_dir, "campos")
        if not os.path.isdir(salida):
            os.makedirs(salida)
        for nombre, activo in sorted(CAMPOS.items()):
            if MODO == "reanudar" and os.path.exists(os.path.join(salida, "%s__H_arriba_ph90.fld" % nombre)):
                continue
            msg("Exportando campos de %s (excitado desde P%d) ..." % (nombre, activo))
            exportar_campos(oProject.SetActiveDesign(nombre), nombre, activo, salida)
        msg("Campos exportados en: " + salida)

    z = comprimir(csv_dir, csv_dir + ".zip")
    if z:
        msg("Archivo para enviar: " + z)
    else:
        msg("No se pudo crear el .zip; comprime a mano la carpeta " + csv_dir, 1)


main()
if fallas:
    msg("Terminado con %d aviso(s). Revisa los mensajes [P2] anteriores." % len(fallas), 1)
else:
    msg("Terminado sin errores.")
