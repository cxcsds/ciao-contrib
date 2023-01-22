#
#  Copyright (C) 2010, 2011, 2014, 2015, 2018
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
Simple smoothing routines provided by Sherpa
for 2D images.

At present, limited to

  gsmooth - gaussian smoothing
  bsmooth - boxcar smoothing
  tsmooth - top-hat smoothing
  fsmooth - smooth by the contents of a file

  ismooth  - smooth image with an image

"""

import numpy as np
import sherpa.utils._psf as psf
import pycrates as pyc

__all__ = ("ismooth", "gsmooth", "bsmooth", "tsmooth", "fsmooth")


# Create the kernels
#
def mk_gauss(sigma, hwidth):
    """Create a gaussian image for smoothing. The
    sigma is given in pixels and hwidth is the number of
    sigma to use for the box width (actually, half the box
    width). The output image is square, with odd size,
    and the kernel is centered in the image.

    A value of sigma=0 will return a (1,1) image with
    a value of 1.

    The image is not normalized.
    """

    if sigma < 0:
        raise ValueError("Gaussian sigma parameter must be >= 0, sent {0}".format(sigma))

    if hwidth <= 0:
        raise ValueError("Gaussian hwidth parameter must be > 0, sent {0}".format(hwidth))

    hw = int(np.ceil(hwidth * sigma))
    if hw == 0:
        kernel = np.ones((1, 1))

    else:
        grids = np.mgrid[-hw:(hw + 1), -hw:(hw + 1)] / (1.0 * sigma)
        yg = grids[0]
        xg = grids[1]
        kernel = np.exp(-1.0 * (xg * xg + yg * yg))

    return kernel


def mk_tophat(radius):
    """Create a tophat kernel with the given radius (in pixels).

    A value of radius=0 will return a (1,1) image with
    a value of 1.

    The output image is not normalized, square, with odd dimensions.
    """

    if radius < 0:
        raise ValueError("Top-hat radius parameter must be >= 0, sent {0}".format(radius))

    hw = int(np.ceil(radius))
    if hw == 0:
        kernel = np.ones((1, 1))

    else:
        grids = np.mgrid[-hw:(hw + 1), -hw:(hw + 1)] / (1.0 * radius)
        yg = grids[0]
        xg = grids[1]
        kernel = np.less_equal(xg * xg + yg * yg, 1.0) * 1.0

    return kernel


def mk_boxcar(radius):
    """Create a box-car kernel with the given radius (in pixels).

    A value of radius=0 will return a (1,1) image with
    a value of 1.

    The output image is not normalized, square, with odd dimensions.
    """

    if radius < 0:
        raise ValueError("Boxcar radius parameter must be >= 0, sent {0}".format(radius))

    hw = int(radius)
    bw = hw * 2 + 1
    return np.ones((bw, bw))


# Smoothing routines
#
def ismooth(image, kernel, origin=None, norm=True):
    """Convolve image with a kernel.

    If norm is True then the kernel will be divided by its total
    before convolution. To use the kernel as is, set norm to False
    (the kernel is always converted to have a datatype of float64
    before use).

    origin is the center to use for the kernel; if set to None then
    the center of the kernel is used. It is given using the numpy indexing
    scheme, so (yval,xval).

    To avoid offsets between the input and output image the kernel should
    have odd dimensions.

    Non-finite pixels in either the image or kernel are replaced by 0.
    Any such pixels in the input image are set back to NaN in the output image,
    but the presence of such values in the kernel image are ignored.

    """

    if image.ndim != 2:
        raise ValueError("ismooth() input image must be 2D, send {0}D".format(image.ndim))
    if kernel.ndim != 2:
        raise ValueError("ismooth() input kernel must be 2D, send {0}D".format(kernel.ndim))

    # convolve takes the dimensionality with X first not last
    ishape = image.shape
    is2 = (ishape[1], ishape[0])

    kshape = kernel.shape

    knx = kshape[1]
    kny = kshape[0]

    ks2 = (knx, kny)

    tcd = psf.tcdData()
    tcd.clear_kernel_fft()

    cimage = np.nan_to_num(image.flatten())

    if norm:
        nkernel = kernel * 1.0 / kernel.sum()
    else:
        nkernel = kernel * 1.0

    if origin is None:
        # We use the same center for even or odd image sizes
        kcx = knx // 2
        kcy = kny // 2
        kcen = (kcx, kcy)
    else:
        kcen = (origin[1], origin[0])

    out = tcd.convolve(cimage,
                       np.nan_to_num(nkernel.flatten()),
                       is2, ks2, kcen)

    out = out.reshape(ishape)
    out[np.isnan(image)] = np.nan
    return out


def gsmooth(image, sigma, hwidth=5):
    """Smooth image by a 2D gaussian with the given sigma (in pixels)
    using a box of half-width hwidth * sigma.

    A value of sigma=0 is the
    "identity" transform (although, due to the use of FFT, the output
    will not exactly match the input in this case).

    NaN (and other non-finite) values in the input are set to 0 for
    the smooth, and then set to NaN on output.
    """

    if image.ndim != 2:
        raise ValueError("gsmooth only works on 2D arrays, sent a {0}D array/".format(image.ndim))

    return ismooth(image, mk_gauss(sigma, hwidth), norm=True)


def tsmooth(image, radius):
    """Smooth image by a top-hat function with the given radius (in pixels).

    A value of radius=0 is the
    "identity" transform (although, due to the use of FFT, the output
    will not exactly match the input in this case).

    NaN (and other non-finite) values in the input are set to 0 for
    the smooth, and then set to NaN on output.
    """

    if image.ndim != 2:
        raise ValueError("tsmooth only works on 2D arrays, sent a {0}D array/".format(image.ndim))

    return ismooth(image, mk_tophat(radius))


def bsmooth(image, radius):
    """Smooth image by a 2D square box with the given radius,
    which is an integer. A value of radius of 1 creates a box of
    3 by 3, hwidth of 2 is 5 by 5.

    A value of radius=0 is the
    "identity" transform (although, due to the use of FFT, the output
    will not exactly match the input in this case).

    NaN (and other non-finite) values in the input are set to 0 for
    the smooth, and then set to NaN on output.
    """

    if image.ndim != 2:
        raise ValueError("bmooth only works on 2D arrays, sent a {0}D array".format(image.ndim))

    return ismooth(image, mk_boxcar(radius))


def fsmooth(image, filename):
    """Smooth image by the image stored in filename.

    Any non-finte values in the input file are set to 0.

    NaN (and other non-finite) values in the input are set to 0 for
    the smooth, and then set to NaN on output.

    """

    cr = pyc.read_file(filename)
    if not isinstance(cr, pyc.IMAGECrate):
        raise ValueError("File '{0}' is not an image!".format(filename))

    kvals = cr.get_image().values.copy()
    if kvals.ndim != 2:
        raise ValueError("Kernel file is not 2D but 0D!".format(kvals.ndim))

    return ismooth(image, kvals)

# End
