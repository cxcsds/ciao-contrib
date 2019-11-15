#
#  Copyright (C) 2012, 2013, 2014, 2015, 2016, 2017, 2019
#            Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Support for X-Spec convolution models provided along with Sherpa
but currently not exposed for use. This is the set of helper
classes and routines; to use the models themselves import the
sherpa_contrib.xspec.xsconvolve model.

This interface has seen limited testing, so please check the
documentation and then the CXC HelpDesk -
https://cxc.harvard.edu/helpdesk/ - if you have problems.

"""

import numpy as np

import sherpa.astro.xspec as xspec
import sherpa.models as models
import sherpa.astro.ui as ui

__all__ = (
    'XSConvolutionKernel',
    'XSConvolutionModel',
    'load_xsconvolve'
)


# Based on sherpa.ui.utils.load_conv
#
def load_xsconvolve(model, instancename):
    """Create an instance of a X-Spec convolution model

    Parameters
    ----------
    model
        The convolution model class (e.g. XSzashift).
    instancename : str
        The name used to refer to this model.

    Notes
    -----
    Creates a model component that implements the given X-Spec
    convolution model. It is expected that a wrapper around
    this will be created for each convolution model, e.g.:

        load_zashift("fred")

    for the convolution model zashift - for instance::

        def load_zashift(instancename):
            load_xsconvolve(XSzashift, instancename)

    There is no validation of model - i.e. that it is a valid
    model instance (a sub-class of XSConvolutionKernel).

    Examples
    --------

    >>> load_xsconv(XSzashift, "fred")
    >>> print(fred)
    >>> set_source(1, fred(powlaw1d.pl))
    """

    cmdl = model(name=instancename)
    ui._session._add_model_component(cmdl)


class XSConvolutionKernel(xspec.XSModel):
    """Handle X-Spec convolution models; this model creates
    XSConvolutionModel instances that are then evaluated by
    Sherpa. Instances of the convolution kernel are created by the
    load_xsconvolve() command rather than the normal
    modelname.instancename syntax.
    """

    def __repr__(self):
        return "<{} kernel instance '{}'>".format(type(self).__name__,
                                                  self.name)

    def __call__(self, model):
        return XSConvolutionModel(model, self)

    def calc(self, pars, rhs, *args, **kwargs):
        """Convolve the model.

        Note that this method is not cached by
        sherpa.models.modelCacher1d (may change in
        the future).
        """

        npars = len(self.pars)
        lpars = pars[:npars]
        rpars = pars[npars:]

        fluxes = np.asarray(rhs(rpars, *args, **kwargs))

        # As of CIAO 4.8, the Sherpa-provided interfaces to the
        # X-Spec convolution models require either
        #     pars, fluxes, edges
        #     pars, fluxes, elo, ehi
        # wihch simplifies this from earlier versions.
        #
        # should **kwargs be sent as well?
        return self._calc(lpars, fluxes, *args)


class XSConvolutionModel(models.CompositeModel, models.ArithmeticModel):
    """The XSConvolutionKernel instance creates these models for
    use by Sherpa. Users should not be creating instances of this
    class.
    """

    @staticmethod
    def wrapobj(obj):
        if isinstance(obj, models.ArithmeticModel):
            return obj
        else:
            return models.ArithmeticFunctionModel(obj)

    def __init__(self, model, wrapper):
        self.model  = self.wrapobj(model)
        self.wrapper = wrapper
        models.CompositeModel.__init__(self,
                                       "{}({})".format(self.wrapper.name,
                                                       self.model.name),
                                       (self.wrapper, self.model))

    # for now this is not cached
    def calc(self, p, *args, **kwargs):
        return self.wrapper.calc(p, self.model.calc,
                                 *args, **kwargs)
