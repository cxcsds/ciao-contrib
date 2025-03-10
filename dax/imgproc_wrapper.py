#!/usr/bin/env python
#
#  Copyright (C) 2019-2023  Smithsonian Astrophysical Observatory
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

'DAX wrapper around various image processing tasks'

import sys
import os

import subprocess as sp
from tempfile import NamedTemporaryFile


class ImageProcTask():
    'Base classs for image processing tasks'

    toolname = None

    def __init__(self, xpa, args):
        'Init: save image, and setup parameters'

        from ciao_contrib.runtool import make_tool
        import datetime

        print("-------------")
        print(datetime.datetime.now())

        self.xpa = xpa

        self.infile = self.save_ds9_image()
        self.keep_infiles = False

        suffix = "_{}.fits".format(self.toolname)
        self.outfile = NamedTemporaryFile(dir=os.environ["DAX_OUTDIR"],
                                          suffix=suffix, delete=False)
        self.region_file = None

        self.tool = make_tool(self.toolname)

        if hasattr(self.tool, "infile"):
            self.tool.infile = self.infile
        if hasattr(self.tool, "outfile"):
            self.tool.outfile = self.outfile.name
            self.img2display = self.outfile.name
        else:
            self.img2display = None

        self.set_args(args)

    def __del__(self):
        '''Delete temp region file'''
        if self.region_file and os.path.exists(self.region_file.name):
            os.unlink(self.region_file.name)

    def apply_region_to_infile(self, regions):
        '''Tools like dmellipse and dmimghull only operate on filtered
        regions.'''

        if regions is None or regions == "":
            return

        if regions.startswith("@"):
            import stk
            regions = "+".join(stk.build(regions.replace("@", "@-")))
        else:
            regions = regions.replace(";", "+").replace("+-", "-").rstrip("+")

        if len(regions) > 768:
            # If a really long region then write to a FITS region
            # file and use that instead.
            self.region_file = NamedTemporaryFile(dir=os.environ["DAX_OUTDIR"],
                                                  suffix=".reg", delete=False)
            self.region_file.close()
            from region import CXCRegion
            reg_obj = CXCRegion(regions)
            reg_obj.write(self.region_file.name, fits=True, clobber=True)
            regions = "region({})".format(self.region_file.name)

        ffilt = "[(x,y)={}]".format(regions)

        print("Using filter '{}'\n".format(ffilt))

        self.infile = self.infile+ffilt
        self.tool.infile = self.infile

    def run_tool(self):
        'Wrapper to run tool'
        return self.tool()

    def run(self):
        'Do it'

        # The "chips_startup.tk" (historical name when chips used for plotting)
        # has the definitions of the start_dax_progress and stop_dax_progress
        # procedures.  We execute these via ds9 using xpa.  Note that the
        # tcl command has to be a single command so it is wrapped in the
        # {}'s.

        try:
            self.xpaset_p(['tcl',
                           '{{start_dax_progress {t}}}'.format(t=self.toolname)])
            if hasattr(self.tool, "clobber") is True:
                self.tool.clobber = True

            print(self.tool)
            print("")
            verb = self.run_tool()

            if verb:
                print(verb)
            self.send_output()

            print("")
            if hasattr(self.tool, "outfile") is True:
                print("Output file: {}".format(self.outfile.name))

        finally:
            self.xpaset_p(['tcl',
                           '{{stop_dax_progress {t}}}'.format(t=self.toolname)])

            if self.keep_infiles is True:
                return

            infiles = self.infile.split(",")
            for infile in infiles:
                if os.path.exists(infile):
                    os.unlink(infile)

    def set_args(self, args):
        'Set argument, in specific classes'
        raise NotImplementedError("Not here")

    def send_output(self):
        'In derived classed'
        raise NotImplementedError("Not here")

    def xpaset_p(self, args):
        'Run xpaset -p (nothing return)'
        cmd = ["xpaset", "-p", self.xpa]

        if isinstance(args, str):
            cmd.extend(args.split())
        else:
            cmd.extend(args)

        sp.run(cmd, check=True)

    def xpaget(self, args, decode=True):
        'Run xpaget, return output as str'
        cmd = ["xpaget", self.xpa]

        if isinstance(args, str):
            cmd.extend(args.split())
        else:
            cmd.extend(args)
        retval = sp.run(cmd, check=True, stdout=sp.PIPE).stdout
        if decode is True:
            retval = retval.decode()
        return retval

    def update_wcs_for_blocking(self, infile):
        'Update the WCS if image has been blocked'

        # ds9 does not update the WCS in the FITS header when it blocks
        # data so we need to.
        #
        # The DM will re-write the WCS to it's own model here.
        # This does "break" WCSs that DM doesn't handle correctly
        # eg full skew matrices, -SIP coords, etc.
        # BUT -- dax is using all DM tools so it's going to
        # get broken at some point anyways.

        from pycrates import read_file
        from pytransform import LINEARTransform, LINEAR2DTransform

        block = float(self.xpaget("block"))
        if block == 1.0:
            return

        img = read_file(infile, mode="rw")
        for axis in img.get_axisnames():
            xform = img.get_transform(axis)
            if xform is None:
                continue

            # Even if image doesn't have 'p' physcial xform, DM
            # adds one.  So we need to be sure we only apply
            # blocking to the linear/linear2d transforms.
            if not isinstance(xform, (LINEARTransform, LINEAR2DTransform)):
                continue

            scale = xform.get_parameter("SCALE")
            if scale is None:
                continue

            scale.set_value(scale.get_value()*block)

        img.write()
        del img
        return

    def save_ds9_image(self):
        'Save image currently displayed by ds9'

        # ds9 can crop images; but when you get the file it
        # sends the whole thing.  We can get the crop info
        # and apply it separately. Note: I'm using image coords (#1,#2)
        # to avoid problems w/ sky vs. pos. vs (x,y).
        crop = self.xpaget("crop image")
        xmid, ymid, xlen, ylen = [float(x) for x in crop.split()]
        xlo = xmid-xlen/2.0
        xhi = xmid+xlen/2.0
        ylo = ymid-ylen/2.0
        yhi = ymid+ylen/2.0
        filt = "[#1={}:{},#2={}:{}]".format(xlo, xhi, ylo, yhi)

        # Get fits image from ds9
        fits = self.xpaget(["fits", ], decode=False)

        # Use dmcopy to filter on cropped region; pipe
        # fits file into dmcopy via stdin.
        ds9_file = NamedTemporaryFile(dir=os.environ["DAX_OUTDIR"],
                                      suffix="_ds9.fits", delete=False)
        cmd = ['dmcopy', '-{}'.format(filt), ds9_file.name, "clobber=yes"]
        dmc = sp.Popen(cmd, stdin=sp.PIPE)
        dmc.stdin.write(fits)
        dmc.communicate()

        self.update_wcs_for_blocking(ds9_file.name)

        return ds9_file.name

    def _get_header(self):
        'Parse FITS header returned by ds9 into dict'

        filehdr = self.xpaget(["fits", "header"])
        filehdr = filehdr.split("\n")

        # Remove excess
        hdr_z = [x for x in filehdr if len(x) > 8]
        hdr_a = [x for x in hdr_z if x[8] == "="]  # FITS std
        hdr_b = [x.split("/")[0] for x in hdr_a]   # strip comments
        hdr_c = [x.replace("'", "") for x in hdr_b]  # remove '
        out_hdr = {}
        for line in hdr_c:
            cut = line.split("=")
            key = cut[0].strip()
            val = cut[1].strip()
            out_hdr[key] = val
        return out_hdr

    @staticmethod
    def setup_ardlib(bpix, filehdr):
        'Create a local ardlib and set bpix parameter(s)'

        import paramio as pio
        ardlibpar = NamedTemporaryFile(dir=os.environ["DAX_OUTDIR"],
                                       suffix="_ardlib.par", delete=False)
        ardlibpar = ardlibpar.name
        # Copy, this make it easy to avoid permission issues
        syspar = pio.paccess("ardlib")
        with open(ardlibpar, "w") as out_par:
            with open(syspar, "r") as in_par:
                for line in in_par.readlines():
                    out_par.write(line)

        if "ACIS" == filehdr["INSTRUME"]:
            from ciao_contrib.runtool import acis_set_ardlib
            acis_set_ardlib(bpix, ardlibfile=ardlibpar)
        elif "HRC-I" == filehdr["DETNAM"]:
            pio.pset(ardlibpar, "AXAF_HRC-I_BADPIX_FILE", bpix[0])
        elif "HRC-S" == filehdr["DETNAM"]:
            pio.pset(ardlibpar, "AXAF_HRC-S_BADPIX_FILE", bpix[0])
        else:
            raise ValueError("Unknown Instrument/Detector configuration")
        return ardlibpar

    def find_aux(self):
        """
        This is a little bit more involved.  The image displayed
        in ds9 is all I've got.  I don't know that it was actually
        loaded from disk, or if it was loaded via xpa, or samp, or
        ... who knows.

        """
        cwd = self.xpaget(["cd", ])   # Where ds9 thinks it is
        dskfile = self.xpaget(["file", ])  # If image is from file on disk
        dskdir = os.path.dirname(dskfile.strip())

        # Get header, we go ahead and just get from ds9 directly
        filehdr = self._get_header()

        if "TELESCOP" not in filehdr or "CHANDRA" != filehdr["TELESCOP"]:
            raise ValueError("This task is only available for Chandra data")

        def multi_try(ftype):
            """
            The concept of the cwd then is murky at best.  I try three options
            - "." (where-ever that is)
            - cwd as reported by ds9.  This will either be the directory
              in which ds9 was launched or the dir where the file is; not sure.
              (and I think this has changed in the past)
            - get the file name and use the dirname off of there.  Honestly
              this is probably the most reliable since most users load from
              disk -- but I just don't know so I have to try all 3.
            """
            from ciao_contrib.ancillaryfiles import find_ancillary_files_header
            for path in [".", cwd, dskdir]:
                flist = find_ancillary_files_header(filehdr, [ftype], cwd=path)
                if flist is not None and flist[0] is not None:
                    return flist
            return None

        retval = {}
        for ftype in ["asol", "mask", "bpix", "dtf"]:
            rval = multi_try(ftype)
            retval[ftype] = None if rval is None else rval[0]

        if retval["bpix"] is not None:
            retval["ardlib"] = self.setup_ardlib(retval["bpix"], filehdr)
        else:
            retval["ardlib"] = "ardlib.par"

        return retval

    def get_coords(self, multi_ok=False):
        """
        Get coords: use crosshair if in crosshair mode,otherwise
          Get selected region, if any selected, otherwise
             Get regions
        """
        if "crosshair" == self.xpaget(["mode", ]).strip():
            xy_str = self.xpaget("crosshair physical")
            xy_str = xy_str.split()
            xpos = float(xy_str[0])
            ypos = float(xy_str[1])
            return (xpos, ypos)

        # Else, regions are more complicated ....
        # Try 'selected' first
        srcreg = self.xpaget("regions -format ciao source -system " +
                             "physical -strip yes selected").strip()

        if "" == srcreg:
            # Try unselected
            srcreg = self.xpaget("regions -format ciao source -system " +
                                 "physical -strip yes").strip()

        if "" == srcreg:
            raise RuntimeError("No source region and not in crosshair mode.")

        if srcreg.startswith("@"):
            raise RuntimeError("Arrr... too many src regions!")

        shapes = srcreg.strip(";").split(";")

        if len(shapes) > 1 and not multi_ok:
            raise RuntimeError("Please select a single region")

        from region import CXCRegion
        xpos = []
        ypos = []

        for shape in shapes:
            reg = CXCRegion(shape)

            if reg.shapes[0].name in ['rectangle', 'polygon', 'field']:
                raise ValueError("Unsupported shape type: try circle or ellipse?")

            xpos.append(reg.shapes[0].xpoints[0])
            ypos.append(reg.shapes[0].ypoints[0])

        if not multi_ok:
            xpos = xpos[0]
            ypos = ypos[0]

        return (xpos, ypos)

    def get_regions(self, src_or_bkg="source"):
        'Get regions via xpa'

        regions = self.xpaget(["regions", "-format", "ciao", "-system",
                               "physical", src_or_bkg, "-strip", "yes"])
        if regions.startswith("@"):
            import stk
            regions = "+".join(stk.build(regions.replace("@", "@-")))
        else:
            regions = regions.replace(";", "+").replace("+-", "-").rstrip("+")

        if regions == "":
            raise RuntimeError("ERROR: No valid regions found")

        return regions

    def use_eventfile(self):
        'Use the event file rather than the image for the infile'

        evt_name = self.xpaget(["file", ]).strip()
        # Funtools to DM conversion
        evt_name = evt_name.replace("EVENTS,", "EVENTS][")

        if os.path.exists(self.tool.infile):
            os.unlink(self.tool.infile)
        self.infile = evt_name
        self.tool.infile = evt_name
        self.keep_infiles = True


