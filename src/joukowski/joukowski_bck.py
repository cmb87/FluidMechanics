import numpy as np
import matplotlib.pyplot as plt
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
import sys

def Juc(z, lam):#Joukowski transformation
    return z+(lam**2)/z

def circle(C, R):
    t=np.linspace(0,2*np.pi, 200)
    return C+R*np.exp(1j*t)


def streamlines(alpha=10, beta=5, Uinf=1, R=1, ratio=1.2):
    #ratio=R/lam
    alpha=np.deg2rad(alpha)# angle of attack
    beta=np.deg2rad(beta)# -beta is the argument of the complex no (Joukovski parameter - circle center)
    if ratio<=1: #R/lam must be >1
        raise ValueError('R/lambda must be >1')
    lam=R/ratio#lam is the parameter of the Joukowski transformation

    ### Center of the circle ###
    zc=lam-R*np.exp(-1j*beta)

    phi = np.linspace(-np.pi, np.pi, 100)
    r = np.linspace(R,6*R, 100)

    r,phi=np.meshgrid(r,phi)
    z=r*np.cos(phi)+1j*r*np.sin(phi) + zc

    ### Zprime ###
    Z=z-zc

    ### Circulation ###
    Gamma = -4*np.pi*Uinf*R*np.sin(beta+alpha)
    # np.log(Z) cannot be calculated correctly due to a numpy bug np.log(MaskedArray);
    #https://github.com/numpy/numpy/issues/8516
    # we perform an elementwise computation

    ### The complex flow f(z) ###
    F = np.zeros(Z.shape, dtype=np.complex)
    V = np.zeros(Z.shape, dtype=np.complex)
    with np.errstate(divide='ignore'):
        for m in range(Z.shape[0]):
            for n in range(Z.shape[1]):
                F[m,n] = Uinf*(Z[m,n]*np.exp(-1j*alpha) + np.exp(1j*alpha)*R**2/Z[m,n]) - 1j*Gamma/(2*np.pi)*np.log((Z[m,n]*np.exp(-1j*alpha))/R)
                V[m,n] = (Uinf*(1-R**2/(Z[m,n]*np.exp(-1j*alpha)))-1j*Gamma/(2*np.pi*Z[m,n]*np.exp(-1j*alpha)))*np.exp(-1j*alpha)/(1-ratio**2/Z[m,n]**2)

    ### Joukovski transformation of the z-plane minus the disc D(zc, R) ### 
    J=Juc(z, lam)
    Circle=circle(zc, R)
    Airfoil=Juc(Circle, lam)

    return J, F, V, Airfoil, 8*np.pi*Uinf**2*lam*np.sin(alpha+beta)


J, F, V, Airfoil, cl = streamlines(alpha=3, beta=25, Uinf=1, R=1.1, ratio=1.5)
levels=np.arange(-2.8, 3.8, 0.2).tolist()

fig=plt.figure()
ax=fig.add_subplot(111)
cp=ax.contour(J.real, J.imag, F.imag,levels=levels, colors='blue', linewidths=1, linestyles='solid')# this means that the flow is evaluated at Juc(z) since c_flow(Z)=C_flow(csi(Z))
#cp=ax.contour(J.real, J.imag, F.real,levels=levels, colors='blue', linewidths=1, linestyles='solid')# this means that the flow is evaluated at Juc(z) since c_flow(Z)=C_flow(csi(Z))
cp=ax.contourf(J.real, J.imag, np.absolute(V), levels=np.arange(0, 3, 0.2).tolist())
cp=ax.contour(J.real, J.imag,  np.absolute(V), levels=np.arange(0, 3, 0.2).tolist(), colors='white', linewidths=0.5, linestyles='solid')# this means that the flow is evaluated at Juc(z) since c_flow(Z)=C_flow(csi(Z))


ax.plot(Airfoil.real, Airfoil.imag)
ax.set_aspect('equal')
plt.show()


print(J.real.shape)
sys.exit()
p = figure(x_range=[-3, 3], y_range=[-3, 3])
p.image(image=[stream_func], x=[-3], y=[-3], dw=[6], dh=[6], palette="Spectral11")

show(p)  # open a browser