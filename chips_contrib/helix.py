#
#  Copyright (C) 2013, 2014, 2015
#            Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
Allow the use in ChIPS of the cubehelix look-up table of
Green, D. A., 2011, `A colour scheme for the display of astronomical intensity images',
Bulletin of the Astronomical Society of India, 39, 289.
http://adsabs.harvard.edu/abs/2011BASI...39..289G

The advantage of this scheme is that it is designed to produce
a set of colors with monotonically-increasing brightness,
both on screen and when printed on a grayscale printer.

Example:

  >>> x = np.arange(-5, 5, 0.1)
  >>> y = np.arange(-5, 5, 0.1)
  >>> xx, yy = np.meshgrid(x, y, sparse=True)
  >>> z = np.sin(xx**2 + yy**2) / (xx**2 + yy**2)
  >>> load_colormap_cubehelix()
  >>> add_image(z, ['colormap', 'usercmap1'])
  >>> add_colorbar(0.5, 1.05)

CubeHelix parameters:

The parameters used to define a scheme are

  start - the start color, which is the direction of the predominant
          color variation at the start of the scheme.

  nrots - the number of rotations in R,G,B between the first and
          last components of the scheme.

  hue   - the hue parameter controls how saturated the colors are.
          A value of 0 creates a grayscale and large values may
          lead to clipping of the components.

  gamma - this controls whether the low (gamma < 1) or high (gamma > 1)
          intensities should be emphasized.

  nlev  - the number of colors to create.

"""

import numpy as np

import pychips

__all__ = ("load_colormap_cubehelix", "get_cubehelix")


def load_colormap_cubehelix(slot=pychips.chips_usercmap1, start=0.5,
                            nrots=-1.5, hue=1.0, gamma=1.0, nlev=256):
    """Set the colormap for the given slot to the cubehelix scheme.

    The first argument, slot, should be one of
    chips_usercmap1, chips_usercmap2, or chips_usercmap3.
    """

    slots = [pychips.chips_usercmap1,
             pychips.chips_usercmap2,
             pychips.chips_usercmap3]
    if slot not in slots:
        raise AttributeError("Invalid slot={} - should be chips_usercmap1, chips_usercmap2, or chips_usercmap3".format(slot))

    (r, g, b) = get_cubehelix(start=start, nrots=nrots, hue=hue,
                              gamma=gamma, nlev=nlev)
    pychips.load_colormap(r, g, b, slot)


def get_cubehelix(start=0.5, nrots=-1.5, hue=1.0, gamma=1.0,
                  nlev=256, clip=True):
    """Return (r,g,b) values for the given cubehelix scheme, where
    the values are clipped to the range 0 to 1 inclusive (unless clip
    is False).

    Unlike the original FORTRAN code this does not report the number
    of clipped elements; to get this information run with clip=False
    and perform the clipping manually; e.g. with np.clip(array,0,1).
    """

    index = np.arange(nlev, dtype=np.float32)
    fract = index / (nlev - 1)
    angle = 2 * np.pi * (start / 3.0 + 1 + nrots * fract)
    gfract = fract**gamma
    amp = hue * gfract * (1 - gfract) / 2.0
    cosa = np.cos(angle)
    sina = np.sin(angle)
    r = fract + amp * (-0.14861 * cosa + 1.78277 * sina)
    g = fract + amp * (-0.29227 * cosa - 0.90649 * sina)
    b = fract + amp * 1.97294 * cosa

    if clip:
        r = np.clip(r, 0, 1)
        g = np.clip(g, 0, 1)
        b = np.clip(b, 0, 1)

    return (r, g, b)

# End
