# -*- coding: utf-8 -*-
# =====================================================================
# Proyecto 2 - Discontinuidad 1: exportar los campos de HFSS en la esquina
#
# Abre el proyecto P2_D1_Curva90_v2, agrega a la curva sin chaflan y con
# chaflan un punto de frecuencia con campos guardados (5 GHz), lo resuelve
# (reutiliza la malla ya convergida, tarda poco) y exporta E y H en dos
# planos horizontales, justo debajo y justo encima de la traza:
#
#   densidad de carga:     rho_s = D_z(arriba) - D_z(abajo)
#   densidad de corriente: J_s   = z x (H(arriba) - H(abajo))
#
# Cada campo se exporta en fase 0 y 90 grados para reconstruir el fasor.
# Los archivos .fld quedan en Documentos\Ansoft\Proyecto2_Microcinta\P2_D1_Campos
#
# Uso: Automation -> Run Script.  Compatible con IronPython 2.7 y CPython 3.
# =====================================================================
import os

try:
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
except Exception:
    pass

PROYECTO = "P2_D1_Curva90_v2"
FREQ = "5GHz"
SWEEP = "Campos5GHz"
H_MM, W_MM, L1_MM = 0.508, 1.14, 6.0
DZ = 0.02                       # distancia de los planos a la traza (mm)
PASO = 0.03                     # separacion de la malla de exportacion (mm)
# ventana alrededor de la esquina (coordenadas del modelo, mm)
X0, X1 = L1_MM - 3.0, L1_MM + W_MM + 0.5
Y0, Y1 = -W_MM / 2 - 0.5, W_MM / 2 + 3.0
DISENOS = [("B_Curva90", ["h", "W", "L1", "Mg"]),
           ("C_Curva90_Chaflan", ["h", "W", "L1", "Mg", "Mt"])]
VALORES = {"h": "0.508mm", "W": "1.14mm", "L1": "6mm", "Mg": "7mm", "Mt": "0.55"}

fallas = []


def msg(texto, nivel=0):
    try:
        oDesktop.AddMessage("", "", nivel, "[P2] " + texto)
    except Exception:
        pass


def intentar(descripcion, variantes, silencioso=False):
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
        fallas.append(descripcion)
        msg("No se pudo: %s (%s)" % (descripcion, ultimo), 1)
    return -1


def mm(x):
    return "%gmm" % x


# ------------------------------ Proyecto -----------------------------
def abrir_proyecto():
    try:
        base = str(oDesktop.GetProjectDirectory())
    except Exception:
        base = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    carpeta = os.path.join(base, "Proyecto2_Microcinta")
    try:
        abiertos = [str(p) for p in oDesktop.GetProjectList()]
    except Exception:
        abiertos = []
    if PROYECTO in abiertos:
        return oDesktop.SetActiveProject(PROYECTO), carpeta
    ruta = os.path.join(carpeta, PROYECTO + ".aedt")
    if not os.path.exists(ruta):
        msg("No encontre %s. Abre el proyecto %s y vuelve a correr el script." % (ruta, PROYECTO), 2)
        return None, carpeta
    return oDesktop.OpenProject(ruta), carpeta


def barrido_campos(oDesign):
    oA = oDesign.GetModule("AnalysisSetup")
    try:
        if SWEEP in [str(s) for s in oA.GetSweeps("Setup1")]:
            return
    except Exception:
        pass
    intentar("punto de frecuencia con campos", [
        lambda: oA.InsertFrequencySweep("Setup1", [
            "NAME:" + SWEEP, "IsEnabled:=", True, "RangeType:=", "SinglePoints",
            "RangeStart:=", FREQ, "RangeEnd:=", FREQ, "SaveSingleField:=", True,
            "Type:=", "Discrete", "SaveFields:=", True, "SaveRadFields:=", False,
            "SMatrixOnlySolveMode:=", "Auto"]),
        lambda: oA.InsertFrequencySweep("Setup1", [
            "NAME:" + SWEEP, "IsEnabled:=", True, "RangeType:=", "LinearCount",
            "RangeStart:=", FREQ, "RangeEnd:=", FREQ, "RangeCount:=", 1,
            "Type:=", "Discrete", "SaveFields:=", True, "SaveRadFields:=", False])])


def exportar(oDesign, nombre, variables, campo, fase, z, etiqueta, salida):
    oF = oDesign.GetModule("FieldsReporter")
    archivo = os.path.join(salida, "%s__%s_%s_ph%d.fld" % (nombre, campo, etiqueta, fase))
    var = []
    for v in variables:
        var += [v + ":=", VALORES[v]]
    intr = ["Freq:=", FREQ, "Phase:=", "%ddeg" % fase]
    ini, fin, paso = [mm(X0), mm(Y0), mm(z)], [mm(X1), mm(Y1), mm(z)], [mm(PASO), mm(PASO), mm(PASO)]
    opciones = ["NAME:ExportOption", "IncludePtInOutput:=", True, "RefCSName:=", "Global",
                "PtInSI:=", True, "FieldInRefCS:=", True]
    sol = "Setup1 : " + SWEEP

    def pila():
        oF.CalcStack("clear")
        oF.EnterQty(campo)
        oF.EnterScalar(fase)
        oF.CalcOp("AtPhase")

    def ex(variacion, conopciones=True):
        pila()
        if conopciones:
            oF.ExportOnGrid(archivo, ini, fin, paso, sol, variacion, opciones, "Cartesian",
                            ["0mm", "0mm", "0mm"], False)
        else:
            oF.ExportOnGrid(archivo, ini, fin, paso, sol, variacion, True, "Cartesian",
                            ["0mm", "0mm", "0mm"], False)

    intentar("exportar %s %s %s fase %d" % (nombre, campo, etiqueta, fase), [
        lambda: ex(var + intr),
        lambda: ex(intr),
        lambda: ex(var + intr, False),
        lambda: ex(intr, False)])


def main():
    oProject, carpeta = abrir_proyecto()
    if oProject is None:
        return
    msg("Proyecto: %s" % PROYECTO)
    salida = os.path.join(carpeta, "P2_D1_Campos")
    if not os.path.isdir(salida):
        os.makedirs(salida)
    for nombre, variables in DISENOS:
        msg("Preparando %s ..." % nombre)
        oDesign = oProject.SetActiveDesign(nombre)
        barrido_campos(oDesign)
        msg("Resolviendo %s a %s (reutiliza la malla) ..." % (nombre, FREQ))
        intentar("resolver " + nombre, [lambda: oDesign.Analyze("Setup1", True),
                                        lambda: oDesign.Analyze("Setup1")])
        for campo in ["E", "H"]:
            for fase in [0, 90]:
                for etiqueta, z in [("abajo", H_MM - DZ), ("arriba", H_MM + DZ)]:
                    exportar(oDesign, nombre, variables, campo, fase, z, etiqueta, salida)
        msg("%s listo." % nombre)

    intentar("guardar proyecto", [lambda: oProject.Save()], silencioso=True)
    open(os.path.join(salida, "info.txt"), "w").write(
        "freq=%s dz=%g paso=%g x=[%g,%g] y=[%g,%g] h=%g W=%g L1=%g\n" % (FREQ, DZ, PASO, X0, X1, Y0, Y1, H_MM, W_MM, L1_MM))
    msg("Archivos en: " + salida)
    if fallas:
        msg("Terminado con %d aviso(s). Revisa los mensajes [P2] anteriores." % len(fallas), 1)
    else:
        msg("Terminado sin errores.")


main()
