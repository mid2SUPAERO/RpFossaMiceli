"""
@authors: Alberto FOSSA' Giuliana Elena MICELI

"""

import numpy as np
import scipy.integrate as spi
from scipy.optimize import root
from copy import deepcopy

from rpfm.utils.keplerian_orbit import KepOrb
from rpfm.utils.const import g0


class DeorbitBurn:

    def __init__(self, sc, dv):

        self.sc = deepcopy(sc)
        self.dv = dv

        self.sc.m0 = self.sc.m0*np.exp(-self.dv/self.sc.Isp/g0)
        self.dm = sc.m0 - self.sc.m0


class HohmannTransfer:

    def __init__(self, gm, ra, rp):

        self.GM = gm
        self.ra = ra
        self.rp = rp

        self.a = (ra + rp)/2
        self.e = (ra - rp)/(ra + rp)

        self.h = (gm*self.a*(1 - self.e**2))**0.5
        self.tof = np.pi/gm**0.5*self.a**1.5

        self.va_circ = (gm/ra)**0.5
        self.vp_circ = (gm/rp)**0.5

        self.va = (2*gm*rp/(ra*(ra + rp)))**0.5
        self.vp = (2*gm*ra/(rp*(ra + rp)))**0.5

        self.dva = self.va_circ - self.va
        self.dvp = self.vp - self.vp_circ

        self.ea = None
        self.theta = None
        self.r = None
        self.u = None
        self.v = None

    def compute_states(self, t):

        nb_nodes = len(t)
        n = (self.GM/self.a**3)**0.5
        ea0 = np.reshape(np.linspace(0, np.pi, nb_nodes), (nb_nodes, 1))

        print("\nSolving Kepler's equation using Scipy root function")

        sol = root(KepOrb.kepler_eqn, ea0, args=(self.e, n, t, 0.0), tol=1e-20)

        print("output:", sol['message'])

        self.ea = np.reshape(sol.x, (nb_nodes, 1))
        self.theta = 2*np.arctan(((1 + self.e)/(1 - self.e))**0.5*np.tan(self.ea/2))
        self.r = self.a*(1 - self.e**2)/(1 + self.e*np.cos(self.theta))
        self.u = self.GM/self.h*self.e*np.sin(self.theta)
        self.v = self.GM/self.h*(1 + self.e*np.cos(self.theta))

        return sol


class PowConstRadius:

    def __init__(self, gm, r, vp, m0, thrust, isp):

        self.GM = gm
        self.R = r
        self.vp = vp
        self.m0 = m0
        self.T = thrust
        self.Isp = isp

        self.tof = None
        self.t = None
        self.theta = None
        self.v = None
        self.m = None
        self.alpha = None

    def compute_tof(self):

        print('\nComputing time of flight for initial powered trajectory at constant R using Scipy solve_ivp function')

        sol = spi.solve_ivp(fun=lambda v, t: self.dt_dv(v, t, self.GM, self.R, self.m0, self.T, self.Isp),
                            t_span=(0, self.vp), y0=[0], rtol=1e-20, atol=1e-20)

        self.tof = sol.y[-1, -1]

        # y, sol = spi.odeint(self.dt_dv, y0=[0], t=[0, self.vp], args=(self.mu, self.R, self.m0, self.F, self.w),
        #                    full_output=1, rtol=1e-9, atol=1e-12, tfirst=True)
        # self.tof = y[-1,-1] #sufrace grazing time of flight (s)

        print('output:', sol['message'])

        return sol

    def compute_states(self, t_eval):

        nb_nodes = len(t_eval)

        print('\nIntegrating ODEs for initial powered trajectory at constant R...')

        try:
            sol = spi.solve_ivp(fun=lambda t, x: self.dx_dt(t, x, self.GM, self.R, self.m0, self.T, self.Isp),
                                t_span=(0, self.tof), y0=[0, 0], t_eval=t_eval, rtol=1e-20, atol=1e-20)

            print('using Scipy solve_ivp function')

            self.t = np.reshape(sol.t, (nb_nodes, 1))
            self.theta = np.reshape(sol.y[0], (nb_nodes, 1))
            self.v = np.reshape(sol.y[1], (nb_nodes, 1))

        except:
            print('time vector not strictly monotonically increasing, using Scipy odeint function')

            y, sol = spi.odeint(self.dx_dt, y0=[0, 0], t=t_eval, args=(self.GM, self.R, self.m0, self.T, self.Isp),
                                full_output=True, rtol=1e-20, atol=1e-20, tfirst=True)
            self.t = np.reshape(t_eval, (nb_nodes, 1))
            self.theta = y[:, 0]
            self.v = y[:, 1]

        print('output:', sol['message'])

        m_flow = - self.T/self.Isp/g0
        self.m = self.m0 + m_flow*self.t

        v_dot = self.dv_dt(self.t, self.v, self.GM, self.R, self.m0, self.T, self.Isp)
        num = self.GM/self.R**2 - self.v**2/self.R
        self.alpha = np.arctan2(num, v_dot)

        return sol

    def dt_dv(self, v, t, gm, r, m0, thrust, isp):

        dt_dv = 1/self.dv_dt(t, v, gm, r, m0, thrust, isp)

        return dt_dv

    @staticmethod
    def dv_dt(t, v, gm, r, m0, thrust, isp):

        dv_dt = ((thrust/(m0 - (thrust/isp/g0)*t))**2 - (gm/r**2 - v**2/r)**2)**0.5

        return dv_dt

    def dx_dt(self, t, x, gm, r, m0, thrust, isp):

        x0_dot = x[1]/r
        x1_dot = self.dv_dt(t, x[1], gm, r, m0, thrust, isp)

        return [x0_dot, x1_dot]