# Define different classes for each output type --------


class ImageProcTaskImgOut(ImageProcTask):
    'Classes that send output image to ds9'

    def send_output(self):
        'Send output, go into tile mode if requsted'

        self.xpaset_p(['fits', 'new', self.img2display])

        from paramio import pget
        if "yes" == pget("dax", "tile"):
            self.xpaset_p(['tile', ])

    def run_tool(self):
        'Runs tool.  Overrides outfile to provide nice blocks name'

        if hasattr(self.tool, "outfile"):
            # If the tool has an outfile, then add the
            # tool name as the extension name, eg
            #    tmp_XYZ123_dmimgadapt.fits[dmimgadapt]
            # This sets the block name to something "nice" and
            # informative, and deterministic.
            fname = self.tool.outfile
            self.tool.outfile = self.tool.outfile + f"[{self.toolname}]"
            verb = self.tool()
            self.tool.outfile = fname
        else:
            verb = self.tool()

        return verb


class ImageProcTaskRegionOut(ImageProcTask):
    'Classes that send output region to ds9'

    def send_output(self):
        'Send region if > 0 rows'

        try:
            # vtpdetect uses src_region
            import pycrates as pc
            src_reg = "{}[src_region]".format(self.tool.outfile)
            pc.read_file(src_reg)
            outreg = src_reg
        except (OSError, IOError):
            outreg = self.tool.outfile

        cmd = ["dmlist", outreg, "counts"]
        nrows = sp.run(cmd, check=True, stdout=sp.PIPE).stdout
        if nrows.decode().strip() == '0':
            print("\n\nNo sources detected\n")
            return

        self.xpaset_p(['regions', 'load', outreg])
        print("\n\nRegions have been loaded in the current frame.\n")

        from paramio import pget
        if "yes" == pget("dax", "prism"):
            self.xpaset_p(["prism", self.tool.outfile])


class ImageProcTaskPlotOut(ImageProcTask):
    'Classes that send output plot to ds9'

    def send_output(self):
        'Send plot to da9'
        cmd = ['ds9_plot_blt', self.plotfile, self.title, self.xpa]
        sp.run(cmd, check=True)

        from paramio import pget
        if "yes" == pget("dax", "prism"):
            self.xpaset_p(["prism", self.tool.outfile])


class ImageProcTaskTextOut(ImageProcTask):
    'Classes that only output text'

    def send_output(self):
        'Send text to ds9; implement in each subclass'
        raise NotImplementedError("Implement reportting in subclass")


# Specific classes for each task ------------------


class Dmimgblob(ImageProcTaskImgOut):
    'CIAO dmimgblob tool'

    toolname = "dmimgblob"

    def set_args(self, args):
        'Arguments: thresold'
        self.tool.threshold = args[0]
        self.tool.srconly = True


class Dmimgadapt(ImageProcTaskImgOut):
    'CIAO dmimgadapt tool'

    toolname = 'dmimgadapt'

    def set_args(self, args):
        'Args: function, minrad, maxrad, numrad, radscal counts'
        self.tool.function = args[0]
        self.tool.minrad = args[1]
        self.tool.maxrad = args[2]
        self.tool.numrad = args[3]
        self.tool.radscale = args[4]
        self.tool.counts = args[5]


