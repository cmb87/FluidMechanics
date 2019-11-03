import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import cv2 
import io

from bokeh.models import ColumnDataSource
from bokeh.io import output_file
from bokeh.plotting import gridplot,figure, show
from bokeh.io import output_file
from bokeh.plotting import gridplot,figure, show
from bokeh.models import ColumnDataSource,FixedTicker


## http://brennen.caltech.edu/fluidbook/basicfluiddynamics/potentialflow/Complexvariables/joukowskiairfoils.pdf 
## http://www.jimhawley.ca/downloads/Joukowski_airfoil_in_potential_flow_without_complex_numbers.pdf
## https://blog.miguelgrinberg.com/post/video-streaming-with-flask/page/10


class JoukowskiAirfoil():
    def __init__(self, Uinf=1, R=1.3, a=1.0, alpha=0.0, beta=1.0, rho=1.0):
        self.Uinf = Uinf
        self.R = R
        self.a = a
        self.rho = rho
        ### angle of attack ###
        self.alpha=np.deg2rad(alpha)
        ### beta is the argument of the complex no (Joukovski parameter - circle center) ###
        self.beta=np.deg2rad(beta)
        self.lam = self.R/self.a

        ### lam must be >1 ###
        #if self.lam<=1: 
        #    raise ValueError('R/a must be >1')

        ### Center of the circle ###
        self.zc = self.a - self.R*np.exp(-1j*self.beta) 

        ### Flowfield varibales ###
        self.F, self.V = None, None
        self.xairfoil, self.zeta = None, None

    ### Circulation (from Kutta Condition) ###
    @property
    def gamma(self):
        return -4*np.pi*self.Uinf*self.R*np.sin(self.beta+self.alpha)
    
    @property
    def lift(self):
        return -self.rho*self.gamma*self.Uinf

    @property
    def drag(self):
        return -self.rho*self.gamma*self.Uinf

    @property
    def lift_coefficient(self):
        return 2*self.lift/(self.rho*self.chord*self.Uinf**2)

    @property
    def drag_coefficient(self):
        return 2*self.lift/(self.rho*self.chord*self.Uinf**2)

    ### Circle ###
    def circle(self, npts=200):
        t = np.linspace(0, 2*np.pi, npts)
        return self.zc + self.R*np.exp(1j*t)

    ### z1 ==> z ###
    def trafo_z1_to_z(self, z1):
        return z1 + self.zc

    ### z ==> z1 ###
    def trafo_z_to_z1(self, z):
        return z - self.zc

    ### z1 ==> z2 ###
    def trafo_z1_to_z2(self, z1):
        return z1*np.exp(-1j*self.alpha)

    ### z2 ==> z1 ###
    def trafo_z2_to_z1(self, z2):
        return z2*np.exp(1j*self.alpha)

    ### Joukowski transformation ###
    def trafo_joukowski(self, z):
        return z+(self.a**2)/z

    ### Calculate the potential field ###
    def calculateFlowField(self, nx=100, ny=100, nairfoil=300, rfac=6):

        r, phi = np.meshgrid(np.linspace(self.R,rfac*self.R, ny), np.linspace(-np.pi, np.pi, nx))
        z1 = r*np.cos(phi)+1j*r*np.sin(phi)
        z2 = self.trafo_z1_to_z2(z1)

        ### The complex flow f(z1) ###
        self.F = np.zeros(z1.shape, dtype=np.complex)
        self.V = np.zeros(z1.shape, dtype=np.complex)
        with np.errstate(divide='ignore'):
            for m in range(z1.shape[0]):
                for n in range(z1.shape[1]):

                    self.F[m,n] = self.Uinf*np.exp(-1j*self.alpha) * (z1[m,n] + self.R**2*np.exp(2j*self.alpha)/z1[m,n]) - 1j*self.gamma/(2*np.pi)*np.log(z2[m,n]/self.R)
                    self.V[m,n] = (self.Uinf*(1-(self.R/z2[m,n])**2)-1j*self.gamma/(2*np.pi*z2[m,n]))*np.exp(-1j*self.alpha)/(1-(self.a/self.trafo_z1_to_z(z1[m,n]))**2)

        ### Joukovski transformation of the z-plane minus the disc D(zc, R) ### 
        self.zeta = self.trafo_joukowski(self.trafo_z1_to_z(z1))
        self.xairfoil = self.trafo_joukowski(self.circle(npts=nairfoil))
        self.chord = self.xairfoil.real.max()-self.xairfoil.real.min()

    ### Plot flowfield ###
    def plot_flowfield(self, returnfig=False, store=False, name="flowfield.png"):

        print("Lift: {:.3f}".format(self.lift))
        print("CL  : {:.3f}".format(self.lift_coefficient))

        fmax = np.around(np.abs(self.F.imag).max(),2)
        vmax = np.around(np.absolute(self.V).max()/self.Uinf,1)

        fig=plt.figure()
        ax=fig.add_subplot(111)
        cp=ax.contour(self.zeta.real, self.zeta.imag, self.F.imag,levels=np.linspace(-fmax, fmax, 30).tolist(), colors='blue', linewidths=1, linestyles='solid')# this means that the flow is evaluated at Juc(z) since c_flow(Z)=C_flow(csi(Z))
        #cp=ax.contour(J.real, J.imag, F.real,levels=levels, colors='blue', linewidths=1, linestyles='solid')# this means that the flow is evaluated at Juc(z) since c_flow(Z)=C_flow(csi(Z))
        cp=ax.contourf(self.zeta.real, self.zeta.imag, np.absolute(self.V)/self.Uinf, levels=np.linspace(0, vmax, 20).tolist())
        cp=ax.contour(self.zeta.real, self.zeta.imag,  np.absolute(self.V)/self.Uinf, levels=np.linspace(0, vmax, 20).tolist(), colors='white', linewidths=0.5, linestyles='solid')# this means that the flow is evaluated at Juc(z) since c_flow(Z)=C_flow(csi(Z))

        ax.plot(self.xairfoil.real, self.xairfoil.imag)
        ax.set_aspect('equal')
        plt.axis('off')

        if store:
            plt.axis([-4,4,-4,4])
            plt.savefig(name, bbox_inches='tight')
            plt.close()
            return 

        if returnfig:
            plt.axis([-4,4,-4,4])
            return fig
        else:
            plt.show()

    ### Plot CP ###
    def plot_cp(self, store=False, name="profile_load.png"):

        x = (self.zeta[:,0].real-self.zeta[:,0].real.min())/(self.zeta[:,0].real.max()-self.zeta[:,0].real.min())
        y = (self.zeta[:,0].imag-self.zeta[:,0].real.min())/(self.zeta[:,0].real.max()-self.zeta[:,0].real.min())
        cp = 1-(np.absolute(self.V[:,0])/self.Uinf)**2

        plt.plot(x,cp)
        plt.grid(True)
        plt.xlabel("x/c [-]")
        plt.ylabel("$c_p$ [-]")

        if store:
            plt.savefig(name, bbox_inches='tight')
            plt.close()
            return 

        plt.show()


    ### For Bokeh ###
    @staticmethod
    def fig2data(fig):
        fig.canvas.draw()
        data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        return data

    ### For Bokeh ###
    @staticmethod
    def fig2dataNew(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=180)
        buf.seek(0)
        img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        buf.close()
        img = cv2.imdecode(img_arr, 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        return img

    ### Plot flowfield ###
    def plot_flowfield_bokeh(self):
        frame = JoukowskiAirfoil.fig2data(self.plot_flowfield(returnfig=True))
        h,w = frame.shape[0], frame.shape[1]

        print(w,h)
        output_file("joukowski.html", title="image.py example")
        p = figure(x_range=[0, w], y_range=[0, h])
        p.image(image=[frame[:,:,:]], x=[0], y=[0], dw=[w], dh=[h])

        show(p)  # open a browser


if __name__ == "__main__":
    sim = JoukowskiAirfoil(Uinf=20, R=1.25, alpha=14.0, beta=20.0, rho=1.0)
    sim.calculateFlowField()
    sim.plot_flowfield()
    #sim.plot_cp()
    #sim.plot_flowfield_bokeh()
