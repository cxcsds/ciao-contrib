#
#  Copyright (C) 2011, 2013, 2015, 2016, 2018, 2019
#            Smithsonian Astrophysical Observatory
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
A basic name resolver for Astronomy object names: convert an
object name to a Right Ascension and Declination, using one of the
following services

 . NED - The NASA/IPAC ExtraGalactic Database at the California Institute of Technology (CalTech)
         http://ned.ipac.caltech.edu/

 . Simbad - The SIMBAD Astronomical Database at the Centre de Donn\'ees astronomiques de Strasbourg (CDS)
            http://simbad.u-strasbg.fr/simbad/

 . VizieR - The VizieR service at CDS or CADC
            http://vizier.u-strasbg.fr/viz-bin/VizieR
            http://vizier.hia.nrc.ca/viz-bin/VizieR

This module provides a simple interface - the identify_name routine -
to a name resolver, which is currently
the one provided by the CADC at
http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadc-target-resolver/
"""

from urllib.parse import quote_plus
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

import ciao_contrib.logger_wrapper as lw

__all__ = ("identify_name", )

logger = lw.initialize_module_logger("cda.resolver")
v5 = logger.verbose5


def strtofloat(val):
    """Convert a string into a float.

    The difference to just calling float(val) is that the error
    is more user-friendly.

    Parameters
    ----------
    val : str
        The number to convert

    Returns
    -------
    answer : float
        The floating-point value corresponding to the input.

    Raises
    ------
    ValueError
        If the number can not be converted.
    """

    try:
        return float(val)

    except ValueError:
        raise ValueError("Unable to convert '{0}' to a float.".format(val))


def identify_name(name):
    """Find the coordinates of an Astronomical object.

    Use the CADC name resolver to identify the given object name.

    Parameters
    ----------
    name : str
        The name of the object. This sent to the CADC server.

    Returns
    -------
    ra, dec, coordsys : number, number, string
        The coordinates, in decimal degrees, and coordinate system
        of the object if it was found.

    Raises
    ------
    ValueError
        This is raised if the object is unknown
    IOError
        This is raised if there was an error contacting the CADC
        service, or the return value could not be understood.

    Notes
    -----
    Other errors from the Python networking stack may also be raised.

    """

    tname = quote_plus(name)
    url = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadc-target-resolver/find?format=ascii&service=all&cached=true&target=" + tname

    # We get a 425 response code when there's no match, so catch this to make
    # it somewhat readable.
    #
    try:
        v5("Name query: {0}".format(url))
        rsp = urlopen(url)

    except HTTPError as he:
        # HTTPError is a subclass of URLError (in Pythohn 2.7 and 3.5)
        # so process first
        code = he.getcode()
        v5("Error from CADC name resolver - status = {0}".format(code))
        if code == 425:
            raise ValueError("No position found matching the name '{0}'.".format(name))
        else:
            v5("HTTPError code={0}".format(code))
            v5(str(he))
            raise he

    except URLError as ue:
        # Is this a sufficient check?
        v5("Error opening URL: {0}".format(ue))
        v5("error.reason = {0}".format(ue.reason))
        if ue.reason.errno == 8:
            raise IOError("Unable to connect to the CADC Name Resolver")
        else:
            raise

    v5("Response from query:")
    out = [None, None, None]
    data = rsp.read().decode('utf8')

    for l in data.split('\n'):
        l = l.strip()
        v5(l)
        if l == "":
            continue

        toks = l.split("=", 1)
        if len(toks) != 2:
            raise IOError("Unable to parse ASCII response from CADC name resolver: {0}".format(l))

        if toks[0] == "ra":
            out[0] = strtofloat(toks[1])

        elif toks[0] == "dec":
            out[1] = strtofloat(toks[1])

        elif toks[0] == "coordsys":
            out[2] = toks[1]

        elif toks[0] == "error":
            return None

    if any([o is None for o in out]):
        raise IOError("Incomplete response from CADC name resolver: {0}".format(out))

    out = tuple(out)
    v5("Position = {0}".format(out))
    return out

# End
