#
#  Copyright (C) 2012, 2013, 2014, 2015, 2017, 2018, 2019
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
Creates the load_xxx routines that load in the XSpec convolution
models.

Note that these models have seen little to no testing so please take
care and report any issues to the CXC HelpDesk at
https://cxc.harvard.edu/helpdesk/

The convolution models follow the load_conv and load_psf commands,
so that you use load_xxx to create an instance, which can then
be used in expressions, where the syntax is "name(yyy)", to
convolve the model expression yyy by the convolution instance
called name.

Example
-------

To convolve an apec model plus gaussian with the lsmooth model,
changing the sigma of the line to 0.5 keV (note that @ is replaced by
At in the parameter name):

  from sherpa_contrib.xspec.xsconvolve import *

  load_xslsmooth("lcomp")
  lcomp.sigaat6kev = 0.5
  print(lcomp)
  set_source(lcomp(xsapec.asrc + xsgaussian.gsrc))

The supported convolution models are listed below, prepend
"load_xs" to the name to find the command used to create
an instance of the model:

  cflux: calculate flux
  clumin: calculate luminosity
  cpflux: calculate photon flux
  gsmooth: gaussian smoothing
  ireflect: reflection from ionized material
  kdblur: convolve with the laor model shape
  kdblur2: convolve with the laor2 model shape
  kerrconv: accretion disk line shape with BH spin as free parameter
  kyconv: convolution using a relativistic line from axisymmetric accretion disk
  lsmooth: lorentzian smoothing
  partcov: partial covering
  rdblur: convolve with the diskline model shape
  reflect: reflection from neutral material
  rfxconv: angle-dependent reflection from an ionized disk
  rgsxsrc: convolve an RGS spectrum for extended emission
  simpl: comptonization of a seed spectrum
  vashift: velocity shift an additive model
  vmshift: velocity shift a multiplicative model
  xilconv: angle-dependent reflection from an ionized disk
  zashift: redshift an additive model
  zmshift: redshift a multiplicative model

