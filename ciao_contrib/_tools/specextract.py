#
#  Copyright (C) 2021, 2023
#        Smithsonian Astrophysical Observatory
#
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#


"""
Routines to support the specextract tool.

"""

__modulename__ = "_tools.specextract"
__toolname__ = "specextract"
__revision__ = "13 November 2023"

import os
import sys

from multiprocessing import cpu_count
import numpy

import cxcdm
import paramio
import stk
import region
import pycrates as pcr

from ciao_contrib._tools import fileio, utils, obsinfo
from ciao_contrib.runtool import make_tool, new_pfiles_environment
from ciao_contrib.logger_wrapper import initialize_logger, make_verbose_level
from ciao_contrib.cxcdm_wrapper import get_block_info_from_file
from ciao_contrib.param_wrapper import open_param_file
from ciao_contrib.proptools import colden

from ciao_contrib.parallel_wrapper import parallel_pool, _check_tty
from sherpa.utils import parallel_map


# Set up the logging/verbose code
initialize_logger(__modulename__)

# Use v<n> to display messages at the given verbose level.
v0 = make_verbose_level(__modulename__, 0)
v1 = make_verbose_level(__modulename__, 1)
v2 = make_verbose_level(__modulename__, 2)
v3 = make_verbose_level(__modulename__, 3)
v4 = make_verbose_level(__modulename__, 4)
v5 = make_verbose_level(__modulename__, 5)

def _set_verbose_progressbar(args,toolname,modulename=None):
    try:
        pfile = open_param_file(args, toolname=toolname)["fp"]
    except Exception:
        sys.exit(1)

    if modulename is None:
        modulename = toolname

    if not _check_tty():
        verb = make_verbose_level(modulename, 1)
    elif paramio.pgetstr(pfile,"parallel").lower() == "no" and paramio.pgeti(pfile, "verbose") == 1:
        verb = make_verbose_level(modulename, 2)
    else:
        verb = make_verbose_level(modulename, 2)

    paramio.paramclose(pfile)

    return verb

vprogress = _set_verbose_progressbar(sys.argv,toolname=__toolname__,modulename=__modulename__)



