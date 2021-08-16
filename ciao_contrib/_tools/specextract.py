import paramio, os, numpy, cxcdm, stk, tempfile
import pycrates as pcr

from ciao_contrib.runtool import dmstat, dmcoords, dmlist, acis_fef_lookup

from ciao_contrib.logger_wrapper import initialize_logger, make_verbose_level
from ciao_contrib.cxcdm_wrapper import get_block_info_from_file

import ciao_contrib._tools.fileio as fileio
import ciao_contrib._tools.utils as utils
import ciao_contrib._tools.obsinfo as obsinfo
from ciao_contrib.proptools import colden

toolname = "_tools.specextract"

# Set up the logging/verbose code
initialize_logger(toolname)

# Use v<n> to display messages at the given verbose level.
v0 = make_verbose_level(toolname, 0)
v1 = make_verbose_level(toolname, 1)
v2 = make_verbose_level(toolname, 2)
v3 = make_verbose_level(toolname, 3)
v4 = make_verbose_level(toolname, 4)
v5 = make_verbose_level(toolname, 5)


#########################################################################################
#
# suppress warnings printed to screen from get_keyvals when probing for blank sky files
# https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
#
########################################################################################

class suppress_stdout_stderr(object):
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
        self.refcoord = params["refcoord"]
        self.rmffile = params["rmffile"]
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

        if all(["ASPHIST" in asptype, "ASPSOL" in asptype]):
            raise IOError("A mix of aspect solution and histogram files were entered into 'asp'; please enter one or a list of either type, not both.\n")

        if all(["ASPHIST" not in asptype, "ASPSOL" not in asptype]):
            raise IOError("Neither aspect histogram nor aspect solution files were found in the 'asp' input. Either the ASPHIST/asphist or ASPSOL FITS HDU is not in the expected place - which could cause the CIAO tools invoked by this script to fail - or a filename was entered incorrectly or does not exist. Exiting.\n")

        if "ASPSOL" in utils.getUniqueSynset(asptype):
            asol = True
            ahist = False

        if "ASPHIST" in utils.getUniqueSynset(asptype):
            asol = False
            ahist = True

        if ahist:
            if asp_cnt != 1 and asp_cnt != src_cnt:
                raise IOError(f"Error: asp stack must have either 1 element or the same number of elements as the source stack.  Source stack={src_cnt}    asp stack={asp_cnt}")

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
                    raise ValueError("OBS_ID information could not be found in source and/or aspect solution files; cannot properly match source files to aspect solution files. Try entering aspect histogram files into 'asp' to work around this requirement.")

                # Quit with an error if any of the source file OBS_ID
                # values are not found in the list of asol OBS_IDs.

                for i in range(0, src_cnt):
                    if str(src_obsid_stk[i]) not in asol_obsid_stk:
                        raise IOError(f"No aspect solution files provided for {src_stk[i]}.")

                # #asol_sorted_grouped = group_by_obsid(asp_stk,"aspsol")
                # asp_stk = group_by_obsid(asp_stk,"aspsol")

                # v3(f"ObsIDs matched to aspect solution files: \n{asp_stk}")

            if asp_cnt != 1 and src_cnt == 1:
                asp_stk = self._sort_files(utils.getUniqueSynset(asp_stk), "aspsol", "TSTART")
                asp_stk = ",".join(asp_stk)

            asp_stk = self.group_by_obsid(asp_stk,"aspsol")            
            v3(f"ObsIDs matched to aspect solution files: \n{asp_stk}")

        if not ahist and not asol:
            asp_stk = [""]
            asp_cnt = len(asp_stk)

        return asp_stk,asp_cnt,asol,ahist


    def _check_files(self,stack,filetype):
        """Check to see if each file in the input stack is readable."""

        count = len(stack)
        if count == 1:
            suffix = ''
        else:
            suffix = 's'

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

            except IOError:
                raise IOError(f"{filetype} file {filename} does not exist or could not be opened.")

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


    def _check_file_pbkheader(self,infile_stack):
        """
        check the input file header contains keywords that were found in the PBK file 
        introduced in Repro IV.
        """

        ## pbkkeys are: 'OCLKPAIR', 'ORC_MODE', 'SUM_2X2', 'FEP_CCD'
        ## asol-derived keys are: 'DY_AVG', 'DZ_AVG', 'DTH_AVG'

        pbk_kw = ("OCLKPAIR","ORC_MODE","SUM_2X2","FEP_CCD")
        # asp_kw = ["DY_AVG","DZ_AVG","DTH_AVG"]

        file_status = []

        for inf in infile_stack:
            inf = fileio.get_file(inf)

            headerkeys = fileio.get_keys_from_file(inf)

            if headerkeys["INSTRUME"] == "ACIS":
                try:
                    verify_keys = []

                    verify_keys.extend([headerkeys.has_key(kw) for kw in pbk_kw])

                    if False in verify_keys:
                        v1(f"WARNING: {fileio.remove_path(inf)} missing header keywords.\n")

                        file_status.append(inf)

                except AttributeError:
                    pbk_kw_list = list(pbk_kw)

                    verify_keys = headerkeys.keys() & pbk_kw_list # find elements in common

                    for s in verify_keys:
                        pbk_kw_list.remove(s)

                    if len(pbk_kw_list) != 0:
                        v1(f"WARNING: {fileio.remove_path(inf)} missing header keywords.\n")

                        file_status.append(inf)

        if file_status != []:
            raise IOError("Input event file(s) missing necessary Repro IV header keywords.  Reprocess data with chandra_repro or add the keywords to the event file(s) with r4_header_update.")


    def _get_keyvals(self,stack,keyname):

        """
        return keys
        """

        keys = []

        for fn in stack:
            try:
                kval = fileio.get_keys_from_file(fn)[keyname]
            except KeyError:
                v1(f"WARNING: The {keyname} header keyword is missing from {fn}")
                kval = None

            keys.append(kval)

        return keys


    def _check_event_stats(self,file,refcoord_check=None,weights_check=None,
                           ewmap_range_check=None):

        """
        Use dmlist to determine the event counts
        and appropriately error out or proceed with the script
        """
        
        dmlist.punlearn()

        if ewmap_range_check is None:
            dmlist.infile = file
        else:
            dmlist.infile = f"{file}[energy={ewmap_range_check}]"

        dmlist.opt = "counts"

        counts = dmlist()

        if counts == "0":
            try:
                if refcoord_check.lower() not in ["","none","indef"]:
                    if weights_check:
                        v1("WARNING: Unweighted responses will be created at the 'refcoord' position.\n")
                    else:
                        v1("WARNING: Using 'refcoord' position to produce response files.\n")
                else:
                    raise IOError(f"{file} has zero counts. Check that the region format is in sky pixels coordinates.")

            except AttributeError:
                if ewmap_range_check is not None:
                    # do we want to error out if the number of counts is smaller than some magic count, instead of just zero?

                    raise IOError(f"{file} has zero counts in the 'energy_wmap={ewmap_range_check}' range needed to generate a weights map.")

            return False

        return True

    
    def _event_stats(self,file,colname):
        """
        Use dmstat to determine the event statistics: source chipx,
        chipy, sky x, sky y, and ccd_id values to use for input
        to asphist, acis_fef_lookup, and arfcorr.
        Since dmstat doesn't return the mode, do this by brute force
        for ccd_id column (psextract algorithm uses mean ccd_id value,
        which isn't appropriate for this quantity).
        """

        dmstat.punlearn()
        dmstat.verbose = "0"

        cr = pcr.read_file(file)
        if cr is None:
            raise IOError(f"Unable to read from file {file}")

        if colname == "ccd_id":

            # Use pycrates to retrieve ccd_id values from user-input event
            # extraction region. Compute the mode of the ccd_id values
            # stored in the array.

            ccdid_vals = pcr.get_colvals(cr, "ccd_id")

            n_elements = list(range(10))

            for i in range(0,10):
                zeros = numpy.array(ccdid_vals)-i
                n_elements[i] = len(ccdid_vals)-len(numpy.nonzero(zeros)[0])

            mode = numpy.where(n_elements==numpy.max(n_elements))[0]
            return mode[0]

        if colname == "chip_id":

            # Use pycrates to retrieve ccd_id values from user-input event
            # extraction region. Compute the mode of the ccd_id values
            # stored in the array.

            chipid_vals = pcr.get_colvals(cr, "chip_id")

            n_elements = list(range(10))

            for i in range(0,10):
                zeros = numpy.array(chipid_vals)-i
                n_elements[i] = len(chipid_vals)-len(numpy.nonzero(zeros)[0])

            mode = numpy.where(n_elements==numpy.max(n_elements))[0]
            return mode[0]

        if colname in ["x","y","chipx","chipy"]:

            if colname in ["x","y"]:
                bin_setting="[bin sky=2]"

            if colname in ["chipx","chipy"]:
                bin_setting="[bin chipx=2,chipy=2]"

            dmstat(f"{file}{bin_setting}")

            max_cnts_src_pos = dmstat.out_max_loc

            src_x = max_cnts_src_pos.split(",")[0]
            src_y = max_cnts_src_pos.split(",")[1]

            if colname == "x":
                return src_x

            if colname == "y":
                return src_y

            if colname == "chipx":
                return int(float(src_x))

            if colname == "chipy":
                return int(float(src_y))

        del(cr)


    def _valid_regstr(self,inf):
        regfilter = fileio.get_filter(inf)

        if any(["=(" in regfilter,"(" not in regfilter]):
            raise IOError(f"There is a problem with the extraction region syntax in: {inf}")


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
            region = get_region_filter(full_filename)[1].split("(")[1].strip(")")
        else:
            region = get_region_filter(full_filename)[1]


        if not _check_filename_set(region):
            return None

        return region

        
    def _sort_files(file_stack, file_type, key):
        """
        Sort a list of files by the value of a given keyword; e.g., for sorting
        a stack of aspect solution files on TSTART before input to mk_asphist().
        """

        file_count = len(file_stack)
        files_orig_order = list(range(file_count))

        for i in range(0, file_count):
            files_orig_order[i] = file_stack[i]

        keyvals_orig_order = self._get_keyvals(file_stack, key)

        if None in keyvals_orig_order:
            raise IOError(f"One or more of the entered {file_type} files is missing the required {key} header keyword value. Exiting.")

        keyvals_sorted = sorted(keyvals_orig_order) #be sure numbers are not strings

        files_sorted = list(range(file_count))

        for i in range(0, file_count):
            sort_ind = keyvals_orig_order.index(keyvals_sorted[i])
            files_sorted[i] = files_orig_order[sort_ind]

        return files_sorted
    
    
    def group_by_obsid(self,file_stack,file_type):
        """
        Read the OBS_ID value from the header of each file in the input stack
        in order to create a dictionary matching each ObsID to one or a list of
        files. Then, this dictionary can be used by other functions in the script
        to assign the appropriate file(s) (e.g., asol) to each source observation,
        by obsid.
        """
        
        # Right now, for simplicity, accept stacks
        # defined as follows:
        #
        # file_stack = stk.stack_build(files)
        #
        # where 'files' is a list or @stack read from
        # specextract parameter file.

        file_count = len(file_stack)

        obsids = self._get_keyvals(file_stack, "OBS_ID")

        # //// NEW 19April2012 ////////////////////////////////
        #badstring=[]
        #for obsid in obsids:
        #    badstring.append(isinstance(obsid, basestring))
        # /////////////////////////////////////////////////////

        if None in obsids:
            raise IOError(f"One or more of the entered {file_type} files is missing an OBS_ID header keyword value or it exists but contains an unexpected value, therefore files cannot be grouped by ObsID and properly matched to input source files. Exiting.")
           # can be just a warning for certain file types, but right now this
           # function is just used for asol


        # //// NEW 19April2012 ////////////////////////////////
        #elif True in badstring:
        #    raise IOError("One or more of the entered %s files contains an unexpected OBS_ID header keyword value,
        #    therefore files cannot be grouped by ObsID and properly matched to input source files. Exiting." % (file_type))
        # /////////////////////////////////////////////////////

        obsid_sort = sorted(obsids) # be sure numbers are not strings

        orig_files = list(range(file_count))
        for i in range(0, file_count):
            orig_files[i] = file_stack[i] #stk_read_num(file_stack, i+1)

        sorted_files = list(range(file_count))
        for i in range(0,file_count):
            sort_ind = obsids.index(obsid_sort[i])
            sorted_files[i] = orig_files[sort_ind]


        if file_type != "aspsol":

            obsid_dict = {}
            for i in range(0,file_count):
                if obsid_sort[i] in obsid_dict:
                    obsid_dict[obsid_sort[i]] = f"{obsid_dict[obsid_sort[i]]},{sorted_files[i]}"
                else:
                    obsid_dict[obsid_sort[i]] = sorted_files[i]

            return obsid_dict

        else:
            asol_tstart = self._get_keyvals(file_stack, "TSTART")

            if None in asol_tstart:
                raise IOError("One or more of the entered aspect solution files is missing a TSTART header keyword value, therefore files cannot be properly sorted and matched to input source files. Exiting.")

            asol_tstart_sort = sorted(asol_tstart) #be sure numbers are not strings

            sort_asolfiles = list(range(file_count))
            asol_obsid_sort = list(range(file_count))

            for i in range(0,file_count):
                tsort_ind = asol_tstart.index(asol_tstart_sort[i])
                sort_asolfiles[i] = orig_files[tsort_ind]
                asol_obsid_sort[i] = obsids[tsort_ind]

            asol_dict={}
            for i in range(0,file_count):
                if asol_obsid_sort[i] in asol_dict:

                    asol_sort = f"{asol_dict[asol_obsid_sort[i]]},{sort_asolfiles[i]}".replace(" ","").split(",")
                    unique_asol_sort = ",".join(utils.getUniqueSynset(asol_sort))

                    if len(asol_sort) != len(unique_asol_sort):
                        v3("WARNING: Duplicate aspect solutions provided.")

                    asol_dict[asol_obsid_sort[i]] = unique_asol_sort
                else:
                    asol_dict[asol_obsid_sort[i]] = sort_asolfiles[i]

            return asol_dict


    def resp_pos(self,infile,asol,refcoord,binimg=2):
        """
        determine coordinates to use to produce responses
        """

        # infile = "full filename"
        dmcoords.punlearn()
        dmcoords.infile = infile
        dmcoords.asolfile = asol
        dmcoords.celfmt = "deg"

        if refcoord != "":
            # returns RA and Dec in decimal degrees
            ra,dec,delme = utils.parse_refpos(refcoord.replace(","," "))

            dmcoords.opt = "cel"
            dmcoords.ra = str(ra)
            dmcoords.dec = str(dec)

            dmcoords()

            skyx = str(dmcoords.x)
            skyy = str(dmcoords.y)

        else:
            ## parse infile region
            if self._get_region(infile) == infile:
                raise IOError("No region filter with the event file, nor a refcoord value, provided to produce response files.")

            else:
                # follow general procedures used in event_stats()

                dmstat.punlearn()
                dmstat.infile = f"{infile}[bin sky={binimg}]"
                dmstat.verbose = "0"
                dmstat.centroid = "yes"
                dmstat()

                # get sky position
                skyx,skyy = dmstat.out_max_loc.split(",")
                #skyx,skyy = dmstat.out_cntrd_phys.split(",") # having issues if centroid falls in a zero-count location

                # convert to chip coordinates
                dmcoords.opt = "sky"
                dmcoords.x = str(skyx)
                dmcoords.y = str(skyy)

                dmcoords()

        chipx = str(int(dmcoords.chipx))
        chipy = str(int(dmcoords.chipy))

        chip_id = str(dmcoords.chip_id)

        ra = float(dmcoords.ra)
        dec = float(dmcoords.dec)

        return ra,dec,skyx,skyy,chipx,chipy,chip_id

    
    def _check_input_stacks(self,infile,bkgfile,outroot,weight,bkgresp,ebin):
        """
        Build stacks for the file input parameters; make sure they are
        readable and not empty. 
        """

        ### source stack ###
        if all([infile, infile.lower() not in [""," ","none"]]):

            # handle a stack of regions, but single input file, in the format: "evt.fits[sky=@reg.lis]",
            # assume no other dmfilter included

            if all([get_region_filter(infile)[0], get_region_filter(infile)[1].startswith("@")]):
                regfile = get_region_filter(infile)[1]
                regfilter = fileio.get_filter(infile)
                fi = self._get_filename(infile)
                regcoord = regfilter.strip("\[\]").replace(regfile,"").replace("=","")

                regstk = stk.build(regfile)

                src_stk = [f"{fi}[{regcoord}={region}]" for region in regstk]

                del(fi)
                del(regfile)
                del(regfilter)
                del(regcoord)
                del(regstk)

            else:
                src_stk = stk.build(infile)

        else:
            src_stk = [""]

        src_count = len(src_stk)

        # error out if there are spaces in absolute paths of the stack
        for path in src_stk:
            if " " in os.path.abspath(path):
                raise IOError(f"The absolute path for the input file, '{os.path.abspath(path)}', cannot contain any spaces")

        # check infiles for CC-mode data and throw warning; also look for merged
        # data or blanksky files and error out
        for inf in src_stk:
            inf = fileio.get_file(inf)
            headerkeys = fileio.get_keys_from_file(f"{inf}[#row=1]")

            # check for blank sky files and maxim's bg files, error out if found:
            try:
                blanksky = headerkeys["CDES0001"]
            except (KeyError,AttributeError):
                blanksky = None

            try:
                mm_blanksky = headerkeys["MMNAME"]
            except (KeyError,AttributeError):
                mm_blanksky = None

            if blanksky is not None:
                if "blank sky event" in blanksky.lower():
                    raise IOError("Cannot use blanksky background files as infile, since responses cannot be produced.\n")

            if mm_blanksky is not None:
                if mm_blanksky.lower().startswith("acis") and "_bg_evt_" in mm_blanksky.lower():
                    raise IOError("Cannot use M.M. ACIS blanksky background files as infile, since responses cannot be produced.\n")

            # check defined response energy range for weighted warm observations
            if weight == "yes" and headerkeys["INSTRUME"] == "ACIS":

                # check focal plane temperature, if >-110C, then check FEF energy range
                # ObsID 114 (observed 2000-01-30 10:40:42) is first observation made at <-119C.
                #
                # mkarf/mkrmf automatically creates response in the available energy range in the FEF file
                # for unweighted responses

                v3("Checking detector focal plane temperature\n")

                fp_temp = headerkeys["FP_TEMP"] - 273.15 # convert from Kelvin to Celsius

                if fp_temp > -110:
                    v3("Checking FEF energy range for warm observation")

                    acis_fef_lookup.punlearn()
                    acis_fef_lookup.infile = inf
                    acis_fef_lookup.chipid = "none"
                    acis_fef_lookup.verbose = "0"

                    try:
                        acis_fef_lookup()
                    except OSError as err_msg:
                        v1(err_msg)
                        self._check_file_pbkheader([inf])

                    fef = acis_fef_lookup.outfile

                    cr_fef = pcr.read_file(fef)
                    fef_energy = cr_fef.get_column("ENERGY").values
                    del(cr_fef)

                    fef_emin = min(fef_energy)
                    fef_emax = max(fef_energy)

                    ebin_min,ebin_max,ebin_de = ebin.split(":")

                    fef_estat = (float(ebin_min) >= fef_emin, float(ebin_max) <= fef_emax)

                    if fef_estat != (True,True):
                        raise ValueError(f"ObsID {headerkeys['OBS_ID']} was made at a warm focal plane temperature, >-110C.  The available calibration products are valid for an energy range of {fef_emin:.3f}-{fef_emax:.3f} keV while the 'energy' parameter has been set to {ebin_min}-{ebin_max} keV (energy={ebin})") # the ":.3f" in the format prints up to three decimal places of the float

            # find CC-mode data, throw warning
            if headerkeys["INSTRUME"] == "ACIS":
                readmode = headerkeys["READMODE"]

                if readmode.upper() == "CONTINUOUS":
                    v1(f"WARNING: Observation taken in CC-mode.  {toolname} may provide invalid responses for {inf}.  Use rotboxes instead of circles/ellipses for extraction regions.")

            # try to find if there is merged data in input stack, throw warning (or error out)
            merge_key = [headerkeys["TITLE"].lower(),
                         headerkeys["OBSERVER"].lower(),
                         headerkeys["OBJECT"].lower(),
                         headerkeys["OBS_ID"].lower()]

            try:
                merge_key.append(headerkeys["DS_IDENT"].lower())
            except KeyError:
                pass

            if "merged" in merge_key:
                raise IOError(f"Merged data sets are unsupported by {toolname}.  Merged events files should not be used for spectral analysis.") # or v1 warning?

            del(merge_key)

        # check infiles for ReproIV header keywords that came from the pbk
        # and derived from the asol.

        self._check_file_pbkheader(src_stk)


        ### outroot stack ###

        if all([outroot, outroot.lower() not in [""," ","none"]]):
            out_stk = stk.build(outroot)

        else:
            out_stk = [""]

        out_count = len(out_stk)

        # error out if there are spaces in absolute paths
        for path in out_stk:
            if " " in os.path.abspath(path):
                raise IOError(f"The absolute path for the outroot, '{os.path.abspath(path)}', cannot contain any spaces")

        ### background stack; ensure it has the same number of elements as the source stack ###
        if all([bkgfile, bkgfile.lower() not in [""," ","none"]]):

            # handle a stack of regions, but single input file, in the format: "evt.fits[sky=@reg.lis]",
            # assume no other dmfilter included
            if all([get_region_filter(bkgfile)[0], get_region_filter(bkgfile)[1].startswith("@")]):
                regfile = get_region_filter(bkgfile)[1]
                regfilter = fileio.get_filter(bkgfile)
                fi = self._get_filename(bkgfile)
                regcoord = regfilter.strip("\[\]").replace(regfile,"").replace("=","")

                regstk = stk.build(regfile)

                bkg_stk = [f"{fi}[{regcoord}={region}]" for region in regstk]

                del(fi)
                del(regfile)
                del(regfilter)
                del(regcoord)
                del(regstk)

            else:
                bkg_stk = stk.build(bkgfile)

            bg_count = len(bkg_stk)

            # error out if there are spaces in absolute paths of the stacks
            for path in bkg_stk:
                if " " in os.path.abspath(path):
                    raise IOError(f"The absolute path for the background file, '{os.path.abspath(path)}', cannot contain any spaces")

            # check background region filter formatted correctly
            for bg in bkg_stk:
                if not get_region_filter(bg)[0]:
                    raise IOError(f"Please specify a valid background spatial region filter for {bg} or use FOV region file.")

            ### check background files are valid ###
            if src_count != bg_count:
                raise IOError(f"Source and background stacks must contain the same number of elements.  Source stack={src_count}    Background stack={bg_count}")

            else:
                # check for blank sky files and Maxim's bg files:
                v1("Checking for blank sky background files...")

                with suppress_stdout_stderr():
                    blanksky = self._get_keyvals(bkg_stk,"CDES0001")
                    mm_blanksky = self._get_keyvals(bkg_stk,"MMNAME")

                blanksky = [kw for kw in blanksky if kw is not None]
                mm_blanksky = [kw for kw in mm_blanksky if kw is not None]

                for blanksky_info in blanksky:
                    if "blank sky event" in blanksky_info.lower():
                        if bkgresp == "yes":
                            raise IOError("Cannot create responses for spectra from blanksky background files.\n")
                        else:
                            v1("WARNING: Extracting background spectra from blanksky background files.\n")

                for mm_blanksky_info in blanksky:
                    if all([mm_blanksky_info.lower().startswith("acis"), "_bg_evt_" in mm_blanksky_info.lower()]):
                        if bkgresp == "yes":
                            raise IOError("Cannot create responses for spectra from M.M. ACIS blanksky background files.\n")
                        else:
                            v1("WARNING: Extracting background spectra from M.M. ACIS blanksky background files.\n")

                # Check that source and background ObsIDs match. 
                src_obsid_stk = self._get_keyvals(src_stk, "OBS_ID")
                bkg_obsid_stk = self._get_keyvals(bkg_stk, "OBS_ID")

                if all([None not in src_obsid_stk, None not in bkg_obsid_stk]):
                    # Check that src & bkg stacks have matching ObsID values
                    # and also same number of each unique value.

                    if all([src_obsid_stk == bkg_obsid_stk, sorted(src_obsid_stk) == sorted(bkg_obsid_stk)]):
                        dobg = True
                        fcount = src_count

                        if bkgresp == "yes":
                            dobkgresp = True
                        else:
                            dobkgresp = False

                    else:
                        if sorted(src_obsid_stk) != sorted(bkg_obsid_stk):
                            v0("WARNING: Background file OBS_IDs differ from source file OBS_IDs; ignoring background input.\n")

                        # Check if the matched src&bkg ObsID values are entered in the
                        # proper matching order.
                        if src_obsid_stk != bkg_obsid_stk:
                            v0("WARNING: 'bkgfile' file order does not match 'infile' file order; ignoring background input.\n")

                        dobg = False
                        dobkgresp = False
                        fcount = src_count

                else:
                    v0("WARNING: OBS_ID information could not be found in one or more source and/or background files. Assuming source and background file lists have a matching order.\n")
                    dobg = True
                    fcount = src_count

                    if bkgresp == "yes":
                        dobkgresp = True
                    else:
                        dobkgresp = False

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

    
    def common_args(self,correct,weight,weight_rmf,bkgresp,refcoord,
                    ptype,gtype,gspec,bggtype,bggspec,ebin,channel,
                    ewmap,binwmap,bintwmap,binarfcorr,wmap_clip,
                    wmap_threshold,tmpdir,clobber,verbose):
        
        common_dict = {"correct" : correct,
                       "weight" : weight,
                       "weight_rmf" : weight_rmf,
                       "refcoord" : refcoord,
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

                # also check that the binarfcorr parameter is greater than zero
                if float(binarfcorr) <= 0:
                    raise ValueError("'binarfcorr' must be greater than zero.")            
        else:
            if float(bintwmap) <= 0 :
                raise ValueError("'binarfwmap' must be greater than zero.")

        # no need to duplicate responses, since src and bkg responses will
        # be the same if refcoord!=""

        if refcoord != "" and bkgresp == "yes":
            v1(f"Responses for source and background are identical at {refcoord}, setting 'bkgresp=no' to avoid duplicate files.")

            bkgresp = "no"

        # Define the binning specification for RMFs output by the script.

        if ptype == "PI":
            rmfbin = f"pi={channel}"
        else:
            rmfbin = f"pha={channel}"

        common_dict["rmfbin"] = rmfbin

        #-----------------------------------------------------------
        # Determine whether or not to group source output spectrum,
        # and set appropriate grouping values.
        #
        # dogroup           # flag set if grouping
        # binspec           # grouping spec
        # gval              # grouping value
        #-----------------------------------------------------------

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

        #----------------------------------------------------------
        # Determine whether or not to group background output 
        # spectrum and set appropriate grouping values.
        #
        # bgdogroup           # flag set if grouping
        # bgbinspec           # grouping spec
        # bggval              # grouping value
        #----------------------------------------------------------

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


    def combine_stacks(self,src_stk,bkg_stk,out_stk,
                       asp,bpixfile,mask,dtffile,dafile,
                       weight,dobkgresp,refcoord,ewmap):

        # check that region extraction syntax does not take the erroneous form:
        # "sky=(src.reg)" or "sky=src.reg" which can lead to unexpected results
        # and very long run times
        try:
            # combine source and background into a list/set to validate with in a single pass
            in_stk = set(src_stk).union(set(bkg_stk))
        except (NameError,TypeError):
            in_stk = src_stk

        for fn in in_stk:
            self._valid_regstr(fn)

        # check counts in input files, and exit if necessary, or produce responses for upper-limits
        for src in src_stk:
            self._check_event_stats(src,refcoord_check=refcoord,weights_check=False)

        # check if there are counts in energy_wmap range for weighted ARFs/sky2tdet creation
        ewmap_srcbg_stk = []

        if weight == "yes":
            ewmap_srcbg_stk.extend(src_stk)

        if dobkgresp:
            ewmap_srcbg_stk.extend(bkg_stk)

        for fn in ewmap_srcbg_stk:
            if fileio.get_keys_from_file(f"{fn}[#row=1]")["INSTRUME"] == "ACIS":
                self._check_event_stats(fn,ewmap_range_check=ewmap)

        # find ancillary files, if exists, add to stack
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

        for key in ancil.keys():                          
            if ancil[key]["var"] == "":
                for obs in src_stk:
                    fobs = obsinfo.ObsInfo(obs)

                    v1(f"Using event file {obs} to determine ancillary files\n")

                    if key is "asol":
                        v3('Looking in header for ASOLFILE keyword\n')
                        asols = fobs.get_asol()
                        asolstr = ",".join(asols)

                        # ancil[key]["stk"].extend(asols)
                        ancil[key]["stk"].append(asolstr)

                        if len(asols) == 1:
                            suffix = ''
                        else:
                            suffix = 's'

                        v1(f"{ancil[key]['v1str']} file{suffix} {asolstr} found.\n")

                    else:
                        if key == "dtf" and fobs.instrument == "ACIS":
                            ancil[key]["stk"].append("")
                        else:
                            v3(f"Looking in header for {key.upper()}FILE keyword\n")
                            ancil[key]["stk"].append(fobs.get_ancillary(key))
                            v1(f"{ancil[key]['v1str']} file {fobs.get_ancillary(key)} found.\n")

            else:
                if type(ancil[key]["var"]) is list:
                    ancil[key]["stk"].append(ancil[key]["var"])

                else:
                    ancil[key]["stk"].extend(stk.build(ancil[key]["var"]))

        #-------------------------------------------------------
        # assign stacks to dictionary entires
        #-------------------------------------------------------

        stk_dict = {"asol" : ancil["asol"]["stk"],
                    "mask" : ancil["mask"]["stk"],
                    "dead time factor" : ancil["dtf"]["stk"],
                    "dead area" : dafile,
                    "badpix" : ancil["bpix"]["stk"]}

        #-------------------------------------------------------
        # ensure file stacks has either 1 or src_count elements
        #-------------------------------------------------------

        stk_count = {}
        src_count = len(src_stk)

        for key,fkey in stk_dict.items():
            if all([type(fkey) is list, "" not in fkey]):
                fkey = ",".join(fkey)

            try:
                if all([fkey, fkey.lower() not in [""," ","none"]]):
                    stk_dict[key] = stk.build(fkey)
                    self._check_files(stk_dict[key],key)
                    count = len(stk_dict[key])

                    if key is not "asol":
                        if count != 1 and src_count != count:
                            raise IOError(f"Error: {key} stack must have either 1 element or the same number of elements as the source stack.  Source stack={src_count}     {key} stack={count}")

                        if key is "badpix":
                            dobpix = True

                else:
                    stk_dict[key] = [""]

                    count = len(stk_dict[key])

                    if key is "badpix":
                        dobpix = False

            except (AttributeError,TypeError):
                stk_dict[key] = [""]

                count = len(stk_dict[key])

                if key is "badpix":
                    dobpix = False

            stk_count[key] = count

        #-------------------------------------------------------
        # check that there are no spaces in ancillary file
        # paths, if specified
        #-------------------------------------------------------

        for key in stk_dict.keys():
            for path in stk_dict[key]:
                if " " in os.path.abspath(path):
                    raise IOError(f"The absolute path for the {key} file, '{os.path.abspath(path)}', cannot contain any spaces")

        #-----------------------------------------------------
        # Determine if asphist or asol files were input
        # to the 'asp' parameter
        #-----------------------------------------------------

        stk_dict["asol"],stk_count["asol"],asolstat,ahiststat = self._asol_asphist(stk_dict["asol"],stk_count["asol"],src_stk)

        return stk_dict, stk_count, asolstat, ahiststat, dobpix


    def obs_args(self,src_stk,out_stk,bkg_stk,asp_stk,bpixfile_stk,rmffile,
                 dtffile_stk,mask_stk,dafile_stk,asolstat,ahiststat,dobpix,
                 common_args,stk_count):        

        weight = common_args.pop("weight",None) # remove keyword from dictionary and copy value
        dobg = common_args["dobg"]
        refcoord = common_args["refcoord"]
        binarfcorr = common_args["binarfcorr"]
        fcount = common_args["fcount"]

        src_count = len(src_stk)
        out_count = len(out_stk)

        #----------------------------------------------------------
        # Determine the file output types, either source files or
        # both source and background files.
        #----------------------------------------------------------

        if dobg:
            otype = ["src","bkg"]
        else:
            otype = ["src"]

        #------------------------------------------------------------------
        # Check all of the input files up front and make sure they are
        # readable. If not, notify the user of each bad file and exit.
        #
        # srcbkg                # the current output type
        # inputfile             # current input file to test
        # table                 # is the infile readable (!NULL)?
        # badfile               # is at least one of the input files bad?
        #
        # Do for each output type we are processing,
        # i.e. "src" or ( "src" and "bkg" )
        #
        #-------------------------------------------------------------------

        for srcbkg in otype:

            # Look at each file in the stack and check for readability.
            if srcbkg == "bkg":
                self._check_files(bkg_stk,"background")
            else:
                self._check_files(src_stk,"source")

        #---------------------------------------------------------
        # For each stack item in the source and background lists:
        #
        #    ) optionally set the ardlib bad pixel file
        #    ) convert src regions to phys. coords for ARF correction
        #    ) extract the spectrum
        #    ) create an ARF
        #    ) create a RMF
        #    ) optionally group the spectrum
        #    ) add header keywords
        #    ) optionally combine output spectra and responses
        #
        #----------------------------------------------------------

        # Do for each output type we are processing,
        # i.e. "src" or ( "src" and "bkg" )

        specextract_dict = {}

        for srcbkg in otype:
            arg_dict = {}

            # Determine which stack to use.
            if srcbkg == "bkg":
                cur_stack = bkg_stk
            else:
                cur_stack = src_stk

            #
            # Run tools for each item in the current stack.
            #
            for i in range(fcount):

                fullfile = cur_stack[i]
                filename = self._get_filename(cur_stack[i])
                instrument = fileio.get_keys_from_file(f"{filename}[#row=1]")["INSTRUME"]

                if fcount == 1:
                    iteminfostr = "\n"
                else:        
                    iteminfostr = f"[{i+1} of {fcount}]\n"


                    
                if instrument == "HRC" and weight == "yes":
                    weight = "no"
                    v1("HRC responses will be unweighted.")

                if not self._check_event_stats(fullfile,refcoord_check=refcoord,weights_check=True):
                    weight = "no"

                #  If we're using an output stack, then grab an item off of the stack
                #  but if not, then append "src1", "src2", etc., to the outroot
                #  parameter for each output file. If the outroot stack count equals 1
                #  but the source stack count is not equal to 1, treat the outroot
                #  parameter as the only root

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
                    obsid = fileio.get_keys_from_file(f"{filename}[#row=1]")["OBS_ID"]
                    asol_arg = asp_stk[f"{obsid}"]

                    if "," in asol_arg:
                        asol_arg = asol_arg.split(",")

                if ahiststat:
                    # set asol_arg for resp_pos
                    asol_arg = "none"

                    aspfile_block = get_block_info_from_file(asp_stk[i])

                    if aspfile_block[0].find("asphist") != -1:
                        if srcbkg != "bkg":
                            v1("Found a Level=3 ahst3.fits file in 'asp' input; the 'asphist' block corresponding to the source region location will be used.\n")

                        if stk_count["asol"] != 1:
                            asphist_arg = f"{stk_dict['asol'][i]}[asphist{self._event_stats(fullfile,'ccd_id')}]"
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

                ra,dec,skyx,skyy,chipx,chipy,chip_id = self.resp_pos(fullfile,asol_arg,refcoord,binimg=2) #binimg=binarfcorr)

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
                    v1("Warning: Skip adding 'bell_nh' header keyword.  No valid data at the source location in the Bell Labs HI Survey (the survey covers RA > -40 deg).\n")

                del(ra,dec)

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

        #######
        #
        #  Test using ~/cxcds_param4/specextract.par:
        #
        #  > import ciao_contrib._tools.specextract as spec
        #  > params,pars = get_par(["specextract.par"]) 
        #  > specdict = spec.ParDicts(params).specextract_dict()
        #
        #######

        common_dict = self.common_args(self.correct,self.weight,self.weight_rmf,self.bkgresp,
                                       self.refcoord,self.ptype,self.gtype,self.gspec,self.bggtype,
                                       self.bggspec,self.ebin,self.channel,self.ewmap,self.binwmap,
                                       self.bintwmap,self.binarfcorr,self.wmap_clip,self.wmap_threshold,
                                       self.tmpdir,self.clobber,self.verbose)

        src_stk, bkg_stk, out_stk, common_dict_append = self._check_input_stacks(self.infile,self.bkgfile,self.outroot,self.weight,self.bkgresp,self.ebin)

        common_dict = {**common_dict,**common_dict_append}

        # print(f"src_stk: {src_stk}")
        # print(f"bkg_stk: {bkg_stk}")
        # print(f"out_stk: {out_stk}")
        # print(f"asp: {asp}")
        # print(f"bpixfile: {bpixfile}")
        # print(f"mask: {mask}")
        # print(f"dtffile: {dtffile}")
        # print(f"dafile: {dafile}")
        # print(f"tmp: {tmpdir}")
    
        stk_dict, stk_count, asolstat, ahiststat, dobpix = self.combine_stacks(src_stk,bkg_stk,out_stk,
                                                                               self.asp,self.bpixfile,
                                                                               self.mask,self.dtffile,self.dafile,
                                                                               common_dict["weight"],
                                                                               common_dict["dobkgresp"],
                                                                               common_dict["refcoord"],
                                                                               common_dict["ewmap"])

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
        filter = True
        region_temp = full_filename.split("sky=")[1]

    elif "(x,y)=" in full_filename:
        filter = True
        region_temp = full_filename.split("(x,y)=")[1]

    elif "pos=" in full_filename:
        filter = True
        region_temp = full_filename.split("pos=")[1]

    else:
        filter = False

        if full_filename.startswith("@"):
            # deal with stacks
            pass
        else:
            region_temp = full_filename
            v1(f"WARNING: A supported spatial region filter was not detected for {full_filename}\n")

    if filter:

        if ")," in region_temp and ") ," in region_temp:

            region_temp2 = region_temp.partition("),")[0]+")"

            if ") ," in region_temp2:
                region = region_temp2.partition(") ,")[0]+")"
            else:
                region = region_temp2

        elif ")," in region_temp:
            region = region_temp.partition("),")[0]+")"

        elif ") ," in region_temp:
            region = region_temp.partition(") ,")[0]+")"

        else:
            region = region_temp.rpartition("]")[0]

    else:
        region = full_filename


    if not _check_filename_set(region):
        raise IOError(f"Please specify a valid spatial region filter for {full_filename} or use FOV region files.")

    return filter,region