class TwoDimAscGuess:

    def __init__(self, gm, r, alt, sc):

        self.GM = gm
        self.R = r
        self.alt = alt
        self.sc = sc

        self.ht = HohmannTransfer(gm, (r + alt), r)
        self.vp = self.ht.vp

        self.pcr = PowConstRadius(gm, r, self.vp, sc.m0, sc.T_max, sc.Isp)
        self.pcr.compute_tof()

        self.tof = self.ht.tof + self.pcr.tof
        self.t = None

        self.r = None
        self.theta = None
        self.u = None
        self.v = None
        self.m = None

        self.T = None
        self.alpha = None

        self.states = None
        self.controls = None

    def compute_trajectory(self, **kwargs):

        if 't' in kwargs:
            self.t = kwargs['t']
        elif 'nb_nodes' in kwargs:
            nb_nodes = kwargs['nb_nodes']
            self.t = np.reshape(np.linspace(0.0, self.tof, nb_nodes), (nb_nodes, 1))

        t_pcr = self.t[self.t <= self.pcr.tof]
        t_ht = self.t[self.t > self.pcr.tof]

        nb_pcr = len(t_pcr)
        nb_ht = len(t_ht)

        self.pcr.compute_states(t_pcr)
        self.ht.compute_states(t_ht - self.pcr.tof)

        self.r = np.vstack((self.R*np.ones((nb_pcr, 1)), self.ht.r))
        self.theta = np.vstack((self.pcr.theta, (self.ht.theta + self.pcr.theta[-1])))
        self.u = np.vstack((np.zeros((nb_pcr, 1)), self.ht.u))
        self.v = np.vstack((self.pcr.v, self.ht.v))

        m_ht = self.pcr.m[-1, -1]
        mf = m_ht*np.exp(-self.ht.dva/self.sc.Isp/g0)

        self.m = np.vstack((self.pcr.m, m_ht*np.ones(((nb_ht - 1), 1)), [mf]))
        self.alpha = np.vstack((self.pcr.alpha, np.zeros((nb_ht, 1))))

        throttle = np.vstack((np.ones((nb_pcr, 1)), np.zeros(((nb_ht - 1), 1)), [1]))

        self.T = self.sc.T_max*throttle

        self.states = np.hstack((self.r, self.theta, self.u, self.v, self.m))
        self.controls = np.hstack((self.T, self.alpha))


if __name__ == '__main__':

    from rpfm.utils.spacecraft import Spacecraft
    from rpfm.utils.primary import Moon

    moon = Moon()
    s = Spacecraft(450., 2.1, g=moon.g)

    tr = TwoDimAscGuess(moon.GM, moon.R, 86870, s)

    t_pcr = np.linspace(0.0, tr.pcr.tof, 500)
    t_ht = np.linspace(0.0, tr.ht.tof, 500) + tr.pcr.tof
    t_all = np.hstack((t_pcr, t_ht[1:]))

    tr.compute_trajectory(t=t_all)