class Csmooth(ImageProcTaskImgOut):
    'CIAO csmooth tool'

    toolname = 'csmooth'

    def set_args(self, args):
        'Args: kernel sigmin sigmax sclmin sclmax'
        self.tool.sclmap = "none"
        self.tool.outsigfile = "none"
        self.tool.outsclfile = "none"
        self.tool.conmeth = "fft"
        self.tool.conkerneltype = args[0]
        self.tool.sigmin = args[1]
        self.tool.sigmax = args[2]
        self.tool.sclmin = args[3]
        self.tool.sclmax = args[4]
        self.tool.sclmode = "compute"


class Dmimgfilt(ImageProcTaskImgOut):
    'CIAO dmimgfilt too'

    toolname = 'dmimgfilt'

    def set_args(self, args):
        'Args: function mask numiter'
        self.tool.function = args[0]
        self.tool.mask = args[1]
        self.tool.numiter = args[2]


class Dmimgthresh(ImageProcTaskImgOut):
    'CIAO dmigmthresh tool'

    toolname = 'dmimgthresh'

    def set_args(self, args):
        'Args: cutoff value'
        self.tool.cut = args[0]
        self.tool.value = args[1]


class Dmnautilus(ImageProcTaskImgOut):
    'CIAO dmnautilus tool'

    toolname = 'dmnautilus'

    def set_args(self, args):
        'ARGS: SNR, method'
        self.tool.snr = args[0]
        self.tool.method = args[1]


class Dmradar(ImageProcTaskImgOut):
    'CIAO dmradar tool'

    toolname = 'dmradar'

    def set_args(self, args):
        '''ARGS: SNR, xcen, ycen methd shape inner outer start range
        ellipticity rotang minrad minangle'''
        self.tool.snr = args[0]
        self.tool.xcenter = args[1]
        self.tool.ycenter = args[2]
        self.tool.method = args[3]
        self.tool.shape = args[4]
        self.tool.rinner = args[5]
        self.tool.router = args[6]
        self.tool.astart = args[7]
        self.tool.arange = args[8]
        self.tool.ellipticity = args[9]
        self.tool.rotang = args[10]
        self.tool.minradius = args[11]
        self.tool.minangle = args[12]


class Dmimgdist(ImageProcTaskImgOut):
    'CIAO dmimgdist tool'

    toolname = 'dmimgdist'

    def set_args(self, args):
        'Args: (none)'
        pass     # no parameters


class Apowerspectrum(ImageProcTaskImgOut):
    'CIAO apowerspectrum tool'

    toolname = 'apowerspectrum'

    def set_args(self, args):
        'Args: (none)'
        self.tool.infilereal = self.infile
        self.tool.infileimag = "none"


class Autocorrelate(ImageProcTaskImgOut):
    'CIAO acrosscorr tool'

    toolname = 'acrosscorr'

    def set_args(self, args):
        'Args: (none)'
        self.tool.infile1 = self.infile
        self.tool.infile2 = "none"


class Crosscorrelate(ImageProcTaskImgOut):
    'CIAO acrosscorr tool'

    toolname = 'acrosscorr'

    def set_args(self, args):
        self.xpaset_p(['frame', 'prev'])
        infile2 = self.save_ds9_image()
        self.xpaset_p(['frame', 'next'])
        self.tool.infile1 = self.infile
        self.tool.infile2 = infile2


class Aconvolve(ImageProcTaskImgOut):
    'CIAO aconvolve tool'

    toolname = 'aconvolve'

    def set_args(self, args):
        'Args: kernel xlen ylen method'
        ker = args[0]
        xlen = args[1]
        ylen = args[2]
        meth = args[3]
        nrad = 4
        kernels = {"gaus": "lib:{ker}(2,{nrad},1,{xx},{yy})",
                   "mexhat": "lib:{ker}(2,{nrad},1,{xx},{yy})",
                   "power": "lib:{ker}(2,{nrad},1,{xx},{yy})",
                   "exp": "lib:{ker}(2,{nrad},1,{xx},{yy})",
                   "tophat": "lib:{ker}(2,1,{xx},{yy})",
                   "box": "lib:{ker}(2,1,{xx},{yy})",
                   "sinc": "lib:{ker}(2,{nrad},1,{xx})",
                   "beta": "lib:{ker}(2,{nrad},1,{xx})",
                   "cone": "lib:{ker}(2,1,{xx})",
                   "pyramid": "lib:{ker}(2,1,{xx})",
                   "sphere": "lib:{ker}(2,{xx})", }
        self.tool.kernelspec = kernels[ker].format(ker=ker, xx=xlen,
                                                   yy=ylen, nrad=nrad)
        self.tool.method = meth


class Dmcopy(ImageProcTaskImgOut):
    'CIAO dmcopy tool (to crop image)'

    toolname = 'dmcopy'

    def set_args(self, args):
        'Args: none'
        pass


class Dmregrid2(ImageProcTaskImgOut):
    'CIAO dmregrid2 tool'

    toolname = 'dmregrid2'

    def set_args(self, args):
        'args: xoff yoff rotang xscale yscale x0 y0 method'
        self.tool.xoffset = float(args[0])*-1.0
        self.tool.yoffset = float(args[1])*-1.0
        self.tool.theta = float(args[2])
        self.tool.xscale = float(args[3])
        self.tool.yscale = float(args[4])

        import pycrates as pc
        _i = pc.read_file(self.infile).get_image().values
        _ylen, _xlen = _i.shape

        if "INDEF" == args[5]:
            self.tool.rotxcenter = int(_xlen/2.0)
        else:
            self.tool.rotxcenter = float(args[5])

        if "INDEF" == args[6]:
            self.tool.rotycenter = int(_ylen/2.0)
        else:
            self.tool.rotycenter = float(args[6])

        self.tool.method = args[7]


class Dmimgcalc(ImageProcTaskImgOut):
    'CIAO dmimgcalc tool'

    toolname = 'dmimgcalc'

    def set_args(self, args):
        'Args: task [value]'

        task = args[0]

        if task in ["add", "mul", "sub_c-p", "sub_p-c", "div_c/p", "div_p/c"]:
            # Get fits image from ds9
            self.xpaset_p(['frame', 'prev'])

            infile2 = self.save_ds9_image()
            self.xpaset_p(['frame', 'next'])

            self.infile = self.tool.infile+","+infile2
            self.tool.infile = self.infile

        # pylint doesn't like this many elif's but
        # anything else is too complicated since number of
        # args is different.
        if "add" == task:
            self.tool.op = "imgout=(img1+img2)"
        elif "sub_c-p" == task:
            self.tool.op = "imgout=(img1-img2)"
        elif "sub_p-c" == task:
            self.tool.op = "imgout=(img2-img1)"
        elif "mul" == task:
            self.tool.op = "imgout=(img1*img2)"
        elif "div_c/p" == task:
            self.tool.op = "imgout=(img1/img2)"
        elif "div_p/c" == task:
            self.tool.op = "imgout=(img2/img1)"
        elif "scale" == task:
            self.tool.op = "imgout=(img1*{})".format(args[1])
        elif "offset" == task:
            self.tool.op = "imgout=(img1+{})".format(args[1])
        elif "pow" == task:
            self.tool.op = "imgout=(img1^{})".format(args[1])
        elif "mod" == task:
            self.tool.op = "imgout=(img1%{})".format(args[1])
        elif task in ["acos", "asin", "atan", "acosh", "asinh", "atanh",
                      "cos", "cosh", "exp", "fabs", "ln", "log", "sin",
                      "sinh", "sqrt", "tan", "tanh", "ceil", "floor",
                      "erf", "erfc", "gamma", "lgamma"]:
            self.tool.op = "imgout={}(img1*1.0)".format(task)
        else:
            raise ValueError("Unknown task")


