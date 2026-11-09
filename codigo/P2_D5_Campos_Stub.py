# -*- coding: utf-8 -*-
# =====================================================================
# Proyecto 2 - Discontinuidades en interconectores de microcinta
# Discontinuidad 5: campos del stub abierto
#
# Abre el proyecto P2_D5_T ya resuelto (la version mas reciente), agrega
# al diseno D_Stub tres puntos de frecuencia con campos guardados:
#    5.5 GHz   el stub mide lambda/4: corte de la transmision
#   10.8 GHz   el stub mide lambda/2: la linea transmite como si no existiera
#   16.15 GHz  el stub mide 3 lambda/4: segundo corte
# los resuelve con la malla que ya tiene (no repite el refinamiento) y
# exporta, con la excitacion por P1:
#   - E y H en los planos z = h -/+ 0.02 mm sobre el stub y la union
#   - E en dos cortes verticales bajo la tira: a lo largo del eje del stub
#     y a lo largo del eje de la linea principal
# Todo queda en P2_D5_Stub_Campos.zip, en la carpeta Proyecto2_Microcinta.
#
# Uso: Automation -> Run Script.  Compatible con IronPython 2.7 y CPython 3.
# =====================================================================
import os

try:
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
except Exception:
    pass

NOMBRE_PROYECTO = "P2_D5_T"
DISENO = "D_Stub"
H_MM, W1_MM, L1_MM, LS_MM = 0.508, 1.14, 6.0, 8.0
FRECUENCIAS = ["5.5GHz", "10.8GHz", "16.15GHz"]
PASO = 0.04
DZ = 0.02
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


# ----------------------------- Campos del stub -----------------------
def etiqueta(freq):
    return freq.replace("GHz", "").replace(".", "p") + "GHz"


def barridos(oDesign):
    oA = oDesign.GetModule("AnalysisSetup")
    try:
        existentes = [str(s) for s in oA.GetSweeps("Setup1")]
    except Exception:
        existentes = []
    nombres = []
    for freq in FRECUENCIAS:
        nombre = "Stub_" + etiqueta(freq)
        nombres.append(nombre)
        if nombre in existentes:
            continue
        intentar("punto con campos a " + freq, [
            lambda: oA.InsertFrequencySweep("Setup1", [
                "NAME:" + nombre, "IsEnabled:=", True, "RangeType:=", "SinglePoints",
                "RangeStart:=", freq, "RangeEnd:=", freq, "SaveSingleField:=", True,
                "Type:=", "Discrete", "SaveFields:=", True, "SaveRadFields:=", False,
                "SMatrixOnlySolveMode:=", "Auto"]),
            lambda: oA.InsertFrequencySweep("Setup1", [
                "NAME:" + nombre, "IsEnabled:=", True, "RangeType:=", "LinearCount",
                "RangeStart:=", freq, "RangeEnd:=", freq, "RangeCount:=", 1,
                "Type:=", "Discrete", "SaveFields:=", True, "SaveRadFields:=", False])])
    return nombres


def resolver_barridos(oDesign, nombres):
    for nombre in nombres:
        msg("Resolviendo %s (usa la malla ya refinada) ..." % nombre)
        k = intentar("resolver " + nombre, [
            lambda: oDesign.Analyze("Setup1 : " + nombre),
            lambda: oDesign.Analyze("Setup1:" + nombre)], silencioso=True)
        if k < 0:
            msg("Se resuelve el diseno completo (puede tardar unos minutos) ...")
            intentar("resolver " + DISENO, [lambda: oDesign.AnalyzeAll()])
            break


