#
#  Copyright (C) 2010, 2011, 2012, 2014, 2015
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
Processing band information (i.e. energy range and representative
energy for instrument maps).
"""

import os

import pycrates
import stk

import ciao_contrib.logger_wrapper as lw

__all__ = ("validate_bands",)

lgr = lw.initialize_module_logger('_tools.bands')
v1 = lgr.verbose1
v3 = lgr.verbose3


def validate_energy_value(enval):
    "Error out if enval is outside the nominal energy range of Chandra."

    if 0.1 <= enval <= 10.0:
        return

    raise ValueError("Energy of {} keV is outside Chandra's nominal range of 0.1 to 10 keV.".format(enval))


def find_keyval(txt, key):
    """Look for key = val in text and return val (as a string). If the key
    is not found then None is returned. The comparison is
    case insensitive.

    This is only intended to support finding ENERGYLO/HI keywords in
    a file created by make_instmap_weights/save_instmap_weights, so
    it only supports one particular format.
    """

    spos = txt.lower().find(key.lower())
    if spos == -1:
        return None

    txt = txt[spos + len(key):].lstrip()
    if not txt.startswith('='):
        return None

    txt = txt[1:].strip()
    if txt == '':
        return None

    epos = txt.find(' ')
    if epos == -1:
        return txt
    else:
        return txt[:epos]


def get_energy_limits(wgtfile):
    """Return (elo,ehi) from wgtfile, which is assumed to have
    been created by make_instmap_weights or save_instmap_weights().
    The return values are floats.

    We first look for ENERG_LO/HI keywords in the file and, if they
    are not present, calculate the values from the first column,
    assuming these values are the mid-points and that the bins
    have the same width.
    """

    elo = None
    ehi = None
    with open(wgtfile, "r") as fh:
        for l in fh.readlines():
            if not l.startswith('#'):
                break

            kv = find_keyval(l, 'ENERG_LO')
            if kv is None:
                kv = find_keyval(l, 'ENERG_HI')
                if kv is not None:
                    ehi = kv
            else:
                elo = kv

    if elo is not None:
        v3("Weight file {} - elo = {}".format(wgtfile, elo))
        try:
            elo = float(elo)
        except:
            v1("Unable to convert ENERGYLO = {} to a float".format(elo))
            elo = None

    if ehi is not None:
        v3("Weight file {} - ehi = {}".format(wgtfile, ehi))
        try:
            ehi = float(ehi)
        except:
            v1("Unable to convert ENERGYHI = {} to a float".format(ehi))
            ehi = None

    if elo is None or ehi is None:
        v3("Calculating energy limits from weight file: {}".format(wgtfile))
        cr = pycrates.read_file(wgtfile)
        x = cr.get_column(0).values
        # could get bin width from the whole array but use the
        # local bin sizes in case the bins are not equal sized,
        # to reduce the error
        elo = (3 * x[0] - x[1]) / 2.0
        ehi = (3 * x[-1] - x[-2]) / 2.0

    return (elo, ehi)


def _val_to_str(v):
    """Return the string representation of v, unless it
    is None, in which case "" is returned.
    """
    if v is None:
        return ""
    else:
        return str(v)


# The EnergyBand classes are a bit of a grab bag of functionality.
# They carry abround the numeric values primarily for equality/duplicate
# checking, using the string versions of lo/hi/mono for creating output
# and file names.
#
# This class is being extended to also support the use of a weights
# file as input; in this case the lo/hi energy range is taken from the
# file and there is no monochromatic energy to deal with.
#
# Instead of the weighted bands being sent an explicit label, we could
# instead use the energy range (in the same way that 1:6:2.5 would use
# a label of 1-6). However, this precludes people from using the same
# energy range but with different spectra in the same run, so try the
# current approach first.
#
# The use of Energy in the label is somewhat unfortunate, as now
# expanding to support PI ranges for HRC.
#
class EnergyBand(object):
    """Base class for representing energy/pi bands. There is
    a lo and high energy (which may be None), a
    filter string for use in filtering data to match this
    range, a label which is used to identify this band
    (e.g. for use in file names), and a copy of the original
    band specification.
    """

    # The column name for the filter (e.g. 'energy', 'pi')
    colname = None

    # The low and high values of the band (if specified)
    # and the units for these values
    loval = None
    hival = None
    units = None

    # The identifier for this band (primarily for use in
    # creating file names).
    bandlabel = ""

    # The energy filter in DM format, e.g. [energy=500:7000]
    dmfilterstr = ""

    # The string displayed to user saying what band has been chosen
    _display = ""

    def __init__(self, espec, bandlabel):
        self.userlabel = espec
        self.bandlabel = bandlabel

    def display(self):
        "Logs information about the band."
        v1(self._display)

    @property
    def key(self):
        """Returns an identifier (e.g. a tuple) that can be used as
        an index for this energy band.
        """
        raise NotImplementedError("{}.key".format(self.__class__.__name__))

    @property
    def instmap_options(self):
        "Return (mono energy, weightfile name)"
        raise NotImplementedError("{}.get_instmap_options".format(self.__class_.__name__))

    def _set_range(self, loval, hival):
        """Set the lo/hi range and the dmfilterstr.

        At present it is not expected that this is called outside of
        object initialization.
        """
        self.loval = loval
        self.hival = hival
        self.dmfilterstr = "[{}={}:{}]".format(self.colname,
                                               _val_to_str(self.loval),
                                               _val_to_str(self.hival))


class MonochromaticEnergyBand(EnergyBand):
    "Base class for energy bands specified with a monochromatic energy"

    # The monochromatic energy, in keV, for the band
    enmono = None

    def __init__(self, espec, bandlabel, enmono):
        self.enmono = enmono
        EnergyBand.__init__(self, espec, bandlabel)

    @property
    def instmap_options(self):
        enmono = self.enmono
        return (enmono, "NONE")

    @property
    def key(self):
        return (self.bandlabel, self.enmono)


# Note that with the current design we store the weightfile value
# twice: once as a weightfile and once as the userlabel.
#
class WeightedEnergyBand(EnergyBand):
    "Base class for energy bands with a weights file"

    # The name of the weight file
    weightfile = None

    def __init__(self, weightfile, bandlabel):
        self.weightfile = weightfile
        EnergyBand.__init__(self, weightfile, bandlabel)

    @property
    def instmap_options(self):
        weightfile = self.weightfile
        return ("1.0", weightfile)

    @property
    def key(self):
        # weightfile is not needed here
        return (self.bandlabel, self.weightfile)


class HRCEnergyBand(MonochromaticEnergyBand):
    "Represent a HRC energy band: wide, pilo:pihi:enmono, or ::enmono (in keV)."

    colname = "pi"
    units = "channel"

    def __init__(self, espec):

        lbl = espec.replace(" ", "").lower()
        emsg = "Valid bands for HRC are wide, ::energy, or pilo:pihi:energy, not {}".format(lbl)
        pilo = None
        pihi = None

        if lbl == "wide":
            self._display = "Using CSC HRC wide science energy band."
            enmono = 1.5
            bandlabel = "wide"

        else:
            bvals = espec.split(":")
            if len(bvals) != 3:
                raise ValueError(emsg)

            bvals = [b.strip() for b in bvals]

            try:
                if bvals[0] != '':
                    pilo = int(bvals[0])

                if bvals[1] != '':
                    pihi = int(bvals[1])

                enmono = float(bvals[2])
            except ValueError:
                raise ValueError(emsg)

            # Could allow one of these to be missing, but this
            # makes coming up with a good naming scheme harder,
            # and I do not think is that useful.
            if pilo is None and pihi is None:
                bandlabel = "all"
            elif pilo is not None and pihi is not None:
                bandlabel = "{}-{}".format(pilo, pihi)
            else:
                raise ValueError(emsg)

            validate_energy_value(enmono)
            self._display = "Using PI={}:{} with a monochromatic energy of {} keV.".format(_val_to_str(pilo), _val_to_str(pihi), enmono)

        # Make sure that dmfilterstr is set up
        self._set_range(pilo, pihi)
        MonochromaticEnergyBand.__init__(self, espec, bandlabel, enmono)

    # def key(self):
    #    "Return a key that indexes this band"
    #    return (self.enmono, )


class HRCWeightedEnergyBand(WeightedEnergyBand):
    "Represent a HRC energy band: spectral weights file"

    colname = "pi"
    units = "channel"

    def __init__(self, weightfile, bandlabel):
        """bandlabel is the text to use to identify this band (e.g. in
        file names).
        """

        self._display = "{} uses weights file {}".format(bandlabel, weightfile)

        # Make sure that dmfilterstr is set up
        self._set_range(None, None)
        WeightedEnergyBand.__init__(self, weightfile, bandlabel)

    # def key(self):
    #    "Return a key that indexes this band"
    #    return (self.weightfile, self.bandlabel)


class ACISEnergyBand(MonochromaticEnergyBand):
    """Represent an ACIS energy band:

      broad, ultrasoft, soft, medium, hard
      elo:ehi:emono

    where numeric values are in keV.

    Note that CSC is not a valid band here.
    """

    colname = "energy"
    units = "keV"

    _csc_bands = {
        "broad":      ("ACIS broad",      [0.5, 7.0, 2.3],   "0.5:7.0:2.3"),
        "ultrasoft":  ("ACIS ultra-soft", [0.2, 0.5, 0.4],   "0.2:0.5:0.4"),
        "soft":       ("ACIS soft",       [0.5, 1.2, 0.92],  "0.5:1.2:0.92"),
        "medium":     ("ACIS medium",     [1.2, 2.0, 1.56],  "1.2:2.0:1.56"),
        "hard":       ("ACIS hard",       [2.0, 7.0, 3.8],   "2.0:7.0:3.8"),
        }

    def __init__(self, espec):

        lbl = espec.replace(" ", "").lower()
        emsg = "Valid bands for ACIS are broad, ultrasoft, soft, medium, hard, or elo:ehi:ecenter in keV, not {}".format(espec)

        try:
            binfo = self._csc_bands[lbl]
            self._display = "Using CSC {} science energy band.".format(binfo[0])
            band = binfo[1]
            bvals = binfo[2].split(":")

        except KeyError:
            bvals = espec.split(":")
            if len(bvals) != 3:
                raise ValueError(emsg)

            band = []
            for bval in bvals:
                if bval == "":
                    raise ValueError(emsg)

                try:
                    val = float(bval)
                except ValueError:
                    raise ValueError(emsg)

                validate_energy_value(val)
                band.append(val)

            self._display = "Using energy range {} to {} keV and exposure-map energy of {} keV.".format(band[0], band[1], band[2])

        if lbl.find(":") == -1:
            bandlabel = lbl
        else:
            bandlabel = "{}-{}".format(bvals[0], bvals[1])

        self._set_range(band[0], band[1])
        MonochromaticEnergyBand.__init__(self, espec, bandlabel, band[2])

    def _set_range(self, loval, hival):
        if loval is None:
            raise ValueError("The low energy value can not be None for ACIS data")
        if hival is None:
            raise ValueError("The high energy value can not be None for ACIS data")
        self.loval = loval
        self.hival = hival
        self.dmfilterstr = "[energy={}:{}]".format(self.loval * 1000,
                                                   self.hival * 1000)

    # def key(self):
    #    "Return a key that indexes this band"
    #    return (self.elo, self.ehi, self.enmono)


class ACISWeightedEnergyBand(WeightedEnergyBand):
    "Represent an ACIS energy band: spectral weights file"

    colname = "energy"
    units = "keV"

    def __init__(self, weightfile, bandlabel):
        """bandlabel is the text to use to identify this band (e.g. in
        file names).
        """

        (elo, ehi) = get_energy_limits(weightfile)
        validate_energy_value(elo)
        validate_energy_value(ehi)
        self._display = "{} uses weights file {} ({} to {} keV)".format(bandlabel, weightfile, elo, ehi)

        self._set_range(elo, ehi)
        WeightedEnergyBand.__init__(self, weightfile, bandlabel)

    def _set_range(self, loval, hival):
        if loval is None:
            raise ValueError("The low energy value can not be None for ACIS data")
        if hival is None:
            raise ValueError("The high energy value can not be None for ACIS data")
        self.loval = loval
        self.hival = hival
        self.dmfilterstr = "[energy={}:{}]".format(self.loval * 1000,
                                                   self.hival * 1000)

    # def key(self):
    #    "Return a key that indexes this band"
    #    return (self.elo, self.ehi, self.weightfile)


def validate_hrc_bands(inputs):
    """Ensure bands are valid for HRC data.

    The current implementation will only ever return a singleton list;
    an error is raised if multiple distinct bands are input.
    """

    v3("Validating energy bands for HRC")

    # HRC data can use
    #   file name
    #   wide
    #   default
    #   ::enmono
    #   pilo:pihi:enmono
    #
    # where enmono is in keV and pilo/pihi are in
    # channels.
    out = []
    check = set()
    bandnum = 1

    for espec in stk.build(inputs):

        if os.path.exists(espec):
            lbl = "band{}".format(bandnum)
            bandnum += 1
            band = HRCWeightedEnergyBand(espec, lbl)
        else:
            espec = espec.replace(" ", "").lower()
            if espec == "default":
                espec = "wide"
            band = HRCEnergyBand(espec)

        if band.key in check:
            continue

        out.append(band)
        check.add(band.key)

    if len(out) > 1:
        raise ValueError("Unable to set multiple bands with HRC data (bands={})".format(inputs))

    return out


def validate_acis_bands(inputs):
    "Ensure bands are valid for ACIS data."

    v3("Validating energy bands for ACIS")

    # ACIS data can use
    #    file name
    #    default
    #    ultrasoft, soft, medium, hard, broad, csc
    #    elo:ehi:enmono
    #
    # We could do this in one loop, but split out to make it a
    # bit clearer to read.
    #
    # would use a set for especs, but need to retain the order
    especs = []

    def add_espec(espec):
        if espec not in especs:
            especs.append(espec)

    for espec in stk.build(inputs):
        if os.path.isfile(espec):
            add_espec((True, espec))
        else:
            espec = espec.replace(" ", "").lower()
            if espec == "default":
                add_espec((False, "broad"))
            elif espec == "csc":
                add_espec((False, "soft"))
                add_espec((False, "medium"))
                add_espec((False, "hard"))
            else:
                add_espec((False, espec))

    out = []
    check1 = set()
    check2 = {}
    bandnum = 1
    for (isfile, espec) in especs:
        if isfile:
            lbl = "band{}".format(bandnum)
            bandnum += 1
            band = ACISWeightedEnergyBand(espec, lbl)
        else:
            band = ACISEnergyBand(espec)

        if band.key in check1:
            continue

        # By checking on the userlabel we are really checking on
        # energy ranges when given explicitly: i.e. 0.5:2:1,0.5:2:1.5
        # will be caught here, but 0.5:7:2,broad will be allowed
        # through.
        #
        try:
            espec2 = check2[band.bandlabel]
            raise ValueError("Bands {} and {} have the same label ({}).".format(espec, espec2, band.userlabel))

        except KeyError:
            pass

        out.append(band)
        check1.add(band.key)
        check2[band.bandlabel] = espec

    return out


def validate_bands(instrume, inputs):
    """Parse the bands input, returning an array of
    EnergyBand objects. This list is guaranteed to:

      - not contain repeats, even if the input contains
           broad and 0.5:7:2.3

      - have unique energy bands, so an input of
           0.5:2:1,0.5:2:1.5
        is invalid

    You can have different bands with the same monochromatic
    energy.

    The first value in a repeated band is used, so
       inputs="0.5:7:2.3,broad"
    will return the 0.5:7:2.3 version even though it might
    be nicer for the user to have the broad version returned.

    If a file name is given then it is assumed to be a spectral
    weights file; the energy range is taken from the weights file
    (either from the ENERG_LO/HI 'keywords' in the header added
    by make_instmap_weights/save_instmap_weights() or, if these
    are not found, the limits are computed from the array). The
    file names for these files include 'band<n>', where <n>
    is an integer, starting at 1.

    A value of 'default' is converted to 'broad' (ACIS) or
    'wide' (HRC).
    """

    if instrume == "HRC":
        out = validate_hrc_bands(inputs)
    else:
        out = validate_acis_bands(inputs)

    if out == []:
        raise ValueError("Unable to validate bands={}".format(inputs))

    for band in out:
        band.display()

    return out

# End