class Wavdetect(ImageProcTaskRegionOut):
    'CIAO wavdetect tool'

    toolname = 'wavdetect'

    def set_args(self, args):
        'Args: scales expfile psffile'
        self.tool.scales = args[0]
        self.tool.scellfile = self.tool.outfile+"_scell"
        self.tool.imagefile = self.tool.outfile+"_reconimg"
        self.tool.defnbkgfile = self.tool.outfile+"_nbkg"
        self.tool.interdir = os.environ["DAX_OUTDIR"]
        self.tool.expfile = args[1][1:].strip('"')  # strip off leading 'e'
        self.tool.psffile = args[2][1:].strip('"')  # strip off leading 'p'
        self.tool.sigthresh = args[3]


class Celldetect(ImageProcTaskRegionOut):
    'CIAO celldetect tool'

    toolname = 'celldetect'

    def set_args(self, args):
        'Args: fixedcell expfile psffile thersh'
        self.tool.fixedcell = int(args[0])
        self.tool.expstk = args[1][1:].strip('"')   # strip off leading 'e'
        self.tool.psffile = args[2][1:].strip('"')  # strip off leading 'p'
        self.tool.thresh = float(args[3])


class Vtpdetect(ImageProcTaskRegionOut):
    'CIAO vtpdetect tool'

    toolname = 'vtpdetect'

    def set_args(self, args):
        'Args (none)'
        self.tool.infile = self.tool.infile+"[opt type=i4]"
        self.tool.expfile = args[0][1:].strip('"')    # strip off leading 'e'
        self.tool.scale = float(args[1])
        self.tool.limit = float(args[2])


class Getsrcregion(ImageProcTaskRegionOut):
    'CIAO get_src_region tool'

    toolname = 'get_src_region'

    def set_args(self, args):
        'Args (none)'
        # gsr clobber doesn't work well
        if os.path.exists(self.tool.outfile):
            os.unlink(self.tool.outfile)
        self.tool.invert = True


class Dmimglasso(ImageProcTaskRegionOut):
    'CIAO dmimglasso tool'

    toolname = 'dmimglasso'

    def set_args(self, args):
        'Args: lowval highval'

        xpos, ypos = self.get_coords()

        self.tool.xpos = xpos
        self.tool.ypos = ypos
        self.tool.low_value = args[0]
        self.tool.high_value = args[1]


class Dmcontour(ImageProcTaskRegionOut):
    'CIAO dmcontour tool'

    toolname = 'dmcontour'

    def set_args(self, args):
        'Args: levels'
        self.tool.levels = args[0]


class Skyfov(ImageProcTaskRegionOut):
    'CIAO skyfov tool'

    toolname = 'skyfov'

    def set_args(self, args):
        'Args: none'
        auxfiles = self.find_aux()
        self.tool.mskfile = auxfiles["mask"]
        self.tool.aspect = auxfiles["asol"]


class Dmellipse(ImageProcTaskRegionOut):
    'CIAO dmellipse tool'

    toolname = 'dmellipse'

    def set_args(self, args):
        'Args: fraction shape'
        self.tool.fraction = args[0]
        self.tool.shape = args[1]
        try:
            regions = self.get_regions().strip()
            self.apply_region_to_infile(regions)
        except RuntimeError:
            pass  # use whole image


class Dmimghull(ImageProcTaskRegionOut):
    'CIAO dmimghull tool'

    toolname = 'dmimghull'

    def set_args(self, args):
        'Args: fraction shape'
        self.tool.tolerance = args[0]
        try:
            regions = self.get_regions().strip()
            self.apply_region_to_infile(regions)
        except RuntimeError:
            pass  # use whole image


class Dmimgproject(ImageProcTaskPlotOut):
    'CIAO dmimgproject tool'

    toolname = 'dmimgproject'

    def set_args(self, args):
        'Args: fraction shape'
        stat = args[0]
        self.tool.axis = args[1]
        try:
            regions = self.get_regions()
            self.apply_region_to_infile(regions)
        except RuntimeError:
            pass   # Use whole image

        cols = "[cols {},{}]".format(self.tool.axis, stat)
        self.plotfile = self.tool.outfile + cols

        self.title = "Project {} Profile {}".format(stat, self.tool.outfile)


class Dmimghist(ImageProcTaskPlotOut):
    'CIAO dmimghist tool'

    toolname = 'dmimghist'

    def set_args(self, args):
        'Args: none'
        try:
            regions = self.get_regions()
            self.apply_region_to_infile(regions)
        except RuntimeError:
            pass   # Use whole image

        self.tool.hist = "1"

        self.plotfile = self.tool.outfile + "[cols bin,counts]"
        self.title = "Pixel Histogram {}".format(self.tool.outfile)


class Imgmoment(ImageProcTaskTextOut):
    'CIAO imgmoment task'

    toolname = 'imgmoment'

    def set_args(self, args):
        'Args: none'
        try:
            regions = self.get_regions()
            self.apply_region_to_infile(regions)
        except RuntimeError:
            pass   # Use whole image

    def send_output(self):
        'Nicely format output'
        print("{:>20s} : {}".format("Total (0th)", self.tool.m_0_0))
        print("{:>20s} : {}, {}".format("Centroid (1st)", self.tool.x_mu,
                                        self.tool.y_mu))
        print("{:>20s} : {}".format("Angle abt centroid", self.tool.phi))
        print("{:>20s} : {}".format("1-sigma in X", self.tool.xsig))
        print("{:>20s} : {}".format("1-sigma in Y", self.tool.ysig))
        print("{:>20s} :".format("Moment matrix"))
        print("{:22s} {:12.5g}\t{:12.5g}\t{:12.5g}".format(" ", self.tool.m_0_0, self.tool.m_0_1, self.tool.m_0_2))
        print("{:22s} {:12.5g}\t{:12.5g}\t{:12.5g}".format(" ", self.tool.m_1_0, self.tool.m_1_1, self.tool.m_1_2))
        print("{:22s} {:12.5g}\t{:12.5g}\t{:12.5g}".format(" ", self.tool.m_2_0, self.tool.m_2_1, self.tool.m_2_2))


class Dmstat(ImageProcTaskTextOut):
    'CIAO dmstat task'

    toolname = 'dmstat'

    def set_args(self, args):
        'Args: none'
        try:
            regions = self.get_regions()
            self.apply_region_to_infile(regions)
        except RuntimeError:
            pass  # Use whole image

        self.tool.centroid = True
        self.tool.median = False
        self.tool.sigma = False
        self.tool.verbose = 0

    def send_output(self):
        '''Nicely format output

        We actually re-run dmstat a 2nd time here since centroid=yes|no
        changes output and we want both.
        '''
        print("{:>20s} : {}".format("Image Axes", self.tool.out_columns))
        print("{:>20s} : {}".format("Centroid (physical)",
                                    self.tool.out_cntrd_phys))

        self.tool.centroid = False
        self.tool.sigma = True
        self.tool.median = True
        self.tool()

        print("{:>20s} : {}".format("Minimum", self.tool.out_min))
        print("{:>20s} : {}".format("Maximum", self.tool.out_max))
        print("{:>20s} : {}".format("Average", self.tool.out_mean))
        print("{:>20s} : {}".format("Sum", self.tool.out_sum))
        print("{:>20s} : {}".format("Median", self.tool.out_median))
        print("{:>20s} : {}".format("Area (pixels)", self.tool.out_good))
        print("{:>20s} : {}".format("NULL pixels", self.tool.out_null))
        print("{:>20s} : {}".format("Coords min pix", self.tool.out_min_loc))
        print("{:>20s} : {}".format("Coords max pix", self.tool.out_max_loc))


class Arestore(ImageProcTaskImgOut):
    'CIAO arestore task'

    toolname = "arestore"

    def set_args(self, args):
        'Args: none'

        # Keep infile for arestore.  Use the
        # filtered file to obtain an estimate of the PSF
        keep_infile = self.tool.infile

        regions = self.get_regions().strip()
        self.apply_region_to_infile(regions)

        # Crop PSF just using dmcopy
        from ciao_contrib.runtool import make_tool
        dmcopy = make_tool("dmcopy")
        dmcopy.infile = self.tool.infile
        dmcopy.outfile = self.tool.outfile+".psf"
        dmcopy(clobber=True)

        self.tool.infile = keep_infile
        self.tool.psffile = dmcopy.outfile
        self.tool.numiter = 20


