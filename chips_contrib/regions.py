#
#  Copyright (C) 2009, 2010, 2011, 2015
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

"""Region-based routines for ChIPS.
"""

import pychips.all as chips

from ciao_contrib.logger_wrapper import initialize_module_logger

import ciao_contrib.region.fov as fov

logger = initialize_module_logger("chips.regions")

v1 = logger.verbose1
v2 = logger.verbose2
v3 = logger.verbose3
v4 = logger.verbose4

__all__ = ("add_fov_region", )


class DisplayFOVRegion(fov.FOVRegion):
    """Display the FOV files using ChIPS."""

    def _validate_plot(self, wcs=False, minvals=None, maxvals=None):
        """Helper routine. Checks that plot and axes exist,
        creating them if necessary.

        Returns a tuple containing flags to indicate whether
        the X and Y axes were created by this routine.

        The wcs flag determines whether this is a WCS (hence TAN
        projection in CIAO 4.3) plot or not.
        """

        icur = chips.info_current()
        needs_xaxis = icur is None or icur.find("X Axis [") == -1
        needs_yaxis = icur is None or icur.find("Y Axis [") == -1

        v2("Need to create X / Y axis: {0} / {1}".format(needs_xaxis, needs_yaxis))
        rval = (needs_xaxis, needs_yaxis)

        if not needs_xaxis and not needs_yaxis:
            return rval

        # Shouldn't this be enforced by the class hierarchy?
        #
        if wcs and self.eqpos_transform is None:
            raise ValueError("There is no EQPOS transform available for plotting.")

        if minvals is None:
            (xlo, ylo) = (0, 0)
        else:
            (xlo, ylo) = minvals

        if maxvals is None:
            (xhi, yhi) = (0, 0)
        else:
            (xhi, yhi) = maxvals

        # We force the creation of both axes if WCS is chosen, since adding a
        # transform. It could (possibly?) be done with an existing axis
        # but leave that for a later revision.
        #
        if wcs:
            v3("Adding WCS axes: X = {0} to {1} and Y = {2} to {3}".format(
                xlo, xhi, ylo, yhi))

            chips.add_axis(chips.XY_AXIS, 0, xlo, xhi, ylo, yhi,
                           self.eqpos_transform)

            chips.set_plot_xlabel("RA")
            chips.set_xaxis(["tickformat", "ra"])

            chips.set_plot_ylabel("Dec")
            chips.set_yaxis(["tickformat", "dec"])

        else:
            if needs_xaxis:
                v3("Adding X axis: {0} to {1}".format(xlo, xhi))
                chips.add_axis(chips.X_AXIS, 0, xlo, xhi)
                chips.set_plot_xlabel("X")

            if needs_yaxis:
                v3("Adding Y axis: {0} to {1}".format(ylo, yhi))
                chips.add_axis(chips.Y_AXIS, 0, ylo, yhi)
                chips.set_plot_xlabel("Y")

        ratio = "1:1"
        v2("Setting data-aspect ratio to {0}".format(ratio))
        chips.set_data_aspect_ratio(ratio)

        return rval

    def add_as_region(self, wcs="world", attrs=None):
        """Add the FOV as a region.

        If no axes exist, then ones will be created. This is different
        to normal regions but necessary here, since the coordinates of
        the polygon are not in plot- or frame-normalized coordinates.

        If axes are added and wcs is 'world' then we use the transform
        associated with the EQPOS column to create WCS-TAN axes.

        The plot limits *will* be changed to ensure the new region is
        visible, even if the automin/max values for the axes are unset.

        wcs must be one of world, eqpos, physical, or pos.

        attrs should be one of:
          attribute list
          attribute string
          ChipsRegion object

        """

        wcsl = wcs.lower()
        if wcsl in ["world", "eqpos"]:
            is_wcs = True
            fov = self.eqpos
            fov_min = self.eqpos_min
            fov_max = self.eqpos_max

        elif wcsl in ["physical", "pos", "sky"]:
            is_wcs = False
            fov = self.pos
            fov_min = self.pos_min
            fov_max = self.pos_max

        else:
            raise ValueError("wcs can not be set to '{0}'".format(wcs))

        v2(">> Opening UNDO buffer")
        chips.open_undo_buffer()
        try:

            (addx, addy) = self._validate_plot(wcs=is_wcs,
                                               minvals=fov_min,
                                               maxvals=fov_max)

            # Get the existing plot range in data coordinates. We convert
            # from the plot-normalized system here since we can then avoid
            # worrying about whether an axis is reversed or if it crosses
            # ra=360/0.
            #
            (xl, yl) = chips.convert_coordinate([0, 0],
                                                chips.PLOT_NORM,
                                                chips.DATA)
            (xu, yu) = chips.convert_coordinate([1, 1],
                                                chips.PLOT_NORM,
                                                chips.DATA)
            v3("Existing plot range: x = {0} to {1}".format(xl, xu))
            v3("Existing plot range: y = {0} to {1}".format(yl, yu))

            # Current plot limits
            pxl = 0
            pxu = 1
            pyl = 0
            pyu = 1

            for ccd in fov.keys():

                v2("Adding FOV for CCD_ID = {0}".format(ccd))
                x = fov[ccd][0]
                y = fov[ccd][1]

                # It is easier to split apart using the user-supplied
                # attributes from the add_region call, since this way
                # there needs to be no processing of attrs here.
                #
                name = "obsid{0}-ccd{1}".format(self.obsid, ccd)
                v2("Adding region: {0}".format(name))
                chips.add_region(x, y, ["id", name])
                if attrs is not None:
                    v3("Setting attributes to {0}".format(attrs))
                    chips.set_region(attrs)

                # Check limits: we use the plot-normalized coordinate system
                #
                for i in range(x.size):
                    (px, py) = chips.convert_coordinate([x[i], y[i]],
                                                        chips.DATA,
                                                        chips.PLOT_NORM)
                    if px < pxl:
                        xl = x[i]
                        pxl = px
                        v4("Shifting plot xmin to {0} (idx={1})".format(pxl, i))
                    elif px > pxu:
                        xu = x[i]
                        pxu = px
                        v4("Shifting plot xmax to {0} (idx={1})".format(pxu, i))

                    if py < pyl:
                        yl = y[i]
                        pyl = py
                        v4("Shifting plot ymin to {0} (idx={1})".format(pyl, i))
                    elif py > pyu:
                        yu = y[i]
                        pyu = py
                        v4("Shifting plot ymax to {0} (idx={1})".format(pyu, i))

            # Change the limits if necessary
            #
            if chips.get_data_aspect_ratio() == "":
                if pxl < 0 or pxu > 1:
                    v3("Setting x axis: {0} to {1}".format(xl, xu))
                    chips.limits(chips.X_AXIS, xl, xu)
                if pyl < 0 or pyu > 1:
                    v3("Setting y axis: {0} to {1}".format(yl, yu))
                    chips.limits(chips.Y_AXIS, yl, yu)

            else:
                if pxl < 0 or pxu > 1 or pyl < 0 or pyu > 1:
                    v3("Setting x axis: {0} to {1} and y axis: {2} to {3}".format(xl, xu, yl, yu))
                    chips.limits(xl, xu, yl, yu)

        except:
            v2("<< Discarding UNDO buffer")
            chips.discard_undo_buffer()
            raise

        v2("<< Closing UNDO buffer")
        chips.close_undo_buffer()


