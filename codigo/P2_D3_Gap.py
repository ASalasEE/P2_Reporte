# -*- coding: utf-8 -*-
# =====================================================================
# Proyecto 2 - Discontinuidades en interconectores de microcinta
# Discontinuidad 3: gap (corte) en serie en la linea de 50 ohm
#
# La linea de 50 ohm (W = 1.14 mm) se interrumpe con una separacion s.
# Se simulan cinco separaciones, de 0.1 mm (acoplamiento fuerte) a 3 mm
# (practicamente dos extremos abiertos), con el mismo modelo que las
# discontinuidades anteriores (caja grande, malla fina, gemelos sin
# perdidas, puertos sin renormalizar y lineas de referencia para quitar
# el error de los puertos).
#
# Disenos:
#   A1_Ref50, A1_Ref50_SinPerd        linea recta de-embebida a longitud cero
#   B1..B5_Gap_<s> (+ _SinPerd)       gap de s = 0.1, 0.2, 0.5, 1.0 y 3.0 mm
#
# Al terminar exporta los CSV y, para s = 0.2 y 1.0 mm, los campos a 5 GHz:
# E y H justo debajo y encima de la traza (carga y corriente) y E en el
# plano vertical que pasa por el eje de la linea (lineas de campo del gap).
# Todo queda comprimido en P2_D3_Gap_CSV.zip.
#
# Si algun diseno excede el limite de malla de la version estudiantil, el
# script lo vuelve a resolver solo, deteniendose en el ultimo pase valido.
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
NOMBRE_PROYECTO = "P2_D3_Gap"

# Sustrato Rogers RO4003C: h = 0.508 mm, er = 3.55, tan d = 0.0027
H_MM = 0.508
W1_MM = 1.14      # 50 ohm  (W/h = 2.24)
L1_MM = 6.0       # tramo recto entre cada puerto y la discontinuidad
MG_MM = 7.0       # margen lateral desde el borde de la traza
HB_FAC = 14       # altura de la caja de aire = 14h
ER = "3.55"
TAND = "0.0027"
GAPS = [0.1, 0.2, 0.5, 1.0, 3.0]   # separaciones (mm)

F_SOL = "20GHz"
F_INI, F_FIN, F_PASO = "0.1GHz", "20GHz", "0.05GHz"
MAX_PASES = 15
MIN_PASES = 3
DELTA_S = 0.005

SOLUCION = "Setup1 : Sweep1"
F_CAMPOS = "5GHz"
BARRIDO_CAMPOS = "Campos5GHz"
DZ_CAMPOS = 0.02  # distancia de los planos horizontales a la traza (mm)
LIMITES = {}      # (pases maximos, pases convergidos) por diseno, si hace falta
fallas = []