class Dmfilth(ImageProcTaskImgOut):
    'CIAO dmfilth task'

    toolname = 'dmfilth'

    def set_args(self, args):
        self.tool.method = args[0]

        #
        # Okay, a lot more prep work then the other tasks.  We
        # Get the src and bkg regions via xpa.  We need to be
        # sure separate them and match them up (using dmgroupreg).
        #

        def get_region_flavor(srcbkg):
            'Get region via xpa and add ds9 tag info'

            regout = self.xpaget(["regions", srcbkg, "-format", "ds9",
                                  "-system", "physical", "-strip", "yes"])
            if regout == "":
                raise RuntimeError("No valid {} regions found".format(srcbkg))

            regout = regout.split(";")
            regout = regout[1:]   # Strip off leading 'physical;'
            bkg = srcbkg if srcbkg == "background" else ""
            regout = [xx+" # {} tag={{{}}}".format(bkg, ii)
                      for ii, xx in enumerate(regout)
                      if xx != ""]
            regout = "\n".join(regout)
            return regout

        all_regs = get_region_flavor("source")
        all_regs = all_regs + "\n" + get_region_flavor("background") + "\n"
        all_name = self.tool.outfile+".all.reg"
        src_name = self.tool.outfile+".src.reg"
        bkg_name = self.tool.outfile+".bkg.reg"

        with open(all_name, "w") as fptr:
            fptr.write(all_regs)

        from ciao_contrib.runtool import make_tool
        dmgroupreg = make_tool("dmgroupreg")
        dmgroupreg.infile = all_name
        dmgroupreg.srcoutfile = src_name
        dmgroupreg.bkgoutfile = bkg_name
        dmgroupreg.exclude = False if self.tool.method == "POLY" else True
        dmgroupreg(clobber=True)

        # Stack @- mean never add path
        self.tool.srclist = "@-"+src_name
        self.tool.bkglist = "@-"+bkg_name


class Dmextract(ImageProcTaskPlotOut):
    'CIAO dmextract tool for radial profiles'

    toolname = "dmextract"

    def set_args(self, args):
        'args: units'

        regout = self.xpaget("regions source -format ds9 -system physical")
        ds9_reg = self.tool.outfile+".ds9.reg"
        with open(ds9_reg, "w") as fptr:
            fptr.write(regout)

        ciao_reg = self.tool.outfile+".ciao.reg"

        from ciao_contrib.runtool import make_tool
        convert = make_tool("convert_ds9_region_to_ciao_stack")
        convert.infile = ds9_reg
        convert.outfile = ciao_reg

        try:
            convert(verbose=0, clobber=True)
        except OSError:
            print("ERROR: No valid regions found")
            raise

        keep_infile = self.tool.infile
        self.tool.infile = "{}[bin (x,y)=@-{}]".format(self.tool.infile,
                                                       ciao_reg)
        self.tool.opt = "generic"

        try:
            bkgreg = self.get_regions(src_or_bkg="background").strip()
            if bkgreg:
                self.tool.bkg = f"{keep_infile}[bin (x,y)={bkgreg}]"
        except Exception as bad:
            print("Continuing without background.")

        if 'physical' == args[0]:
            cols = "[cols rmid,sur_bri]"
        elif 'arcsec' == args[0]:
            cols = "[cols cel_rmid,sur_bri]"
        else:
            raise RuntimeError("Unknown units")

        self.plotfile = self.tool.outfile+cols
        self.title = "Radial Profile "+self.tool.outfile


class Dmimgpick(ImageProcTaskPlotOut):
    'CIAO dmimgpick tool'

    toolname = 'dmimgpick'

    def set_args(self, args):
        'Args: method col2plot'

        regout = self.xpaget("regions -format ds9 -system physical")
        polys = [x for x in regout.split("\n") if x.startswith("poly")]
        if not polys:
            raise RuntimeError("No polygons found")

        regfile = self.tool.outfile + ".poly.reg"
        from region import CXCRegion
        # We only want the last polygon
        CXCRegion(polys[-1]).write(regfile, fits=True, clobber=True)

        self.tool.imgfile = self.tool.infile
        self.tool.infile = regfile + "[cols x,y]"
        self.tool.method = args[0]

        cols = "[cols {},#2]".format(args[1])
        self.plotfile = self.tool.outfile + cols
        self.title = "{} pixel values".format(args[0])

    def send_output(self):
        'Need to do a little manip before plotting'

        from ciao_contrib.runtool import make_tool
        dmlist = make_tool("dmlist")
        print(dmlist(self.tool.outfile, op="data,clean,array"))

        from pycrates import read_file
        import numpy as np
        from crates_contrib.utils import add_colvals

        tab = read_file(self.tool.outfile, mode="rw")
        xvals = tab.get_column("x").values
        yvals = tab.get_column("y").values
        meanx = np.average(xvals)
        meany = np.average(yvals)
        radii = np.hypot(xvals-meanx, yvals-meany)
        angles = np.rad2deg(np.arctan2(yvals-meany, xvals-meanx))
        rows = np.ones_like(xvals).cumsum(axis=1)

        add_colvals(tab, "radius", radii, unit="pixels")
        add_colvals(tab, "angle", angles, unit="deg")
        add_colvals(tab, "rownum", rows)
        tab.write()

        super().send_output()


class Ecfcalc(ImageProcTaskPlotOut):
    'Contrib script ecf_calc'

    toolname = 'ecf_calc'

    def set_args(self, args):
        'args: none'

        regout = self.get_regions()

        from region import CXCRegion
        valid_shape = None
        for shape in regout.split("+"):
            if not shape:
                continue

            atreg = CXCRegion(shape).shapes[0]

            if atreg.name not in ['circle', 'ellipse', 'box', 'rotbox']:
                print("Skipping shape='{}'".format(atreg.name))
                continue

            valid_shape = atreg
            self.tool.xpos = atreg.xpoints[0]
            self.tool.ypos = atreg.ypoints[0]
            if atreg.name == 'circle':
                self.tool.radius = atreg.radii[0]
            else:
                from math import sqrt
                rad1 = atreg.radii[0]
                rad2 = atreg.radii[1]
                self.tool.radius = sqrt(rad1*rad1+rad2*rad2)
            break     # Use 1st shape we find.

        if valid_shape is None:
            raise RuntimeError("No valid shapes (circle, ellipse, box) found")

        print("\nUsing region {}\n".format(str(valid_shape)))

        self.tool.binsize = 1.0
        if args[0] == 'default':
            self.tool.fraction = "0.01,0.025,0.05,0.075,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.85,0.9,0.95,0.99"
        else:
            self.tool.fraction = args[0]

        self.plotfile = self.tool.outfile+"[cols r_mid,fraction]"
        self.title = "Enclosed Counts Fraction "+self.tool.outfile

    def send_output(self):
        'Tweak output after plotting'
        super().send_output()
        self.xpaset_p("plot shape circle")
        self.xpaset_p("plot smooth linear")


class Ditherregion(ImageProcTaskPlotOut):
    'CIAO dither_region tool'

    toolname = 'dither_region'

    def set_args(self, args):
        'Args: none ; but this does require files found in hdr'

        auxfiles = self.find_aux()

        regions = self.get_regions()

        self.tool.wcsfile = self.tool.infile
        self.tool.infile = auxfiles["asol"]
        self.tool.region = regions
        self.tool.maskfile = auxfiles["mask"]
        self.tool.ardlib = auxfiles["ardlib"]

        self.plotfile = self.tool.outfile+"[cols time,fracarea]"
        self.title = "Dither Region for {}".format(self.tool.outfile)


