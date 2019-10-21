"""
@authors: Alberto FOSSA' Giuliana Elena MICELI

"""

import numpy as np

from rpfm.utils.primary import Moon
from rpfm.utils.spacecraft import Spacecraft
from rpfm.analyzer.analyzer_heo_2d import TwoDimLLO2HEOAnalyzer

# trajectory
moon = Moon()
llo_alt = 100e3  # initial LLO altitude [m]
heo_rp = 3150e3  # target HEO periselene radius [m]
heo_period = 6.5655*86400  # target HEO period [s]

# spacecraft
isp = 450.  # specific impulse [s]
twr = 2.1  # initial thrust/weight ratio [-]
sc = Spacecraft(isp, twr, g=moon.g)

# NLP
method = 'gauss-lobatto'
segments = 400
order = 3
solver = 'SNOPT'
snopt_opts = {'Major feasibility tolerance': 1e-8, 'Major optimality tolerance': 1e-8,
              'Minor feasibility tolerance': 1e-8}

# additional settings
run_driver = True  # solve the NLP
exp_sim = True  # perform explicit simulation

# analyzer
tr = TwoDimLLO2HEOAnalyzer(moon, sc, llo_alt, heo_rp, heo_period, None, method, segments, order,
                           solver, snopt_opts=snopt_opts)

if run_driver:

    f = tr.run_driver()

    if exp_sim:
        tr.nlp.exp_sim()

tr.get_solutions(explicit=exp_sim)

print(tr)

tr.plot()