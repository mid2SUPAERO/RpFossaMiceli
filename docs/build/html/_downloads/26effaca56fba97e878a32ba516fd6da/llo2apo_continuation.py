"""
LLO to Apoapsis with Continuation
=================================

This examples computes a series of LLO to HEO transfers modeled as an initial finite burn to leave the LLO, a ballistic
arc and a final impulsive burn to inject at the apoapsis of the target HEO.
Subsequent solutions are obtained using a continuation method for decreasing thrust/weight ratios.

@authors: Alberto FOSSA' Giuliana Elena MICELI

"""

import numpy as np

from latom.utils.primary import Moon
from latom.utils.spacecraft import Spacecraft
from latom.analyzer.analyzer_heo_2d import TwoDimLLO2ApoContinuationAnalyzer
from latom.data.continuation.data_continuation import dirname_continuation

rec_file = 'example.pkl'  # file ID in latom.data.continuation where the data are serialized or None

# trajectory
moon = Moon()
llo_alt = 100e3  # initial LLO altitude [m]
heo_rp = 3150e3  # target HEO periselene radius [m]
heo_period = 6.5655 * 86400  # target HEO period [s]

# spacecraft
isp = 400.  # specific impulse [s]
log_scale = False  # twr_list in logarithmic scale or not
twr_list = np.arange(1.0, 0.09, -0.1)  # range of thrust/weight ratios in absolute/logarithmic scale [-]

# maximum thrust/weight ratio in absolute value [-]
if log_scale:
    twr0 = np.exp(twr_list[0])
else:
    twr0 = twr_list[0]

sc = Spacecraft(isp, twr0, g=moon.g)  # Spacecraft object

# NLP
method = 'gauss-lobatto'
segments = 200
order = 3
solver = 'IPOPT'
snopt_opts = {'Major feasibility tolerance': 1e-12, 'Major optimality tolerance': 1e-12,
              'Minor feasibility tolerance': 1e-12}

# additional settings
run_driver = True  # solve the NLP
exp_sim = True  # perform explicit simulation

tr = TwoDimLLO2ApoContinuationAnalyzer(moon, sc, llo_alt, heo_rp, heo_period, None, twr_list, method, segments, order,
                                       solver, snopt_opts=snopt_opts, check_partials=False, log_scale=log_scale)

if run_driver:

    tr.run_continuation()  # solve all subsequent NLP

    if exp_sim:  # explicit simulation from last NLP solution
        tr.nlp.exp_sim()

tr.get_solutions(explicit=exp_sim, scaled=False)  # retrieve solutions
print(tr)  # print summary

if rec_file is not None:  # save data in latom.data.continuation using the provided file ID
    tr.save('/'.join([dirname_continuation, rec_file]))

tr.plot()  # plot the results