class PsfContour(ImageProcTask):
    'CIAO psf_contour tool'

    toolname = 'psf_contour'

    def _convert_sky_to_cel(self):
        from pycrates import read_file

        xpos, ypos = self.get_coords(multi_ok=True)

        # OK to hard code eqpos, must be chandra data anyway
        eqpos_t = read_file(self.tool.infile).get_transform("eqpos")

        xypos = list(zip(xpos, ypos))
        radec = eqpos_t.apply(xypos)
        outfile = self.outfile.name.replace(".fits", "_pos.dat")

        with open(outfile, "w") as fp:
            fp.write("#RA\tDEC\n")
            for r, d in radec:
                fp.write(f"{r}\t{d}\n")

        return outfile

    def set_args(self, args):
        'Args: method, energy, fraction, fovfile'
        self.use_eventfile()

        self.tool.pos = self._convert_sky_to_cel()
        self.tool.outroot = self.outfile.name.replace(".fits", "")
        self.tool.method = args[0]
        self.tool.energy = args[1]
        self.tool.fraction = args[2]
        self.tool.fovfile = args[3]

    def _send_multiple_regions(self, suffix):
        'Display the regions in ds9'

        outroot = self.outfile.name.replace(".fits", "")
        ii = 1
        while True:
            outfile = f'{outroot}_i{ii:04d}_{suffix}'
            if not os.path.exists(outfile):
                break
            self.xpaset_p(f"regions load {outfile}")
            print(f"Loaded region file {outfile}")
            ii += 1

    def send_output(self):
        'Display the regions'
        self._send_multiple_regions("src.reg")


class BkgFixedCounts(PsfContour):
    'CIAO bkg_fixed_counts tool'

    toolname = 'bkg_fixed_counts'

    def set_args(self, args):
        'Args: min_counts fov inner energy max_rad src_stk'

        self.use_eventfile()
        self.tool.pos = self._convert_sky_to_cel()
        self.tool.outroot = self.outfile.name.replace(".fits", "")
        self.tool.min_counts = args[0]
        self.tool.fovfile = args[1]
        self.tool.inner_ecf = args[2]
        self.tool.energy = args[3]
        self.tool.max_radius = args[4]
        self.tool.src_region = args[5]

    def send_output(self):
        'Display the regions'
        self._send_multiple_regions("bkg.reg")


class Reprojectimage(ImageProcTaskImgOut):
    'CIAO reproject_image tool'

    toolname = 'reproject_image'

    def set_args(self, args):
        '''Args: method coords

        matches current frame to the previous frame
        '''

        self.xpaset_p(['frame', 'prev'])
        infile2 = self.save_ds9_image()
        self.xpaset_p(['frame', 'next'])

        self.tool.matchfile = infile2
        self.tool.method = args[0]
        self.tool.coord_sys = args[1]


class Simulatepsf(ImageProcTaskImgOut):
    'Contrib simulate_psf tool'

    toolname = 'simulate_psf'

    def set_args(self, args):
        'args:  energy flux blur niter steak pileup ideal extend'

        import paramio as pio
        randseed = pio.pget("dax", "random_seed")

        xpos, ypos = self.get_coords()
        auxfiles = self.find_aux()

        from ciao_contrib.runtool import make_tool
        dmcoords = make_tool("dmcoords")
        dmcoords(infile=self.tool.infile, op="sky", x=xpos, y=ypos,
                 celfmt="deg")
        self.tool.outroot = self.outfile.name.removesuffix(".fits")
        self.tool.ra = dmcoords.ra
        self.tool.dec = dmcoords.dec
        self.tool.spectrumfile = ""
        self.tool.monoenergy = args[0]
        self.tool.flux = args[1]
        self.tool.blur = args[2]
        self.tool.numiter = args[3]
        self.tool.numsig = 1
        self.tool.minsize = 256
        self.tool.readout_streak = ("1" == args[4])
        self.tool.pileup = ("1" == args[5])
        self.tool.ideal = ("1" == args[6])
        self.tool.extended = ("1" == args[7])
        self.tool.keep = True
        self.tool.asolfile = auxfiles["asol"]
        self.tool.random_seed = randseed
        self.img2display = self.tool.outroot + ".psf"


class Dmcoords(ImageProcTaskTextOut):
    'CIAO dmcoords tool'

    toolname = 'dmcoords'

    def set_args(self, args):
        'Args: none'
        xpos, ypos = self.get_coords()
        self.tool.x = xpos
        self.tool.y = ypos
        self.tool.op = "sky"

    def send_output(self):
        _keep = ['chip', 'tdet', 'det ', 'ra ', 'dec ',
                 'logical', 'theta', 'phi', 'x', 'y']
        out = str(self.tool).split("\n")
        for line in out:
            for keep in _keep:
                if line.strip().startswith(keep):
                    print(line)


class Psfsizesrcs(ImageProcTaskRegionOut):
    'Contrib psfsize_srcs'

    toolname = 'psfsize_srcs'

    def set_args(self, args):
        'Args: energy fraction'

        xpos, ypos = self.get_coords()
        from ciao_contrib.runtool import dmcoords
        dmcoords(self.tool.infile, op="sky", x=xpos, y=ypos)

        ra_dec = "{}, {}".format(dmcoords.ra, dmcoords.dec)
        self.tool.pos = ra_dec
        self.tool.energy = args[0]
        self.tool.ecf = args[1]


class Srcpsffrac(ImageProcTaskTextOut):
    'Contrib src_psffrac script'

    toolname = 'src_psffrac'

    def set_args(self, args):
        'Args: energy'

        regs = self.xpaget("regions source -format ciao -system physical selected")
        if "" == regs:
            regs = self.xpaget("regions source -format ciao -system physical")
            if "" == regs:
                raise RuntimeError("Please draw a source region")

        regs = regs.split("\n")
        regs = [x for x in regs if x[0:3] in ['cir', 'box', 'ell']]
        if len(regs) > 1:
            raise RuntimeError("Please select a single region")
        self.tool.region = regs[0]
        self.tool.energy = args[0]

    def send_output(self):
        from pycrates import read_file
        tab = read_file(self.tool.outfile)
        theta = tab.get_column("theta").values[0]
        phi = tab.get_column("phi").values[0]
        radius = tab.get_column("r").values[0]
        psffrac = tab.get_column("psffrac").values[0]

        outstr = "\n"
        outstr = outstr + "theta: {:.2f}'\t".format(theta)
        outstr = outstr + "phi: {:.2f}deg\t".format(phi)
        outstr = outstr + "radius: {:.2f}pix\t".format(radius)
        outstr = outstr + "energy: {}keV\t".format(self.tool.energy)
        outstr = outstr + "PSFFRAC: {:.4g}\n".format(psffrac)
        print(outstr)


class Glvary(ImageProcTaskPlotOut):
    'CIAO glvary tool'

    toolname = 'glvary'

    def set_args(self, args):
        'args: none'
        self.use_eventfile()
        region = self.get_regions().strip()
        self.apply_region_to_infile(region)
        self.tool.lcfile = self.tool.outfile+".lc"

        self.title = "G-L Lightcurve {}".format(self.tool.lcfile)
        self.plotfile = self.tool.lcfile + "[cols time,count_rate]"


class Pfold(ImageProcTaskPlotOut):
    'CIAO pfold tool'

    toolname = 'pfold'

    def set_args(self, args):
        'args: minperiod maxperiod'
        self.use_eventfile()
        region = self.get_regions().strip()
        self.apply_region_to_infile(region)
        self.tool.periodgrid = "{}:{}:1".format(args[0], args[1])
        self.tool.pdot = 0

        self.title = "Period Fold {}".format(self.tool.outfile)
        self.plotfile = self.tool.outfile+"[cols period,sigma_rate]"


class Dmepha(ImageProcTaskPlotOut):
    'CIAO dmextract tool w/ PHA output'

    toolname = 'dmextract'

    def set_args(self, args):
        'args: none'

        self.use_eventfile()
        keep_infile = self.tool.infile
        try:
            bkgreg = self.get_regions(src_or_bkg="background").strip()
            self.apply_region_to_infile(bkgreg)
            self.tool.bkg = self.tool.infile
            plotcol = "net_rate"
        except RuntimeError:
            self.tool.bkg = ""
            plotcol = "count_rate"

        self.tool.infile = keep_infile
        self.infile = keep_infile
        srcreg = self.get_regions()
        self.apply_region_to_infile(srcreg)

        self.tool.infile = self.tool.infile + "[bin pha=::4]"
        self.tool.opt = "pha1"

        self.plotfile = self.tool.outfile + "[cols channel,{}]".format(plotcol)
        self.title = "PHA Spectrum {}".format(self.infile)


