#
#  Copyright (C) 2011, 2013, 2015, 2016, 2018, 2019, 2020, 2022, 2023
#  Smithsonian Astrophysical Observatory
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
https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadc-target-resolver/

For cases when the CADC resolver is not available it falls back to
using the Sesame interface from CDS: http://vizier.u-strasbg.fr/vizier/doc/sesame.htx

"""

import ssl

from urllib.parse import quote_plus
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

import xml.etree.ElementTree as ET

import ciao_contrib.logger_wrapper as lw

__all__ = ("identify_name", )

logger = lw.initialize_module_logger("cda.resolver")
v4 = logger.verbose4
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
        raise ValueError(f"Unable to convert '{val}' to a float.") from None


def query_url(name, url, method, context=None):
    """Wrap up handling of errors for a URL call.

    Parameters
    ----------
    name : str
    url : str
    method : {"CADC", "Sesame"}
    context : optional
       If set, send to urlopen

    """

    # We get a 425 response code when there's no match, so catch this to make
    # it somewhat readable, at least for CADC. For Sesame it appears to be
    # different.
    #
    try:
        v5(f"{method} name query: {url}    context is None: {context is None}")
        return urlopen(url, context=context)

    except HTTPError as he:
        # HTTPError is a subclass of URLError so process first
        code = he.getcode()
        v5(f"Error from {method} name resolver - status = {code}")

        if method == "CADC" and code == 425:
            raise ValueError(f"No position found matching the name '{name}'.") from he

        v5(str(he))
        raise he

    except URLError as ue:
        # Is this a sufficient check?
        v5(f"Error opening URL: {ue}")
        v5(f"error.reason = {ue.reason}")
        v5(f"error.reason.errno = {ue.reason.errno}")

        # We can get SSL certificate errors reported here, so check
        # for them. This is not a "nice" way to be doing this. Is
        # there a better one?
        #
        reason = str(ue.reason)
        if context is None and reason.find("CERTIFICATE_VERIFY_FAILED") != -1:
            # Try with an unverified context - which we pass back to query_url so
            # that we do not have to repeat all the try/except work.
            #
            v5("Skipping to an unverified SSL context")
            context = ssl._create_unverified_context()
            return query_url(name, url, method, context=context)

        if ue.reason.errno == 8:
            raise IOError(f"Unable to connect to the {method} Name Resolver") from ue

        raise ue


def identify_name_cadc(name):
    """Find the coordinates of an Astronomical object from the CADC.

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
    url = "https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadc-target-resolver/find?format=ascii&service=all&cached=true&target=" + tname

    rsp = query_url(name, url, "CADC")

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
            raise IOError(f"Unable to parse ASCII response from CADC name resolver: {l}")

        if toks[0] == "ra":
            out[0] = strtofloat(toks[1])

        elif toks[0] == "dec":
            out[1] = strtofloat(toks[1])

        elif toks[0] == "coordsys":
            out[2] = toks[1]

        elif toks[0] == "error":
            return None

    if any(o is None for o in out):
        raise IOError(f"Incomplete response from CADC name resolver: {out}")

    out = tuple(out)
    v5(f"Position = {out}")
    return out


def identify_name_sesame(name):
    """Find the coordinates of an Astronomical object from CDS/Sesame.

    Use the Sesame name resolver to identify the given object name.

    Parameters
    ----------
    name : str
        The name of the object. This sent to the Sesame server.

    Returns
    -------
    ra, dec, coordsys : number, number, string
        The coordinates, in decimal degrees, and coordinate system
        of the object if it was found. The coordsys value is
        always set to 'ICRS'.

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

    # I used to use ~NSV but that sudenly stopped working, so switched
    # to ~SNV.
    #
    tname = quote_plus(name)
    url = 'https://cdsweb.u-strasbg.fr/cgi-bin/nph-sesame/-ox/~SNV?' + tname

    rsp = query_url(name, url, "Sesame")

    v5("Response from query:")
    data = rsp.read().decode('utf8')
    v5(data)

    # parse as XML
    # root = ET.parse(rsp).getroot()
    v4("Parsing response as XML")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as err:
        raise IOError("Unable to parse response from Sesame name server") from err

    rslvs = root.findall('Target/Resolver')
    if len(rslvs) == 0:
        raise ValueError(f"No position found matching the name '{name}'.")

    # Pick the first response (there should be only one. but just in case)
    v4(f"Found {len(rslvs)} Resolver components")
    rslv = rslvs[0]
    xra = rslv.find('jradeg')
    xde = rslv.find('jdedeg')
    if xra is None:
        raise IOError("Missing RA of source in respose from Sesame")
    if xde is None:
        raise IOError("Missing Declination of source in respose from Sesame")

    v5(f"RA=[{xra.text}] Dec=[{xde.text}]")

    try:
        ra = float(xra.text)
    except ValueError:
        raise IOError(f"Invalid RA response from Sesame ({xra.text})") from None

    try:
        dec = float(xde.text)
    except ValueError:
        raise IOError(f"Invalid Declination response from Sesame ({xde.text})") from None

    # WE ASSUME THE POSITION IS ICRS
    out = (ra, dec, 'ICRS')
    v5(f"Position = {out}")
    return out


def identify_name(name):
    """Find the coordinates of an Astronomical object.

    Use CADC name resolver to identify the given object name.
    Fall over to Sesame/CDS if this fails.

    Parameters
    ----------
    name : str
        The name of the object.

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
        This is raised if there was an error contacting the name
        servers, or the return value could not be understood.

    Notes
    -----
    Other errors from the Python networking stack may also be raised.

    """

    try:
        return identify_name_cadc(name)
    except (ValueError, OSError):
        # urllib errors seem to be suclasses of OSError so the
        # above should be general enough to identify a problem
        # with the CADC case.
        return identify_name_sesame(name)


# End
