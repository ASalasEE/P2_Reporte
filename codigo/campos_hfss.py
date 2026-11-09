"""Lee los campos exportados de HFSS y calcula rho_s y J_s sobre la traza."""
import os, numpy as np
D = "datos/P2_D1_Campos"
EPS0, ER = 8.8541878128e-12, 3.55
W, L1, h = 1.14, 6.0, 0.508
AC = 2 * 0.55 * W

def leer(nombre, campo, lado, fase):
    a = np.loadtxt(os.path.join(D, "%s__%s_%s_ph%d.fld" % (nombre, campo, lado, fase)), skiprows=2)
    x, y = a[:, 0] * 1e3, a[:, 1] * 1e3          # mm
    xs, ys = np.unique(np.round(x, 6)), np.unique(np.round(y, 6))
    ix = np.searchsorted(xs, np.round(x, 6)); iy = np.searchsorted(ys, np.round(y, 6))
    V = np.full((len(ys), len(xs), 3), np.nan)
    V[iy, ix, :] = a[:, 3:6]
    return xs, ys, V

def fasor(nombre, campo, lado):
    xs, ys, A0 = leer(nombre, campo, lado, 0)
    _, _, A90 = leer(nombre, campo, lado, 90)
    return xs, ys, A0 - 1j * A90               # Re{F e^{j phi}}: phi=0 -> Re F, phi=90 -> -Im F

def dentro_local(X, Y, tipo):
    sq = (X >= 0) & (X <= W) & (Y >= 0) & (Y <= W)
    hz = (X < 0) & (Y >= 0) & (Y <= W)
    vt = (X >= 0) & (X <= W) & (Y > W)
    m = sq | hz | vt
    if tipo == "chaflan":
        m = m & ((X - Y) <= W - AC)
    return m

def cargar(nombre, tipo):
    xs, ys, Eb = fasor(nombre, "E", "abajo")
    _, _, Ea = fasor(nombre, "E", "arriba")
    _, _, Hb = fasor(nombre, "H", "abajo")
    _, _, Ha = fasor(nombre, "H", "arriba")
    rho = EPS0 * (Ea[..., 2] - ER * Eb[..., 2])      # C/m^2
    dH = Ha - Hb
    Jx, Jy = -dH[..., 1], dH[..., 0]                  # J = z x (Ha - Hb)
    xl, yl = xs - L1, ys + W / 2                      # coordenadas locales (esquina en [0,W]x[0,W])
    X, Y = np.meshgrid(xl, yl)
    m = dentro_local(X, Y, tipo)
    # margen de media celda para no tomar puntos sobre el borde exacto
    arm = m & (X > -2.6 * W) & (X < -2.4 * W)
    rref = np.nanmean(np.abs(rho[arm]))
    Jm = np.sqrt(np.abs(Jx) ** 2 + np.abs(Jy) ** 2)
    jref = np.nanmean(Jm[arm])
    # fase de referencia: corriente del brazo en su maximo
    ph = -np.angle(np.nanmean(Jx[arm]))
    return dict(xl=xl, yl=yl, X=X, Y=Y, m=m, rho=rho, Jx=Jx, Jy=Jy,
                S=np.where(m, np.abs(rho) / rref, np.nan), JN=np.where(m, Jm / jref, np.nan),
                JXr=np.where(m, np.real(Jx * np.exp(1j * ph)), 0), JYr=np.where(m, np.real(Jy * np.exp(1j * ph)), 0),
                rref=rref, jref=jref)

from scipy.interpolate import RegularGridInterpolator

def metricas(r, tipo):
    X, Y, m = r["X"], r["Y"], r["m"]
    rho_abs = np.where(m, np.abs(r["rho"]), np.nan)
    c = W / 4
    med = lambda A, mk: float(np.nanmean(A[mk & m]))
    ext = (X >= W - c) & (X <= W) & (Y >= 0) & (Y <= c)
    intc = (X >= 0) & (X <= c) & (Y >= W - c) & (Y <= W)
    band = ((X - Y) <= W - AC) & ((X - Y) >= W - AC - c * np.sqrt(2)) & (X <= W) & (Y >= 0) & (X >= W - AC) & (Y <= AC)
    sq = (X >= 0) & (X <= W) & (Y >= 0) & (Y <= W)
    arm = m & (X > -2.6 * W) & (X < -2.4 * W)
    # carga total en el cuadrado de la esquina frente a un cuadrado W x W del brazo
    n_full = np.sum(sq)
    Qrel = np.nansum(rho_abs[sq & m]) / (np.nanmean(rho_abs[arm]) * n_full)
    # fraccion de la carga del cuadrado en su mitad exterior (lado de la esquina exterior, x > y)
    Qout = np.nansum(rho_abs[sq & m & (X > Y)]) / np.nansum(rho_abs[sq & m])
    # fraccion de la corriente que cruza la diagonal x + y = W por su mitad interior
    fx = RegularGridInterpolator((r["yl"], r["xl"]), np.nan_to_num(r["Jx"]), bounds_error=False, fill_value=0)
    fy = RegularGridInterpolator((r["yl"], r["xl"]), np.nan_to_num(r["Jy"]), bounds_error=False, fill_value=0)
    if tipo == "curva":
        x_end = W                       # la diagonal llega a la esquina exterior (W, 0)
    else:
        x_end = (2 * W - AC) / 2 + W / 2  # interseccion de x + y = W con el borde del chaflan x - y = W - AC
        x_end = (W + (W - AC)) / 2
    t = np.linspace(0, x_end, 400)
    pts = np.stack([W - t, t], axis=1)        # (y, x) sobre x + y = W, desde la esquina interior
    jn = (fx(pts) + fy(pts)) / np.sqrt(2)
    dl = np.sqrt(2) * (t[1] - t[0])
    Itot = np.sum(jn) * dl
    mitad = t <= x_end / 2
    Iin = np.sum(jn[mitad]) * dl
    out = dict(Qrel=float(Qrel), Qout=float(Qout), Iin=float(abs(Iin) / abs(Itot)),
               Cint=med(r["S"], intc), Jint=med(r["JN"], intc))
    if tipo == "curva":
        out.update(Cext=med(r["S"], ext), Jext=med(r["JN"], ext))
    else:
        out.update(Cch=med(r["S"], band), Jch=med(r["JN"], band))
    return out