class Dmepi(ImageProcTaskPlotOut):
    'CIAO dmextract tool w/ PI output'

    toolname = 'dmextract'

    def set_args(self, args):
        'args: none'

        self.use_eventfile()
        keep_infile = self.tool.infile
        try:
            bkgreg = self.get_regions(src_or_bkg="background").strip()
            self.apply_region_to_infile(bkgreg)
            self.tool.bkg = self.tool.infile
            plotcol = "net_rate"
        except RuntimeError:
            self.tool.bkg = ""
            plotcol = "count_rate"

        self.tool.infile = keep_infile
        self.infile = keep_infile
        srcreg = self.get_regions()
        self.apply_region_to_infile(srcreg)

        self.tool.infile = self.tool.infile + "[bin pi=::1]"
        self.tool.opt = "pha1"

        self.plotfile = self.tool.outfile + "[cols channel,{}]".format(plotcol)
        self.title = "PI Spectrum {}".format(self.infile)


class Dmetime(ImageProcTaskPlotOut):
    'CIAO dmextract tool w/ TIME output'

    toolname = 'dmextract'

    def set_args(self, args):
        'args: timebin'

        self.use_eventfile()
        keep_infile = self.tool.infile
        try:
            bkgreg = self.get_regions(src_or_bkg="background").strip()
            self.apply_region_to_infile(bkgreg)
            self.tool.bkg = self.tool.infile
            plotcol = "net_rate"
        except RuntimeError:
            self.tool.bkg = ""
            plotcol = "count_rate"

        self.tool.infile = keep_infile
        self.infile = keep_infile
        srcreg = self.get_regions()
        self.apply_region_to_infile(srcreg)

        self.tool.infile = self.tool.infile + "[bin time=::{}]".format(args[0])
        self.tool.opt = "ltc1"

        self.plotfile = self.tool.outfile + "[cols dt,{}]".format(plotcol)
        self.title = "Light Curve {}".format(self.infile)


class Dmeexpno(ImageProcTaskPlotOut):
    'CIAO dmextract tool w/ Expno output'

    toolname = 'dmextract'

    def set_args(self, args):
        'args: binsize'

        self.use_eventfile()
        keep_infile = self.tool.infile
        try:
            bkgreg = self.get_regions(src_or_bkg="background").strip()
            self.apply_region_to_infile(bkgreg)
            self.tool.bkg = self.tool.infile
            plotcol = "net_rate"
        except RuntimeError:
            self.tool.bkg = ""
            plotcol = "count_rate"

        self.tool.infile = keep_infile
        self.infile = keep_infile
        srcreg = self.get_regions()
        self.apply_region_to_infile(srcreg)

        from ciao_contrib.runtool import dmstat
        dmstat(self.tool.infile+"[cols expno]", sigma=False,
               centroid=False, median=False)

        self.tool.infile = self.tool.infile + "[bin expno=:{}:{}]".format(dmstat.out_max, args[0])
        self.tool.opt = "ltc1"

        self.plotfile = self.tool.outfile + "[cols expno,{}]".format(plotcol)
        self.title = "EXPNO Lightcurve {}".format(self.infile)


class Functs(ImageProcTaskTextOut):
    'Net counts akin to funtools functs task'

    toolname = 'dmextract'

    def set_args(self, args):
        'args: none'

        try:
            bkgreg = self.get_regions('background').strip()
            self.tool.bkg = f"{self.tool.infile}[bin (x,y)={bkgreg}]"
            self.my_bkg = bkgreg
        except Exception as bad:
            self.tool.bkg = ""
            self.my_bkg = ""

        # Unlike other tasks, when this task runs with multiple source
        # regions
        #  - anything that is excluded, is excluded from all sources
        #  - if B overlaps A, then B is excluded from A (but A is not modified).
        #  - All background shapes are added together to form a single background
        srcreg = self.get_regions('source').strip()
        from region import CXCRegion
        srcreg = CXCRegion(srcreg)

        # separate include and exclude regions
        incl = [src for src in srcreg if src.shapes[0].include.val == 1]
        xcld = [src for src in srcreg if src.shapes[0].include.val == 0]

        # combine all excluded regions together
        from functools import reduce
        xcld = reduce(lambda aa, bb: aa + bb, xcld, CXCRegion())
        incl2 = [src*xcld for src in incl] if len(xcld) else incl

        # remove overlaps from prior sources
        onlysrc = [incl2[0]]
        for src in incl2[1:]:
            onlysrc.append(src-onlysrc[-1])

        # write to a temp .lis file
        srcstk = NamedTemporaryFile(dir=os.environ["DAX_OUTDIR"],
                                    suffix="_srcreg.lis")
        with open(srcstk.name, "w") as fp:
            for src in onlysrc:
                fp.write(str(src)+"\n")

        self.tool.infile = self.tool.infile + f"[bin (x,y)=@-{srcstk.name}]"
        self.tool.opt = "generic"
        self.srcstk = srcstk

    def send_output(self):
        """
        Because sometime dmlist just won't do
        """

        infile = self.outfile.name
        srcstk = self.srcstk.name
        bkg = self.my_bkg

        def print_tab(cols, units, rows, bkg=False):
            'print out the table values'
            r2 = [[f"{v:<16g}" for v in r] for r in rows]
            if bkg:
                r2 = [r2[0]]

            print("#" + "".join([f"{x:16s}" for x in cols]))
            print("#" + "".join([f"{x:16s}" for x in units]))

            for r in r2:
                print(" " + "".join([f"{x:16s}" for x in r]))

        def get_units_and_rows(cols):
            'get column units and values'
            units = [tab.get_column(x).unit for x in cols]
            vals = [tab.get_column(x).values for x in cols]

            rows = list(zip(*vals))
            return units, rows

        from pycrates import read_file
        tab = read_file(infile)

        _cols = ["COMPONENT", "NET_COUNTS", "NET_ERR", "NET_RATE", "ERR_RATE",
                 "SUR_BRI", "SUR_BRI_ERR", "CEL_BRI", "CEL_BRI_ERR"]
        cols = [x for x in _cols if tab.column_exists(x)]
        units = [tab.get_column(x).unit for x in cols]
        vals = [tab.get_column(x).values for x in cols]

        if bkg:
            sa = tab.get_column("area").values
            ba = tab.get_column("bg_area").values
            bc = tab.get_column("bg_counts").values
            be = tab.get_column("bg_err").values
            bkg_cts = (sa/ba)*bc
            bkg_err = (sa/ba)*be
            bunits = tab.get_column("bg_counts").unit

            idx = cols.index("ERR_RATE")
            idx = idx+1
            cols.insert(idx, "BGREG_ERR")
            cols.insert(idx, "BGREG_COUNTS")
            units.insert(idx, bunits)
            units.insert(idx, bunits)
            vals.insert(idx, bkg_err)
            vals.insert(idx, bkg_cts)

        rows = list(zip(*vals))

        print("#Background subtracted data\n")
        print_tab(cols, units, rows)

        # ----------
        cols = ["COMPONENT", "COUNTS", "ERR_COUNTS", "COUNT_RATE", "COUNT_RATE_ERR", "AREA", "CEL_AREA"]
        cols = [x for x in cols if tab.column_exists(x)]
        units, rows = get_units_and_rows(cols)
        print("\n\n#source region(s):")
        with open(srcstk, "r") as fp:
            for ll in fp.readlines():
                print("#"+ll.strip())
        print("")
        print_tab(cols, units, rows)

        # -------------
        if bkg:
            cols = ["BG_COUNTS", "BG_ERR", "BG_RATE", "BG_AREA"]
            cols = [x for x in cols if tab.column_exists(x)]
            units, rows = get_units_and_rows(cols)
            print("\n\n#background region(s):")
            print("#{}\n".format(bkg))
            print_tab(cols, units, rows, bkg=True)

        print("")
        print("Errors are set to Gaussian 1-sigma.")
        print("Net Counts, Rate, and Errors are approximate.  Use srcflux for a more accurate count rate, error, and upper limit estimation")


