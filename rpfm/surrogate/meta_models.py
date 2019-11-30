"""
@authors: Alberto FOSSA' Giuliana Elena MICELI

"""

import numpy as np

from openmdao.api import Problem, MetaModelStructuredComp
from rpfm.utils.pickle_utils import load, save
from rpfm.utils.spacecraft import Spacecraft
from rpfm.nlp.nlp_2d import TwoDimAscConstNLP, TwoDimAscVarNLP, TwoDimAscVToffNLP, TwoDimDescVarNLP, TwoDimDescVLandNLP


class MetaModel:

    def __init__(self, interp_method='cubic', rec_file=None):

        self.mm = MetaModelStructuredComp(method=interp_method, training_data_gradients=True)
        self.p = Problem()
        self.p.model.add_subsystem('mm', self.mm, promotes=['Isp', 'twr'])

        if rec_file is not None:

            d = load(rec_file)

            self.twr = d['twr']
            self.Isp = d['Isp']
            self.m_prop = d['m_prop']
            self.failures = d['failures']

            self.mm.add_input('twr', training_data=self.twr)
            self.mm.add_input('Isp', training_data=self.Isp)
            self.mm.add_output('m_prop', training_data=self.m_prop)

            self.p.setup()
            self.p.final_setup()

    @staticmethod
    def solve(body, sc, alt, t_bounds, method, nb_seg, order, solver, snopt_opts=None, u_bound=None, **kwargs):

        return None, None

    def sampling(self, body, twr_lim, isp_lim, alt, t_bounds, method, nb_seg, order, solver, nb_samp, snopt_opts=None,
                 u_bound=None, rec_file=None, **kwargs):

        self.twr = np.linspace(twr_lim[0], twr_lim[1], nb_samp[0])
        self.Isp = np.linspace(isp_lim[0], isp_lim[1], nb_samp[1])

        self.m_prop = np.zeros(nb_samp)
        self.failures = np.zeros(nb_samp)

        for i in range(nb_samp[0]):
            for j in range(nb_samp[1]):

                sc = Spacecraft(self.Isp[j], self.twr[i], g=body.g)

                self.m_prop[i, j], self.failures[i, j] = self.solve(body, sc, alt, t_bounds, method, nb_seg, order,
                                                                    solver, snopt_opts=snopt_opts, u_bound=u_bound,
                                                                    **kwargs)

        self.mm.add_input('twr', training_data=self.twr)
        self.mm.add_input('Isp', training_data=self.Isp)
        self.mm.add_output('m_prop', training_data=self.m_prop)

        self.p.setup()
        self.p.final_setup()

        if rec_file is not None:

            d = {'Isp': self.Isp, 'twr': self.twr, 'm_prop': self.m_prop, 'failures': self.failures}
            save(d, rec_file)


class TwoDimAscConstMetaModel(MetaModel):

    @staticmethod
    def solve(body, sc, alt, t_bounds, method, nb_seg, order, solver, snopt_opts=None, u_bound=None, **kwargs):

        nlp = TwoDimAscConstNLP(body, sc, alt, kwargs['theta'], (-np.pi / 2, np.pi / 2), kwargs['tof'], t_bounds,
                                method, nb_seg, order, solver, 'powered', snopt_opts=snopt_opts, u_bound=u_bound)

        f = nlp.p.run_driver()
        nlp.cleanup()
        m_prop = 1. - nlp.p.get_val(nlp.phase_name + '.timeseries.states:m')[-1, -1]

        return m_prop, f


class TwoDimAscVarMetaModel(MetaModel):

    @staticmethod
    def solve(body, sc, alt, t_bounds, method, nb_seg, order, solver, snopt_opts=None, u_bound=None, **kwargs):

        nlp = TwoDimAscVarNLP(body, sc, alt, (-np.pi / 2, np.pi / 2), t_bounds, method, nb_seg, order, solver,
                              'powered', snopt_opts=snopt_opts, u_bound=u_bound)

        f = nlp.p.run_driver()
        nlp.cleanup()
        m_prop = 1. - nlp.p.get_val(nlp.phase_name + '.timeseries.states:m')[-1, -1]

        return m_prop, f


class TwoDimAscVToffMetaModel(MetaModel):

    @staticmethod
    def solve(body, sc, alt, t_bounds, method, nb_seg, order, solver, snopt_opts=None, u_bound=None, **kwargs):

        nlp = TwoDimAscVToffNLP(body, sc, alt, kwargs['alt_safe'], kwargs['slope'], (-np.pi / 2, np.pi / 2), t_bounds,
                                method, nb_seg, order, solver, 'powered', snopt_opts=snopt_opts, u_bound=u_bound)

        f = nlp.p.run_driver()
        nlp.cleanup()
        m_prop = 1. - nlp.p.get_val(nlp.phase_name + '.timeseries.states:m')[-1, -1]

        return m_prop, f


class TwoDimDescVarMetaModel(MetaModel):

    @staticmethod
    def solve(body, sc, alt, t_bounds, method, nb_seg, order, solver, snopt_opts=None, u_bound=None, **kwargs):

        nlp = TwoDimDescVarNLP(body, sc, alt, (0.0, 3 / 2 * np.pi), t_bounds, method, nb_seg, order, solver, 'powered',
                               snopt_opts=snopt_opts, u_bound=u_bound)

        f = nlp.p.run_driver()
        nlp.cleanup()
        m_prop = 1. - nlp.p.get_val(nlp.phase_name + '.timeseries.states:m')[-1, -1]

        return m_prop, f


class TwoDimDescVLandMetaModel(MetaModel):

    @staticmethod
    def solve(body, sc, alt, t_bounds, method, nb_seg, order, solver, snopt_opts=None, u_bound=None, **kwargs):

        nlp = TwoDimDescVLandNLP(body, sc, alt, kwargs['alt_safe'], kwargs['slope'], (0.0, 3 / 2 * np.pi), t_bounds,
                                 method, nb_seg, order, solver, 'powered', snopt_opts=snopt_opts, u_bound=u_bound)

        f = nlp.p.run_driver()
        nlp.cleanup()
        m_prop = 1. - nlp.p.get_val(nlp.phase_name + '.timeseries.states:m')[-1, -1]

        return m_prop, f


if __name__ == '__main__':

    from rpfm.utils.primary import Moon

    moon = Moon()
    a = TwoDimAscConstMetaModel()
    a.sampling(moon, [1.1, 4.0], [250., 500.], 100e3, None, 'gauss-lobatto', 20, 3, 'SNOPT', nb_samp=(15, 15),
               theta=np.pi/18, tof=500., rec_file='meta_model_test.pkl')