def excitar_p1(oDesign):
    oS = oDesign.GetModule("Solutions")
    lista = [["Name:=", "1:1", "Magnitude:=", "1W", "Phase:=", "0deg"],
             ["Name:=", "2:1", "Magnitude:=", "0W", "Phase:=", "0deg"]]
    return intentar("excitar P1", [
        lambda: oS.EditSources([["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False]] + lista),
        lambda: oS.EditSources(lista)], silencioso=True)


def exportar(oDesign, nombre, freq, salida):
    oF = oDesign.GetModule("FieldsReporter")
    sol = "Setup1 : " + nombre
    var = ["h:=", mm(H_MM), "L1:=", mm(L1_MM), "Mg:=", "7mm"]
    opciones = ["NAME:ExportOption", "IncludePtInOutput:=", True, "RefCSName:=", "Global",
                "PtInSI:=", True, "FieldInRefCS:=", True]
    x0, x1 = L1_MM - 2.0, L1_MM + W1_MM + 2.0
    y0, y1 = -0.8, W1_MM / 2 + LS_MM + 0.6
    xc = L1_MM + W1_MM / 2
    tag = etiqueta(freq)
    tareas = []
    for campo in ["E", "H"]:
        for lado, z in [("abajo", H_MM - DZ), ("arriba", H_MM + DZ)]:
            tareas.append(("%s_%s" % (campo, lado), campo, [mm(x0), mm(y0), mm(z)], [mm(x1), mm(y1), mm(z)],
                           [mm(PASO)] * 3))
    # cortes verticales bajo la tira (de la tierra a la tira), para el voltaje
    tareas.append(("E_vert_stub", "E", [mm(xc), mm(-0.4), "0mm"], [mm(xc), mm(y1), mm(H_MM - 0.01)],
                   [mm(0.02)] * 3))
    tareas.append(("E_vert_linea", "E", [mm(0.5), "0mm", "0mm"], [mm(2 * L1_MM + W1_MM - 0.5), "0mm", mm(H_MM - 0.01)],
                   [mm(0.02)] * 3))
    for etiq, campo, ini, fin, pasos in tareas:
        for fase in [0, 90]:
            archivo = os.path.join(salida, "Stub_%s__%s_ph%d.fld" % (tag, etiq, fase))
            intr = ["Freq:=", freq, "Phase:=", "%ddeg" % fase]

            def ex(variacion, conopciones=True, campo=campo, fase=fase,
                   archivo=archivo, ini=ini, fin=fin, pasos=pasos):
                oF.CalcStack("clear")
                oF.EnterQty(campo)
                oF.EnterScalar(fase)
                oF.CalcOp("AtPhase")
                extra = opciones if conopciones else True
                oF.ExportOnGrid(archivo, ini, fin, pasos, sol, variacion, extra,
                                "Cartesian", ["0mm", "0mm", "0mm"], False)

            intentar("campo %s %s fase %d" % (tag, etiq, fase), [
                lambda: ex(var + intr),
                lambda: ex(intr),
                lambda: ex(var + intr, False),
                lambda: ex(intr, False)])
    try:
        open(os.path.join(salida, "info_Stub_%s.txt" % tag), "w").write(
            "freq=%s fuente=P1 dz=%g x=[%g,%g] y=[%g,%g] paso=%g h=%g W=%g L1=%g Ls=%g\n" % (
                freq, DZ, x0, x1, y0, y1, PASO, H_MM, W1_MM, L1_MM, LS_MM))
    except Exception:
        pass


def main():
    try:
        oDesktop.RestoreWindow()
    except Exception:
        pass
    carpeta = carpeta_proyectos()
    oProject, ruta = abrir_existente(carpeta)
    if oProject is None:
        return
    oDesign = oProject.SetActiveDesign(DISENO)
    nombres = barridos(oDesign)
    intentar("guardar", [lambda: oProject.Save()], silencioso=True)
    resolver_barridos(oDesign, nombres)
    intentar("guardar", [lambda: oProject.Save()], silencioso=True)
    excitar_p1(oDesign)
    salida = os.path.join(carpeta, "P2_D5_Stub_Campos")
    if not os.path.isdir(salida):
        os.makedirs(salida)
    for nombre, freq in zip(nombres, FRECUENCIAS):
        msg("Exportando campos a %s ..." % freq)
        exportar(oDesign, nombre, freq, salida)
    z = comprimir(salida, salida + ".zip")
    if z:
        msg("Archivo para enviar: " + z)
    else:
        msg("No se pudo crear el .zip; comprime a mano la carpeta " + salida, 1)


main()
if fallas:
    msg("Terminado con %d aviso(s). Revisa los mensajes [P2] anteriores." % len(fallas), 1)
else:
    msg("Terminado sin errores.")