class suppress_stdout_stderr(object):
    #########################################################
    #
    # suppress warnings printed to screen from get_keyvals
    # when probing for blank sky files
    #
    #########################################################
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.

    This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
    '''

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close the null files
        for fd in self.null_fds + self.save_fds:
            os.close(fd)



class ParDicts(object):
    def __init__(self,params):
        self.params = params

        self.infile = params["infile"]
        self.outroot = params["outroot"]
        self.weight = params["weight"]
        self.weight_rmf = params["weight_rmf"]
        self.correct = params["correctpsf"]
        self.combine = params["combine"]
        self.bkgfile = params["bkgfile"]
        self.bkgresp = params["bkgresp"]
        self.asp = params["asp"]
        self.resp_pos = params["resp_pos"]
        self.refcoord = params["refcoord"]
        self.rmffile = params["rmffile"]
        self.streakspec = params["streakspec"]
        self.ptype = "PI" #params["ptype"]
        self.gtype = params["gtype"]
        self.gspec = params["gspec"]
        self.bggtype = params["bggtype"]
        self.bggspec = params["bggspec"]
        self.ebin = params["ebin"]
        self.channel = params["channel"]
        self.ewmap = params["ewmap"]
        self.binwmap = params["binwmap"]
        self.bintwmap = params["binarfwmap"]
        self.binarfcorr = params["binarfcorr"]
        self.dtffile = params["dtffile"]
        self.mask = params["mskfile"]
        self.dafile = params["dafile"]
        self.bpixfile = params["bpixfile"]
        self.tmpdir = params["tmpdir"]
        self.clobber = params["clobber"]
        self.verbose = params["verbose"]
        self.mode = params["mode"]

        self.wmap_clip = params["wmap_clip"]
        self.wmap_threshold = params["wmap_threshold"]

        if params["parallel"].lower() == "no":
            self.nproc = "1"

        if not params["nproc"].isnumeric():
            self.nproc = cpu_count()
        else:
            self.nproc = int(params["nproc"])


    def _asol_asphist(self,asp_stk,asp_cnt,src_stk):
        """
        Determine if asphist or asol files were input
        to the 'asp' parameter and build the appropriate
        stack accordingly. (Must check all files since
        the invoked tool 'asphist' won't complain if
        histogram files are incorrectly input.)
        """

        src_cnt = len(src_stk)
        asptype = self._get_keyvals(asp_stk, "CONTENT")

        if all(["ASPHIST" in asptype,
                any(["ASPSOL" in asptype, "ASPSOLOBI" in asptype, "ASPSOL3" in asptype])
        ]):
            raise IOError("A mix of aspect solution and histogram files \
were entered into 'asp'; please enter one or a list of either type, not both.\n")

        if all(["ASPHIST" not in asptype, "ASPSOL" not in asptype,
                "ASPSOLOBI" not in asptype, "ASPSOL3" not in asptype
        ]):
            raise IOError("Neither aspect histogram nor aspect solution \
files were found in the 'asp' input. Either the ASPHIST/asphist or ASPSOL \
FITS HDU is not in the expected place - which could cause the CIAO tools \
invoked by this script to fail - or a filename was entered incorrectly or \
does not exist. Exiting.\n")

        if "ASPHIST" in utils.getUniqueSynset(asptype):
            asol = False
            ahist = True
        else:
            asol = True
            ahist = False

        if ahist and asp_cnt not in (1,src_cnt):
            raise IOError(f"Error: asp stack must have either 1 element or the same number \
of elements as the source stack.  Source stack={src_cnt}    asp stack={asp_cnt}")

        if asol:
            # Build the aspect solution ('asol') file stack:
            if asp_cnt != 1 and src_cnt != 1:

                # Compile lists of the OBS_IDs found in the
                # input source and asol file headers, exiting with
                # an error if the requisite OBS_ID information
                # is not found or is mismatched.

                src_obsid_stk = self._get_keyvals(src_stk, "OBS_ID")
                asol_obsid_stk = self._get_keyvals(asp_stk, "OBS_ID")

                if any([None in src_obsid_stk, None in asol_obsid_stk]):
                    raise ValueError("OBS_ID information could not be found in source \
and/or aspect solution files; cannot properly match source files to \
aspect solution files. Try entering aspect histogram files into \
'asp' to work around this requirement.")

                # Quit with an error if any of the source file OBS_ID
                # values are not found in the list of asol OBS_IDs.

                for i in range(src_cnt):
                    if str(src_obsid_stk[i]) not in asol_obsid_stk:
                        raise IOError(f"No aspect solution files provided for {src_stk[i]}.")

            if asp_cnt != 1 and src_cnt == 1:
                asp_stk = self._sort_files(utils.getUniqueSynset(asp_stk), "aspsol", "TSTART")
                asp_stk = ",".join(asp_stk)

            asp_stk = self.group_by_obsid(asp_stk,"aspsol")
            v3(f"ObsIDs matched to aspect solution files: \n{asp_stk}")

        if not ahist and not asol:
            asp_stk = [""]
            asp_cnt = len(asp_stk)

        return asp_stk,asp_cnt,asol,ahist


    def _build_srcbkg_stk(self, infpar, checkreg=True):
        """
        return stack list generated by input parameter, otherwise an empty list
        """

        if all([infpar, infpar.lower() not in [""," ","none"]]):

            # handle a stack of regions, but single input file, in
            # the format: "evt.fits[sky=@reg.lis]", assume no other
            # dmfilter included

            if checkreg and all([get_region_filter(infpar)[0], get_region_filter(infpar)[1].startswith("@")]):
                regfile = get_region_filter(infpar)[1]
                regfilter = fileio.get_filter(infpar)
                fi = self._get_filename(infpar)
                regcoord = regfilter.strip("[]").replace(regfile,"").replace("=","")

                regstk = stk.build(regfile)

                fn_stk = [f"{fi}[{regcoord}={region}]" for region in regstk]

                del fi, regfile, regfilter, regcoord, regstk

            else:
                fn_stk = stk.build(infpar)

            for fn in fn_stk:
                if "\r" in fn:
                    inf = infpar.strip("@")
                    raise IOError(f"EOL: the line ends in the ASCII stack file, '{inf}', using \
Windows/DOS-style carriage return & line feed (CRLF) rather than Unix-compatible line feed only.")

        else:
            fn_stk = []

        return fn_stk


    def _check_files(self,stack,filetype):
        """
        Check to see if each file in the input stack is readable.
        """

        count = len(stack)
        if count == 1:
            suffix = ""
        else:
            suffix = "s"

        v2(f"Checking {filetype} file{suffix} for readability...")

        for s in stack:
            filename = s
            v2(f"  validating file: {filename}")

            if filename.upper() in ["CALDB","NONE"]:
                v3("  ... skipping")
                continue

            v3("  ... checking if it exists")

            try:
                table = cxcdm.dmTableOpen(filename)

            except IOError as exc:
                raise IOError(f"{filetype} file {filename} does not exist or could not be opened.") from exc

            cxcdm.dmTableClose(table)


    def _get_filename(self,full_filename):
        """
        Pass in the full filename
        i.e.  dir/source.fits[sky=region(dir/source.reg)]
        and return the filename w/o filter
        i.e.  filename = dir/source.fits
        """

        # filename = filename w/o filter

        #
        # NB: strip off the filter by scanning the string
        # until the first "[", "'[", or ""[".
        #

        brack = "["
        squot_brack = "'["
        dquot_brack = "\""+"["

        if dquot_brack in str(full_filename):
            filename = full_filename.split(dquot_brack)[0]

        elif squot_brack in str(full_filename):
            filename = full_filename.split(squot_brack)[0]

        else:
            filename = full_filename.split(brack)[0]

        if not _check_filename_set(filename):
            return None

        return filename


    def _check_file_pbkheader(self,headerkeys):
        """
        check the input file header contains keywords that were found
        in the PBK file introduced in Repro IV.
        """

        ## pbkkeys are: 'OCLKPAIR', 'ORC_MODE', 'SUM_2X2', 'FEP_CCD'
        ## asol-derived keys are: 'DY_AVG', 'DZ_AVG', 'DTH_AVG'

        pbk_kw = ("OCLKPAIR","ORC_MODE","SUM_2X2","FEP_CCD")
        # asp_kw = ["DY_AVG","DZ_AVG","DTH_AVG"]

        file_status = True

        if headerkeys["INSTRUME"] == "ACIS":
            try:
                verify_keys = []

                verify_keys.extend([headerkeys.has_key(kw) for kw in pbk_kw])

                if False in verify_keys:
                    v1(f"WARNING: {fileio.remove_path(headerkeys['inf'])} missing header keywords.\n")

                    file_status = False

            except AttributeError:
                pbk_kw_list = list(pbk_kw)

                verify_keys = headerkeys.keys() & pbk_kw_list # find elements in common

                for s in verify_keys:
                    pbk_kw_list.remove(s)

                if len(pbk_kw_list) != 0:
                    v1(f"WARNING: {fileio.remove_path(headerkeys['inf'])} missing header keywords.\n")

                    file_status = False

        if not file_status:
            raise IOError("Input event file(s) missing necessary Repro IV header keywords.  Reprocess \
data with chandra_repro or add the keywords to the event file(s) with r4_header_update.")


    def _get_keyvals(self,stack,keyname):
        """
        return keys
        """

        keys = []

        for fn in stack:
            try:
                kval = fileio.get_keys_from_file(f"{fn}[#row=0]")[keyname]
            except KeyError:
                v1(f"WARNING: The {keyname} header keyword is missing from {fn}")
                kval = None

            keys.append(kval)

        return keys


    def _check_event_stats(self,file,refcoord_check=None,
                           weights_check=None,ewmap_range_check=None):
        """
        Use dmlist to determine the event counts
        and appropriately error out or proceed with the script
        """

        with new_pfiles_environment(ardlib=False,copyuser=False):
            dmlist = make_tool("dmlist")

            dmlist.punlearn()

            if ewmap_range_check is None:
                dmlist.infile = file
            else:
                dmlist.infile = f"{file}[energy={ewmap_range_check}]"

            dmlist.opt = "counts"

            counts = dmlist()

        if counts == "0":
            try:
                if refcoord_check.lower() in ["","none","indef"]:
                    raise IOError(f"{file} has zero counts. Check that the region correct (e.g. wrong region, coordinates not in sky pixels or degrees).")

                if weights_check:
                    v1("WARNING: Unweighted responses will be created at the 'refcoord' position.\n")
                else:
                    v1("WARNING: Using 'refcoord' position to produce response files.\n")

            except AttributeError as exc:
                if ewmap_range_check is not None:
                    ## do we want to error out if the number of counts is
                    ## smaller than some magic count, instead of just zero?

                    raise IOError(f"{file} has zero counts in the \
'energy_wmap={ewmap_range_check}' eV range needed to generate a weights map.") from exc

            return False

        return True


    def _event_stats(self,file,colname,args=None):
        """
        Use dmstat to determine the event statistics: source chipx,
        chipy, sky x, sky y, and ccd_id values to use for input
        to asphist, acis_fef_lookup, and arfcorr.
        Since dmstat doesn't return the mode, do this by brute force
        for ccd_id column (psextract algorithm uses mean ccd_id value,
        which isn't appropriate for this quantity).
        """

        if colname in ["x","y","chipx","chipy"]:
            if colname in ["x","y"]:
                bin_setting = "[bin sky=2]"

            if colname in ["chipx","chipy"]:
                bin_setting = "[bin chipx=2,chipy=2]"

            if args is not None:
                if args["weight"] == "no" and args["correct"] == "yes":
                    binarfcorr = max(args["binarfcorr"], 1) # if binarfcorr < 1, set to 1

                    if colname in ["x","y"]:
                        bin_setting = f"[bin sky={binarfcorr}]"

                    if colname in ["chipx","chipy"]:
                        bin_setting = f"[bin chipx={binarfcorr},chipy={binarfcorr}]"


            with new_pfiles_environment(ardlib=False,copyuser=False):
                dmstat = make_tool("dmstat")

                dmstat.punlearn()
                dmstat.verbose = 0

                dmstat(f"{file}{bin_setting}")

                src_x,src_y = dmstat.out_max_loc.split(",")

            if colname == "x":
                return src_x

            if colname == "y":
                return src_y

            if colname == "chipx":
                return int(float(src_x))

            if colname == "chipy":
                return int(float(src_y))

        if colname in ["ccd_id", "chip_id"]:
            # Use pycrates to retrieve ccd_id/chip_id values from user-input event
            # extraction region. Compute the mode of the ccd_id/chip_id values
            # stored in the array.

            cr = pcr.read_file(file)

            if cr is None:
                raise IOError(f"Unable to read from file {file}")

            vals = cr.get_column(colname).values

            chips,counts = numpy.unique(vals,return_counts=True)

            mode = chips[counts.tolist().index(max(counts))]

            del cr

            return mode

        return None


    def _valid_regstr(self,inf):
        """
        validate region filter string
        """

        regfilter = fileio.get_filter(inf)

        if any(["=(" in regfilter, "(" not in regfilter]):
            raise IOError(f"There is a problem with the extraction region syntax in: {inf}")


    def _check_region_crlf(self,inf):
        """
        ensure the ASCII region file is in Unix compatible line feed format
        rather than Windows carriage return & line feed (CRLF) format
        """

        regfilter = fileio.get_filter(inf)

        if "=region(" in regfilter:
            regfiles = [s[:s.index(")")].replace("region(","") for s in regfilter.split("=") if s.startswith("region(")]

            for regfile in regfiles:
                ## check if region is FITS or text format ##
                try:
                    with open(regfile, mode="rt") as binarycheckfile:
                        binarycheckfile.read() # a FITS/binary file will throw a UnicodeDecodeError
                                               # when opened in 'read-text' mode then read()

                    with open(regfile, mode="rb") as r:
                        if b"\r\n" in r.read():
                            ## n.b.: modify region file by doing
                            ## `cat regfile | tr -d '\015' > regfile.lf-only`
                            raise IOError(f"EOL: the line ends in the ASCII region file, '{regfile}', \
using Windows/DOS-style carriage return & line feed (CRLF) rather than \
Unix-compatible line feed only.")

                except FileNotFoundError:
                    raise IOError(f"region file '{regfile}' not found") from None

                except UnicodeDecodeError:
                    pass


    def _get_region(self,full_filename):
        """
        Pass in the full filename
        i.e.  dir/source.fits[sky=region(dir/source.reg)]
        and return the region without filename or filter
        i.e.  region = source.reg
        for use in correct_arf() function
        """

        # region = region without filename or filter syntax

        #
        # NB: strip off the filename by splitting the string
        # at "sky=", and then cleaning up the dm filter portion
        # of this result.
        #

        if "region" in get_region_filter(full_filename)[1]:
            reg = get_region_filter(full_filename)[1].split("(")[1]
            reg = reg[:reg.find(")")]
        else:
            reg = get_region_filter(full_filename)[1]

        if not _check_filename_set(region):
            return None

        return reg


    def _sort_files(self, file_stack, file_type, key):
        """
        Sort a list of files by the value of a given keyword; e.g., for sorting
        a stack of aspect solution files on TSTART before input to mk_asphist().
        """

        keyvals_orig_order = self._get_keyvals(file_stack, key)

        if None in keyvals_orig_order:
            raise IOError(f"One or more of the entered {file_type} files is missing the required {key} header keyword value. Exiting.")

        keyvals_sorted = sorted(keyvals_orig_order) #be sure numbers are not strings

        # files_sorted = []
        #
        # for k in keyvals_sorted:
        #     sort_ind = keyvals_orig_order.index(k)
        #     files_sorted.append(file_stack[sort_ind])

        files_sorted = [file_stack[keyvals_orig_order.index(k)] for k in keyvals_sorted]

        return files_sorted


    def group_by_obsid(self,file_stack,file_type):
        """
        Read the OBS_ID value from the header of each file in the input stack
        in order to create a dictionary matching each ObsID to one or a list of
        files. Then, this dictionary can be used by other functions in the script
        to assign the appropriate file(s) (e.g., asol) to each source observation,
        by obsid.
        """

        if all([isinstance(file_stack,str), "," in file_stack]):
            file_stack = file_stack.split(",")

        file_count = len(file_stack)

        obsids = self._get_keyvals(file_stack, "OBS_ID")


        if None in obsids:
            raise IOError(f"One or more of the entered {file_type} files is \
missing an OBS_ID header keyword value or it exists but contains \
an unexpected value, therefore files cannot be grouped by ObsID \
and properly matched to input source files. Exiting.")
            # can be just a warning for certain file types, but right now this
            # function is just used for asol

        obsid_sort = sorted(obsids) # be sure numbers are not strings

        orig_files = list(range(file_count))
        for i in range(file_count):
            orig_files[i] = file_stack[i]

        sorted_files = list(range(file_count))
        for i in range(file_count):
            sort_ind = obsids.index(obsid_sort[i])
            sorted_files[i] = orig_files[sort_ind]


        if file_type != "aspsol":

            obsid_dict = {}
            for i in range(file_count):
                if obsid_sort[i] in obsid_dict:
                    obsid_dict[obsid_sort[i]] = f"{obsid_dict[obsid_sort[i]]},{sorted_files[i]}"
                else:
                    obsid_dict[obsid_sort[i]] = sorted_files[i]

            return obsid_dict

        # else (None not in obsids) #
        asol_tstart = self._get_keyvals(file_stack, "TSTART")

        if None in asol_tstart:
            raise IOError("One or more of the entered aspect solution files is missing a TSTART \
header keyword value, therefore files cannot be properly sorted and matched to input \
source files. Exiting.")

        asol_tstart_sort = sorted(asol_tstart) # be sure numbers are not strings

        sort_asolfiles = list(range(file_count))
        asol_obsid_sort = list(range(file_count))

        for i in range(file_count):
            tsort_ind = asol_tstart.index(asol_tstart_sort[i])
            sort_asolfiles[i] = orig_files[tsort_ind]
            asol_obsid_sort[i] = obsids[tsort_ind]

        asol_dict={}
        for i in range(file_count):
            if asol_obsid_sort[i] in asol_dict:

                asol_sort = f"{asol_dict[asol_obsid_sort[i]]},{sort_asolfiles[i]}".replace(" ","").split(",")
                unique_asol_sort = ",".join(utils.getUniqueSynset(asol_sort))

                if len(asol_sort) != len(unique_asol_sort):
                    v3("WARNING: Duplicate aspect solutions provided.")

                asol_dict[asol_obsid_sort[i]] = unique_asol_sort
            else:
                asol_dict[asol_obsid_sort[i]] = sort_asolfiles[i]

        return asol_dict


    def get_resp_pos(self,infile,asol,srcbkg,dobkgresp,resp_pos,refcoord,binimg=2):
        """
        determine coordinates to use to produce responses
        """

        with new_pfiles_environment(ardlib=False,copyuser=False):
            ## infile = "full filename"
            dmcoords = make_tool("dmcoords")

            dmcoords.punlearn()
            dmcoords.infile = infile
            dmcoords.asolfile = asol
            dmcoords.celfmt = "deg"

            if refcoord != "":
                # returns RA and Dec in decimal degrees
                ra,dec,delme = utils.parse_refpos(refcoord.replace(","," "))

                dmcoords.opt = "cel"
                dmcoords.ra = ra
                dmcoords.dec = dec

            else:
                ## parse infile region ##
                if self._get_region(infile) == infile:
                    raise IOError("No region filter with the event file, nor a refcoord \
value, provided to produce response files.")

                if resp_pos.lower() in ["centroid","max"]:
                    dmstat = make_tool("dmstat")

                    dmstat.punlearn()
                    dmstat.infile = f"{infile}[bin sky={binimg}]"
                    dmstat.verbose = 0
                    dmstat.centroid = True
                    dmstat()

                    ## get centroided sky position ##
                    if resp_pos.lower() == "centroid":
                        skyx,skyy = dmstat.out_cntrd_phys.split(",")

                        # if centroid falls in a zero-count location, NaN's will be returned
                        if 'nan' in [skyx,skyy]:
                            raise ValueError("Region centroiding failed, please select \
another 'resp_pos' method to determine the position to calculate the unweighted responses.")

                    ## get sky position using maximal location encompassed by the region ##
                    else:
                        skyx,skyy = dmstat.out_max_loc.split(",")

                else:
                    try:
                        if resp_pos.lower() == "regextent":
                            ## determine response location using center of region extent ##
                            regext = region.CXCRegion(pcr.read_file(f"{infile}[#row=0]").get_subspace_data(1,"sky").region).extent()

                            skyx = 0.5*(regext["x0"] + regext["x1"])
                            skyy = 0.5*(regext["y0"] + regext["y1"])

                        if resp_pos.lower() == "region":
                            regcent = region.CXCRegion(pcr.read_file(f"{infile}[#row=0]").get_subspace_data(1,"sky").region)

                            if len(regcent) > 1 and not all([srcbkg == "bkg", not dobkgresp]):
                                v1("Warning: more than 1 shape found, using the coordinates of the first defined shape")

                            if regcent.shapes[0].name.lower() in ["polygon","rectangle"]:
                                skyx = numpy.mean(regcent.shapes[0].xpoints)
                                skyy = numpy.mean(regcent.shapes[0].ypoints)
                            else:
                                skyx = regcent.shapes[0].xpoints[0]
                                skyy = regcent.shapes[0].ypoints[0]

                    except KeyError as exc:
                        raise IOError(f"'resp_pos={resp_pos}': The use of pixel masks can only be used \
when 'resp_pos' is set to 'MAX' or 'CENTROID'.") from exc

                #######################################################
                # ## ... or ...
                # ## use get_sky_limits instead of region module since it's
                # ## agnostic on coordinates used for extraction region
                #
                # get_sky_limits = make_tool("get_sky_limits")
                #
                # get_sky_limits.punlearn()
                #
                # get_sky_limits.image = f"{infile}[bin sky={binimg}]"
                # get_sky_limits.precision = numpy.abs(numpy.floor(numpy.log10(binimg))) + 2
                # get_sky_limits.verbose = 0
                # get_sky_limits()
                #
                # x,y = get_sky_limits.xygrid.split(",")
                # x = [float(n) for n in x.split(":")[:-1]]
                # y = [float(n) for n in y.split(":")[:-1]]
                #
                # skyx = 0.5*(x[0]+x[1])
                # skyy = 0.5*(y[0]+y[1])
                #
                #######################################################

                # convert to chip coordinates
                dmcoords.opt = "sky"
                dmcoords.x = skyx
                dmcoords.y = skyy

            dmcoords()

            skyx = str(dmcoords.x)
            skyy = str(dmcoords.y)

            chipx = str(int(dmcoords.chipx))
            chipy = str(int(dmcoords.chipy))

            chip_id = str(dmcoords.chip_id)

            ra = float(dmcoords.ra)
            dec = float(dmcoords.dec)

        return ra,dec,skyx,skyy,chipx,chipy,chip_id


    def check_fp_temp(self,kwdict,inf,ebin):
        """
        check focal plane temperature, if >-109C prior to 2000-01-29T20:00:00
        (Chandra Time: 65563201), then check FEF energy range for mkrmf
        """

        #####################################################################################
        #
        # ObsID 114 (observed 2000-01-30 10:40:42) is first observation made at <-119C.
        #
        # mkarf/mkrmf automatically creates response in the available energy range
        # in the FEF file for unweighted responses
        #
        #####################################################################################

        v3("Checking detector focal plane temperature\n")

        mkrmf_tstop = 65563201

        fp_temp = kwdict["FP_TEMP"] - 273.15 # convert from Kelvin to Celsius
        tstart = kwdict["TSTART"]

        if fp_temp > -109 and tstart < mkrmf_tstop:
            v3("Checking FEF energy range for warm observation")

            with new_pfiles_environment(ardlib=False,copyuser=False):
                acis_fef_lookup = make_tool("acis_fef_lookup")

                acis_fef_lookup.punlearn()
                acis_fef_lookup.infile = inf
                acis_fef_lookup.chipid = "none"
                acis_fef_lookup.verbose = 0

                try:
                    acis_fef_lookup()
                except OSError as err_msg:
                    v1(err_msg)
                    self._check_file_pbkheader(kwdict)

                fef = acis_fef_lookup.outfile

            cr_fef = pcr.read_file(fef)
            fef_energy = cr_fef.get_column("ENERGY").values
            del cr_fef

            fef_emin = min(fef_energy)
            fef_emax = max(fef_energy)

            ebin_min,ebin_max,ebin_de = ebin.split(":")

            fef_estat = (float(ebin_min) >= fef_emin, float(ebin_max) <= fef_emax)

            if fef_estat != (True,True):
                raise ValueError(f"ObsID {kwdict['OBS_ID']} was made at a warm \
focal plane temperature, >-109C before 2000-01-29T20:00:00.  The \
available calibration products are valid for an energy range of \
{fef_emin:.3f}-{fef_emax:.3f} keV while the 'energy' parameter has \
been set to {ebin_min}-{ebin_max} keV (energy={ebin})") # the ":.3f" in the format prints up to three decimal places of the float


    def _check_merged_input(self,kwdict,toolname):
        """
        check if the input file has been merged using its header keywords
        """

        keys_to_check = ['TITLE', 'OBSERVER', 'OBJECT', 'OBS_ID', 'DS_IDENT']

        for mkey in keys_to_check:
            if mkey in kwdict and kwdict[mkey].lower() == "merged":
                raise IOError(f"Merged data sets are unsupported by {toolname}.  \
Merged events files should not be used for spectral analysis.") # or v1 warning?


    def _check_ppr(self,kwdict,toolname):
        """
        check if the input file has been generated by psf_project_ray
        """

        if kwdict["HDUNAME"].lower() != "rayevent":
            return

        for key,val in kwdict.items():
            if not key.upper().startswith("HDUCLAS") or val.lower() != "psfray":
                continue

            raise IOError(f"Event files generated by psf_project_ray are not supported by {toolname}.")


    def _check_blanksky(self,headerkeys,srcbkg_kw,bkgresp):
        """
        Check inputs for header indicators of blanksky files.
        Throw warning or error out as necessary
        """

        v3("Checking for blanksky background files...")

        # check for blank sky files and Maxim's bg files, error out if found:
        with suppress_stdout_stderr():
            try:
                blanksky = headerkeys["CDES0001"]
            except (KeyError,AttributeError):
                blanksky = None

            try:
                mm_blanksky = headerkeys["MMNAME"]
            except (KeyError,AttributeError):
                mm_blanksky = None

        if srcbkg_kw == "background":
            if blanksky is not None and "blank sky event" in blanksky.lower():
                if bkgresp == "yes":
                    raise IOError("Cannot create responses for spectra from blanksky background files.\n")

                v1("WARNING: Extracting background spectra from blanksky background files.\n")

            if mm_blanksky is not None and all([mm_blanksky.lower().startswith("acis"),
                                                "_bg_evt_" in mm_blanksky.lower()]):
                if bkgresp == "yes":
                    raise IOError("Cannot create responses for spectra from M.M. ACIS blanksky background files.\n")

                v1("WARNING: Extracting background spectra from M.M. ACIS blanksky background files.\n")

        else:
            if blanksky is not None and "blank sky event" in blanksky.lower():
                raise IOError("Cannot use blanksky background files as infile, since responses cannot be produced.\n")

            if mm_blanksky is not None and all([mm_blanksky.lower().startswith("acis"),
                                                "_bg_evt_" in mm_blanksky.lower()]):
                raise IOError("Cannot use M.M. ACIS blanksky background files as infile, since responses cannot be produced.\n")


    def _check_streakspec(self,weight,refcoord,instrument):
        if instrument.upper() != "ACIS":
            raise IOError("Readout streak spectrum extraction can only be done with ACIS TE-mode observations.")

        if weight == "yes":
            raise IOError("Readout streak spectrum requires unweighted responses, set 'weight=no'.")

        if refcoord == "":
            raise IOError("Readout streak spectrum requires source postion to generate response using the 'refcoord' parameter.")


    def paralleltests(self,parallelfunc,args,method="map",numcores=None):
        """
        run various parameter test functions in parallel
        """

        if method.lower() == "map":
            status = parallel_map(parallelfunc,args,numcores=numcores)
        elif method.lower() == "pool":
            status = parallel_pool(parallelfunc,args,ncores=numcores)
        else:
            status = [parallelfunc(f) for f in args] # do things serially

        for stat in status:
            if isinstance(stat,Exception):
                raise stat


    def check_input_stacks(self,infile,bkgfile,outroot,weight,bkgresp,refcoord,streakspec,ebin,nproc):
        """
        Build stacks for the file input parameters; make sure they are
        readable and not empty.
        """

        ### source stack ###
        src_stk = self._build_srcbkg_stk(infile)
        src_count = len(src_stk)

        ### background stack ###
        bkg_stk = self._build_srcbkg_stk(bkgfile)
        bkg_count = len(bkg_stk)

        ### outroot stack ###
        out_stk = self._build_srcbkg_stk(outroot,checkreg=False)
        out_count = len(out_stk)

        if out_count == 0:
            out_stk = [""]

        ### error out if there are spaces in absolute paths of the stacks ###
        fn_dict_stk = [*[{"source" : s} for s in src_stk], *[{"background" : b} for b in bkg_stk]]

        for path in [*fn_dict_stk, *[{"outroot" : o} for o in out_stk]]:
            for key,fn in path.items():
                if " " in os.path.abspath(fn):
                    raise IOError(f"The absolute path for the {key.replace('source','input')} file, \
'{os.path.abspath(fn)}', cannot contain any white spaces")

        #####################################################################################
        #
        # check that region extraction syntax does not take the erroneous form:
        # "sky=(src.reg)" or "sky=src.reg" which can lead to unexpected results
        # and very long run times
        #
        # combine source and background into a set (to eliminate duplicates)
        # and validate in a single pass
        #
        #####################################################################################

        fn_stk = numpy.ravel([[{"filename" : fn, "check" : "regstr"},{"filename" : fn, "check" : "crlf"}] for fn in set(src_stk).union(bkg_stk)])

        def parallel_region_check(args):
            fn = args["filename"]
            check = args["check"]

            try:
                if check == "crlf":
                    self._check_region_crlf(fn)

                if check == "regstr":
                    self._valid_regstr(fn)

            except Exception as E:
                return E

            return None

        self.paralleltests(parallel_region_check,fn_stk,method="map",numcores=nproc)

        # for fn in set(src_stk).union(bkg_stk):
        #     self._valid_regstr(fn)
        #     self._check_region_crlf(fn)


        ### check files in source and background stacks ###
        fn_header_stk = [{k : {**fileio.get_keys_from_file(f"{fileio.get_file(fn)}[#row=0]"),
                               "inf" : fileio.get_file(fn)}}
                         for sd in fn_dict_stk for k,fn in sd.items()]

        for d in fn_header_stk:
            for srcbkg_kw,headerkeys in d.items():

                ## check for CTI_APP keyword
                try:
                    cti_app_val = headerkeys["CTI_APP"]

                    if cti_app_val.upper() == "NONE":
                        raise IOError(f"File {headerkeys['inf']} is missing a \
CTI_APP header keyword, required by many CIAO tools; an ARF will not be created. \
Try re-running specextract after reprocessing your data.\n")

                except KeyError as exc:
                    if headerkeys["INSTRUME"] == "HRC":
                        pass
                    else:
                        if srcbkg_kw == "source" or all([srcbkg_kw == "background", bkgresp == "yes"]):
                            raise IOError(f"File {headerkeys['inf']} is missing a \
CTI_APP header keyword, required by many CIAO tools; an ARF will not be created. \
Try re-running specextract after reprocessing your data.\n") from exc

                ## check for event files generated by psf_project_ray
                self._check_ppr(headerkeys,__toolname__)

                ## check for CC-mode data and throw warning
                if headerkeys["INSTRUME"] == "ACIS" and headerkeys["READMODE"].upper() == "CONTINUOUS":
                    v1(f"WARNING: Observation taken in CC-mode.  {__toolname__} may \
provide invalid responses for {headerkeys['inf']}.  Use rotboxes instead of \
circles/ellipses for extraction regions.")

                if srcbkg_kw == "source":
                    ## check infiles for ReproIV header keywords that came from the pbk
                    ## and derived from the asol.
                    self._check_file_pbkheader(headerkeys)

                    ## try to find if there is merged data in input stack, throw
                    ## warning (or error out)
                    self._check_merged_input(headerkeys,__toolname__)

                    ## verify parameters are valid if trying to extract readout streak spectrum
                    if streakspec == "yes":
                        self._check_streakspec(weight,refcoord,instrument=headerkeys["INSTRUME"])

                ## check blanksky
                self._check_blanksky(headerkeys,srcbkg_kw,bkgresp)

        ### check ACIS focal-plane temperature ###
        fp_temp_check = [{"srcbkg_kw" : srcbkg_kw,
                          "weight" : weight,
                          "bkgresp" : bkgresp,
                          "ebin" : ebin,
                          "hdr" : headerkeys}
                         for fhs in fn_header_stk
                         for srcbkg_kw,headerkeys in fhs.items() if headerkeys["INSTRUME"]=="ACIS"]

        if fp_temp_check != []:

            def parallel_fptemp(args):
                srcbkg_kw = args["srcbkg_kw"]
                weight = args["weight"]
                bkgresp = args["bkgresp"]
                ebin = args["ebin"]
                headerkeys = args["hdr"]

                if all([srcbkg_kw == "source", weight == "yes"]) or all([srcbkg_kw == "background", bkgresp == "yes"]):
                    try:
                        self.check_fp_temp(headerkeys,headerkeys["inf"],ebin)
                    except Exception as E:
                        return E

                return None

            self.paralleltests(parallel_fptemp,fp_temp_check,method="map",numcores=nproc)

        ### check background files are valid ###
        if bkg_count > 0:
            ## ensure background stack has the same number of elements as the source stack
            if src_count != bkg_count:
                raise IOError(f"Source and background stacks must contain the same \
number of elements.  Source stack={src_count}    Background stack={bkg_count}")

            ## check background region filter formatted correctly
            for bg in bkg_stk:
                if not get_region_filter(bg)[0]:
                    raise IOError(f"Please specify a valid background spatial region filter for {bg} or use FOV region file.")

            ## Check that source and background ObsIDs match
            src_obsid_stk = [hdrkey["OBS_ID"] for hd in fn_header_stk for srcbkg,hdrkey in hd.items() if srcbkg == "source"]

            bkg_obsid_stk = self._get_keyvals(bkg_stk,"OBS_ID")
            # bkg_obsid_stk = [hdrkey["OBS_ID"] for hd in fn_header_stk for srcbkg,hdrkey in hd.items() if srcbkg == "background"]

            if all([None not in src_obsid_stk, None not in bkg_obsid_stk]):

                src_obsid_stk = [int(i) for i in src_obsid_stk]
                bkg_obsid_stk = [int(i) for i in bkg_obsid_stk]

                ## Check that src & bkg stacks have matching ObsID values
                ## and also same number of each unique value.
                if all([src_obsid_stk == bkg_obsid_stk, sorted(src_obsid_stk) == sorted(bkg_obsid_stk)]):
                    dobg = True
                    fcount = src_count

                    dobkgresp = (bkgresp == "yes")

                else:
                    if sorted(src_obsid_stk) != sorted(bkg_obsid_stk):
                        v0("WARNING: Background file OBS_IDs differ from source file OBS_IDs; ignoring background input.\n")

                    ## Check if the matched src&bkg ObsID values are entered in the
                    ## proper matching order.
                    if src_obsid_stk != bkg_obsid_stk:
                        v0("WARNING: 'bkgfile' file order does not match 'infile' file order; ignoring background input.\n")

                    dobg = False
                    dobkgresp = False
                    fcount = src_count

            else:
                v0("WARNING: OBS_ID information could not be found in one or more source \
and/or background files. Assuming source and background file lists have a matching order.\n")
                dobg = True
                fcount = src_count

                dobkgresp = (bkgresp == "yes")

        else:
            dobg = False
            dobkgresp = False
            fcount = src_count
            bkg_stk = None

        common_dict = {"bkgresp" : bkgresp,
                       "dobkgresp" : dobkgresp,
                       "dobg" : dobg,
                       "fcount" : fcount}

        return src_stk,bkg_stk,out_stk,common_dict


    def common_args(self,correct,weight,weight_rmf,bkgresp,resp_pos,refcoord,
                    streakspec,ptype,gtype,gspec,bggtype,bggspec,
                    ebin,channel,ewmap,binwmap,bintwmap,binarfcorr,wmap_clip,
                    wmap_threshold,tmpdir,clobber,verbose):

        common_dict = {"correct" : correct,
                       "weight" : weight,
                       "weight_rmf" : weight_rmf,
                       "bkgresp" : bkgresp,
                       "resp_pos" : resp_pos,
                       "refcoord" : refcoord,
                       "streakspec" : streakspec,
                       "ptype" : ptype,
                       "ebin" : ebin,
                       "channel" : channel,
                       "gtype" : gtype,
                       "bggtype" : bggtype,
                       "binarfcorr" : binarfcorr,
                       "bintwmap" : bintwmap,
                       "ewmap" : ewmap,
                       "binwmap" : binwmap,
                       "wmap_clip" : wmap_clip,
                       "wmap_threshold" : wmap_threshold,
                       "tmpdir" : tmpdir,
                       "clobber" : clobber,
                       "verbose" : verbose}

        if correct == "yes":
            if weight == "yes":
                v0("WARNING: The 'correct' parameter is ignored when 'weight=yes'.")
            else:
                v2("Note: all input source regions are converted to physical coordinates for point-source analysis with ARF correction.")

                ## also check that the binarfcorr parameter is greater than zero
                if float(binarfcorr) <= 0:
                    raise ValueError("'binarfcorr' must be greater than zero.")
        else:
            if float(bintwmap) <= 0 :
                raise ValueError("'binarfwmap' must be greater than zero.")

        ## no need to duplicate responses, since src and bkg responses will
        ## be the same if refcoord!=""
        if refcoord != "" and bkgresp == "yes":
            v1(f"Responses for source and background are identical at {refcoord}, setting 'bkgresp=no' to avoid duplicate files.")

            bkgresp = "no"

            common_dict["bkgresp"] = bkgresp

        ## define the binning specification for RMFs output by the script.
        if ptype == "PI":
            rmfbin = f"pi={channel}"
        else:
            rmfbin = f"pha={channel}"

        common_dict["rmfbin"] = rmfbin

        ## determine whether source spectrum should be grouped and
        ## setup grouping if necessary
        if gtype.upper() == "NONE":
            dogroup = False

        else:
            dogroup = True

            if gtype.upper() == "BIN":
                binspec = gspec
                gval = ""
            else:
                binspec = ""
                gval = gspec

            common_dict["gval"] = gval
            common_dict["binspec"] = binspec

        common_dict["dogroup"] = dogroup

        ## determine whether background spectrum should be grouped and
        ## setup grouping if necessary
        if bggtype.upper() == "NONE":
            bgdogroup = False

        else:
            bgdogroup = True

            if bggtype.upper() == "BIN":
                bgbinspec = bggspec
                bggval = ""
            else:
                bgbinspec = ""
                bggval = bggspec

            common_dict["bggval"] = bggval
            common_dict["bgbinspec"] = bgbinspec

        common_dict["bgdogroup"] = bgdogroup

        return common_dict


    def combine_stacks(self,src_stk,bkg_stk,
                       asp,bpixfile,mask,dtffile,dafile,
                       weight,dobkgresp,refcoord,ewmap,
                       nproc):

        ## check counts in input files, and exit if necessary, or produce responses for upper-limits
        src_dict = [{"file" : fn,
                     "refcoord_check" : refcoord,
                     "weights_check" : False,
                     "ewmap_range_check" : None}
                    for fn in src_stk]

        ## check if there are counts in energy_wmap range for weighted ARFs/sky2tdet creation
        ewmap_srcbg_stk = []

        if weight == "yes":
            ewmap_srcbg_stk.extend(src_stk)

        if dobkgresp:
            ewmap_srcbg_stk.extend(bkg_stk)

        ewmap_srcbg_dict = [{"file" : fn,
                             "ewmap_range_check" : ewmap,
                             "refcoord_check" : None,
                             "weights_check" : None}
                            for fn in ewmap_srcbg_stk]

        # run the checks in parallel
        def parallel_event_stats(args):
            file = args["file"]
            refcoord_check = args["refcoord_check"]
            weights_check = args["weights_check"]
            ewmap_range_check = args["ewmap_range_check"]

            try:
                if not weights_check:
                    return self._check_event_stats(file,
                                                   refcoord_check=refcoord_check,
                                                   weights_check=False)

                if ewmap_range_check is not None and fileio.get_keys_from_file(f"{file}[#row=0]")["INSTRUME"] == "ACIS":
                    return self._check_event_stats(file,
                                                   ewmap_range_check=ewmap_range_check)
                return None

            except Exception as E:
                return E

        self.paralleltests(parallel_event_stats,
                           [*src_dict,*ewmap_srcbg_dict],
                           method="map",numcores=nproc)

        ## find ancillary files, if exists, add to stack
        ancil = {"asol" : {"var" : asp,
                           "stk" : [],
                           "v1str" : "Aspect solution"},
                 "bpix" : {"var" : bpixfile,
                           "stk" : [],
                           "v1str" : "Bad pixel"},
                 "mask" : {"var" : mask,
                           "stk" : [],
                           "v1str" : "Mask"},
                 "dtf" : {"var" : dtffile,
                          "stk" : [],
                          "v1str" : "HRC dead time factor"}}

        for key,val in ancil.items():
            if val["var"] == "":
                for obs in src_stk:
                    fobs = obsinfo.ObsInfo(f"{obs}[#row=0]")

                    v2(f"Using event file '{obs}' to determine ancillary files\n")

                    if key == "asol":
                        v3('Looking in header for ASOLFILE keyword\n')
                        asols = fobs.get_asol()
                        asolstr = ",".join(asols)

                        # val["stk"].extend(asols)
                        val["stk"].append(asolstr)

                        if len(asols) == 1:
                            suffix = ""
                        else:
                            suffix = "s"

                        vprogress(f"{val['v1str']} file{suffix} {asolstr} found.\n")

                    else:
                        if key == "dtf" and fobs.instrument == "ACIS":
                            val["stk"].append("")
                        else:
                            v3(f"Looking in header for {key.upper()}FILE keyword\n")
                            val["stk"].append(fobs.get_ancillary(key))
                            vprogress(f"{val['v1str']} file {fobs.get_ancillary(key)} found.\n")

            else:
                if isinstance(val["var"],list):
                    val["stk"].append(val["var"])
                else:
                    val["stk"].extend(stk.build(val["var"]))


        ### assign stacks to dictionary entires ###
        stk_dict = {"asol" : ancil["asol"]["stk"],
                    "mask" : ancil["mask"]["stk"],
                    "dead time factor" : ancil["dtf"]["stk"],
                    "dead area" : dafile,
                    "badpix" : ancil["bpix"]["stk"]}


        ## ensure file stacks has either 1 or src_count elements
        stk_count = {}
        src_count = len(src_stk)

        for key,fkey in stk_dict.items():
            if all([isinstance(fkey,list), "" not in fkey]):
                fkey = ",".join(fkey)

            # from regtest environment '/dev/null' can inadvertently be expanded
            # out as '../../../../../../dev/null' leading to erroneous failures
            if isinstance(fkey,str) and \
               fkey.lower().endswith("/dev/null") and \
               fkey.lower().startswith("../"):
                fkey = "/dev/null"

            try:
                if all([fkey, fkey.lower() not in [""," ","none","/dev/null"]]):
                    stk_dict[key] = stk.build(fkey)
                    self._check_files(stk_dict[key],key)
                    count = len(stk_dict[key])

                    if key != "asol":
                        if count not in (1,src_count):
                            raise IOError(f"Error: {key} stack must have either 1 \
element or the same number of elements as the source stack.  \
Source stack={src_count}     {key} stack={count}")

                        if key == "badpix":
                            dobpix = True

                else:
                    stk_dict[key] = [""]

                    count = len(stk_dict[key])

                    if key == "badpix":
                        dobpix = False

            except (AttributeError,TypeError):
                stk_dict[key] = [""]

                count = len(stk_dict[key])

                if key == "badpix":
                    dobpix = False

            stk_count[key] = count

        ## check that there are no spaces in ancillary file
        ## paths, if specified
        for key,val in stk_dict.items():
            for path in val:
                if " " in os.path.abspath(path):
                    raise IOError(f"The absolute path for the {key} file, '{os.path.abspath(path)}', cannot contain any spaces")

        ## Determine if asphist or asol files were input
        ## to the 'asp' parameter
        stk_dict["asol"],stk_count["asol"],asolstat,ahiststat = self._asol_asphist(stk_dict["asol"],stk_count["asol"],src_stk)

        return stk_dict, stk_count, asolstat, ahiststat, dobpix


    def obs_args(self,src_stk,out_stk,bkg_stk,asp_stk,bpixfile_stk,rmffile,
                 dtffile_stk,mask_stk,dafile_stk,asolstat,ahiststat,dobpix,
                 common_args,stk_count):

        weight = common_args.pop("weight",None) # remove keyword from dictionary and copy value
        dobg = common_args["dobg"]
        dobkgresp = common_args["dobkgresp"]
        resp_pos = common_args["resp_pos"]
        refcoord = common_args["refcoord"]
        binarfcorr = common_args["binarfcorr"]
        fcount = common_args["fcount"]

        src_count = len(src_stk)
        out_count = len(out_stk)

        ## Determine the file output types, either source files or
        ## both source and background files.
        if dobg:
            otype = ["src","bkg"]
        else:
            otype = ["src"]

        ## Check all of the input files up front and make sure they are
        ## readable. If not, notify the user of each bad file and exit.
        for srcbkg in otype:

            # Look at each file in the stack and check for readability.
            if srcbkg == "bkg":
                self._check_files(bkg_stk,"background")
            else:
                self._check_files(src_stk,"source")


        ## For each stack item in the source and background lists:
        specextract_dict = {}

        for srcbkg in otype:
            arg_dict = {}

            # Determine which stack to use.
            if srcbkg == "bkg":
                cur_stack = bkg_stk
            else:
                cur_stack = src_stk

            # Run tools for each item in the current stack.
            for i in range(fcount):

                fullfile = cur_stack[i]
                filename = self._get_filename(cur_stack[i])
                instrument = fileio.get_keys_from_file(f"{filename}[#row=0]")["INSTRUME"]

                if fcount == 1:
                    iteminfostr = "\n"
                else:
                    iteminfostr = f"[{i+1} of {fcount}]\n"

                if instrument == "HRC" and weight == "yes":
                    weight = "no"
                    v1("HRC responses will be unweighted.")

                if not self._check_event_stats(fullfile,refcoord_check=refcoord,weights_check=True):
                    weight = "no"

                # If we're using an output stack, then grab an item off of the stack
                # but if not, then append "src1", "src2", etc., to the outroot
                # parameter for each output file. If the outroot stack count equals 1
                # but the source stack count is not equal to 1, treat the outroot
                # parameter as the only root

                if out_count == 1 and src_count > 1:
                    outdir, outhead = utils.split_outroot(out_stk[0])

                    if outhead == "":
                        full_outroot = f"{outdir}{srcbkg}{i+1}"
                    else:
                        full_outroot = f"{outdir}{outhead}{srcbkg}{i+1}"

                else:
                    outdir, outhead = utils.split_outroot(out_stk[i])

                    if outhead == "":
                        full_outroot = f"{outdir}{srcbkg}"

                    else:
                        if "bkg" == srcbkg:
                            full_outroot = f"{outdir}{outhead}{srcbkg}"
                        else:
                            full_outroot = f"{outdir}{outhead.rstrip('_')}"


                # If asol and not asphist files were input to
                # 'asp' parameter, set asol argument passes to
                # mk_asphist() for creating aspect histogram file
                # input to create_arf_*.

                if asolstat:
                    kw = fileio.get_keys_from_file(f"{filename}[#row=0]")

                    try:
                        obsid = kw["OBS_ID"]
                        asol_arg = asp_stk[f"{obsid}"]

                        if "," in asol_arg:
                            asol_arg = asol_arg.split(",")

                    except KeyError:
                        asol_arg = None

                        if obsid == "0" or kw["DATACLAS"].lower() == "simulated":
                            asol_arg = utils.getUniqueSynset(asp_stk.values())

                if ahiststat:
                    # set asol_arg for get_resp_pos
                    asol_arg = "none"

                    aspfile_block = get_block_info_from_file(asp_stk[i])

                    if aspfile_block[0].find("asphist") != -1:
                        if srcbkg != "bkg":
                            v1("Found a Level=3 ahst3.fits file in 'asp' input; the 'asphist' \
block corresponding to the source region location will be used.\n")

                        if stk_count["asol"] != 1:
                            asphist_arg = f"{asp_stk[i]}[asphist{self._event_stats(fullfile,'ccd_id')}]"
                        else:
                            if asp_stk[i].startswith("@"):
                                asphist_arg = f"{','.join(stk.build(asp_stk[0]))}[asphist{self._event_stats(fullfile,'ccd_id')}]"
                            else:
                                asphist_arg = f"{asp_stk[0]}[asphist{self._event_stats(fullfile,'ccd_id')}]"

                    else:
                        if stk_count["asol"] != 1:
                            asphist_arg = asp_stk[i]
                        else:
                            if asp_stk[i].startswith("@"):
                                asphist_arg = ",".join(stk.build(asp_stk[0]))
                            else:
                                asphist_arg = asp_stk[0]


                # Set bpixfile argument passes to set_badpix().
                if dobpix:
                    if stk_count["badpix"] != 1:
                        bpix_arg = bpixfile_stk[i]
                    else:
                        if bpixfile_stk[i].startswith("@"):
                            bpix_arg = ",".join(stk.build(bpixfile_stk[0]))
                        else:
                            bpix_arg = bpixfile_stk[0]


                # Set mask argument passes to create_arf_ext (mkwarf).
                if stk_count["mask"] != 1:
                    msk_arg  = mask_stk[i]
                else:
                    if mask_stk[i].startswith("@"):
                        msk_arg = ",".join(stk.build(mask_stk[i]))
                    else:
                        msk_arg = mask_stk[0]


                # Set dafile argument passes to create_arf_*.
                if stk_count["dead area"] != 1:
                    da_arg = dafile_stk[i]
                else:
                    if dafile_stk[0].startswith("@"):
                        da_arg = ",".join(stk.build(dafile_stk[0]))
                    else:
                        da_arg = dafile_stk[0]


                # Set dtffile argument passes to mk_asphist().
                if stk_count["dead time factor"] != 1:
                    dtf_arg = dtffile_stk[i]
                else:
                    if dtffile_stk[0].startswith("@"):
                        dtf_arg = ",".join(stk.build(dtffile_stk[0]))
                    else:
                        dtf_arg = dtffile_stk[0]


                # set up arguments dictionary
                arg_dict = {"srcbkg" : srcbkg,
                            "fullfile" : fullfile,
                            "filename" : filename,
                            "full_outroot" : full_outroot,
                            "instrument" : instrument,
                            "weight" : weight,
                            "da" : da_arg,
                            "dtf" : dtf_arg,
                            "msk" : msk_arg,
                            "dobpix" : dobpix,
                            "iteminfostr" : iteminfostr}

                if dobpix:
                    arg_dict["bpix"] = bpix_arg
                if ahiststat:
                    arg_dict["asphist"] = asphist_arg
                if asolstat:
                    arg_dict["asol"] = asol_arg


                #########################################################
                #
                # determine coordinates to use to produce responses
                #
                #########################################################

                if weight == "no" and common_args["correct"] == "yes":
                    ra,dec,skyx,skyy,chipx,chipy,chip_id = self.get_resp_pos(fullfile,asol_arg,
                                                                             srcbkg,dobkgresp,
                                                                             resp_pos,refcoord,
                                                                             binimg=binarfcorr)
                else:
                    ra,dec,skyx,skyy,chipx,chipy,chip_id = self.get_resp_pos(fullfile,asol_arg,
                                                                             srcbkg,dobkgresp,
                                                                             resp_pos,refcoord,
                                                                             binimg=2)

                arg_dict["skyx"] = skyx
                arg_dict["skyy"] = skyy
                arg_dict["chip_id"] = chip_id
                arg_dict["chipx"] = chipx
                arg_dict["chipy"] = chipy

                # determine hydrogen column density based on extraction region centroid
                # or refcoord to add to PI header in units of 1e-22 cm**-2
                nrao_nh = colden(ra,dec,dataset="nrao")

                if nrao_nh not in [None,"-",0.0]:
                    nrao_nh *= 0.01

                    arg_dict["nrao_nh"] = nrao_nh

                bell_nh = colden(ra,dec,dataset="bell")

                if bell_nh not in [None,"-",0.0]:
                    bell_nh *= 0.01

                    arg_dict["bell_nh"] = bell_nh
                else:
                    v1("Warning: Skip adding 'bell_nh' header keyword.  No valid data at the \
source location in the Bell Labs HI Survey (the survey covers RA > -40 deg).\n")

                if instrument == "ACIS":
                    if int(chipx) < 1:
                        v1(f"chipx={chipx} for ACIS-{chip_id}; using chipx=1 for FEF and RMF look up.\n")
                        chipx = "1"
                    if int(chipy) < 1:
                        v1(f"chipy={chipy} for ACIS-{chip_id}; using chipy=1 for FEF and RMF look up.\n")
                        chipy = "1"
                    if int(chipx) > 1024:
                        v1(f"chipx={chipx} for ACIS-{chip_id}; using chipx=1024 for FEF and RMF look up.\n")
                        chipx = "1024"
                    if int(chipy) > 1024:
                        v1(f"chipy={chipy} for ACIS-{chip_id}; using chipy=1024 for FEF and RMF look up.\n")
                        chipy = "1024"

                    arg_dict["chipx"] = chipx
                    arg_dict["chipy"] = chipy

                # Set the rmffile argument pass to determine_rmf_tool() [for ACIS only].
                if instrument == "ACIS":
                    ccdid_val = f"(ccd_id={chip_id})"

                    if rmffile == "CALDB":
                        rmffile_ccd = f"{rmffile}{ccdid_val}"
                        null_rmffile = False

                    elif "CALDB(" in str(rmffile):
                        rmffile_ccd = rmffile
                        null_rmffile = False

                    else:
                        rmffile_ccd = f"CALDB{ccdid_val}"
                        null_rmffile = True

                    #arg_dict["ccdid_val"] = ccdid_val
                    arg_dict["rmffile_ccd"] = rmffile_ccd
                    arg_dict["null_rmffile"] = null_rmffile

                else:
                    arg_dict["rmffile"] = rmffile

                # set src/bkg item dictionary
                specextract_dict[f"{srcbkg}{i+1}"] = {**arg_dict, **common_args}

        return specextract_dict


    def specextract_dict(self):
        """
        return dictionary of parameter arguments to run specextract
        for each src/bkg independently
        """

        ###############################################################
        #
        #  Test using ~/cxcds_param4/specextract.par:
        #
        #  > import ciao_contrib._tools.specextract as spec
        #  > params,pars = get_par(["specextract.par"])
        #  > specdict = spec.ParDicts(params).specextract_dict()
        #
        ###############################################################

        common_dict = self.common_args(self.correct,self.weight,self.weight_rmf,self.bkgresp,self.resp_pos,
                                       self.refcoord,self.streakspec,self.ptype,self.gtype,self.gspec,self.bggtype,
                                       self.bggspec,self.ebin,self.channel,self.ewmap,self.binwmap,
                                       self.bintwmap,self.binarfcorr,self.wmap_clip,self.wmap_threshold,
                                       self.tmpdir,self.clobber,self.verbose)

        src_stk, bkg_stk, out_stk, common_dict_append = self.check_input_stacks(self.infile,
                                                                                self.bkgfile,
                                                                                self.outroot,
                                                                                common_dict["weight"],
                                                                                common_dict["bkgresp"],
                                                                                common_dict["refcoord"],
                                                                                common_dict["streakspec"],
                                                                                common_dict["ebin"],
                                                                                self.nproc)

        common_dict = {**common_dict,**common_dict_append}

        stk_dict, stk_count, asolstat, ahiststat, dobpix = self.combine_stacks(src_stk,bkg_stk,self.asp,
                                                                               self.bpixfile,self.mask,
                                                                               self.dtffile,self.dafile,
                                                                               common_dict["weight"],
                                                                               common_dict["dobkgresp"],
                                                                               common_dict["refcoord"],
                                                                               common_dict["ewmap"],
                                                                               self.nproc)

        obs_dict = self.obs_args(src_stk,out_stk,bkg_stk,stk_dict["asol"],
                                 stk_dict["badpix"],self.rmffile,stk_dict["dead time factor"],
                                 stk_dict["mask"],stk_dict["dead area"],asolstat,
                                 ahiststat,dobpix,common_dict,stk_count)

        return obs_dict



def _check_filename_set(filename):
    if not filename:
        return False

    filename = str(filename).upper()

    if filename in ["NULL","NONE",""," "]:
        return False

    return True



def get_region_filter(full_filename):
    """
    Pass in the full filename
    i.e.  dir/source.fits[sky=region(dir/source.reg)]
    and return the filter without filename
    i.e.  region_filter = region(source.reg)
    for input to arfcorr
    """

    # region_filter = dm spatial region filter minus filename
    #                 and any other filters which may be present

    #
    # NB: strip off the filename by splitting the string
    # at "sky=" or "(x,y)=", and then cleaning up the dm
    # filter portion of this result.
    #
    # Note: the 'exclude' DM region filter syntax is unsupported
    # by sky2tdet for 'weight=yes'; by dmextract when 'weight=no';
    # and by dmmakereg when 'weight=no' and 'correct=yes'.
    # (dmextract won't output an error, but the WMAP doesn't make
    # it into the output spectrum as it should, causing a
    # calquiz error downstream).

    if "sky=" in full_filename:
        reg_filter = True
        region_temp = full_filename.split("sky=")[1]

    elif "(x,y)=" in full_filename:
        reg_filter = True
        region_temp = full_filename.split("(x,y)=")[1]

    elif "pos=" in full_filename:
        reg_filter = True
        region_temp = full_filename.split("pos=")[1]

    else:
        reg_filter = False

        if full_filename.startswith("@"):
            # deal with stacks
            pass
        else:
            region_temp = full_filename
            v1(f"WARNING: A supported spatial region filter was not detected for {full_filename}\n")

    if reg_filter:
        if ")," in region_temp and ") ," in region_temp:

            region_temp2 = region_temp.partition("),")[0]+")"

            if ") ," in region_temp2:
                reg = region_temp2.partition(") ,")[0]+")"
            else:
                reg = region_temp2

        elif ")," in region_temp:
            reg = region_temp.partition("),")[0]+")"

        elif ") ," in region_temp:
            reg = region_temp.partition(") ,")[0]+")"

        else:
            reg = region_temp.rpartition("]")[0]

    else:
        reg = full_filename

    if not _check_filename_set(reg):
        raise IOError(f"Please specify a valid spatial region filter for {full_filename} or use FOV region files.")

    return reg_filter,reg
