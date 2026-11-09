# 📌 Guía de Colaboración y Control de Versiones

> **Nota para el equipo:** Para mantener la organización del proyecto, evitar errores de compilación y prevenir la pérdida o sobrescritura de trabajo, todos los integrantes deben seguir estas pautas de trabajo en LaTeX y Git.

---

## 1. Organización de Archivos en LaTeX

* **Archivo Principal (`main.tex`):** Este archivo contiene la estructura global del documento, la carga de paquetes y la configuración del preámbulo. **No modifiques las configuraciones globales ni el preámbulo sin antes consultarlo con el equipo.**
* **Archivos Individuales:** Cada integrante debe desarrollar su apartado en un archivo `.tex` independiente dentro de la carpeta del proyecto (por ejemplo, `secciones/introduccion.tex`, `secciones/metodologia.tex`).
* **Inclusión de Contenido:** Los archivos individuales se vinculan en el documento principal mediante el comando:
  ```latex
  \input{secciones/tu_archivo.tex}
  ```
* **Sección de Colaboradores:** Cada integrante debe trabajar exclusivamente en su archivo asignado y verificar que sus referencias y notas al pie queden correctamente dentro de su apartado antes de solicitar la revisión final.

---

## 2. Flujo de Trabajo con Git (Terminal y VS Code)

Puedes trabajar usando la terminal integrada de VS Code (`Ctrl + ~`) o la pestaña gráfica de **Control de código fuente** (`Ctrl + Shift + G`).

### 🔹 Paso 1: Actualizar el proyecto (`git pull`)
Antes de empezar a escribir o editar cualquier archivo, descarga siempre la versión más reciente del repositorio para evitar conflictos y asegurarte de tener los últimos avances de tus compañeros:
```bash
git pull
```
*(En VS Code: Menú de tres puntos `...` $\rightarrow$ **Pull**, o clic en el icono de sincronización en la barra azul inferior).*

### 🔹 Paso 2: Preparar los cambios (`git add .`)
Una vez que hayas editado tu sección, agrega los archivos modificados al área de preparación (*staging*):
```bash
git add .
```
*(En VS Code: Haz clic en el icono **`+`** al lado de tus archivos modificados bajo la pestaña de Cambios).*

### 🔹 Paso 3: Guardar localmente (`git commit`)
Registra tus avances guardando un punto de control con un mensaje claro y descriptivo sobre lo que realizaste:
```bash
git commit -m "Agregado apartado de metodología"
```
*(En VS Code: Escribe el mensaje en la casilla superior de texto y presiona `Ctrl + Enter` o el botón azul **Commit**).*

### 🔹 Paso 4: Subir cambios al repositorio (`git push`)
Envía tus avances al repositorio remoto para que el resto del equipo pueda verlos y sincronizarlos:
```bash
git push
```
*(En VS Code: Haz clic en el botón **Sincronizar cambios** o `...` $\rightarrow$ **Push**).*

---

## 💡 Reglas Generales de Colaboración

1. **Hábitos de Sincronización:** Ejecuta siempre `git pull` al iniciar tu jornada de trabajo y `git push` al terminar.
2. **Evitar Editar `main.tex` al mismo tiempo:** Para prevenir conflictos de fusión (*merge conflicts*), limita las ediciones en `main.tex` a solo incluir tu archivo mediante `\input{}`.
3. **Commits Pequeños y Frecuentes:** Es preferible hacer varios *commits* cortos especificando cada avance que un único *commit* masivo al final.
4. **Control de Archivos Temporales:** No subas archivos de compilación de LaTeX (`.aux`, `.log`, `.fls`, `.out`, `.synctex.gz`, `.pdf`). Asegúrate de que estén agregados a tu archivo `.gitignore`.