def add_fov_region(fov, *args):
    """Add the FOV regions to the current plot. If no axes exist in
    the plot then ones will be created (so unlike normal regions).

    Usage:

      add_fov_region(filename | crate)
      add_fov_region(filename | crate, wcs)
      add_fov_region(filename | crate, argument list)
      add_fov_region(filename | crate, argument string)
      add_fov_region(filename | crate, ChipsRegion)
      add_fov_region(filename | crate, wcs, argument list)
      add_fov_region(filename | crate, wcs, argument string)
      add_fov_region(filename | crate, wcs, ChipsRegion)

    where the first argument is either the name of a CIAO fov region
    file, or a Crate containing the data (e.g. read in by the Crates'
    read_file routine).

    The optional wcs argument defines the coordinate
    system to use and can be one of:

      world, or eqpos        - use EQPOS
      physical, sky, or pos  - use the SKY coordinate system

    The default value is 'world'. Note that the logical coordinate
    system is not supported.

    The last argument is used to specify the attributes of the region.
    It can be an attribute list, attribute string, or a ChipsRegion
    object. Only region attributes can be changed.

    The attrs argument should only be sent the same values as would be
    used in a set_region call - so not the id value.

    The routine creates one region for each CCD_ID in the region
    file, and gives it a name of obsid<obsid>-<ccd_id> - e.g.
    obsid1234-3 for the ACIS-I3 chip of ObsId 1234.

    This routine has not been tested out on FOV files for HRC data.

    """

    nargs = len(args)
    if nargs > 2:
        raise TypeError("add_fov_region takes at most 3 arguments, sent {0}".format(1 + nargs))

    wcs_okay = ["world", "eqpos", "physical", "pos", "sky"]
    wcs = "world"
    attrs = None

    if nargs == 2:
        wcs = args[0]
        attrs = args[1]

    elif nargs == 1:
        # guess whether the user meant the WCS or a region attribute
        arg = args[0]
        if hasattr(arg, "lower") and arg.lower() in wcs_okay:
            wcs = arg
        else:
            attrs = arg

    if wcs.lower() not in wcs_okay:
        raise ValueError("wcs must be one of {0}, not '{1}'".format(
                         ", ".join(wcs_okay), wcs))

    r = DisplayFOVRegion(fov)
    r.add_as_region(wcs=wcs, attrs=attrs)

# End
