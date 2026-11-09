exec(open("load_v2.py").read())
Z0=50.0
def tnet(x):
    S11=x["S11"]; S21=x["S21"]; S22=S11; S12=S21
    den=(1-S11)*(1-S22)-S12*S21
    Z11=Z0*((1+S11)*(1-S22)+S12*S21)/den
    Z21=Z0*2*S21/den
    w=2*np.pi*x["f"]*1e9
    C=-1/(w*np.imag(Z21)); L=np.imag(Z11-Z21)/w
    return C,L
for d in DES:
    C,L=tnet(data[d]); data[d]["C"]=C; data[d]["L"]=L
    data[d]["Zeq"]=np.sqrt(2*L/C); data[d]["tau"]=C*Z0-2*L/Z0
