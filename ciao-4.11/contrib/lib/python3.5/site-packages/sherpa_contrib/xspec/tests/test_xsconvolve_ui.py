#
#  Copyright (C) 2017
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

"""Test the integration of the XSPEC convolution models with the ui layer.

There's no testing of model evaluation, as that is done for the lower
level. The assumption here is that if a XSConvolutionKernel is created
then we can rely on the evaluation tests in test_xsconvolve.py.

"""

from sherpa.astro import ui
from sherpa.utils.err import IdentifierErr

from sherpa_contrib.xspec import xsconvolve
from sherpa_contrib.xspec.xsmodels import XSConvolutionKernel

# Hard-coded list of models that are expected to exist
# and the number of thawed and frozen parameters.
#
_models = [
    ('cflux', 1, 2),
    ('gsmooth', 1, 1),
    ('ireflect', 1, 6),
    ('kdblur', 1, 3),
    ('kdblur2', 1, 5),
    ('kerrconv', 2, 5),
    ('lsmooth', 1, 1),
    ('partcov', 1, 0),
    ('rdblur', 1, 3),
    ('reflect', 1, 4),
    ('simpl', 2, 1),
    ('zashift', 0, 1),
    ('zmshift', 0, 1)]


def test_load_exists():
    """Do the load_xsXXX variants exist?"""

    for mname, _, _ in _models:
        func = 'load_xs{}'.format(mname)
        assert func in xsconvolve.__all__, func
        

def test_load_creates_kernel():
    """Do the load_xsXXX functions create a convolution kernel with npars?"""

    ui.clean()

    # if this fails then something very strange is going on
    try:
        ui.get_model_component('delme')
        assert False, 'Why does delme exist?'
    except IdentifierErr:
        pass
    
    for mname, nthaw, nfrozen in _models:
        func = 'load_xs{}'.format(mname)
        f = getattr(xsconvolve, func)
        f('delme')

        mdl = ui.get_model_component('delme')
        assert isinstance(mdl, XSConvolutionKernel), \
            "{} creates XSConvolutionKernel".format(mname)
        
        assert len(mdl.pars) == nthaw + nfrozen, \
            '{}: number of pars matches'.format(mname)

        nf = sum([1 for p in mdl.pars if p.frozen])
        assert nf == nfrozen, \
            '{}: number of frozen pars matches'.format(mname)

    ui.clean()



if __name__ == "__main__":

    test_load_exists()
    test_load_creates_kernel()
