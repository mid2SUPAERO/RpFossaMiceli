"""
@authors: Alberto FOSSA' Giuliana Elena MICELI

"""

import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy


class TwoDimAltProfile:

    def __init__(self, r, states, states_exp=None, thrust=None, threshold=1e-6, r_min=None):

        self.R = deepcopy(r)

        self.r = deepcopy(states[:, 0])
        self.theta = deepcopy(states[:, 1])

        if thrust is not None:  # variable thrust

            states_pow = states[(thrust >= threshold).flatten(), :]
            states_coast = states[(thrust < threshold).flatten(), :]

            self.r_pow = deepcopy(states_pow[:, 0])
            self.theta_pow = deepcopy(states_pow[:, 1])
            self.r_coast = deepcopy(states_coast[:, 0])
            self.theta_coast = deepcopy(states_coast[:, 1])

        if states_exp is not None:

            self.r_exp = deepcopy(states_exp[:, 0])
            self.theta_exp = deepcopy(states_exp[:, 1])

        if r_min is not None:

            self.r_min = deepcopy(r_min)

    def plot(self):

        fig, ax = plt.subplots(1, 1, constrained_layout=True)

        if hasattr(self, 'r_min'):

            ax.plot(self.theta*180/np.pi, (self.r_min - self.R)/1e3, color='k', label='safe altitude')

        if hasattr(self, 'r_exp'):  # explicit simulation

            ax.plot(self.theta_exp*180/np.pi, (self.r_exp - self.R)/1e3, color='g', label='explicit')

        if hasattr(self, 'r_pow'):  # implicit solution with variable thrust

            ax.plot(self.theta_coast * 180 / np.pi, (self.r_coast - self.R) / 1e3, 'o', color='b', label='coast')
            ax.plot(self.theta_pow*180/np.pi, (self.r_pow - self.R)/1e3, 'o', color='r', label='powered')

        else:  # implicit solution with constant thrust

            ax.plot(self.theta*180/np.pi, (self.r - self.R)/1e3, 'o', color='b', label='implicit')

        ax.set_ylabel('h (km)')
        ax.set_xlabel('theta (deg)')
        ax.set_title('Altitude profile')
        ax.grid()
        ax.legend(loc='best')


class TwoDimTrajectory:

    def __init__(self, r_moon, r_orbit, states):

        ang = np.linspace(0.0, 2 * np.pi, 500)

        # Moon
        self.x_moon = r_moon/1e3 * np.cos(ang)
        self.y_moon = r_moon/1e3 * np.sin(ang)

        # orbit
        self.x_orbit = r_orbit/1e3 * np.cos(ang)
        self.y_orbit = r_orbit/1e3 * np.sin(ang)

        # trajectory
        self.x = states[:, 0]/1e3 * np.cos(states[:, 1])
        self.y = states[:, 0]/1e3 * np.sin(states[:, 1])

    def plot(self):

        fig, ax = plt.subplots(constrained_layout=True)

        ax.plot(self.x_moon, self.y_moon, label='Moon surface')
        ax.plot(self.x_orbit, self.y_orbit, label='Target orbit')
        ax.plot(self.x, self.y, label='Trajectory')

        ax.set_aspect('equal')
        ax.grid()

        limit = np.ceil(self.x_orbit[0]/1e3)*1e3
        ticks = np.linspace(-limit, limit, 9)

        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.tick_params(axis='x', rotation=60)

        ax.set_xlabel('x (km)')
        ax.set_ylabel('y (km)')
        ax.set_title('Optimal trajectory')
        ax.legend(bbox_to_anchor=(1, 1), loc=2)
