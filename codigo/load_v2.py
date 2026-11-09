import csv, numpy as np, os
D="datos/P2_D1_Curva90_v2_CSV"
DES=["A_Referencia","B_Curva90","C_Curva90_Chaflan","A0_Ref_SinPerd","B0_Curva90_SinPerd","C0_Chaflan_SinPerd"]
def rd(name):
    rows=list(csv.reader(open(os.path.join(D,name))))
    return rows[0], rows[1:]
def cplx(s):
    s=s.replace(" ","").replace("i","j")
    return complex(s)
data={}
for d in DES:
    h,r=rd(d+"__01_S11_S21_dB.csv"); f=np.array([float(x[0]) for x in r]); s11db=np.array([float(x[1]) for x in r]); s21db=np.array([float(x[2]) for x in r])
    h,r=rd(d+"__05_Fase_deg.csv"); a11=np.array([float(x[1]) for x in r]); a21=np.array([float(x[2]) for x in r])
    h,r=rd(d+"__04_Smith_S11.csv"); S11c=np.array([cplx(x[1]) for x in r])
    h,r=rd(d+"__07_Balance_potencia.csv"); pl=np.array([float(x[1]) for x in r])
    h,r=rd(d+"__03_VSWR.csv"); vswr=np.array([float(x[1]) for x in r])
    data[d]=dict(f=f,s11db=s11db,s21db=s21db,a11=a11,a21=a21,S11=S11c,pl=pl,vswr=vswr,
                 S21=10**(s21db/20)*np.exp(1j*np.radians(a21)))