class Dmegeneric(ImageProcTaskPlotOut):
    'CIAO dmextract tool generic columns'

    toolname = 'dmextract'

    def set_args(self, args):
        'args: bincol binspec'

        self.use_eventfile()
        keep_infile = self.tool.infile
        try:
            bkgreg = self.get_regions(src_or_bkg="background").strip()
            self.apply_region_to_infile(bkgreg)
            self.tool.bkg = self.tool.infile
            plotcol = "net_counts"
        except RuntimeError:
            self.tool.bkg = ""
            plotcol = "counts"

        self.tool.infile = keep_infile
        self.infile = keep_infile
        srcreg = self.get_regions()
        self.apply_region_to_infile(srcreg)

        binspec = "[bin {}={}]".format(args[0], args[1])

        self.tool.infile = self.tool.infile + binspec
        self.tool.opt = "generic"

        self.plotfile = self.tool.outfile + "[cols {},{}]".format(args[0], plotcol)
        self.title = "Histogram {}".format(self.infile)


class Srcflux(ImageProcTaskTextOut):

    toolname = 'srcflux'


    def set_args(self, args):
        """args:
        bands, model, model_params, absmodel, absmodel_params, psfmethod"""

        self.use_eventfile()
        self.tool.outroot = self.outfile.name.replace(".fits", "")
        os.makedirs(self.tool.outroot, exist_ok=True)
        self.tool.outroot = os.path.join(self.tool.outroot, "out")

        self.tool.bands = args[0]
        self.tool.model = args[1]
        self.tool.paramvals = args[2]
        self.tool.absmodel = args[3]
        self.tool.absparams = args[4]
        self.tool.psfmethod = args[5]

        try:
            srcreg = self.get_regions("source").strip()
        except Exception as bad:
            raise RuntimeError("Source region is required")
        self.tool.srcreg = srcreg

        try:
            bkgreg = self.get_regions("background").strip()
        except Exception as bad:
            raise RuntimeError("Background region is required")
        self.tool.bkgreg = bkgreg

        from region import CXCRegion
        mypos = CXCRegion(srcreg)

        if len(mypos) > 1:
            print("Source region has more than 1 shape. Using coordinates from the first shape only.")

        s0 = mypos.shapes[0]
        if s0.name in ['circle', 'ellipse', 'box', 'point', 'annulus',
                       'pie', 'sector']:
            x0 = s0.xpoints[0]
            y0 = s0.ypoints[0]
        elif s0.name in ['field', 'polygon']:
            raise NotImplementedError("Not ready for these yet")
        elif s0.name in ['rectangle', ]:
            x0 = (s0.xpoints[0]+s0.xpoints[1])/2.0
            y0 = (s0.ypoints[0]+s0.ypoints[1])/2.0
        else:
            raise RuntimeError("Unknown region type")

        from ciao_contrib.runtool import make_tool
        dmcoords = make_tool("dmcoords")
        dmcoords.infile = self.tool.infile
        dmcoords.op = "sky"
        dmcoords.x = x0
        dmcoords.y = y0
        dmcoords.celfmt = "deg"
        dmcoords()

        self.tool.pos = f"{dmcoords.ra},{dmcoords.dec}"
        self.tool.bkgresp = False
        self.tool.verbose = 0

    def send_output(self):

        from glob import glob
        outfile = self.tool.outroot+"_summary.txt"
        with open(outfile,"r") as fp:
            mydat = fp.readlines()

        for dat in mydat:
            print(dat.rstrip())

        print(f"\nOutput files have the root file name: {self.tool.outroot}")

        from paramio import pget
        outfiles = glob(f"{self.tool.outroot}*.flux")
        for outfile in outfiles:
            if "yes" == pget("dax", "prism"):
                self.xpaset_p(["prism", outfile])


class Srcextent(ImageProcTaskTextOut):
    'CIAO srcextent script'

    toolname = 'srcextent'


    def _sim_psf(self, mono_energy):
        import paramio as pio
        randseed = pio.pget("dax", "random_seed")

        xpos, ypos = self.get_coords()
        auxfiles = self.find_aux()

        from ciao_contrib.runtool import make_tool
        dmcoords = make_tool("dmcoords")
        dmcoords(infile=self.infile, op="sky", x=xpos, y=ypos,
                 celfmt="deg")

        simulate_psf = make_tool("simulate_psf")
        simulate_psf.infile = self.infile
        simulate_psf.outroot = self.outfile.name.removesuffix(".fits")
        simulate_psf.ra = dmcoords.ra
        simulate_psf.dec = dmcoords.dec
        simulate_psf.spectrumfile = ""
        simulate_psf.monoenergy = mono_energy
        simulate_psf.flux = 1.0e-3
        simulate_psf.blur = 0.07
        simulate_psf.numiter = 1
        simulate_psf.numsig = 1
        simulate_psf.minsize = 256
        simulate_psf.maxsize = 512
        simulate_psf.readout_streak = False
        simulate_psf.pileup = False
        simulate_psf.ideal = True
        simulate_psf.extended = False
        simulate_psf.keep = True
        simulate_psf.asolfile = auxfiles["asol"]
        simulate_psf.random_seed = randseed
        simulate_psf()

        # Need to use the _i0000.psf file since it has not been normalized
        self.tool.psffile = simulate_psf.outroot+"_i0000.psf"

    def _get_pixel_size_in_arcsec(self):
        'Get pixel size and covert to arcsec'

        def get_delta(names_to_check, scale_name, coord):
            'Get delta for physical and wcs axes'
            sky_name = ""
            for check in names_to_check:
                if check in coord_names:
                    idx = coord_names.index(check)
                    sky_name = img.get_axisnames()[idx]
                    break

            if sky_name == "":
                raise ValueError(f"Cannot find {coord} coordinates")

            xform = img.get_transform(sky_name)
            sky_delta = [x.get_value() for x in xform.get_parameter_list()
                         if scale_name in x.get_name().lower()]
            if len(sky_delta) == 0:
                raise ValueError(f"Cannot get {coord} pixel size")
            
            sky_delta = sky_delta[0]
            if abs(sky_delta[0]) != abs(sky_delta[1]):
                raise ValueError(f"{coord} pixels must be square")

            return abs(sky_delta[0])

        from pycrates import read_file
        img = read_file(self.infile)
        
        coord_names = [x.lower() for x in img.get_axisnames()]
                
        sky_delta = get_delta(["sky", "pos", "(x,y)"], "scale", "physical")
        cel_delta = get_delta(['eqpos', 'eqsrc', 'cel'], "delt", "celestial")

        pixel_size = sky_delta*cel_delta*3600.0
        return pixel_size

    def _get_estimates(self):

        from ciao_contrib.runtool import make_tool

        regions = self.get_regions()
        imgmom = make_tool("imgmoment")
        
        imgmom.infile = f"{self.infile}[(x,y)={regions}]"
        imgmom()
        
        xpos = float(imgmom.x_mu)
        ypos = float(imgmom.y_mu)
        
        mjr = float(imgmom.xsig)
        mnr = float(imgmom.ysig)
        
        from math import sqrt
        logical_size = sqrt(mjr*mjr+mnr*mnr)/sqrt(2.0)

        delta = self._get_pixel_size_in_arcsec()

        logical_size *= delta
        
        return xpos, ypos, logical_size


    def set_args(self, args):
        'args:  makepsf energy'

        if args[0] == "1":
            self._sim_psf(float(args[1]))
        else:
            self.tool.psffile = ""

        regions = self.get_regions()
        
        regfile = self.outfile.name.removesuffix(".fits")+".reg"
        from region import CXCRegion
        CXCRegion(regions).write(regfile, fits=True, clobber=True)

        self.tool.srcfile = f"{self.infile}[(x,y)={regions}]"
        self.tool.regfile = regfile
        self.tool.verbose = 3

        xx, yy, ss = self._get_estimates()
        self.tool.x0 = xx
        self.tool.y0 = yy
        self.tool.srcsize = ss


    def send_output(self):
        'report results, just using verbose=3 output for this tool'
        
        pass
        