"""

from sherpa.models import Parameter

import sherpa.astro.xspec._xspec as _xspec

from sherpa_contrib.xspec.xsmodels import XSConvolutionKernel, load_xsconvolve

__all__ = (
    'load_xscflux',
    'load_xsclumin',
    'load_xscpflux',
    'load_xsgsmooth',
    'load_xsireflect',
    'load_xskdblur',
    'load_xskdblur2',
    'load_xskerrconv',
    'load_xskyconv',
    'load_xslsmooth',
    'load_xspartcov',
    'load_xsrdblur',
    'load_xsreflect',
    'load_xsrfxconv',
    'load_xsrgsxsrc',
    'load_xssimpl',
    'load_xsvashift',
    'load_xsvmshift',
    'load_xsxilconv',
    'load_xszashift',
    'load_xszmshift'
)


# The wrapper code that Sherpa generates for the _xspec.C_xxx
# routines includes a call to the X-Spec initialization routines,
# so it is not needed to call something like
#     xspec.get_xsversion()
# here

class XScflux(XSConvolutionKernel):
    _calc = _xspec.C_cflux

    def __init__(self, name='xscflux'):
        self.Emin = Parameter(name, 'Emin', 0.5, min=0.0, max=1e6,
                              hard_min=0.0, hard_max=1e6, frozen=True,
                              units='keV')
        self.Emax = Parameter(name, 'Emax', 10.0, min=0.0, max=1e6,
                              hard_min=0.0, hard_max=1e6, frozen=True,
                              units='keV')
        self.lg10Flux = Parameter(name, 'lg10Flux', -12.0, min=-100.0,
                                  max=100.0, hard_min=-100.0, hard_max=100.0,
                                  frozen=False, units='cgs')
        XSConvolutionKernel.__init__(self, name, (self.Emin,
                                                  self.Emax,
                                                  self.lg10Flux
                                                  ))


class XSclumin(XSConvolutionKernel):
    _calc = _xspec.C_clumin

    def __init__(self, name='xsclumin'):
        self.Emin = Parameter(name, 'Emin', 0.5, min=0.0, max=1e6,
                              hard_min=0.0, hard_max=1e6, frozen=True,
                              units='keV')
        self.Emax = Parameter(name, 'Emax', 10.0, min=0.0, max=1e6,
                              hard_min=0.0, hard_max=1e6, frozen=True,
                              units='keV')
        self.Redshift = Parameter(name, 'Redshift', 0, min=-0.999, max=10,
                                  hard_min=-0.999, hard_max=10, frozen=True)
        self.lg10Lum = Parameter(name, 'lg10Lum', -40.0, min=-100.0,
                                 max=100.0, hard_min=-100.0, hard_max=100.0,
                                 frozen=False, units='cgs')
        XSConvolutionKernel.__init__(self, name, (self.Emin,
                                                  self.Emax,
                                                  self.Redshift,
                                                  self.lg10Lum
                                                  ))


class XScpflux(XSConvolutionKernel):
    _calc = _xspec.C_cpflux

    def __init__(self, name='xscpflux'):
        self.Emin = Parameter(name, 'Emin', 0.5, min=0.0, max=1e6,
                              hard_min=0.0, hard_max=1e6, frozen=True,
                              units='keV')
        self.Emax = Parameter(name, 'Emax', 10.0, min=0.0, max=1e6,
                              hard_min=0.0, hard_max=1e6, frozen=True,
                              units='keV')
        self.Flux = Parameter(name, 'Flux', 1.0, min=0.0, max=1e10,
                              hard_min=0.0, hard_max=1e10,
                              frozen=False, units='')
        XSConvolutionKernel.__init__(self, name, (self.Emin,
                                                  self.Emax,
                                                  self.Flux
                                                  ))


class XSgsmooth(XSConvolutionKernel):
    _calc = _xspec.C_gsmooth

    def __init__(self, name='xsgsmooth'):
        self.SigAt6keV = Parameter(name, 'SigAt6keV', 1.0, min=0.0, max=10.0,
                                   hard_min=0.0, hard_max=20.0,
                                   frozen=False, units='keV')
        self.Index = Parameter(name, 'Index', 0.0, min=-1.0, max=1.0,
                               hard_min=-1.0, hard_max=1.0, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.SigAt6keV, self.Index))


class XSireflect(XSConvolutionKernel):
    _calc = _xspec.C_ireflct

    def __init__(self, name='xsireflect'):
        self.rel_refl = Parameter(name, 'rel_refl', 0.0, min=-1.0, max=1e6,
                                  hard_min=-1.0, hard_max=1e6, frozen=False)
        self.Redshift = Parameter(name, 'Redshift', 0.0, min=-0.999, max=10.0,
                                  hard_min=-0.999, hard_max=10.0, frozen=True)
        self.abund = Parameter(name, 'abund', 1.0, min=0.0, max=1e6,
                               hard_min=0.0, hard_max=1e6, frozen=True)
        self.Fe_abund = Parameter(name, 'Fe_abund', 1.0, min=0.0, max=1e6,
                                  hard_min=0.0, hard_max=1e6, frozen=True)
        self.cosIncl = Parameter(name, 'cosIncl', 0.45, min=0.05, max=0.95,
                                 hard_min=0.05, hard_max=0.95, frozen=True)
        self.T_disk = Parameter(name, 'T_disk', 3e4, min=1e4, max=1e6,
                                hard_min=1e4, hard_max=1e6, frozen=True,
                                units='K')
        self.xi = Parameter(name, 'xi', 1.0, min=0.0, max=1e3, hard_min=0.0,
                            hard_max=5e3, frozen=True, units='erg cm/s')
        XSConvolutionKernel.__init__(self, name, (self.rel_refl,
                                                  self.Redshift,
                                                  self.abund,
                                                  self.Fe_abund,
                                                  self.cosIncl,
                                                  self.T_disk,
                                                  self.xi
                                                  ))


class XSkdblur(XSConvolutionKernel):
    _calc = _xspec.C_kdblur

    def __init__(self, name='xskdblur'):
        self.Index = Parameter(name, 'Index', 3.0, min=-10.0, max=10.0,
                               hard_min=-10.0, hard_max=10.0, frozen=True)
        self.Rin_G = Parameter(name, 'Rin_G', 4.5, min=1.235, max=400.0,
                               hard_min=1.235, hard_max=400.0, frozen=True)
        self.Rout_G = Parameter(name, 'Rout_G', 100.0, min=1.235, max=400.0,
                                hard_min=1.235, hard_max=400.0, frozen=True)
        self.Incl = Parameter(name, 'Incl', 30.0, min=0.0, max=90.0,
                              hard_min=0.0, hard_max=90.0, frozen=False,
                              units='deg')
        XSConvolutionKernel.__init__(self, name, (self.Index,
                                                  self.Rin_G,
                                                  self.Rout_G,
                                                  self.Incl
                                                  ))


class XSkdblur2(XSConvolutionKernel):
    _calc = _xspec.C_kdblur2

    def __init__(self, name='xskdblur2'):
        self.Index = Parameter(name, 'Index', 3.0, min=-10.0, max=10.0,
                               hard_min=-10.0, hard_max=10.0, frozen=True)
        self.Rin_G = Parameter(name, 'Rin_G', 4.5, min=1.235, max=400.0,
                               hard_min=1.235, hard_max=400.0, frozen=True)
        self.Rout_G = Parameter(name, 'Rout_G', 100.0, min=1.235, max=400.0,
                                hard_min=1.235, hard_max=400.0, frozen=True)
        self.Incl = Parameter(name, 'Incl', 30.0, min=0.0, max=90.0,
                              hard_min=0.0, hard_max=90.0, frozen=False,
                              units='deg')
        self.Rbreak = Parameter(name, 'Rbreak', 20.0, min=1.235, max=400.0,
                                hard_min=1.235, hard_max=400.0, frozen=True)
        self.Index1 = Parameter(name, 'Index1', 3.0, min=-10.0, max=10.0,
                                hard_min=-10.0, hard_max=10.0, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Index,
                                                  self.Rin_G,
                                                  self.Rout_G,
                                                  self.Incl,
                                                  self.Rbreak,
                                                  self.Index1))


class XSkerrconv(XSConvolutionKernel):
    _calc = _xspec.C_spinconv

    def __init__(self, name='xskerrconv'):
        self.Index = Parameter(name, 'Index', 3.0, min=-10.0, max=10.0,
                               hard_min=-10.0, hard_max=10.0, frozen=True)
        self.Index1 = Parameter(name, 'Index1', 3.0, min=-10.0, max=10.0,
                                hard_min=-10.0, hard_max=10.0, frozen=True)
        self.r_br_g = Parameter(name, 'r_br_g', 6.0, min=1.0, max=400.0,
                                hard_min=1.0, hard_max=400.0, frozen=True)
        self.a = Parameter(name, 'a', 0.998, min=0.0, max=0.998,
                           hard_min=0.0, hard_max=0.998, frozen=False)
        self.Incl = Parameter(name, 'Incl', 30.0, min=0.0, max=90.0,
                              hard_min=0.0, hard_max=90.0, frozen=False,
                              units='deg')
        self.Rin_ms = Parameter(name, 'Rin_ms', 1.0, min=1.0, max=400.0,
                                hard_min=1.0, hard_max=400.0, frozen=True)
        self.Rout_ms = Parameter(name, 'Rout_ms', 400.0, min=1.0, max=400.0,
                                 hard_min=1.0, hard_max=400.0, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Index,
                                                  self.Index1,
                                                  self.r_br_g,
                                                  self.a,
                                                  self.Incl,
                                                  self.Rin_ms,
                                                  self.Rout_ms
                                                  ))


class XSkyconv(XSConvolutionKernel):
    _calc = _xspec.kyconv

    def __init__(self, name='xskyconv'):
        self.a = Parameter(name, 'a', 0.9982, min=0.0, max=1.0,
                           hard_min=0.0, hard_max=1.0, frozen=False,
                           units='GM/c')
        self.theta_o = Parameter(name, 'theta_o', 30.0, min=0.0, max=89.0,
                                 hard_min=0.0, hard_max=89.0, frozen=False,
                                 units='deg')
        self.rin = Parameter(name, 'rin', 1.0, min=1.0, max=1000.0,
                             hard_min=1.0, hard_max=1000.0, frozen=True,
                             units='GM/c^2')
        self.ms = Parameter(name, 'ms', 1.0, min=0.0, max=1.0,
                            hard_min=0.0, hard_max=1.0, frozen=True)
        self.rout = Parameter(name, 'rout', 400.0, min=1.0, max=1000.0,
                              hard_min=1.0, hard_max=1000.0, frozen=True,
                              units='GM/c^2')
        self.alpha = Parameter(name, 'alpha', 3.0, min=-20.0, max=20.0,
                               hard_min=-20.0, hard_max=20.0, frozen=True)
        self.beta = Parameter(name, 'beta', 3.0, min=-20.0, max=20.0,
                              hard_min=-20.0, hard_max=20.0, frozen=True)
        self.rb = Parameter(name, 'rb', 400.0, min=1.0, max=1000.0,
                            hard_min=1.0, hard_max=1000.0, frozen=True,
                            units='GM/c^2')
        self.zshift = Parameter(name, 'zshift', 0.0, min=-0.999, max=10.0,
                                hard_min=-0.999, hard_max=10.0, frozen=True)
        self.limb = Parameter(name, 'limb', 0.0, min=0.0, max=2.0,
                              hard_min=0.0, hard_max=2.0, frozen=True)
        self.ne_loc = Parameter(name, 'ne_loc', 100.0, min=3.0, max=5000.0,
                                hard_min=3.0, hard_max=5000.0, frozen=True)
        self.normal = Parameter(name, 'normal', 1.0, min=-1.0, max=100.0,
                                hard_min=-1.0, hard_max=100.0, frozen=True)

        pars = (self.a, self.theta_o, self.rin, self.ms, self.rout,
                self.alpha, self.beta, self.rb, self.zshift, self.limb,
                self.ne_loc, self.normal)
        XSConvolutionKernel.__init__(self, name, pars)


class XSlsmooth(XSConvolutionKernel):
    _calc = _xspec.C_lsmooth

    def __init__(self, name='xslsmooth'):
        self.SigAt6keV = Parameter(name, 'SigAt6keV', 1.0, min=0.0, max=10.0,
                                   hard_min=0.0, hard_max=20.0, frozen=False,
                                   units='keV')
        self.Index = Parameter(name, 'Index', 0.0, min=-1.0, max=1.0,
                               hard_min=-1.0, hard_max=1.0, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.SigAt6keV, self.Index))


class XSpartcov(XSConvolutionKernel):
    _calc = _xspec.C_PartialCovering

    def __init__(self, name='xspartcov'):
        self.CvrFract = Parameter(name, 'CvrFract', 0.5, min=0.05, max=0.95,
                                  hard_min=0.0, hard_max=1.0, frozen=False)
        XSConvolutionKernel.__init__(self, name, (self.CvrFract,))


class XSrdblur(XSConvolutionKernel):
    _calc = _xspec.C_rdblur

    def __init__(self, name='xsrdblur'):
        self.Betor10 = Parameter(name, 'Betor10', -2.0, min=-10.0, max=20.0,
                                 hard_min=-10.0, hard_max=20.0, frozen=True)
        self.Rin_M = Parameter(name, 'Rin_M', 10.0, min=6.0, max=1000.0,
                               hard_min=6.0, hard_max=10000.0, frozen=True)
        self.Rout_M = Parameter(name, 'Rout_M', 1000.0, min=0.0,
                                max=1000000.0, hard_min=0.0,
                                hard_max=10000000.0, frozen=True)
        self.Incl = Parameter(name, 'Incl', 30.0, min=0.0, max=90.0,
                              hard_min=0.0, hard_max=90.0, frozen=False,
                              units='deg')
        XSConvolutionKernel.__init__(self, name, (self.Betor10,
                                                  self.Rin_M,
                                                  self.Rout_M,
                                                  self.Incl
                                                  ))


class XSreflect(XSConvolutionKernel):
    _calc = _xspec.C_reflct

    def __init__(self, name='xsreflect'):
        self.rel_refl = Parameter(name, 'rel_refl', 0.0, min=-1.0, max=1e6,
                                  hard_min=-1.0, hard_max=1e6, frozen=False)
        self.Redshift = Parameter(name, 'Redshift', 0.0, min=-0.999, max=10.0,
                                  hard_min=-0.999, hard_max=10.0, frozen=True)
        self.abund = Parameter(name, 'abund', 1.0, min=0.0, max=1e6,
                               hard_min=0.0, hard_max=1e6, frozen=True)
        self.Fe_abund = Parameter(name, 'Fe_abund', 1.0, min=0.0, max=1e6,
                                  hard_min=0.0, hard_max=1e6, frozen=True)
        self.cosIncl = Parameter(name, 'cosIncl', 0.45, min=0.05, max=0.95,
                                 hard_min=0.05, hard_max=0.95, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.rel_refl,
                                                  self.Redshift,
                                                  self.abund,
                                                  self.Fe_abund,
                                                  self.cosIncl
                                                  ))


class XSrfxconv(XSConvolutionKernel):
    _calc = _xspec.C_rfxconv

    def __init__(self, name='xsrfxconv'):
        self.rel_refl = Parameter(name, 'rel_refl', -1.0, min=-1.0, max=1e6,
                                  hard_min=-1.0, hard_max=1e6)
        self.redshift = Parameter(name, 'redshift', 0.0, min=0.0, max=4.0,
                                  hard_min=0.0, hard_max=4.0, frozen=True)
        self.Fe_abund = Parameter(name, 'Fe_abund', 1.0, min=0.5, max=3,
                                  hard_min=0.5, hard_max=3, frozen=True)
        self.cosIncl = Parameter(name, 'cosIncl', 0.5, min=0.05, max=0.95,
                                 hard_min=0.05, hard_max=0.95, frozen=True)
        self.log_xi = Parameter(name, 'log_xi', 1.0, min=1.0, max=6.0,
                                hard_min=1.0, hard_max=6.0)
        XSConvolutionKernel.__init__(self, name, (self.rel_refl,
                                                  self.redshift,
                                                  self.Fe_abund,
                                                  self.cosIncl,
                                                  self.log_xi
                                                  ))


class XSrgsxsrc(XSConvolutionKernel):
    _calc = _xspec.rgsxsrc

    def __init__(self, name='xsrgsxsrc'):
        self.order = Parameter(name, 'order', -1.0, min=-3.0, max=-1,
                               hard_min=-3.0, hard_max=-1, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.order,))


class XSsimpl(XSConvolutionKernel):
    _calc = _xspec.C_simpl

    def __init__(self, name='xssimpl'):
        self.Gamma = Parameter(name, 'Gamma', 2.3, min=1.1, max=4.0,
                               hard_min=1.0, hard_max=5.0, frozen=False)
        self.FracSctr = Parameter(name, 'FracSctr', 0.05, min=0.0, max=0.4,
                                  hard_min=0.0, hard_max=1.0, frozen=False)
        self.UpScOnly = Parameter(name, 'UpScOnly', 1.0, min=0.0, max=100.0,
                                  hard_min=0.0, hard_max=100.0, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Gamma,
                                                  self.FracSctr,
                                                  self.UpScOnly
                                                  ))


class XSvashift(XSConvolutionKernel):
    _calc = _xspec.C_vashift

    def __init__(self, name='xsvashift'):
        self.Redshift = Parameter(name, 'Velocity', 0.0,
                                  min=-1e4, max=1e4,
                                  hard_min=-1e4, hard_max=1e4,
                                  units='km/s', frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Velocity,))


class XSvmshift(XSConvolutionKernel):
    _calc = _xspec.C_vmshift

    def __init__(self, name='xsvmshift'):
        self.Redshift = Parameter(name, 'Velocity', 0.0,
                                  min=-1e4, max=1e4,
                                  hard_min=-1e4, hard_max=1e4,
                                  units='km/s', frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Velocity,))


class XSxilconv(XSConvolutionKernel):
    _calc = _xspec.C_xilconv

    def __init__(self, name='xsxilconv'):
        self.rel_refl = Parameter(name, 'rel_refl', -1.0, min=-1.0, max=1e6,
                                  hard_min=-1.0, hard_max=1e6)
        self.redshift = Parameter(name, 'redshift', 0.0, min=0.0, max=4.0,
                                  hard_min=0.0, hard_max=4.0, frozen=True)
        self.Fe_abund = Parameter(name, 'Fe_abund', 1.0, min=0.5, max=3.0,
                                  hard_min=0.5, hard_max=3.0, frozen=True)
        self.cosIncl = Parameter(name, 'cosIncl', 0.5, min=0.05, max=0.95,
                                 hard_min=0.05, hard_max=0.95, frozen=True)
        self.log_xi = Parameter(name, 'log_xi', 1.0, min=1.0, max=1e6,
                                hard_min=1.0, hard_max=1e6)
        self.cutoff = Parameter(name, 'cutoff', 300.0, min=20.0, max=300.0,
                                hard_min=20.0, hard_max=300.0,
                                units='keV', frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.rel_refl,
                                                  self.redshift,
                                                  self.Fe_abund,
                                                  self.cosIncl,
                                                  self.log_xi,
                                                  self.cutoff
                                                  ))


class XSzashift(XSConvolutionKernel):
    _calc = _xspec.C_zashift

    def __init__(self, name='xszashift'):
        self.Redshift = Parameter(name, 'Redshift', 0.0, min=-0.999, max=10.0,
                                  hard_min=-0.999, hard_max=10, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Redshift,))


class XSzmshift(XSConvolutionKernel):
    _calc = _xspec.C_zmshift

    def __init__(self, name='xszmshift'):
        self.Redshift = Parameter(name, 'Redshift', 0.0, min=-0.999, max=10.0,
                                  hard_min=-0.999, hard_max=10, frozen=True)
        XSConvolutionKernel.__init__(self, name, (self.Redshift,))


# Now the load_xxx commands

def load_xscflux(name):
    """Create an instance of the X-Spec cflux convolution model.
    """
    load_xsconvolve(XScflux, name)


def load_xsclumin(name):
    """Create an instance of the X-Spec clumin convolution model.
    """
    load_xsconvolve(XSclumin, name)


def load_xscpflux(name):
    """Create an instance of the X-Spec cpflux convolution model.
    """
    load_xsconvolve(XScpflux, name)


def load_xsgsmooth(name):
    """Create an instance of the X-Spec gsmooth convolution model.
    """
    load_xsconvolve(XSgsmooth, name)


def load_xsireflect(name):
    """Create an instance of the X-Spec ireflect convolution model.
    """
    load_xsconvolve(XSireflect, name)


def load_xskdblur(name):
    """Create an instance of the X-Spec kdblur convolution model.
    """
    load_xsconvolve(XSkdblur, name)


def load_xskdblur2(name):
    """Create an instance of the X-Spec kdblur2 convolution model.
    """
    load_xsconvolve(XSkdblur2, name)


def load_xskerrconv(name):
    """Create an instance of the X-Spec kerrconv convolution model.
    """
    load_xsconvolve(XSkerrconv, name)


def load_xskyconv(name):
    """Create an instance of the X-Spec kyconv convolution model.
    """
    load_xsconvolve(XSkyconv, name)


def load_xslsmooth(name):
    """Create an instance of the X-Spec lsmooth convolution model.
    """
    load_xsconvolve(XSlsmooth, name)


def load_xspartcov(name):
    """Create an instance of the X-Spec partcov convolution model.
    """
    load_xsconvolve(XSpartcov, name)


def load_xsrdblur(name):
    """Create an instance of the X-Spec rdblur convolution model.
    """
    load_xsconvolve(XSrdblur, name)


def load_xsreflect(name):
    """Create an instance of the X-Spec reflect convolution model.
    """
    load_xsconvolve(XSreflect, name)


def load_xsrfxconv(name):
    """Create an instance of the X-Spec rfxconv convolution model.
    """
    load_xsconvolve(XSrfxconv, name)


def load_xsrgsxsrc(name):
    """Create an instance of the X-Spec rgsxsrc convolution model.
    """
    load_xsconvolve(XSrgsxsrc, name)


def load_xssimpl(name):
    """Create an instance of the X-Spec simpl convolution model.
    """
    load_xsconvolve(XSsimpl, name)


def load_xsvashift(name):
    """Create an instance of the X-Spec vashift convolution model.
    """
    load_xsconvolve(XSvashift, name)


def load_xsvmshift(name):
    """Create an instance of the X-Spec vmshift convolution model.
    """
    load_xsconvolve(XSvmshift, name)


def load_xsxilconv(name):
    """Create an instance of the X-Spec xilconv convolution model.
    """
    load_xsconvolve(XSxilconv, name)


def load_xszashift(name):
    """Create an instance of the X-Spec zashift convolution model.
    """
    load_xsconvolve(XSzashift, name)


def load_xszmshift(name):
    """Create an instance of the X-Spec zmshift convolution model.
    """
    load_xsconvolve(XSzmshift, name)
