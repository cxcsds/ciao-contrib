#
#  Copyright (C) 2022  Smithsonian Astrophysical Observatory
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

"Pixlib object with wrappers to simplify grating coordinates"

__all__ = ['TGPixlib',]

from pixlib import Pixlib


class TGPixlib(Pixlib):
    'Make converting to/from grating coordinates easier'

    # pylint: disable=too-many-instance-attributes

    def __init__(self, keywords):
        'Setup pixlib params based on keyword values'

        Pixlib.__init__(self, "chandra", "geom")
        self._set_instrument(keywords)
        self._set_sim(keywords)
        self._setup_wcs(keywords)
        self.zero_xy = None
        self.grating_keyword = keywords["GRATING"]

    def _set_instrument(self, keywords):
        'Set detector (ACIS|HRC-I|HRC-S)'

        if keywords["INSTRUME"] == "HRC":
            self.detector = keywords["DETNAM"]
        else:
            self.detector = keywords["INSTRUME"]

    def _set_sim(self, keywords):
        'Set SIM values and mirror alignment values'

        sim = [float(keywords["SIM_X"]),
               float(keywords["SIM_Y"]),
               float(keywords["SIM_Z"])]
        dsim = (float(0.0),    # DX is alway 0.0
                -1*float(keywords["DY_AVG"]),
                -1*float(keywords["DZ_AVG"]))
        droll = float(keywords["DTH_AVG"])

        self.aimpoint = sim
        self.mirror = (tuple(dsim), droll)

    def _setup_wcs(self, keywords):
        'Setup WCS transforms from sky|det|cel coords'

        def _make_transform(crota, crpix, crval, cdelt):
            'Wrapper to create Transform object'
            import pytransform as pt
            mytan = pt.WCSTANTransform()
            mytan.get_parameter("CROTA").set_value(crota)
            mytan.get_parameter("CRPIX").set_value(crpix)
            mytan.get_parameter("CRVAL").set_value(crval)
            mytan.get_parameter("CDELT").set_value(cdelt)
            return mytan

        # PNT are the optical axis (det)
        crval = [float(keywords["RA_PNT"]), float(keywords["DEC_PNT"])]
        crota = float(keywords["ROLL_PNT"])
        # NOM gives us the tangent point
        crnom = [float(keywords["RA_NOM"]), float(keywords["DEC_NOM"])]

        # get center of DET coord system by asking for on-axis
        # location (0, 0)
        crpix = self.msc2fpc((-1* self.flength, 0, 0))
        cdelt = [self.fp_scale / 3600.0] * 2     # replicate value
        cdelt[0] *= -1

        self.dettan = _make_transform(crota, crpix, crval, cdelt)
        # 0.0 : North is up
        self.skytan = _make_transform(0.0, crpix, crnom, cdelt)

    def _set_grating_order_arm_pos(self, grattype, order, zero_xy=None):
        'Helper to set grating order and arm'

        # pylint: disable=attribute-defined-outside-init
        # (these are properties of the Pixlib object)

        self.grating = grattype
        self.grt_order = order

        if zero_xy is None:
            zero_xy = self.zero_xy
        fpc_zo = self.sky_to_det(*zero_xy)
        fc_zo = self.fpc2fc(fpc_zo)
        self.grt_zo = fc_zo

    def sky_to_det(self, skyxx, skyyy):
        'Convert sky to det (via celestial coords)'

        # *1.0 make sure is a float
        radec = self.skytan.apply([[skyxx*1.0, skyyy*1.0]])
        r_d = [radec[0][0], radec[0][1]]

        detxy = self.dettan.invert([r_d])    # fpc
        dxy = [detxy[0][0], detxy[0][1]]
        return dxy

    def sky_to_grating_angles(self, sky_xy, grattype, order, zero_xy=None):
        'Convert sky to grating angles, tg_r and tg_d [degrees]'
        self._set_grating_order_arm_pos(grattype, order, zero_xy)
        my_fpc_coords = self.sky_to_det(*sky_xy)
        gdp = self.fpc2gdp(my_fpc_coords)
        gac = self.gdp2gac(gdp)    # tg_r, tg_d
        return gac

    def sky_to_grating_energy(self, sky_xy, grattype, order, zero_xy=None):
        'Convert sky to grating energy, [keV]'
        gac = self.sky_to_grating_angles(sky_xy, grattype, order, zero_xy)
        energy = self.grt_energy(gac)
        return energy

    def _energy_to_gac(self, energy, order):
        'Use energy in keV'
        from math import asin, degrees
        __angstrom_to_kev = 12.398
        wav = __angstrom_to_kev/energy

        # $\sin \beta = \frac{m \lambda }{p}$
        period = self.grt_prop[0]

        sin_b = (order * wav) / period
        beta = asin(sin_b)    # ARHHH --- RADIANS!!!!
        gac = (degrees(beta), 0.0)  # always use 0 for cross dispersion
        return gac

    @staticmethod
    def _mnc_to_chip(mnc_ray):
        'Convert mirror nodal coords to chip'

        # Simplified version of _fpc2chip_extend from pixlib.py

        # pylint: disable=protected-access

        import pixlib.pixlib as low_level
        from ctypes import c_double, c_int

        g_origin = (c_double * 3)(0.0, 0.0, 0.0)
        low_level._libc.pix_get_OTG_origin(g_origin)

        mnc = (c_double * 3)(mnc_ray[0], mnc_ray[1], mnc_ray[2])
        chip = (c_double * 2)(0.0, 0.0)
        chip_id = (c_int * 1)(0)
        lsi = (c_double * 3)(0.0, 0.0, 0.0)
        low_level._libc.pix_ray_to_detector(g_origin, mnc, chip_id, chip, lsi)

        return (chip_id[0], (chip[0], chip[1]))

    def _gzo_to_chip(self, gzo):
        'Convert from grating zero order coords to chip'

        # Taken from dmcoords:back.c::energy_to_chip

        fc_ray = self.gzo2fc(gzo)
        zero_ray = self.gzo2fc((0.0, 0.0, 0.0))
        mnc_ray = [a - b for a, b in zip(fc_ray, zero_ray)]

        # -- Normalize vector
        from math import sqrt
        nrm = sqrt(sum([a*a for a in mnc_ray]))
        mnc_ray = [a/nrm for a in mnc_ray]

        return self._mnc_to_chip(mnc_ray)

    def grating_energy_to_chip(self, energy, grattype, order, zero_xy=None):
        'Convert grating energy to chip coordinates'
        self._set_grating_order_arm_pos(grattype, order, zero_xy)
        gac = self._energy_to_gac(energy, order)
        gzo = self.gac2gzo(gac)
        return self._gzo_to_chip(gzo)

    def chip_to_sky(self, chipid, chip):
        'Convert chip coords to sky coords'
        det = self.chip2fpc((chipid, chip))
        ra_dec = self.dettan.apply([det])    # ra, dec
        sky_xy = self.skytan.invert(ra_dec)
        return sky_xy[0]

