"""
@authors: Alberto FOSSA' Giuliana Elena MICELI

"""

import numpy as np

from rpfm.surrogate.meta_models import TwoDimAscConstMetaModel

# MetaModel settings
distributed = False  # variables distributed across multiple processes
extrapolate = False  # extrapolation for out-of-bounds inputs

# interpolation method among slinear, lagrange2, lagrange3, cubic, akima, scipy_cubic, scipy_slinear, scipy_quintic
interp_method = 'lagrange3'

training_data_gradients = True  # compute gradients wrt output training data
vec_size = 1  # number of points to evaluate at once
rec_file = 'desc_vland_mm.pkl'  # name of the file on which the solution is serialized

a = TwoDimAscConstMetaModel(distributed=distributed, extrapolate=extrapolate, method=interp_method,
                            training_data_gradients=training_data_gradients, vec_size=vec_size, rec_file=rec_file)

a.p['twr'] = [1.25]
a.p['Isp'] = [492.5]

a.p.run_model()
a.plot()

print('Total failures: ' + str(np.sum(a.failures)))
print(a.p['mm.m_prop'])