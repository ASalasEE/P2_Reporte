import csv, numpy as np, os
DD="datos/P2_Diagnostico_Referencia_CSV"
D1="datos/P2_D1_Curva90_CSV"
VAR=["R2_Orig_SinPerdidas","R3_Orig_SinDeembed","R4_Orig_CarasPEC","R5_Grande_ABC","R6_Grande_CarasPEC","R7_Grande_PEC_SinPerd"]
def rd(path):
    rows=list(csv.reader(open(path))); return rows[1:]
dd={}
def cargar(nombre, carpeta):
    r=rd(os.path.join(carpeta,nombre+"__01_S11_S21_dB.csv"))
    f=np.array([float(x[0]) for x in r]); s11=np.array([float(x[1]) for x in r]); s21=np.array([float(x[2]) for x in r])
    r=rd(os.path.join(carpeta,nombre+"__05_Fase_deg.csv")); a11=np.array([float(x[1]) for x in r]); a21=np.array([float(x[2]) for x in r])
    r=rd(os.path.join(carpeta,nombre+"__07_Balance_potencia.csv")); pl=np.array([float(x[1]) for x in r])
    dd[nombre]=dict(f=f,s11=s11,s21=s21,a11=a11,a21=a21,pl=pl)
cargar("A_Referencia", D1)
for v in VAR: cargar(v, DD)