def etiqueta(s):
    return ("%.1f" % s).replace(".", "p")


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
    propia linea) y con de-embedding de L1 hasta el plano del escalon."""
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


def variables_salida(oDesign):
    oV = oDesign.GetModule("OutputVariable")
    hechas = []
    for nombre, expr in [
            ("VSWR_P1", "(1+mag(S(1,1)))/(1-mag(S(1,1)))"),
            ("VSWR_P2", "(1+mag(S(2,2)))/(1-mag(S(2,2)))"),
            # potencia que ni se refleja ni se transmite: radiacion + perdidas
            ("P_perdida", "1-mag(S(1,1))^2-mag(S(2,1))^2"),
            ("P_perdida2", "1-mag(S(2,2))^2-mag(S(1,2))^2")]:
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

    reporte("01_S_dB", "Rectangular Plot",
            [["dB(S(1,1))", "dB(S(2,1))", "dB(S(2,2))"]])
    reporte("02_Gamma_mag", "Rectangular Plot", [["mag(S(1,1))", "mag(S(2,2))"]])
    v = [["VSWR_P1", "VSWR_P2"]] if "VSWR_P2" in salidas else []
    reporte("03_VSWR", "Rectangular Plot", v + [["VSWR(1)", "VSWR(2)"]])
    reporte("04_Smith", "Smith Chart", [["S(1,1)", "S(2,2)"], ["S(1,1)"]])
    reporte("05_Fase_deg", "Rectangular Plot",
            [["ang_deg(S(1,1))", "ang_deg(S(2,1))", "ang_deg(S(2,2))"]])
    reporte("06_Zo_puertos", "Rectangular Plot",
            [["re(Zo(1))", "im(Zo(1))", "re(Zo(2))", "im(Zo(2))"],
             ["mag(Zo(1))", "mag(Zo(2))"]])
    p = [["P_perdida", "P_perdida2"]] if "P_perdida2" in salidas else []
    reporte("07_Balance_potencia", "Rectangular Plot",
            p + [["1-mag(S(1,1))^2-mag(S(2,1))^2", "1-mag(S(2,2))^2-mag(S(1,2))^2"]],
            silencioso=True)
    reporte("08_S_complejos", "Rectangular Plot",
            [["re(S(1,1))", "im(S(1,1))", "re(S(2,1))", "im(S(2,1))",
              "re(S(1,2))", "im(S(1,2))", "re(S(2,2))", "im(S(2,2))"]])
    reporte("09_Gamma_puertos", "Rectangular Plot",
            [["re(Gamma(1))", "im(Gamma(1))", "re(Gamma(2))", "im(Gamma(2))"],
             ["re(Gamma(1:1))", "im(Gamma(1:1))", "re(Gamma(2:1))", "im(Gamma(2:1))"]],
            silencioso=True)


# ------------------------- Construccion de disenos -------------------
def construir(oProject, nombre, tipo, perdidas=True, s=None):
    msg("Construyendo %s ..." % nombre)
    oDesign = nuevo_diseno(oProject, nombre)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    intentar("unidades mm", [lambda: oEditor.SetModelUnits(
        ["NAME:Units Parameter", "Units:=", "mm", "Rescale:=", False])],
        silencioso=True)

    nombres_var = ["h", "W1", "L1", "Mg", "Hb", "Hp", "Pw"]
    variable(oDesign, "h", mm(H_MM))
    variable(oDesign, "W1", mm(W1_MM))
    variable(oDesign, "L1", mm(L1_MM))
    variable(oDesign, "Mg", mm(MG_MM))
    variable(oDesign, "Hb", "%g*h" % HB_FAC)  # altura de la caja de aire
    variable(oDesign, "Hp", "8*h")            # altura de los puertos
    variable(oDesign, "Pw", "5*W1")           # ancho de los puertos
    if tipo == "gap":
        variable(oDesign, "s", mm(s))
        nombres_var.append("s")
        XMAX, xmax = "2*L1+s", 2 * L1_MM + s
    else:
        XMAX, xmax = "2*L1", 2 * L1_MM
    YMIN, YMAX = "-W1/2-Mg", "W1/2+Mg"
    ANCHO_Y = "(%s)-(%s)" % (YMAX, YMIN)
    mat = "RO4003C" if perdidas else "RO4003C_SinPerdidas"

    # Volumenes
    caja(oEditor, "Sustrato", ("0mm", YMIN, "0mm"), (XMAX, ANCHO_Y, "h"),
         mat, "(0 128 0)", 0.6)
    caja(oEditor, "Aire", ("0mm", YMIN, "h"), (XMAX, ANCHO_Y, "Hb-h"),
         "vacuum", "(128 255 255)", 0.9)

    # Traza superior: una pieza (referencia) o dos separadas por s (gap)
    if tipo == "gap":
        lamina(oEditor, "Traza1", [("0mm", "-W1/2", "h"), ("L1", "-W1/2", "h"),
                                   ("L1", "W1/2", "h"), ("0mm", "W1/2", "h")], "(255 128 64)", 0)
        lamina(oEditor, "Traza2", [("L1+s", "-W1/2", "h"), (XMAX, "-W1/2", "h"),
                                   (XMAX, "W1/2", "h"), ("L1+s", "W1/2", "h")], "(255 128 64)", 0)
        trazas = ["Traza1", "Traza2"]
    else:
        lamina(oEditor, "Traza", [("0mm", "-W1/2", "h"), (XMAX, "-W1/2", "h"),
                                  (XMAX, "W1/2", "h"), ("0mm", "W1/2", "h")], "(255 128 64)", 0)
        trazas = ["Traza"]
    rect_plano(oEditor, "Tierra", "Z", "0mm", ("0mm", XMAX), (YMIN, YMAX),
               "(255 200 120)", 0.3)

    # Puertos (altura Hp) y laminas de radiacion (resto de las caras)
    G = "(200 200 200)"
    ZB, ZP, ZS = ("0mm", "Hb"), ("0mm", "Hp"), ("Hp", "Hb")
    rect_plano(oEditor, "Rad_Arriba", "Z", "Hb", ("0mm", XMAX), (YMIN, YMAX), G, 0.9)
    rect_plano(oEditor, "Rad_Ymin", "Y", YMIN, ("0mm", XMAX), ZB, G, 0.9)
    rect_plano(oEditor, "Rad_Ymax", "Y", YMAX, ("0mm", XMAX), ZB, G, 0.9)
    rad = ["Rad_Arriba", "Rad_Ymin", "Rad_Ymax"]
    for k, x in [("1", "0mm"), ("2", XMAX)]:
        rect_plano(oEditor, "P" + k, "X", x, ("-Pw/2", "Pw/2"), ZP)
        rect_plano(oEditor, "Rad_X%sa" % k, "X", x, ("Pw/2", YMAX), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_X%sb" % k, "X", x, (YMIN, "-Pw/2"), ZB, G, 0.9)
        rect_plano(oEditor, "Rad_X%sc" % k, "X", x, ("-Pw/2", "Pw/2"), ZS, G, 0.9)
        rad += ["Rad_X%sa" % k, "Rad_X%sb" % k, "Rad_X%sc" % k]

    # Fronteras
    if perdidas:
        cond_finita(oDesign, "Cu_Traza", trazas)
        cond_finita(oDesign, "Cu_Tierra", ["Tierra"])
    else:
        perfecto(oDesign, "PEC_Traza", trazas)
        perfecto(oDesign, "PEC_Tierra", ["Tierra"])
    radiacion(oDesign, rad)

    # Puertos (linea de integracion de tierra a la traza)
    puerto(oDesign, "1", "P1", ["0mm", "0mm", "0mm"], ["0mm", "0mm", mm(H_MM)])
    puerto(oDesign, "2", "P2", [mm(xmax), "0mm", "0mm"], [mm(xmax), "0mm", mm(H_MM)])

    analisis(oDesign, nombre, campos=(nombre in CAMPOS))
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
    oDesign = oProject.SetActiveDesign(nombre)
    intentar("resolver " + nombre, [lambda: oDesign.AnalyzeAll()], silencioso=True)
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
    return ok


def exportar_csv(oProject, nombre, carpeta):
    oDesign = oProject.SetActiveDesign(nombre)
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


# ------------------- Campos junto a la traza (5 GHz) -----------------
#   densidad de carga:     rho_s = D_z(arriba) - D_z(abajo)
#   densidad de corriente: J_s   = z x (H(arriba) - H(abajo))
#   lineas de campo:       E en el plano vertical y = 0
# Cada campo se exporta en fase 0 y 90 grados para reconstruir el fasor.
def exportar_campos(oDesign, nombre, s, salida):
    oF = oDesign.GetModule("FieldsReporter")
    var = ["h:=", mm(H_MM), "W1:=", mm(W1_MM), "L1:=", mm(L1_MM), "Mg:=", mm(MG_MM), "s:=", mm(s)]
    sol = "Setup1 : " + BARRIDO_CAMPOS
    opciones = ["NAME:ExportOption", "IncludePtInOutput:=", True, "RefCSName:=", "Global",
                "PtInSI:=", True, "FieldInRefCS:=", True]
    x0, x1 = L1_MM - 1.5, L1_MM + s + 1.5
    tareas = []
    for campo in ["E", "H"]:
        for etiqueta_z, z in [("abajo", H_MM - DZ_CAMPOS), ("arriba", H_MM + DZ_CAMPOS)]:
            tareas.append(("%s_%s" % (campo, etiqueta_z), campo,
                           [mm(x0), mm(-1.0), mm(z)], [mm(x1), mm(1.0), mm(z)], [mm(0.02)] * 3))
    xv0, xv1 = L1_MM - 1.2, L1_MM + s + 1.2
    tareas.append(("E_vertical", "E", [mm(xv0), "0mm", "0mm"], [mm(xv1), "0mm", mm(1.3)], [mm(0.01)] * 3))
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
            "freq=%s dz=%g s=%g x=[%g,%g] y=[-1,1] paso=0.02 vertical x=[%g,%g] z=[0,1.3] paso=0.01 h=%g W1=%g L1=%g\n" % (
                F_CAMPOS, DZ_CAMPOS, s, x0, x1, xv0, xv1, H_MM, W1_MM, L1_MM))
    except Exception:
        pass


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
    try:
        abiertos = [str(p) for p in oDesktop.GetProjectList()]
    except Exception:
        abiertos = []
    if NOMBRE_PROYECTO in abiertos:
        return oDesktop.SetActiveProject(NOMBRE_PROYECTO), os.path.join(carpeta, NOMBRE_PROYECTO + ".aedt")
    ruta = os.path.join(carpeta, NOMBRE_PROYECTO + ".aedt")
    if not os.path.exists(ruta):
        msg("No encontre %s. Abre el proyecto %s y vuelve a correr el script." % (ruta, NOMBRE_PROYECTO), 2)
        return None, ruta
    return oDesktop.OpenProject(ruta), ruta


# -------------------------------- Main -------------------------------
DISENOS = [("A1_Ref50", "recta50", True, None), ("A1_Ref50_SinPerd", "recta50", False, None)]
for _i, _s in enumerate(GAPS):
    _n = "B%d_Gap_%s" % (_i + 1, etiqueta(_s))
    DISENOS += [(_n, "gap", True, _s), (_n + "_SinPerd", "gap", False, _s)]
CAMPOS = {"B2_Gap_0p2": 0.2, "B4_Gap_1p0": 1.0}

# MODO = "completo": crea el proyecto con todos los disenos y los resuelve.
# MODO = "reanudar": abre P2_D3_Gap y solo resuelve y exporta los disenos que
#   todavia no tengan CSV (por ejemplo, si la corrida se interrumpio).
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
        material_sustrato(oProject, "RO4003C", TAND)
        material_sustrato(oProject, "RO4003C_SinPerdidas", "0")
        for nombre, tipo, perdidas, s in DISENOS:
            construir(oProject, nombre, tipo, perdidas, s)
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
    for nombre, tipo, perdidas, s in DISENOS:
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
        for nombre, s in sorted(CAMPOS.items()):
            if MODO == "reanudar" and os.path.exists(os.path.join(salida, "%s__E_vertical_ph90.fld" % nombre)):
                continue
            msg("Exportando campos de %s ..." % nombre)
            exportar_campos(oProject.SetActiveDesign(nombre), nombre, s, salida)
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
