# See README.me for general info about CrissCross

# List of things I still need to do:
# - add back in ds9 figure generation so users can see where confusion occurs on the evt2 fits image.
# - add functionality for user to calculate confusion between two selected sources in a field of view and print results to screen.
# - Standardize names, e.g. "heh/meg" can be armtype, arm_par, arm, etc.  I should pick one and use it everywhere.
# - sort input parameters, e.g. always start with subest source (or put that in dict?), where osip, skyconverter, evtcrates go?
# - width_of_exclusion_region has hardcoded parameters for the extraction. Should be read from file.
# - Write parameters values used to run into header (either as history or as keywords)
# - rename "level" in output to "flag" and remove numeric flag for text output.
# - output "0th_order_confused_counts" is really CONFUSER counts in the original version. What do we want? Also doesn't take OSIP into account. Do we want that?
##########################################################################################
##########################################################################################
##########################################################################################
import itertools
from pathlib import Path
import os
import glob
import shutil
import time

import numpy as np
from numpy.lib import recfunctions as rfn

from pycrates import (
    read_file,
    write_file,
    get_keyval,
    read_pha,
    write_pha,
    is_pha_type1,
    is_pha_type2,
    update_crate_checksum,
    get_history_records,
    set_key,
)
from crates_contrib.utils import make_table_crate
from ciao_contrib import runtool as rt
from iocaldb import OSIP, Sky2Chandra, Cel2Chandra
from widthofexclusion import counts_circle_band, pnt_src_masking_region


############## CONSTANTS ##############
tg_part_name = ["zeroth order", "heg", "meg", "leg"]

X_R = 8632.48  # rowland diameter in mm constant

# period in angstroms constant. Note, this is value from telD1999-07-23geomN0006.fits in CALDB
Period = {
    "meg": 4001.95,  # however in marxsim it uses 4001.41 A
    "heg": 2000.81,
}
mm_per_pix = 0.023987  # pixel size in mm for acis same for I and S;  pix size in arcsec is 0.492''

hc = 4.1357e-15 * 2.998e18
"conversion for E = hc/lamda where h and c are units of plancks const and angstrom/s"

############################################################

##### FLAG DEFINITIONS #####
# Which flag do they get if the intersection point is outside the CCD?
flags_spec = {
    "outside_primary_source_wave_coverage": 1,  # 995
    "outside_confuser_source_wave_coverage": 2,  # 996
    "outside_osip_range": 4,
    "confuser_has_no_0th_order_counts": 8,  # 992
    "confuser_has_0_disp_counts_in_order": 16,  # 981
    "confusion_smaller_than_conf_ratio": 32,  # 985
    "confused_has_0_disp_counts_and_confuser_gtr_0": 64,  # 980
    "confusion_above_conf_ratio": 128,  # 986
}
flags_spec_levels = {"clean": -1, "warn": 0, "confused": 64}

flags_pnt = {
    "confusing_pntsrc_but_no_counts": 1,  # 9999
    "confusing_pntsrc_but_relatively_few_counts": 2,  # 9998
    "confusing_pntsrc_too_weak_and_too_far": 4,  # 9997
    "pntsrc_conf_outside_resp_region": 8,  # 9995
    "pntsrc_confusion": 16,  # 9996
}
flags_pnt_levels = {"clean": 0, "warn": 2, "confused": 16}

flags_arm = {"arm_confusion": 1}
flags_arm_levels = {"clean": 0, "warn": 0, "confused": 1}

flags = {
    "spec": (flags_spec, flags_spec_levels),
    "pnt": (flags_pnt, flags_pnt_levels),
    "arm": (flags_arm, flags_arm_levels),
}


###### OUTPUT DEFINITIONS ######
rec_type = np.dtype(
    dtype=[
        ("src_id", "<i8"),
        ("confuser_srcid", "<i8"),
        ("0_order_confused_counts", "<f8"),
        ("grating_type", "<U3"),
        ("order", "<i8"),
        ("confusing_order", "<i8"),
        ("confusion_type", "<U4"),
        ("confusion_wave", "<f8"),
        ("wave_low", "<f8"),
        ("wave_high", "<f8"),
        ("flag", "<i8"),
    ]
)

#############FUNCTION DEFINITIONS###############
def calc_off_axis_modifier(theta_arcsec):
    """

    At larger off-axis angles, the PSF gets larger and thus point sources and grating arms
    look wider.

    Parameters
    ----------
    theta_arcsec : float
        off-axis angle in arcseconds

    Returns
    -------
    modifier : float
        multiplier to apply to distances
    """
    out = np.ones_like(theta_arcsec)
    out[theta_arcsec > 180] = 2
    out[theta_arcsec > 360] = 3
    return out


def make_output_dir(cc_outdir, obsid_par, clobber_par=False):
    """
    Creates a CrissCross directory to hold all output. Each obsID will get its own subdir. Reports back to main
    function if output dir exists so it can exit without removing if clobber=False.

    Parameters
    ----------
    cc_outdir : str
        directory name or path to hold all CrissCross output.
    obsid_par : str
        obsID value of the observation used for naming subdirectory.
    clobber_par : bool
        boolean which is set by main function to determine whether cc subdirs should be clobbered when run.
    """
    # create a subdir for each obsID run
    output_dir = f"{cc_outdir}/output_dir_obsid_{obsid_par}"
    already_exists = os.path.isdir(output_dir)

    # if an output directory for this obsID already exists then delete it first
    if clobber_par and already_exists:
        shutil.rmtree(output_dir)

    os.makedirs(cc_outdir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    return (output_dir, already_exists)


def get_header_par(fits_file, keyword_par):
    """
    Retrieves header keyword value

    Parameters
    ----------
    fits_file : str
        fits file which holds the relevant header keyword
    keyword_par : str`
        header keyword value to retrieve
    """

    rt.dmkeypar.punlearn()
    a = rt.dmkeypar(infile=fits_file, keyword=keyword_par)
    return_val = rt.dmkeypar.value

    return return_val


# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# See wavedetect open question at top
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
def run_wavdetect(
    evt2_file=None,
    outdir=None,
    outroot="sdetect",
    binsize=2.0,
    bands="broad",
    psfecf=0.9,
    verbose=0,
    clobber="yes",
):
    """
    Performs source detection on an obsID with the goal of determining the number of 0th order counts for each
    source in field. The only file used in CrissCross by this function is the wavdetect.outfile source detection table.
    This function is run if user does not provide source table. Function runs fluximage and wavdetect on an evt2 file
    and requires a evt2 directory setup such that the ancillary ACIS files can be automatically found by CIAO.

    Parameters
    ----------
    evt2_file : str
        event file for running the source detection.
    outdir : str
        directory for holding the wavdetect output.
    outroot : str
        root for naming wavdetect output.
    binsize : float
        CIAO tool fluximage parameter binning factor. binsize=4 corresponds to 1.968 arcseconds pixels for ACIS.
    bands : str
        CIAO tool fluximage par denoting the energy bands used for exposure-corrected images. See band definitions in
        the CSC documentation. Example options are 'broad': 0.5-7.0 keV with eff E of 2.3 keV, 'soft','medium','hard'.
    psfecf : float
        fluximage par for creating a PSF map with the provided encircled energy fraction.
    verbose : int
        CIAO verbose level for printing log to screen.
    clobber : bool
        CIAO clobber value to overwrite files.
    """

    print(
        f"\nNo input wavdetect source fits table provided so running wavdetect on {evt2_file} with binsize={binsize}, bands={bands} and psfecf={psfecf}."
    )
    print(
        "If you wish to use other wavdetect parameters please run wavdetect and provide a wavdetect source fits table.\n"
    )

    rt.fluximage.punlearn()
    rt.fluximage.infile = evt2_file
    rt.fluximage.outroot = f"{outdir}/{outroot}"
    rt.fluximage.binsize = binsize
    rt.fluximage.bands = bands
    rt.fluximage.psfecf = psfecf
    rt.fluximage.verbose = verbose
    rt.fluximage.clobber = "yes"

    rt.fluximage()

    rt.wavdetect.punlearn()
    rt.wavdetect.infile = f"{outdir}/{outroot}_{bands}_thresh.img"
    rt.wavdetect.psffile = f"{outdir}/{outroot}_{bands}_thresh.psfmap"
    rt.wavdetect.outfile = f"{outdir}/{outroot}_src.fits"
    rt.wavdetect.scellfile = f"{outdir}/{outroot}_scell.fits"
    rt.wavdetect.imagefile = f"{outdir}/{outroot}_imgfile.fits"
    rt.wavdetect.defnbkgfile = f"{outdir}/{outroot}_nbgd.fits"
    rt.wavdetect.regfile = f"{outdir}/{outroot}_src.reg"
    rt.wavdetect.verbose = verbose
    rt.wavdetect.clobber = clobber

    rt.wavdetect()

    return f"{outdir}/{outroot}_src.fits"


def wavedetect_match_obsid(fits_list_par, wavdetect_list_par):
    """
    Uses the obsID header value from the evt file (fits_list) and wavedetect source tables (wavedetect_list)
    to reorder the wavdetect_list to match the evt2_list. If users provide a list of evt2 and wavdetect source tables
    then this function ensures they are not mis-matched when running in CrissCross.

    Parameters
    ----------
    fits_list_par : str
        a single evt2 filename or a list of evt2 file names.
    wavdetect_list_par : str
        a single wavdetect output source table or a list of them.
    """

    fits_obsid = []
    wave_obsid = []

    wavedetect_sorted = []

    for i in range(0, len(fits_list_par)):
        wave_obsid.append(
            get_header_par(fits_file=wavdetect_list_par[i], keyword_par="obs_id")
        )
        fits_obsid.append(
            get_header_par(fits_file=fits_list_par[i], keyword_par="obs_id")
        )

    for i in range(0, len(fits_list_par)):
        for j in range(0, len(wave_obsid)):
            if fits_obsid[i] == wave_obsid[j]:
                wavedetect_sorted.append(wavdetect_list_par[j])

    return wavedetect_sorted


def load_sourcelist(filename=None, subset_list=False):
    """
    Load an ascii, tsv or fits file with RA, DEC and ID columns using pycrates. If an ID column is not found for the
    full list of field sources then and ID column is generated. The file is expected to have a header column
    of #RA DEC ID. If it does not then the first two columns read in will be treated as RA and DEC and a warning
    message is printed to screen. This function is used for both the main source list and the subset list. The subset
    list must be matched to the main_list source ID (or element number) using match_subset_to_main().

    Parameter
    ---------
    filename = str
        ascii, tsv or fits table with RA, DEC and ID columns.
    subset_list = bool
        Boolean denoting whether this function is to be run on the main list of sources or the subset list of sources.
    """

    if filename is not None:
        # default to setting a flag to no generate the ID column
        gen_id = False

        # read the data file in and get info about columns
        cratedata = read_file(filename)
        colnames = cratedata.get_colnames()
        crate_len = len(colnames)

        # check to see if user forgot to put hash in front of column header which would result in crate being type <U17
        if cratedata.get_column(colnames[0]).values.dtype == "<U17":
            raise TypeError(
                "\nFirst row of file cannot be of string format. If header columns are present please ensure # is first character of line.\n"
            )

        elif crate_len < 2:
            raise TypeError(
                f'\nERROR reading "{filename}". Please ensure file type is ascii or tsv and there are at least two columns (RA DEC) in degrees\n'
            )

        # if len=2 then probably only RA and DEC present. For the subset_list, do NOT create new ID values because they
        # must match the main_list IDs.
        elif crate_len == 2 and not subset_list:
            print(
                "No ID column found so IDs will be generated from 0 to length of file"
            )
            gen_id = True

        # if len=3 the prob RA, DEC, ID so check ID column to make sure they can be converted to integers necessary for
        #  naming purposes
        elif crate_len == 3:
            idcol_test = cratedata.get_column(colnames[2]).values
            try:
                idcol_test.astype(int)
            except:
                raise TypeError("Third column of input file need to be integers")

            if len(np.unique(idcol_test)) != len(idcol_test):
                raise TypeError(
                    "ID column does not contain unique identifier for each source"
                )

            if colnames[2] != "ID" and colnames[2] != "id":
                print(
                    f'Warning -- Column 2 of "{filename}" is not ID or id. Assuming it is ID from now on.'
                )

        else:
            print(
                f'File "{filename}" contains more than three columns and the rest will be ignored.'
            )

        # check if the first two columns have typical names of RA and DEC otherwise warn.
        if colnames[0] != "RA" and colnames[0] != "ra":
            print(
                f'Warning -- Column 1 of "{filename}" is not RA or ra. Assuming it is RA from now on.'
            )
        if colnames[1] != "DEC" and colnames[1] != "dec":
            print(
                f'Warning -- Column 2 of "{filename}" is not DEC or dec. Assuming it is DEC from now on.'
            )

        RA = cratedata.get_column(colnames[0]).values
        DEC = cratedata.get_column(colnames[1]).values
        if gen_id:
            ID = np.arange(0, len(RA))
        elif not subset_list:
            ID = cratedata.get_column(colnames[2]).values.astype(int)

        if not subset_list:
            return (RA, DEC, ID)
        elif subset_list:
            return (RA, DEC)
        else:
            raise ValueError("Something went wrong with subset_list truth value.")
    else:
        raise ValueError(
            "CrissCross needs to be run with a list of known sources RA and DEC."
        )


def match_subset_to_main(RA_main, DEC_main, RA_sub, DEC_sub, round_sig=6):
    """
    Matches sources from the subset_list to the main_list by RA and DEC. All sources in the subset list MUST be also in
    the main list and matched via the element number of the input main_list array. For example, if source number 10 in
    the subset_list (row 10) is the same source as row 200 in the main_list, then source 10 will be matched with
    element 200 and CrissCross will use e.g. src_pos_x[200], src_pos_y[200] when handling subset_list source 10. If
    no or multiple matches are found for a single source then error is thrown. Every source must be unique.

    Parameters
    ----------
    RA_main : float, deg
        Right Ascension of main_list source in J2000 degrees
    DEC_main : float, deg
        Declination of main_list source in J2000 degrees
    RA_sub : float, deg
        Right Ascension of subset_list source in J2000 degrees
    DEC_sub : float, deg
        Declination of main_list source in J2000 degrees
    round_sig : int
        Number of digits to round RA/DEC to for matching purposes.
    """

    element = [None] * len(RA_sub)
    # for each source in the subset_list match it using RA and DEC to a source in the main_list. Check for mult matches
    for i in range(0, len(RA_sub)):
        element[i] = np.where(
            (np.round(RA_sub[i], round_sig) == np.round(RA_main, round_sig))
            & (np.round(DEC_sub[i], round_sig) == np.round(DEC_main, round_sig))
        )[0]
        if len(element[i]) == 0:
            raise ValueError(
                f"No match in main list found for subset source RA={RA_sub[i]} and DEC={DEC_sub[i]}. Please make sure RA and DEC value of source to clean matches a source in main_list."
            )

        elif len(element[i]) > 1:
            raise ValueError(
                f"Multiple matches [{len(element[i])}] in main list found for subset source RA={RA_sub[i]} and DEC={DEC_sub[i]}. Please make sure there are no duplicate entries in main list or subset_list"
            )
        # strip array to provide only integer value
        else:
            element[i] = element[i][0]

    return element


def calc_physical_coords(fits_par, RA_par, DEC_par):
    """
    Converts from RA and DEC in WCS degrees to Chandra physical coordinates. This also determines the off-axis angle
    and converts it to arcseconds.

    Parameters
    ----------
    fits_par : str
        evt2 fits file.
    RA_par : str
        Right ascension in degrees.
    DEC_par : str
        Declination in degrees.
    """

    cel_convert = Cel2Chandra(fits_par)

    pos_x_par = np.zeros(len(RA_par))
    pos_y_par = np.zeros(len(DEC_par))
    off_axis_ang = np.zeros(len(RA_par))

    for i in range(0, len(RA_par)):
        a = cel_convert(RA_par[i], DEC_par[i])
        pos_x_par[i] = a["x"][0]
        pos_y_par[i] = a["y"][0]
        off_axis_ang[i] = a["theta"][0] * 60.0  # convert from arcmin to arcsec

    return (pos_x_par, pos_y_par, off_axis_ang)


def find_closest_source(src_x, src_y, wave_file, max_offset=3.0):
    """
    Matches sources from the main_list to the wavdetect source table with the goal of removing erroneous
    disperssed-grating-line sources. Wavdetect is not meant to be run on HETG observations and thus will include many
    'false' detections from the dispersed spectra. This identifies the closest matching source in a group to a single
    source based on Chandra SKY physical coordinates only. If multiple matches are found for a single source within
    max_offset, only the closest of the matches is assigned to the source. This avoids 'double counting'. This returns
    the number of NET_COUNTS associated with 0th order (non-dispersed) detections. NET_COUNTS are used throughout
    CrissCross to determine the severity of confusion.

    Parameters
    ----------
    src_x : float, array
        src x position in Chandra physical units.
    src_y : float, array
        src y position in Chandra physical units.
    wave_file : str
        path to wavdetect output source fits table.
    max_offset : float
        The max distance in arcsec two sources can be before they are no longer considered matchable between the source
        list and the wavdetect table. All sources are treated the same regardless of off-axis angle which is generally
        ok because centroids should be relatively good as determined by wavdetect.
    """

    # ACIS parameters for converting distance from pixels to arcseconds
    acis_platescale = 48.82e-6  # meters/arcsec
    acis_pix_size = 24e-6  # meters / pixel (square pixels)
    acis_arcsec_per_pix = acis_pix_size / acis_platescale

    # read in and assign relevant wavdetect columns
    wave_data = read_file(wave_file)

    src_wave_x_arr = wave_data.POS.X.values
    src_wave_y_arr = wave_data.POS.Y.values
    counts_wave = wave_data.NET_COUNTS.values

    closest_dist_arr = np.empty(
        len(src_x), dtype="float"
    )  # holds the distance in arcsec to the closest matching source from the wavedetect table
    closest_match_arr = np.empty(
        len(src_x), dtype="int"
    )  # holds the index value from the wavedetect table that is the closest match to a source in the source list.

    # these will hold the values above for the matched source AFTER you remove double matches and sources > max_offset.
    final_match_arr = np.empty(len(src_x), dtype=object)
    final_dist_arr = np.empty(len(src_x), dtype=object)

    matched_0th_counts_arr = np.empty(
        len(src_x), dtype="float"
    )  # the final 0th_order counts array (NET_COUNTS) from the wavedetect table MATCHED to the user-provided source list.

    # this loop determines the distance from the user-provided source to ALL the sources in the wavedetect table and
    # only saves a non-bogus value if there is a source with separation < max_offset.
    for i in range(0, len(src_x)):
        dist_arr = []
        dist_arr = np.sqrt(
            (src_x[i] - src_wave_x_arr) ** 2 + (src_y[i] - src_wave_y_arr) ** 2
        )  # This calculates the physical distance from source [i] in the user-provided table to ALL sources in the
        # wavedetect table. This is just the hypotenuse in the xy plane. Note, calculating the ENTIRE array here for
        #  each [i] source and NOT each [i] and each [j] individually.

        closest_dist = []
        closest_dist = (
            np.min(dist_arr) * acis_arcsec_per_pix
        )  # converted from sky coords to arsec

        # if distance is > max offset then assign values of 99999 (bogus) and filter out in next loop. Otherwise,
        # assign matched values.
        if closest_dist <= max_offset:
            closest_dist_arr[i] = closest_dist
            closest_match_arr[i] = np.where(dist_arr == np.min(dist_arr))[0][0]  #
        else:
            closest_dist_arr[i] = 99999
            closest_match_arr[i] = 99999

    # this loop will remove 'double counting' where a single user-provided source might match to multiple wavedetect
    #  sources. This will only match to the closest one and remove that from the pool of potential matches for other sources.
    for i in range(0, len(src_x)):
        common_matches = np.where(
            closest_match_arr == closest_match_arr[i]
        )[
            0
        ]  # this will give an array of index values which all have the same closest matched source.
        common_matches_dist = closest_dist_arr[
            common_matches
        ]  # this will provide an array of all of the distances for the closest matched sources. The idea is that
        # only the closest distance can be assigned to a single source (no double counting).

        if (
            (closest_dist_arr[i] <= max_offset)
            and (closest_dist_arr[i] == np.min(common_matches_dist))
        ):  # if the current source's closest distance is the closest of all the common matches then it is 'correct'
            # and assigned the wavedetect number of counts. Otherwise, counts are set to 0 (not detected)
            final_match_arr[i] = closest_match_arr[i]
            final_dist_arr[i] = closest_dist_arr[i]
            matched_0th_counts_arr[i] = counts_wave[closest_match_arr[i]]
        else:
            final_match_arr[i] = "no match"
            final_dist_arr[i] = "no match"
            matched_0th_counts_arr[i] = 0

    return (final_match_arr, final_dist_arr, matched_0th_counts_arr)


def write_matched_file(
    srcid_par,
    ra_par,
    dec_par,
    counts_par,
    fileroot="matched_source_list",
    output_type="txt",
):
    """
    Creates a csv or txt file to save SrcID, RA, Dec and wave_detect_matched 0th order counts.

    Parameter
    ---------
    srcid_par : int, array
        source ID values from the input main_list.
    ra_par, dec_par : float
        J2000 Right ascension and declination taken from the input main_list
    counts_par : float
        The number of 0th order counts matched to each main_list source using the wavdetect source detection table.
    fileroot : str
        root for naming purposes
    output_type : str
        text file output type to save. Can be 'txt' or 'csv'.
    """

    filestack = np.column_stack((srcid_par, ra_par, dec_par, counts_par))
    if output_type not in ["txt", "csv"]:
        raise ValueError("The only output types accepted are csv and txt.")

    delimiter = {"csv": ",", "txt": "\t"}
    np.savetxt(
        f"{fileroot}.{output_type}",
        filestack,
        delimiter=delimiter[output_type],
        fmt=["%d", "%.6f", "%.6f", "%.1f"],
        header="ID,RA,DEC,0th_counts",
        comments="",
    )


def determine_line_intersect_values(src_pos, norm_arm1, norm_arm2):
    r"""Calculate the intersection of two lines defined by norm_arm1 and norm_arm2.

    Each line is defined by the equation:
    :math:`\vec{X} = \vec{S} + k \cdot \vec{N_{arm}}`

    where :math:`\vec{X}` describes any point on the line
    :math:`\vec{S}` is the source position
    :math:`\vec{N_{arm}}` is the normalized direction vector for the arm
    and :math:`k` is a scalar parameter that describes how far along the line you are from the source.

    Parameters
    ----------
    src_pos : np.ndarray
        An (n, 2) array of source positions.
    norm_arm1 : np.ndarray
        A (2,) array representing the normalized direction vector of the first line.
    norm_arm2 : np.ndarray
        A (2,) array representing the normalized direction vector of the second line.

    Returns
    -------
    k1 : np.ndarray
        An (n, n) array of scalar parameters k for the first line. See the example below for the
        ordering of the elements and the meaning of the indices.
    k2 : np.ndarray
        An (n, n) array of scalar parameters k for the second line. See the example below for the
        ordering of the elements and the meaning of the indices.

    Note
    ----
    See https://en.wikipedia.org/wiki/Line–line_intersection#Given_two_points_on_each_line_segment
    for more details on the mathematical formulation used in this function.

    Example
    -------
    While the geometric :math:`\vec{X} = \vec{S} + k \cdot \vec{N_{arm}}` is simply enough for
    a single point, we are calculating the intersection for multiple sources at once and it is easy
    to get confused about the ordering of the indices in the output arrays and in which dimension
    the array of sources needs to be broadcast. Thus, below is a fill example.

    `src_pos` is an (n, 2) array of source positions, thus

        >>> x_i, y_i = src_pos[i, :]

    The output arrays `k1` and `k2` are (n, n) arrays where the element `k1[i, j]`
    the distance from source i along the first line to the intersection point with the second line
    defined by source j and `norm_arm2`.

    This this definition, you cna obtain the x,y coordinates of all intersection points with:

        >>> intersect = xy[:, np.newaxis, :] + k1[:, :, np.newaxis] * norm_arm1

    or, equivalently,

        >>> intersect = xy[:, np.newaxis, :] + k2[:, :, np.newaxis] * norm_arm2

    In either case, `intersect` is an (n, n, 2) array where `intersect[i, j, :]` gives
    the x,y coordinates of the intersection point between the line defined by source i and
    `norm_arm1` and the line defined by source j and `norm_arm2`.

    """
    if not np.isclose(np.linalg.norm(norm_arm1), 1):
        raise ValueError("norm_arm1 needs to be normalized to length 1.")
    if not np.isclose(np.linalg.norm(norm_arm2), 1):
        raise ValueError("norm_arm2 needs to be normalized to length 1.")
    if np.isclose(np.dot(norm_arm1, norm_arm2), 1):
        raise ValueError(
            "norm_arm1 and norm_arm2 are parallel, so there is no intersection point."
        )
    s_minus_s = src_pos[np.newaxis, :, :] - src_pos[:, np.newaxis, :]
    # broadcast (x y) norm vectors to shape (n, n, 2)
    bvec_norm1 = np.broadcast_to(norm_arm1, s_minus_s.shape)
    bvec_norm2 = np.broadcast_to(norm_arm2, s_minus_s.shape)

    k1_nominator = np.linalg.det(np.stack([s_minus_s, -bvec_norm2], axis=-1))
    k2_nominator = np.linalg.det(np.stack([-bvec_norm1, s_minus_s], axis=-1))
    denominator = np.linalg.det(np.stack([bvec_norm1, bvec_norm2], axis=-1))

    k1 = k1_nominator / denominator
    k2 = k2_nominator / denominator

    return k1.T, k2.T


####SPECTRAL CONFUSION FUNCTIONS####


# Calculate number of counts when determining CONFUSER counts in one order compared to CONFUSED counts in another order.
def calc_num_counts(ratio_pycrates, order, order_zero_counts, bin_start, bin_end):
    """
    Estimates the number of Nth order counts in a spectral arm given a number of 0th order counts and a discrete
    wavelength range. This information comes from the data table of ARF ratios (Nth_order / 0th_order) calculated
    from a single HETG on-axis observation. This is to be used as an approximation and will not be exact. If the
    discrete wavelength range covers several ARF bins then a mean of the spectral response bandpass is calculated.
    Note, some bandpasses cover big dips in ARF and thus mean may affect results.

    Parameters
    ----------
    ratio_pycrates : fits table
        CrissCross fits input table which contains the ratios of responses based on a single on-axis HETG
        observation. Note, since this takes the ratio of different orders, the buildup of ACIS contamination over
        time should not affect this calculation.
    order : crates column
        The crates column associated with HEG/MEG order.
    order_zero_counts : int
        The number of 0th order counts of the confused source determined in the wavelength bandpass where spectral
        confusion occurs. This number will be calculated by counts_circle_band().
    bin_start, bin_end : float
        The first and last wavelength in Angstrom where mean response is taken in the ARF tables.

    Returns
    -------
    num_counts = An estimation of the number of counts from the confusing source expected to be dispersed into
    the confused spectral order.
    avg_ratio_value = The average spectral response in the bin_start, bin_end bandpass used to estimate num_counts.
    """
    bin_lo = ratio_pycrates.BIN_LO.values
    in_range = (bin_start <= bin_lo) & (bin_lo < bin_end)
    order_data = ratio_pycrates.get_column(order)
    avg_ratio_value = np.average(order_data.values[in_range])
    num_counts = avg_ratio_value * order_zero_counts

    return (num_counts, avg_ratio_value)


def spec_confuse_wave(
    subset_sources,
    intersect_info,
    arm,
    counts,
    min_spec_counts,
    min_spec_confuser_counts,
    width_mask_pixel,
    obsid_par,
    outdir,
    osip_frac,
    arf_ratios_dir,
    cutoff,
    osip,
    skyconverter,
    evtcrates,
    spec_confuse_limit,
):
    """
    Calculates the distance from the 0th order of src i to the location where confusion may occur ['intersect_dist']
    and converts that into wavelength in angstroms ['wave'] using the gratings equation.

    Parameters
    ----------
    subset_sources : list of int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    intersets : dict
        Holding information aboout the source locations, arm locations, and arm intersection points.
    armtype : str
        HETG arm type of 'heg' or 'meg'.
    counts : np.array
        number of 0th order counts for all sources
    min_spec_counts, min_spec_confuser_counts : int
        CrissCross input parameter denoting the 0th order counts threshold to consider a source for spectral confusion.
    width_mask_pixel : float
        Full width in pixels of the region that is marked as bad when confusion occurs.
         It is no recommended to go smaller than the default values as they are determined based on the intstrument.
    fits_list_par : str
        evt2 file associated with the observation for the confusion determination.
    obsid_par : str
        obsID value of the observation.
    outdir : str
        Output directory used to create the log file assocaited with running the osip function.
    osip_frac: float
        CrissCross parameter which controls the size of the OSIP window. A value of 1.0 keep 100% of the OSIP window.
        This parameter can be tweaked lower to make the confusion estimate less conservative.
    arf_ratios_dir : str
        Path to CrissCross arf ratios tables necessary to account for efficiencies between orders.

    Notes
    -----

    The logic in this function is complicated so it is summarized here:

    (1) Run the following checks only for the cases where spectral arms intersect and then set flag appropriately:

    (a) If the confuser source intersects the arm of the (potentially) confused source outside of the heg/meg
        cutoff energies (<1 A or >~ 16, 32 A) of the confused source then NO ORDERS of the confuser source could
        confuse so assign a warning flag (flag_995)

    (b) If the intersection occurs in the valid range of wavelengths for meg/heg then check the following for
        EACH order:

        (i) Is the confuser's m order wavelength range within the bounds of HEG/MEG? If not, set warning flag
            (flag_996) and check other orders.

        (ii) If (i) is TRUE, is the confuser's m order within the same wavelength range as the confused source is
            expecting at the location of the intersection (i.e., the OSIP window of the confused source at the
            intersection location)? If not, mark as 'clean' unless a previous order has been flagged as 'warn'
            or 'confused'.

        (iii) If (ii) is TRUE then calculate the number of 0th order counts of the CONFUSER source within the OSIP
        range for the spectral intersection location. If confuser source 0th order has 0 counts then no need to
        check for confusion anymore and set 'warning' flag. If confuser 0th order has > 0 counts then determine
        the number of 0th order counts from the CONFUSED source in the OSIP range. Use the number of 0th order
        counts for both sources and the HEG/MEG-0th-order-to-nth-order ARF tables to estimate the number of
        dispersed counts from both sources landing in the intersection spot of the potentially confused source.
        Use ratio of estimated dispersed counts to determine if confusion occurs and flag appropriately.

    This calculation should account for the heg/meg order efficiencies and ARFs BUT assumes an on-axis source at
    the pointing location. This WILL be slightly different for any other source but to first order it should be ok.
    This calculation uses the AVERAGE response ratio in the calculated OSIP range. If OSIP range is large then
    it is washing out some details in the arfs but for estimation purposes it should be ok.
    """
    # For the meg we need to transpose the first two axis
    intersect = intersect_info["heg_meg_intersects"]
    orders = intersect_info["orders"]
    srcpos = np.diagonal(intersect).T

    if arm == "meg":
        intersect = np.moveaxis(intersect, 1, 0)
    secondary_arm = "meg" if arm == "heg" else "heg"
    mask_interval = width_mask_pixel * mm_per_pix / X_R * Period[arm]
    primary_arf = read_file(
        f"{arf_ratios_dir}/{arm.upper()}_Nth_0th_order_ratios_mkarf.fits"
    )
    secondary_arf = read_file(
        f"{arf_ratios_dir}/{secondary_arm.upper()}_Nth_0th_order_ratios_mkarf.fits"
    )

    intersect = intersect[subset_sources, :, :]
    srcpos_subset = srcpos[subset_sources, :]

    mwave = intersect_info["mwave"][arm][subset_sources, :]
    mwave2 = intersect_info["mwave"][secondary_arm][:, subset_sources].T
    # divide by order number to get wavelength for each order
    wave = mwave[..., np.newaxis] / intersect_info["orders"]
    wave2 = mwave2[..., np.newaxis] / intersect_info["orders"]

    # We now build up the intersections and orders where confusion occurs
    # with a series of step of filtering, each one removing more and more
    # "confusion" candidates, setting more and more of the "confusion" array to False.
    # The first few steps can be done on simple matrix equations, the
    # laters ones are more computationally expensive and so we loop them only
    # over sources and orders where confusion is possible.
    # Arrays that deal with the confuser (e.g. the wavelength at each intersection are
    # of shape (n_confused_sources, n_confuser_sources, n_orders_confused)
    # and arrays that deal with the confuser are
    # of shape (n_confused_sources, n_confuser_sources, n_orders_confuser).
    # The shape of a flag array for all possible confusions cases is:
    # (n_confused_sources, n_confuser_sources, n_orders_confused, n_orders_confuser)
    # so 3D arrays need to be broadcast to the right shape.

    # Step 1: Select spectra and confusers with enough counts to be relevant.
    confusion = (counts > min_spec_counts)[subset_sources, np.newaxis] & (
        counts > min_spec_confuser_counts
    )[np.newaxis, :]
    # Now expand to 4d shape
    confusion = np.tile(
        confusion[:, :, np.newaxis, np.newaxis], (1, 1, len(orders), len(orders))
    )
    # 0 mean "clean". All flags start clean and flages are added step by step.
    flag = np.zeros_like(confusion, dtype=int)
    # Step 2: Negative k values correspond to negative orders and positive k values
    # correspond to positive orders, so mwave / k is always positive for valid
    # intersections.
    # It's 0 for a source compared to itself.
    confusion = confusion & (wave[:, :, :, np.newaxis] > 0)

    # Step 2: Arms that intersect so close in or so far out that confusion would be
    # at undetectable wavelengths can be ignored.
    # That's true if either the confused or the confuser spectrum is in the range of
    # energies that can't be detected with ACIS or the grating's don't disperse them.
    far_out_confused = (wave < cutoff[arm][0]) | (wave > cutoff[arm][1])
    flag[confusion & far_out_confused[:, :, :, np.newaxis]] += flags_spec[
        "outside_primary_source_wave_coverage"
    ]
    confusion = confusion & ~far_out_confused[:, :, :, np.newaxis]
    far_out_confuser = (wave2 < cutoff[secondary_arm][0]) | (
        wave2 > cutoff[secondary_arm][1]
    )
    flag[confusion & far_out_confuser[:, :, np.newaxis, :]] += flags_spec[
        "outside_confuser_source_wave_coverage"
    ]
    confusion = confusion & ~far_out_confuser[:, :, np.newaxis, :]

    # Step 3: Is the confusing arm within the OSIP?

    # For all vallues we consider below, the initial value will be overwritten.
    # Setting the initial value to 1 avoids "devide by zero" errors for elements we don't care about.
    energy_low = np.ones_like(wave, dtype=float)
    energy_high = np.ones_like(wave, dtype=float)

    spec_confuse_log_file = open(f"{outdir}/spec_confuse_{obsid_par}_log.txt", "w")
    for i, j in itertools.product(range(wave.shape[0]), range(wave.shape[1])):
        if confusion[i, j].any():
            result = osip(
                intersect[i, j, 0],
                intersect[i, j, 1],
                (hc / wave[i, j, :]),
                spec_confuse_log_file,
            )
            energy_low[i, j, :] = result[0]
            energy_high[i, j, :] = result[1]
    spec_confuse_log_file.close()
    # convert osip from energy to angstrom and account for user parameter osip_frac (fractional size
    # of osip window of choice --e.g., user could want smaller than large osip window)
    mask_width = (1 - osip_frac) * (hc / energy_low - hc / energy_high)
    osip_low = hc / energy_high + mask_width / 2
    osip_high = hc / energy_low - mask_width / 2

    outside_osip = (wave2[:, :, np.newaxis, :] < osip_low[:, :, :, np.newaxis]) | (
        wave2[:, :, np.newaxis, :] > osip_high[:, :, :, np.newaxis]
    )
    flag[confusion & outside_osip] += flags_spec["outside_osip_range"]
    confusion = confusion & ~outside_osip

    # Step 4: Do we expect any signal from the confuser within the OSIP range?
    confuser_0th_counts = np.full_like(wave2, -1)
    for i, j, o in itertools.product(
        range(wave.shape[0]), range(wave.shape[1]), range(len(orders))
    ):
        if confusion[i, j, o, :].any():
            confuser_0th_counts[i, j, o] = counts_circle_band(
                evtcrates,
                srcpos[j],
                [
                    osip_low[i, j, o],
                    osip_high[i, j, o],
                ],
                skyconverter,
                psffrac=0.9,
            )  # num 0th order counts in contaminating spectrum at SAME osip window of confusion

    flag[confusion & (confuser_0th_counts == 0)[:, :, :, np.newaxis]] += flags_spec[
        "confuser_has_no_0th_order_counts"
    ]
    confusion = confusion & (confuser_0th_counts > 0)[:, :, :, np.newaxis]

    # Step 5: See if confuser contributes any counts.
    confuser_counts_secondary = np.full_like(confusion, -1, dtype=float)

    for i, j, m1, m2 in itertools.product(
        range(wave.shape[0]),
        range(wave.shape[1]),
        range(len(orders)),
        range(len(orders)),
    ):
        if confusion[i, j, m1, m2]:
            order = orders[m2]
            confuser_counts_secondary[i, j, m1, m2], temp = calc_num_counts(
                ratio_pycrates=secondary_arf,
                order=f"{'p' if order > 0 else 'm'}{abs(order)}_to_0",
                order_zero_counts=confuser_0th_counts[i, j, m1],
                bin_start=osip_low[i, j, m1],
                bin_end=osip_high[i, j, m1],
            )

    flag[confusion & (confuser_counts_secondary == 0)] += flags_spec[
        "confuser_has_0_disp_counts_in_order"
    ]

    confusion = confusion & (confuser_counts_secondary > 0)

    # Step 6: Get counts for confused source and calculate confusion ratio.
    confused_0th_counts = np.zeros_like(wave)
    confused_counts_primary = np.zeros_like(wave)

    for i, j, o in itertools.product(
        range(wave.shape[0]), range(wave.shape[1]), range(wave.shape[2])
    ):
        if confusion[i, j, o, :].any():
            order = orders[o]
            confused_0th_counts[i, j, o] = counts_circle_band(
                evtcrates,
                srcpos_subset[i],
                [
                    osip_low[i, j, o],
                    osip_high[i, j, o],
                ],
                skyconverter,
                psffrac=0.9,
            )  # num 0th order counts in the spectrum of interest at osip window of confusion
            confused_counts_primary[i, j, o], temp = calc_num_counts(
                ratio_pycrates=primary_arf,
                order=f"{'p' if order > 0 else 'm'}{abs(order)}_to_0",
                order_zero_counts=confused_0th_counts[i, j, o],
                bin_start=osip_low[i, j, o],
                bin_end=osip_high[i, j, o],
            )

    flag[confusion & (confused_counts_primary == 0)[:, :, :, np.newaxis]] += flags_spec[
        "confused_has_0_disp_counts_and_confuser_gtr_0"
    ]
    confusion = confusion & (confused_counts_primary[:, :, :, np.newaxis] > 0)

    # This will raise a "devide by 0" warning for sources where confused_counts_primary == 0
    # Above, we already marked thos as not-confused and we will never need those values.
    # So, we just hide the error message.
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = confuser_counts_secondary / confused_counts_primary[:, :, :, np.newaxis]
    flag[confusion & (ratio < spec_confuse_limit)] += flags_spec[
        "confusion_smaller_than_conf_ratio"
    ]
    confusion = confusion & (ratio >= spec_confuse_limit)

    flag[confusion] += flags_spec["confusion_above_conf_ratio"]

    src_ids = np.arange(intersect_info["heg_meg_intersects"].shape[0])
    subset_ids = src_ids[subset_sources]
    wave_extracted = np.extract(
        flag > 0, np.broadcast_to(wave[:, :, :, None], flag.shape)
    )

    result = {
        "src_id": np.extract(
            flag > 0,
            np.broadcast_to(subset_ids[:, None, None, None], flag.shape),
        ),
        "confuser_srcid": np.extract(
            flag > 0,
            np.broadcast_to(src_ids[None, :, None, None], flag.shape),
        ),
        "0_order_confused_counts": np.extract(
            flag > 0,
            np.broadcast_to(confused_0th_counts[:, :, :, None], flag.shape),
        ),
        "grating_type": np.full((flag > 0).sum(), arm),
        "order": np.extract(
            flag > 0, np.broadcast_to(orders[None, None, :, None], flag.shape)
        ),
        "confusing_order": np.extract(
            flag > 0, np.broadcast_to(orders[None, None, None, :], flag.shape)
        ),
        "confusion_type": np.full((flag > 0).sum(), "spec"),
        "confusion_wave": wave_extracted,
        "wave_low": wave_extracted - mask_interval / 2,
        "wave_high": wave_extracted + mask_interval / 2,
        "flag": np.extract(flag > 0, flag),
    }
    return np.rec.fromarrays([result[n] for n in rec_type.names], dtype=rec_type)


####POINT SOURCE CONFUSION FUNCTIONS####
def pntsrc_dist_to_spec(src_pos, norm_arm):
    r"""Get distance of each point from line, and line position closest to each point.

    Calculate the distance from each point in src_pos to the line defined
    by norm_arm and passing through each point in src_pos.

    The line is defined by the equation:
    :math:`\vec{X} = \vec{S} + k \cdot \vec{N}_{arm}`

    where :math:`\vec{X}` describes any point on the line
    :math:`\vec{S}` is the source position
    :math:`\vec{N}_{arm}` is the normalized direction vector for the arm
    and :math:`k` is a scalar parameter that describes how far along the line you are from the source.

    Parameters
    ----------
    src_pos : np.ndarray
        An (n, 2) array of source positions.
    norm_arm : np.ndarray
        A (2,) array representing the normalized direction vector of the line.

    Returns
    -------
    k : np.ndarray
        An (n, n) array of scalar parameters k for each pair of source positions.
        :math:`\vec{S} + k \cdot \vec{N_{arm}}` is the point on the line closest
        to the source position.
        k[i, :] gives the k values for the line defined by source position i to the
        point of closed approach for each source position
        (so, ``k[i,i] == 0`` because it's the distance of a source to itself).
    distance_to_line : np.ndarray
        An (n, n) array of distances from each source position to the
        line defined by norm_arm.

    Note
    ----
    See https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Vector_formulation
    for more details on the mathematical formulation used in this function.
    """
    s_minus_s = src_pos[None, :, :] - src_pos[:, None, :]
    k = np.vecdot(s_minus_s, norm_arm)
    vec_along_line = k[:, :, None] * norm_arm
    vec_perpendicular_to_line = s_minus_s - vec_along_line
    distance_to_line = np.linalg.norm(vec_perpendicular_to_line, axis=-1)

    return k, distance_to_line


def pntsrc_confuse_wave(
    subset_sources,
    intersect_info,
    arm,
    src_off_axis_par,
    zero_order_counts,
    max_pntsrc_dist,
    min_spec_counts,
    min_pntsrc_counts,
    cutoff,
    osip,
    skyconverter,
    evtcrates,
    logfile_par,
    evt_frac_thresh=0.1,
):
    r"""
    Identifies when point source confusion occurs within the thresholds provided by the user. If a 0th order source is
    sufficiently bright and close to the dispersed spectrum of another source then it will be identified as having
    point source confusion.  This function uses output from pntsrc_dist_to_spec() with the roll angle to determine
    where/if point source confusion occurs. NOTE: a single confusing point source can only confuse a single arm for
    each 'confused' source. So this loop will only flag a single arm for each confused source per confuser source.

    Parameters
    ----------
    pntsrc_dict : dictionary
        Point source confusion dict which holds all possible pntsrc confusion entries for every source in main_list.
        This dictionary is modified in place by this function.
    distance_along_line : np.ndarray
        An (n, n) array of distances along the line for each pair of source positions.
        :math:`\vec{S} + k \cdot \vec{N_{arm}}` is the point on the line closest
        to the source position.
        k[i, :] gives the k values for the line defined by source position i to the
        point of closed approach for each source position
        (so, ``k[i,i] == 0`` because it's the distance of a source to itself).
    distance_to_line : np.ndarray
        An (n, n) array of distances from each source position to the
        line defined by norm_arm.
    arm_par : str
        HETG 'heg' or 'meg' arm.
    src_off_axis_par : float
        Off-axis angle of the source in arcseconds
    counts_par : int
        The number of 0th order counts.
    max_pntsrc_dist_par : int
        CrissCross parameter threshold in number of pixels for how far a point source can be perpendicular to a
        disperssed spectrum before it is no longer considered in the confusion calculation. This number can be increased
        to reduce the number of potentially confusing point sources.
    min_spec_counts : int
        CrissCross parameter threshold in counts above which a confused source is considered bright enough for point
        source confusion estimation.
    min_pntsrc_counts : int
        CrissCross parameter threshold in counts above which a 0th order source is bright enough to be
        considered as a confuser source of another source's spectrum.
    logfile_par : str
        Name of the logfile for capturing pnt_src_masking_region() log output.
    evt_frac_thresh : float
        Fraction of events allowed by confuser before considering confusion occurs (0.1 = 10%)
    """
    orders = intersect_info["orders"]
    mwave = intersect_info["mwave"][arm][subset_sources, :]
    wave = mwave[..., np.newaxis] / orders
    srcpos = np.diagonal(intersect_info["heg_meg_intersects"]).T
    zero_counts = zero_order_counts[subset_sources]

    off_axis_modifier = calc_off_axis_modifier(src_off_axis_par)
    off_axis_limit = max_pntsrc_dist * off_axis_modifier

    # Array shape is (n_confused_sources, n_confuser_sources, n_orders_confuser).
    confusion = np.ones_like(wave, dtype=bool)
    flag = np.zeros_like(wave, dtype=int)
    distance2line = intersect_info["point2arm"][arm][subset_sources, :]

    confusion = confusion & (distance2line < off_axis_limit)[:, :, np.newaxis]
    confusion = confusion & (zero_counts > min_spec_counts)[:, np.newaxis, np.newaxis]
    confusion = (
        confusion & (zero_order_counts > min_pntsrc_counts)[np.newaxis, :, np.newaxis]
    )
    # A source does not confuse itself, i.e. distance to source is > 0:
    confusion = confusion & (distance2line > 0)[:, :, np.newaxis]

    pntsrc_confuse_log_file = open(f"{logfile_par}", "w")

    wave_low = np.zeros_like(wave)
    wave_high = np.zeros_like(wave)
    for i, j, o in itertools.product(
        range(wave.shape[0]), range(wave.shape[1]), range(wave.shape[2])
    ):
        if confusion[i, j, o]:  # only calculate for potential sources of confusion
            wave_low[i, j, o], wave_high[i, j, o] = pnt_src_masking_region(
                evtcrates,
                osip,
                skyconverter,
                srcpos[i],
                srcpos[j],
                np.abs(intersect_info["point2arm"][arm][i, j]),
                wave[i, j, o],
                tg_part_name.index(arm),
                evt_frac_thresh,
                pntsrc_confuse_log_file,
            )

    pntsrc_confuse_log_file.close()

    flag[confusion & (wave_low == 9999.0)] = flags_pnt["confusing_pntsrc_but_no_counts"]
    confusion = confusion & (wave_low != 9999.0)

    outside_range = (wave < cutoff[arm][0]) | (wave > cutoff[arm][1])
    flag[confusion & outside_range] = flags_pnt["pntsrc_conf_outside_resp_region"]
    confusion = confusion & ~outside_range

    flag[confusion & (wave_low == 9998.0)] = flags_pnt[
        "confusing_pntsrc_but_relatively_few_counts"
    ]
    confusion = confusion & (wave_low != 9998.0)

    flag[confusion & (wave_low == 9997.0)] = flags_pnt[
        "confusing_pntsrc_too_weak_and_too_far"
    ]
    confusion = confusion & (wave_low != 9997.0)

    flag[confusion] = flags_pnt["pntsrc_confusion"]

    src_ids = np.arange(intersect_info["heg_meg_intersects"].shape[0])
    subset_ids = src_ids[subset_sources]

    result = {
        "src_id": np.extract(
            flag > 0,
            np.broadcast_to(subset_ids[:, None, None], flag.shape),
        ),
        "confuser_srcid": np.extract(
            flag > 0,
            np.broadcast_to(src_ids[None, :, None], flag.shape),
        ),
        "0_order_confused_counts": np.extract(
            flag > 0,
            np.broadcast_to(zero_counts[:, None, None], flag.shape),
        ),
        "grating_type": np.full((flag > 0).sum(), arm),
        "order": np.extract(
            flag > 0, np.broadcast_to(orders[None, None, :], flag.shape)
        ),
        "confusing_order": np.zeros((flag > 0).sum(), dtype=int),
        "confusion_type": np.full((flag > 0).sum(), "pnt"),
        "confusion_wave": np.extract(flag > 0, wave),
        "wave_low": np.extract(flag > 0, wave_low),
        "wave_high": np.extract(flag > 0, wave_high),
        "flag": np.extract(flag > 0, flag),
    }
    return np.rec.fromarrays([result[n] for n in rec_type.names], dtype=rec_type)


####ARM CONFUSION FUNCTIONS####


def calc_ccd_energy_res():
    """
    Creates an array of ACIS resolving power as a function of wavelength for MEG and HEG. Matches a polynomial fit of the
    ACIS resolving power as a function of energy (fig 6.14 in the proposers obseravtory guide) to the HEG/MEG arms to
    calculate the OSIP boundaries for two sources that suffer arm confusion.

    Returns
    -------
    res_power_arm_maxed : ACIS resolving power as a function of wavelength for 'heg' or 'meg'
    hetg_arr_arm : an array of wavelengths at the spectral resolution of 'heg' or 'meg'

    """
    p = np.polynomial.Polynomial(
        [
            3.13566434e01,
            2.94110334e-02,
            -2.62121212e-06,
            1.12276612e-10,
        ]
    )
    ccd_lam_arm = np.arange(0.01, 32, 0.01)
    ccd_E_arm = hc / ccd_lam_arm
    res_power = ccd_E_arm / p(ccd_E_arm)
    # Grating spectra are never extracted below 1 Ang, because they overlap the zeroth order there.
    # So, it doesn't really matter that the polynomial fit blows up in that region,
    # but to make plots look nice, we fix is to the max of the resolving power.
    res_power[ccd_lam_arm < 1] = np.max(res_power)
    return res_power, ccd_lam_arm


def arm_confuse_wave(
    subset_sources,
    intersect_info,
    arm,
    src_off_axis_par,
    zero_counts,
    min_arm_counts,
    max_arm_dist,
    nsig_par=6.0,
):
    r"""
    Calculates ratio of 0th order counts (net_counts_confuser / net_counts_confused) for sources with potential
    arm confusion. This parameter is used in loop logic to flag arm confusion but also printed to final table to
    allow user's judgement in determining if they want to remove associated confusion or not.  Also calculates the
    distance from the 0th order confused source (wavelength) where the 0th order of the confuser falls
    on the spectrum. This distance (dx) is then used in later calculations to determine the wavelenght bounds where
    arm confusion can occur.

    Notes
    -----
    Arm confusion is calculated using an off_axis_modifier which is an ESTIMATE of how the off-axis angle of
    the confuser source may impact arm confusion due to its larger PSF size. This is separated into three spatial bins
    of [< 3' (arcmin)], [> 3' and < 6'] and [> 6'] using Fig 4.13 of the Chandra proposers observing guide which shows
    the HRMA encircled energy fraction for off-axis sources. Focusing on the 1.5 keV curve,  if a 1'' PSF is 2pix up and
    2pix down (4pix but confusing source also has 4pix so equals 8pix then + 2 just in case = 10 =
    max_arm_dist) then I can *assume* the number of pixels = 4*the eef. So at 2'' its off axis angle of
    4' so then its 4pix*2+2 * 2 and so on and so on. Should be ok cause most sources at least [i] will be < 3' but
    there may be issues for far off-axis sources espcially if they also intersect with other far off-axis sources.

    Many of the arm conf pars are the same as point source confusion since arm confusion occurs when a (bright)
    0th order point sources falls on the spectrum of a source of interest.

    Parameters
    ----------
    subset_sources : list of int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    distance_along_line : np.ndarray
        An (n, n) array of distances along the line for each pair of source positions.
        :math:`\vec{S} + k \cdot \vec{N_{arm}}` is the point on the line closest
        to the source position.
        k[i, :] gives the k values for the line defined by source position i to the
        point of closest approach for each source position
        (so, ``k[i,i] == 0`` because it's the distance of a source to itself).
    distance_to_line : np.ndarray
        An (n, n) array of distances from each source position to the
        line defined by norm_arm.
    arm_par : str
        HETG 'heg' or 'meg' arm.
    src_off_axis_par : float
        Off-axis angle of the source in arcseconds
    counts_par : int
        The number of 0th order counts.
    nsig_par : float
         Approximation for how wide the OSIP range is for order sorting when determining which events are part of the
         Nth order spectrum.

    Returns
    -------
    arm_conf : numpy.rec.array
        Information about each occurance of confusion.
        Only valid confusion is listed, all sources and arm combinations
        processed that are not listed are to be considered unconfused.
    """
    # First order confused by 2nd order is much less dramatic than third order confused by first order.
    # In the spectral confusion there are already routine to deal with that.
    # Let's use those here, too.
    # Moritz: For next version

    distance2line = intersect_info["point2arm"][arm][subset_sources, :]
    n_sources = distance2line.shape[1]
    orders = intersect_info["orders"]

    off_axis_modifier = calc_off_axis_modifier(src_off_axis_par)

    confuser_close_enough = (
        distance2line
        < max_arm_dist
        * off_axis_modifier[np.newaxis, :]
        * off_axis_modifier[:, np.newaxis]
    ) & (zero_counts > min_arm_counts)[np.newaxis, :]
    # A source has distance=0 from itself, but that's not confusion.
    np.fill_diagonal(confuser_close_enough, False)

    # Many sources are too faint to confuse anything.
    # To keep arrays from getting too big in memory, we don't consider those faint
    # source any further for arm confusion.
    # Because we will need the index array of potentially confusing sources often
    # we give it a shorthand name "iconf" for "index_of_confusers"
    iconf = np.any(confuser_close_enough, axis=0)
    confuser_close_enough = confuser_close_enough[subset_sources, :]
    mwave = intersect_info["mwave"][arm][subset_sources, :][:, iconf]

    res_power, wave_arr = calc_ccd_energy_res()

    fwhm2sig = np.sqrt(np.log(256))
    # This is the right-hand-side in the equation within the loop
    rhs = nsig_par * wave_arr / (res_power * fwhm2sig)

    # "orders" is defined above but for readability of formulas below match notation
    # one would use in a paper.
    # m1 : order number of the confused arm
    # m2 : order number of the confuser arm
    m1 = orders
    m2 = m1

    # For each source, we check for all confusers in all order m1 and all confusing orders m2
    # in a matrix operation.
    # We thus create a 4D view of the wavelength array with the following dimensions:
    # (n_sources, n_confusers, n_orders_of_source, n_orders_of_confuser)
    # Note that np.broadcast to doesn't create a new array in memory, it just allows allows
    # the same numbers with indices in more dimensions.
    wave_arr4d = np.broadcast_to(
        wave_arr[:, np.newaxis, np.newaxis, np.newaxis],
        (wave_arr.shape[0], iconf.sum(), len(m1), len(m2)),
    )

    # I would love to do all sources at once in array notation, but I estimated
    # the size of the intermediate array "confused" and it would be too big to fit in
    # memory for typical users.
    arm_conf = []

    for i in range(len(subset_sources)):
        if np.sum(confuser_close_enough[i, :]) == 0:
            continue  # skip this source if there are no potential confusers
        # the dimension of "confused" will be
        # (n_wavelengths, n_confusers, n_orders_m1, n_orders_m2)
        # Note that `None` has the same meaning as `np.newaxis` but is shorter to type
        term1 = wave_arr[:, None, None] * (
            1 - m1[:, None] / m2[None, :]
        )  # shape (n_wavelengths, n_orders_m1, n_orders_m2)
        term2 = mwave[i, :, None] / m2  # shape (n_confusers, n_orders_m2)

        # Source is confused if
        # - the confuser is close enough to the spectrum (confuser_close_enough)
        # - the wavelength difference between the confused and confuser arm is smaller than sigma * resolution (rhs)
        confused = confuser_close_enough[i, iconf][None, :, None, None] & (
            np.abs(term1[:, None, :, :] - term2[None, :, None, :])
            < rhs[:, None, None, None]
        )
        wav_low = np.min(wave_arr4d, axis=0, where=confused, initial=np.inf)
        wav_high = np.max(wave_arr4d, axis=0, where=confused, initial=0)

        confusion = confused.sum(axis=0) > 0
        confuser_srcid_numbers = np.arange(n_sources)[iconf]
        confuser_srcid = np.extract(
            confusion,
            np.broadcast_to(confuser_srcid_numbers[:, None, None], confusion.shape),
        )

        # For m1=m2, the arms meet asymptocially at infinity.
        # Intersection of a source with itself, gives 0/0, but those cases are
        # filtered out by setting the diagonal of confuser_close_enough to False above.
        # So, we simply suppress warninges here.
        with np.errstate(divide="ignore", invalid="ignore"):
            intersect_wav = mwave[i, :, None, None] / (
                m1[None, :, None] - m2[None, None, :]
            )

        result = {
            "src_id": np.full(confusion.sum(), subset_sources[i]),
            "confuser_srcid": confuser_srcid,
            "0_order_confused_counts": zero_counts[confuser_srcid],
            "grating_type": np.full(confusion.sum(), arm),
            "order": np.extract(
                confusion, np.broadcast_to(m1[None, :, None], confusion.shape)
            ),
            "confusing_order": np.extract(
                confusion, np.broadcast_to(m2[None, None, :], confusion.shape)
            ),
            "confusion_type": np.full(confusion.sum(), "arm"),
            "confusion_wave": np.abs(np.extract(confusion, intersect_wav)),
            "wave_low": np.abs(np.extract(confusion, wav_low)),
            "wave_high": np.abs(np.extract(confusion, wav_high)),
            "flag": np.full(confusion.sum(), flags_arm["arm_confusion"]),
        }
        arm_conf.append(
            np.rec.fromarrays([result[n] for n in rec_type.names], dtype=rec_type)
        )

    return rfn.stack_arrays([arm_conf])


####TABLE OUTPUT FUNCTIONS####


def write_full_conf_table(
    records,
    output_dir,
    obsid,
    src_id=None,
    RA=None,
    DEC=None,
    cc_table_root=None,
    level="confused",
    add_description=False,
):
    if level not in ["confused", "warn", "clean"]:
        raise ValueError("Invalid level. Must be 'confused', 'warn', or 'clean'.")

    to_write = np.zeros(len(records), dtype=bool)
    for conftype, (flag, levels) in flags.items():
        to_write = to_write | (records["confusion_type"] == conftype) & (
            records["flag"] >= levels[level]
        )

    if src_id is not None:
        to_write = to_write & (records["src_id"] == src_id)

    records = records[to_write]

    # Add a column "ObsID" to the front of recrod array
    rec_obsid = np.rec.fromarrays([np.full(len(records), obsid)], names=["obsID"])
    names = records.dtype.names
    records = rfn.rec_append_fields(rec_obsid, names, [records[n] for n in names])

    if add_description:
        severity = np.full(len(records), "clean", dtype="<U8")
        for conftype, (flag, levels) in flags.items():
            for lev in ["clean", "warn", "confused"]:
                severity[
                    (records["confusion_type"] == conftype)
                    & (records["flag"] >= levels[lev])
                ] = lev

        # Get a reverse lookup from flag values to strings.
        # This simple reversing of dicts works because we don't add flag values together
        # e.g. no intersection is ever flag 2 and 4 = 6.
        flags_lookup = {}
        for conf_type, d in flags.items():
            flags_lookup[conf_type] = {v: k for k, v in d[0].items()}
        descr = [flags_lookup[row["confusion_type"]][row["flag"]] for row in records]
        records = rfn.rec_append_fields(
            records, ["level", "flag_comment"], [severity, descr]
        )

    merged_crate = make_table_crate(records)
    # allow users to name table if CrissCross is only run on a single source
    if src_id is not None:
        if RA is None or DEC is None:
            raise ValueError("RA and DEC must be provided if src_id is specified.")
        set_key(
            merged_crate,
            name="RA_conf",
            data=RA,
            unit="deg",
            desc="RA of src with potential HETG confusion",
        )
        set_key(
            merged_crate,
            name="DEC_conf",
            data=DEC,
            unit="deg",
            desc="Dec of src with potential HETG confusion",
        )

    if cc_table_root is not None or len(set(records["src_id"])) == 1:
        filename = (
            f"{output_dir}/confused_{cc_table_root}_consolidated_obsID_{obsid}.fits"
        )
    else:
        filename = (
            f"{output_dir}/confused_src_{src_id}_consolidated_obsID_{obsid}.fits",
        )
    write_file(merged_crate, filename, clobber=True)


def end_of_run_cleanup(output_dir_list_par, obsid_par, wavdetect_par=False):
    """
    Cleans up directory at end of CrissCross run. Creates a wavdetect file output folder if CrissCross runs wavdetect
    and moves the appropraite files there. Also checks the confusion tables to make sure they are not empty
    (no confusion) and if so it deletes the empty ones.

    Parameters
    ----------
    output_dir_list_par : str
        Output directory where CrissCross files are saved
    obsid_par : str
        ObsID associated with the observation.
    wavdetect_par : bool
        Boolean to identify whether CrissCross ran wavdetect or the user supplied the table on their own. This affects
        whether wavdetect ancillar files were created and need to be moved to a new dir for cleanup.
    """

    # create the directories to hold CrissCross files
    table_dir = f"{output_dir_list_par}/confusion_output_files/table_fits_data"
    os.makedirs(table_dir, exist_ok=True)

    # if CrissCross ran wavdetec then create wavdetect dir and move files there
    if wavdetect_par:
        wav_dir = f"{output_dir_list_par}/confusion_output_files/wavdetect_output"
        os.makedirs(wav_dir)
        wave_files = glob.glob(f"{output_dir_list_par}/wavdetect_obsid_{obsid_par}*")
        for i in wave_files:
            shutil.move(i, wav_dir)

    # identify the confusion tables that were created and delete the tables that are 'empty' (no confusion) based on
    # known empty file sizes (revisit this in future).
    output_table_full = glob.glob(
        f"{output_dir_list_par}/confused_*full_obsID_{obsid_par}.fits"
    )
    output_table_consolidated = glob.glob(
        f"{output_dir_list_par}/confused_*consolidated_obsID_{obsid_par}.fits"
    )

    for i in range(len(output_table_full)):
        file_size_table = os.stat(output_table_full[i])
        if (
            file_size_table.st_size == 46080
        ):  # note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the
            # number of columns!
            os.remove(output_table_full[i])

    for i in range(len(output_table_consolidated)):
        file_size_table = os.stat(output_table_consolidated[i])
        if (
            file_size_table.st_size == 5760
        ):  # note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the
            # number of columns!
            os.remove(output_table_consolidated[i])

    # move the remaining table files to the table directory
    files_to_move = glob.glob(
        f"{output_dir_list_par}/confused_*_obsID_{obsid_par}.fits"
    )
    # check that some files exist after removing the tables that have no confusion.
    if len(files_to_move) == 0:
        print(
            "WARNING -- No confusion tables exist after removing empty tables. No confusion identified with input source(s) or something went wrong in CrissCross."
        )
    else:
        for i in files_to_move:
            shutil.move(i, table_dir)

    return ()


def time_logger(mode, time_started=[], time_counter=[], message=[]):
    """
    Creates a time logger and prints relevant steps in the code to the screen.

    Parameters
    ---------
    mode : str
        Controls much of the logic how function prints info to screen. Options are 'start', 'update', 'end'.
    time_started : time object
        The time at the moment of program execution
    time_counter : int
        A counter to count the number of times the function was run throughout the program.
    message : str
        A message to print to the screen when executed.

    Example usage
    -------------

    time_log_start, time_log_counter = time_logger(mode='start')
    time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter,
    message='message 1')
    time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter,
    message='message 2')

    """
    if mode == "start":
        time_start = time.time()
        time_log_counter = 0
        time_log_start = time_start

        obj = time.localtime()
        t = time.asctime(obj)

        print("\n")
        print("CrissCross Time Start:")
        print(t)
        print("\n")

        return (time_log_start, time_log_counter)

    elif mode == "update":
        time_counter_update = time_counter + 1
        time_log_elapsed = round((time.time() - time_started) / 60, 2)
        time_log_obj = time.localtime()  # these three are necessary to print local time in readable format AND its still of by four hours SIGHHH

        t_log = time.asctime(time_log_obj)
        print("\n")
        print(f"TIME LOG #{time_counter_update}  -- {message}")
        print(t_log)
        print("%s minutes have elapsed" % (time_log_elapsed))
        print("\n")

        return time_counter_update

    elif mode == "end":
        time_stop = time.time()
        total_time = round((time_stop - time_started) / 60, 2)
        print()
        print(f"total elapsed time has been {total_time} minutes.")
        print()

        return total_time

    else:
        print("mode was not set to appropriate value")

    return ()


def find_resp_files(pha2_file_par, resp_type_par, resp_dir_par=None):
    """
    Identifies ARFs and RMFs that are associated with an HETG PHA2 file.  This currently utilizes the 'response' and
    'tg' directories created by the data systems and chandra_repro pipelines and thus might not work for all PHA2 HETG
    files.

    Parameters
    ----------

    pha2_file_par : PHA2 fits file
         PHA2 spectrum which is typically provided in the chandra archive of a downloaded HETG observation or after
         running chandra_repro on a chandra HETG obsID.
    resp_type_par: 'arf' or 'rmf'
        The type of response files for matchign to PHA spectra
    resp_dir_par: directory
        The directory where the HETG response files associated with the PHA2 file are located. If none provided, it
        will attempt to search for them.

    Returns
    ----------
    resp_list_par: list
    Returns a list of ARF or RMF files found.

    """

    # if user enters 'ARF' or 'RMF' then lower case for later glob use
    resp_type_par = resp_type_par.lower()

    # check to make sure responses are either arf or rmf
    if resp_type_par != "arf" and resp_type_par != "rmf":
        raise ValueError("Response type must be either arf or rmf")

    # load the pha2 file and obtain the crate where relevant information is stored
    pha2_dataset = read_pha(pha2_file_par)
    spec_crate_par = pha2_dataset.get_crate(2)

    # identify the number of spectra in the PHA2 file
    num_spec_par = len(spec_crate_par.TG_M.values)

    # determine which pipeline the PHA2 file came from (archive vs CIAO user)
    creator_key = get_keyval(spec_crate_par, "CREATOR")

    if "Version DS" in creator_key:
        # if users pha2_file_par is a long path or a single file, strip the name and check for the root so the resp
        # glob doesn't get any extra unrelated files in the response dir.

        # Note, the strings in this section are based on the DS standard naming.
        pha_name = Path(pha2_file_par).name
        pha_root = pha_name.partition("_pha2.fits")[0]

        if resp_dir_par is not None:  # use provided resp_dir_par
            resp_list_par = glob.glob(
                f"{resp_dir_par}/{pha_root}*{resp_type_par}2.fits*"
            )
        else:
            pha_dir = Path(
                pha2_file_par
            ).parent  # need to get directory where PHA2 file is located
            resp_list_par = glob.glob(
                f"{pha_dir}/responses/{pha_root}*{resp_type_par}2.fits*"
            )

    elif (
        "Version CIAO" in creator_key
    ):  # this is produced via chandra_repro or user custom spectral extraction
        # read the header to search for the PHA2 root name which is often the same root as the responses
        hist = get_history_records(spec_crate_par)
        pha_root = ""  # set to '' for checking later in case pha_root not found

        # if chandra_repro was used to produce the PHA2 file then a ':root" value is saved in the header history.
        # This identifies that value.
        for i in range(0, len(hist)):
            if ":root=" in hist[i][1]:  # find the line where the :root command was used
                root_line = (
                    hist[i][1].split("=", 1)[1].strip()
                )  # strip the unnecessary stuff but leaves the extra spaces
                pha_root = root_line.split(" ")[
                    0
                ]  # remove everything after the root value
                break  # stops searching hist for the appropriate line after it is found

        # if pha_root is not overwritten at this point then throw error because it means it was not found
        if pha_root == "":
            raise ValueError(
                "Could not identify PHA2 file root. Please load responses manually."
            )

        # use glob and pha_root to find the responses
        if resp_dir_par is not None:  # use provided resp_dir_par
            resp_list_par = glob.glob(f"{resp_dir_par}/{pha_root}*.{resp_type_par}")
        else:
            pha_dir = Path(
                pha2_file_par
            ).parent  # need to get directory where PHA2 file is located
            resp_list_par = glob.glob(
                f"{pha_dir}/tg/{pha_root}*.{resp_type_par}"
            )  # use the root name of the PHA2 file to ID the responses. This way users can have many extractions in a
            # single dir but it will only grab the appropriate ones.

    # if the creator of the PHA2 file is not DS or CIAO then exit.
    else:
        raise ValueError(
            "Cannot determine the creator of PHA2 file and responses will have to be loaded manually"
        )

    # check to make sure at least some files were found
    if len(resp_list_par) < 1:
        raise ValueError(
            "Could not identify responses. Please load responses manually."
        )

    # check that the length of the arf or RMF lists match the number of PHA spec in the PHA2 file
    if len(resp_list_par) != num_spec_par:
        print(
            f"WARNING-- The identified number of {resp_type_par.upper()}s [{len(resp_list_par)}] does not match the number of PHA spectra [{num_spec_par}] in the PHA2 file. Only the responses found will be included.\n"
        )

    return resp_list_par


def match_resp_order(pha2_file_par, resp_list_par, resp_type_par):
    """
    This uses the PHA2 file structure and matches the input response file list/array (resp_list_par) to the appropriate
    PHA2 spectrum using the header keywords tg_m, tg_part and obsid. This function is designed to take the output of
    find_resp_files() and put them in order of the PHA2 spectra.

    Parameters
    ----------

    pha2_file_par : PHA2 fits file
         PHA2 spectrum which is typically provided in the chandra archive of a downloaded HETG observation or after
         running chandra_repro on a chandra HETG obsID.
    resp_type_par: 'arf' or 'rmf'
        The type of response files for matchign to PHA spectra
    resp_dir_par: directory
        The directory where the HETG response files associated with the PHA2 file are located. If none provided, it
        will attempt to search for them.

    Returns
    ----------

    matched_resp_list_par: array
        Returns an array of ARF or RMF file paths matched to the order (arrangement) of the input PHA2 file. The string
        value 'no match' is returned for elements where there is a spectrum in the PHA2 file but no matching response
        file.

    """

    # check to make sure responses are either arf or rmf
    if resp_type_par != "arf" and resp_type_par != "rmf":
        raise ValueError("Response type must be either arf or rmf")

    # reads in the pha2 file and checks how many spectra (orders) it includes.
    pha2_dataset = read_pha(pha2_file_par)
    spec_crate_par = pha2_dataset.get_crate(2)

    # identify the file arrangement of the HETG orders and HEG/MEG arms via the PHA2 file
    tg_m_arr = spec_crate_par.TG_M.values
    tg_part_arr = spec_crate_par.TG_PART.values
    tg_obsid = get_keyval(spec_crate_par, "OBS_ID")

    # determine the number of spectra in the pha2 file based on the length of one of the tg arrays:
    num_spec_pha2 = len(tg_m_arr)

    # warn user if the number of PHA2 spectra are different than the number of response files (either found
    # automatically or provided manually)
    if len(resp_list_par) != num_spec_pha2:
        print(
            f"\nWARNING -- The number of {resp_type_par} files [{len(resp_list_par)}] does not equal the number of spectra in the PHA2 file [{num_spec_pha2}]. Only responses that match with a spectrum will be included.\n"
        )

    # create empty lists to later append HEG/MEG arm, order and obsID values from the response files headers
    resp_m_arr = []
    resp_tg_part_arr = []
    resp_obsid_arr = []

    # read each response file and append appropriate header value
    for i in range(0, len(resp_list_par)):
        resp_data = read_file(resp_list_par[i])
        resp_m_arr.append(get_keyval(resp_data, "TG_M"))
        resp_tg_part_arr.append(get_keyval(resp_data, "TG_PART"))
        resp_obsid_arr.append(get_keyval(resp_data, "OBS_ID"))

    # convert obsid lists to numpy arrays for later use with np.where() for obsID checking
    tg_obsid = np.array(tg_obsid)
    resp_obsid_arr = np.array(resp_obsid_arr)

    # create an empty object array the same size as the PHA2 file (number of spectra) to hold either 'no match' or the
    # path to the matched response file
    matched_resp_list_par = np.array([""] * num_spec_pha2, dtype="object")

    # for each spectra, use tg_m, tg_part and obsID to match to a single response file. Print appropriate errors.
    for i in range(0, num_spec_pha2):
        match_resp = np.where(
            (resp_m_arr == tg_m_arr[i])
            & (resp_tg_part_arr == tg_part_arr[i])
            & (resp_obsid_arr == tg_obsid)
        )[0].tolist()
        if len(match_resp) == 1:
            matched_resp_list_par[i] = resp_list_par[
                match_resp[0]
            ]  # this is the element in the response array that match the i_th element of the PHA2 file.
        elif len(match_resp) > 1:
            raise ValueError(
                f"ERROR, more than one {resp_type_par.upper()} match found for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}. "
            )
        elif len(match_resp) == 0:
            matched_resp_list_par[i] = "no match"
            print(
                f"Warning, no {resp_type_par.upper()} found for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}."
            )
        else:
            raise ValueError(
                f"ERROR - Something with wrong identifying {resp_type_par.upper()}s for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}"
            )

    # report the files matched to the screen in a nice format so it is clear it worked or didn't work
    print("\nThe following response files were found\n")

    print()
    for i in range(0, num_spec_pha2):
        print(
            f"{tg_part_name[tg_part_arr[i]]}{tg_m_arr[i]:+n} -- {resp_type_par.upper()}: {matched_resp_list_par[i]}"
        )
    print()

    # returns the array of matched responses in the same order as the PHA2 spectra
    return matched_resp_list_par


def clean_spec(cc_table, pha_file, spec_root, arf_file=None, resp_dir=None):
    """
    Uses confusion tables produced by CrissCross to create 'cleaned' PHA1 or PHA2 spectra and ARF response files. The
    confusion tables identify portions of a source's spectrum that may have erroneous events that should not be
    included in any spectral analysis. After identifying the PHA type (1 vs 2), this function checks to make sure the
    ARF files provided match the PHA spectra (order and arm) and uses clean_data() to set the appropriate PHA
    (COUNTS, STAT_ERROR) and ARF (SPECRESP, FRACEXPO) columns to zero where confusion occurs. This function writes a
    'cleaned' copy of the input PHA and ARF files.

    Parameters
    ----------

    cc_table: fits table
        CrissCross produced confusion table for a single source and single obsID.
    pha_file: fits file
        HETG PHA1 or PHA2 spectral file of the source that needs cleaning.
     spec_root: string
        A root for file naming purposes.
    arf_file: string or list
        A file path or list of file paths to ARFs matching the input pha file.
    resp_dir: directory
        The directory where the ARFs associated with the pha_file is stored.

    """

    def clean_data(
        cc_table,
        pha_crate,
        arf_data_var,
        pha_arm_var,
        pha_order_var,
        pha_element,
        conf_flag_var="confused",
    ):
        """
        Creates copies of the relevant PHA1/PHA2 and ARF columns and modifies them (sets to zero) using a CrissCross
        confusion table.

        Parameters
        ----------

        cc_table: fits table
            CrissCross produced confusion table for a single source and single obsID.
        pha_crate: Crate object
            The Crate data for a single spectrum (e.g., HEG+1)
        arf_data_var: Crate object
            The Crate data for a single ARF response matched to a spectrum (e.g., HEG+1)
        pha_arm_var: int (1 or 2)
            The tg_part value associated with the spectrum (1 = HEG, 2 = MEG)
        pha_order_var: int (-3, -2, -1, 1, 2, 3)
            The order associated with the spectrum (e.g., 1 for HEG+1 and -3 for MEG-3)
        pha_element: integer
            The element of the PHA2 file assocaited with the spectrum 'pha_crate'. If standard HETG PHA2 file
            [order,element] = HEG: -3,0; -2,1; -1,2; +1,3; +2,4; +3,5 MEG: -3,6; -2,7; -1,8; +1,9; +2,10; +3,11)
        conf_flag_var: string 'confused'
            The string associated with spectral confusion. If 'confused', spectra will be cleaned by setting all
            'confused' values to zero. A future update will allow 'confused' and/or 'warn' to be zeroed out.


        Returns
        ----------

        cleaned_spec_var, cleaned_staterr_var, cleaned_specresp_var, cleaned_fracexpo_var: arrays
            Returns a copy of the SPEC, STAT_ERR, SPECRESP, and FRACEXPO arrays with values associated with the
            identified wavelengths of confusion set to zero (or 1.86603 for STAT_ERR).
        """

        # reads in the confusion and PHA data
        cc_data = read_file(cc_table)
        pha_data_var = pha_crate.get_crate(2)

        # PHA1 and PHA2 files have to be treated slightly differently because of how crates stores values. This is to
        # avoid having to slice off each crate spectrum from the PHA2 file.
        if is_pha_type1(pha_crate):
            counts_arr = pha_data_var.COUNTS.values
            stat_err_arr = pha_data_var.STAT_ERR.values
            specresp_arr = arf_data_var.SPECRESP.values
            fracexpo_arr = arf_data_var.FRACEXPO.values
            bin_low_arr = pha_data_var.BIN_LO.values
            bin_high_arr = pha_data_var.BIN_HI.values

        elif is_pha_type2(pha_crate):
            counts_arr = pha_data_var.COUNTS.values[pha_element]
            stat_err_arr = pha_data_var.STAT_ERR.values[pha_element]
            specresp_arr = (
                arf_data_var.SPECRESP.values
            )  # ARFs are not in PHA2 (array) format and thus don't need a pha_element
            fracexpo_arr = (
                arf_data_var.FRACEXPO.values
            )  # ARFs are not in PHA2 (array) format and thus don't need a pha_element
            bin_low_arr = pha_data_var.BIN_LO.values[pha_element]
            bin_high_arr = pha_data_var.BIN_HI.values[pha_element]

        else:
            raise ValueError("PHA datatype must be 1 or 2")

        # copies the counts and stat_err column of the PHA file for modification
        cleaned_spec_var = counts_arr.copy()
        cleaned_staterr_var = stat_err_arr.copy()

        # copies the SPECRESP and fracexpo columns from the arf
        cleaned_specresp_var = specresp_arr.copy()
        cleaned_fracexpo_var = fracexpo_arr.copy()

        # for every row of the confusion table that match the input PHA spectrum order and tg_part, identify the
        # elements (rows) associated with wavelengths (bin_low and bin_hi) that need to be cleaned. Note, this assumes
        # the PHA bin_lo and bin_hi values are identical to the ARF file (which should be the case).
        for i in range(0, len(cc_data.wave_low.values)):
            if (
                cc_data.flag.values[i] == conf_flag_var
                and cc_data.grating_type.values[i] == pha_arm_var
                and cc_data.order.values[i] == pha_order_var
            ):
                elements_to_clean = np.where(
                    (bin_low_arr >= cc_data.wave_low.values[i])
                    & (bin_high_arr <= cc_data.wave_high.values[i])
                )  # identify elements

                # clean PHA (spectrum)
                cleaned_spec_var[elements_to_clean] = (
                    0.0  # set elements that overlap to zero
                )
                cleaned_staterr_var[elements_to_clean] = (
                    1.86603  # double check that this makes sense and the stat_err is always this value for zero counts.
                    # I suspect instead I should take min of this column and set it to that.
                )

                # clean ARF (response)
                cleaned_specresp_var[elements_to_clean] = 0.0
                cleaned_fracexpo_var[elements_to_clean] = 0.0

        # return the cleaned arrays values.
        return (
            cleaned_spec_var,
            cleaned_staterr_var,
            cleaned_specresp_var,
            cleaned_fracexpo_var,
        )

    # Read the PHA file and determine if PHA1 or PHA2. Uses read_pha() to bring along the necessary PHA extensions.
    pha_crate_dataset = read_pha(pha_file)

    if is_pha_type1(pha_crate_dataset):
        pha_data = pha_crate_dataset.get_crate(2)  # Crate 2 contains the PHA data
        arf_data = read_file(arf_file)

        # determine the heg/meg arm, order and obsID of the PHA spectrum and make sure it matches the ARF
        tg_part = get_keyval(
            pha_data, "TG_PART"
        )  # tg_part = 1 = heg; tg_part = 2 = meg
        tg_m = get_keyval(pha_data, "TG_M")
        tg_obs = get_keyval(pha_data, "OBS_ID")
        tg_part_arf = get_keyval(arf_data, "TG_PART")
        tg_m_arf = get_keyval(arf_data, "TG_M")
        tg_obs_arf = get_keyval(arf_data, "OBS_ID")

        # if parameters dont match between ARF and PHA then throw error
        if tg_obs != tg_obs_arf or tg_m != tg_m_arf or tg_part != tg_part_arf:
            raise ValueError(
                "One of the following is not consistent between the PHA file and ARF: HEG/MEG arm, order, obsID"
            )

        # use clean_data() to create copies of the appropriate PHA and ARF arrays where wavelenghts with confusion are
        # set to 0
        cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = clean_data(
            cc_table=cc_table,
            pha_crate=pha_crate_dataset,
            arf_data_var=arf_data,
            pha_arm_var=pha_arm,
            pha_order_var=pha_order,
            pha_element=0,
            conf_flag_var="confused",
        )

        # replaces the original arrays in the loaded crates with the new arrays
        pha_data.COUNTS.values = cleaned_spec
        pha_data.STAT_ERR.values = cleaned_staterr
        arf_data.SPECRESP.values = cleaned_specresp
        arf_data.FRACEXPO.values = cleaned_fracexpo

        # appends the original files to the history for record keeping
        pha_data.add_record(
            "HISTORY",
            f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ",
        )
        arf_data.add_record(
            "HISTORY",
            f"This cleaned ARF was created using the ARF file: {arf_file} and the CrissCross cleaning table: {cc_table}. ",
        )

        update_crate_checksum(pha_data)
        update_crate_checksum(arf_data)

        # setup tgpart and order to be consistent with values in confusion tables for file naming.
        pha_arm = tg_part_name[tg_part]
        pha_order = f"{tg_m:+n}"

        # saves a new file while maintaining the original header.
        write_pha(
            pha_crate_dataset,
            f"{spec_root}_obsid_{tg_obs}_{pha_arm}{pha_order}_cleaned.pha",
            clobber=True,
        )
        write_file(
            arf_data,
            f"{spec_root}_obsid_{tg_obs}_{pha_arm}{pha_order}_cleaned.arf",
            clobber=True,
        )

    # PHA2 files need to be treated a little different because they are arrays of arrays and order/arm info is not in
    # header. Also the arfs may be out of order if user provides a list of arfs.
    elif is_pha_type2(pha_crate_dataset):
        # if user enters their own arf or list of arfs then make sure they match the PHA2 file format (e.g., pha2 meg+1
        # has to be same array element as arf meg+1)
        if arf_file is not None:
            if type(arf_file) is str:
                arf_file = list(
                    [arf_file]
                )  # make sure arf_file variable is a list just in case user enters a single file as 'file1' instead of ['file1'].

            # check and arrange that the user input arf file(s) are in the correct order of the PHA2 spectra.
            # matched_resp_list will create an array that matches the PHA2 format.
            matched_resp_list = match_resp_order(
                pha2_file_par=pha_file, resp_list_par=arf_file, resp_type_par="arf"
            )

        # if user doesn't enter arfs then try to find them either using the user included response dir or the standard
        # CIAO-produced file structure
        else:
            print(
                "Warning, no ARF response files provided in parameter arf_file. Attempting to find them."
            )
            resp_list = find_resp_files(
                pha2_file_par=pha_file, resp_type_par="arf", resp_dir_par=resp_dir
            )

            if len(resp_list) == 0:
                raise ValueError(
                    "No response files found. Try including a directory with resp_dir_par or include a list of response paths with arf_file parameter."
                )

            # matched_resp_list will create an array that matches the PHA2 format.
            matched_resp_list = match_resp_order(
                pha2_file_par=pha_file, resp_list_par=resp_list, resp_type_par="arf"
            )

        # read the PHA data and obtain the tg_m, tg_part and obsID values
        pha_data_full = pha_crate_dataset.get_crate(2)

        tg_m_arr = pha_data_full.TG_M.values
        tg_part_arr = pha_data_full.TG_PART.values
        tg_obs = get_keyval(pha_data_full, "OBS_ID")

        pha_order_arr = [
            f"{i:+n}" for i in tg_m_arr
        ]  # this is to make sure the order has a + or - sign in front of it for file naming purposes
        pha_arm_arr = [
            tg_part_name[i] for i in tg_part_arr
        ]  # this is to make sure the arm is named 'heg' or 'meg' for file naming purposes

        # only run clean_data() for the spectra that have a matched response file so identify which elements of the
        # matched_resp_list have both a spectrum and associated ARF.
        spec_to_clean = np.where(
            matched_resp_list != "no match"
        )[
            0
        ]  # note, the 'no match' string comes from match_resp_order() so be careful if that changes.

        # run clean_data() for every arm and order which have a spectrum and matching ARF
        for i in spec_to_clean:
            arf_data = read_file(
                matched_resp_list[i]
            )  # load the arf from match_resp_list because it is already matched to the appropriate PHA2 file

            cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = (
                clean_data(
                    cc_table=cc_table,
                    pha_crate=pha_crate_dataset,
                    arf_data_var=arf_data,
                    pha_arm_var=pha_arm_arr[i],
                    pha_order_var=pha_order_arr[i],
                    pha_element=i,
                    conf_flag_var="confused",
                )
            )

            # replaces the original arrays with the new arrays
            pha_data_full.COUNTS.values[i] = cleaned_spec
            pha_data_full.STAT_ERR.values[i] = cleaned_staterr
            arf_data.SPECRESP.values = cleaned_specresp
            arf_data.FRACEXPO.values = cleaned_fracexpo

            # update the ARF header and write out the file
            arf_data.add_record(
                "HISTORY",
                f"This cleaned ARF was created using the ARF file: {matched_resp_list[i]} and the CrissCross cleaning table: {cc_table}. ",
            )
            update_crate_checksum(arf_data)

            write_file(
                arf_data,
                f"{spec_root}_obsid_{tg_obs}_{pha_arm_arr[i]}{pha_order_arr[i]}_cleaned.arf",
                clobber=True,
            )

        # appends the original files to the history of the new file for record keeping
        pha_data_full.add_record(
            "HISTORY",
            f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ",
        )

        update_crate_checksum(pha_data_full)

        # saves a new PHA2 file while maintaining the original header.
        write_pha(
            pha_crate_dataset, f"{spec_root}_obsid_{tg_obs}_cleaned.pha2", clobber=True
        )

    else:
        raise ValueError("Input PHA file was not a PHA1 or PHA2 type file")

    return ()


######### MAIN CrissCross RUN FUNCTION ##############


def run_crisscross(
    cc_outdir="criss_cross_output",
    arf_ratios_dir="input_files",
    main_list="input_files/full_coup_src_list.tsv",
    subset_src_list="input_files/subset_onc.tsv",
    clean_single_RA=None,
    clean_single_DEC=None,
    clean_single_root=None,
    evt2_file=None,
    wavdetect_file=None,
    clobber_par=False,
    max_pntsrc_dist=8,
    min_pntsrc_counts=5,
    min_spec_counts=3,
    min_spec_confuser_counts=50,
    osip_frac=1.0,
    spec_confuse_limit=0.1,
    max_arm_dist=8,
    min_arm_counts=50,
    arm_nsig=6.0,
    meg_cutoff_low=1.0,
    meg_cutoff_high=32.0,
    heg_cutoff_low=1.0,
    heg_cutoff_high=16.0,
    highest_order=3,
    writing_level="confused",
):
    """
    Main function for running criss cross. CrissCross identifies portions of a sources spectrum where events from other
    field sources may be errouneously assigned to the extracted source with standard CIAO processing. CrissCross
    produces a fits table for each source which tabulates the wavelength location where confusion occurs for all HETG
    arms (heg+meg) and orders -3 to +3. CrissCross requires the evt2 file that was used to extract a source's spectra
    and a list of RA+DEC (main_list) for every X-ray source in the field of view. A list of sources in the field of
    view can often be obtained by running wavdetect on the same field if there are non-HETG archival Chandra
    observations. CrissCross can create spectral confusion tables for all sources present in a secondary
    (subset_src_list) list or can be run for a single source using the 'clean_single_RA/DEC' parameters.

    If users have PHA files extracted using the relevant evt2 file they can run clean_spec() using the CrissCross
    confusion tables as input to remove confused counts from their spectra before performing their spectral analysis.

    Parameters
    ----------
    cc_outidr : str
        A directory for holding the output of CrissCross. If it does not exist then it will be made.
    arf_ratios_dir : str
        The directory which holds the ARF response ratios fits tables necessary for Crisscross.
    main_list : str
        A tsv or ascii file with columns RA, DEC, ID of source positions. This is used to distinguish real sources in a
        wavdetect source table from false sources (identified from the dispersed spectra). This can include sources
        outside of an individual chandra obsID FOV.
    subset_src_list : str
        A tsv or ascii file of sources to create confusion tables for. This should be a subset of main_list and include
        sources bright enough for HETG spectral extraction. The table format requires columns RA, and DEC.
    clean_single_RA, clean_single_DEC : float
        RA and DEC for a single source if the user wishes to create only one confusion table. Format must be
        J2000 degrees.
    evt2_file : str
        A single evt2 file or a list of evt2 files which contain sources in main_list and subset_src_list.
    wavdetect_file : str, None
        A single wavdetect source fits table or a list of wavdetect source fits tables. This is the '*src.fits' file
        output from wavdetect. If no files are included (e.g., wavdetect_file=None) then wavdetect will be run during
        execution of CrissCross.
    clobber_par : bool
        If clobber_par = True then CrissCross overwrites previous CrissCross run if output directory already exists.
    highest_order : int
        The highest order of the HETG spectra to consider for confusion. Default is 3 which means orders -3, -2, -1, 1, 2, and
        3 are included in the confusion calculations.

    Special Parameters
    ------------------
    max_pntsrc_dist : int
        Field sources whose 0th order position is less than or equal to this distance, measured in ACIS pixels
        perpendicular from the dispersed spectrum of an extracted source, will be included as potential point source
        confusion (default: 8).
    min_pntsrc_counts : int
        Field sources with 0th order event counts greater than this threshold will be considered for potential point
        source confusion (default: 5).
    min_spec_counts : int
        Minimum number of 0th order counts for an extracted source to be considered bright enough to consider whether
        field sources can cause confusion (default: 3).
    min_spec_confuser_counts : int
        Minimum number of 0th order counts for a field source to be considered bright enough to disperse spectra and
        potentially contaminate the spectrum of an extracted source (default: 50).
    osip_frac : float
        A fraction from 0. to 1. denoting the portion of an OSIP (Order Sorting Integrated Probability) range to be
        used in the spectral intersection calculation. 1.0 means 100% of the OSIP window is used (default: 1.0).
    spec_confuse_limit : float
        The fraction of dispersed events allowed in a spectral confusion region before deciding the region is
        contaminated (and thus later ignored in spectral fitting). A value of 0.1 means if confuser 'Src B' contributes
        more than 10% of counts in the confused portion of the spectrum of 'Src A' then the spectral region of Src A is
        flagged as confused. Note: The number of counts from each source in the affected spectral intersection region
        (wavelength range) is estimated using the HETG instrument effeciency (ARF) and the number of 0th order counts
        from each source within the wavelength range (default: 0.1).
    max_arm_dist : float
        Two bright sources whose 0th order distance, measured in ACIS pixels perpendicular from one soruce to the
        dispersed spectrum of an extracted source, is less than this will be considered as potential arm confusion.
        Users can increase this parameter if they believe spectra are unfairly being flagged as arm confused. Note: an
        on-axis spectrum has a width of approximately 5 pixels and thus if two on-axis sources are within 10 pixels
        then it is possible they can contaminate eachother (default: 8.0).
    arm_nsig : float
        Approximation for how wide the OSIP range is for order sorting when determining which events are part of the
        Nth order spectrum. This parameter is for arm confusion only and increasing it will cause larger portions of a
        spectrum to be considered confused by arm confusion (default: 6.0).
    min_arm_counts : int
        The minimum number of 0th order counts a confuser source can have before being considered a candidate for arm
        confusion. Note, while it depends on the spectrum, if a 0th order source has 50 counts then there are only
        approximately (1.3 * 50) = 65 dispersed counts in the sum of all arms (HEG/MEG) and orders (default: 50).
    meg_cutoff_low, meg_cutoff_high : float
        The wavelength boundaries for all confusion calculations in Angstroms. If users only care about e.g., the 5-10
        A region of meg then they can set meg_cutoff_low=5.0 and meg_cutoff_high=10.0 and only confusion that occurs
        within this wavelength region is considered. This parameter is not used for arm confusion (default: 1.0, 32.0).
    heg_cutoff_low, heg_cutoff_high : float
        The wavelength boundaries for all confusion calculations in Angstroms. If users only care about e.g., the 5-10
        A region of meg then they can set heg_cutoff_low=5.0 and heg_cutoff_high=10.0 and only confusion that occurs
        within this wavelength region is considered. This parameter is not used for arm confusion (default: 1.0, 16.0).

    """

    # sanitize clobber
    if clobber_par == "True":
        clobber_par = True
    if clobber_par == "False":
        clobber_par = False

    # sanitize the evt2_file input so it is a list
    if evt2_file is None:
        raise ValueError("Please provide an evt2 file")
    # convert a single file into a list so it can work with loop
    elif type(evt2_file) is str:
        evt2_file = [evt2_file]
    elif type(evt2_file) is not list:
        raise ValueError(
            "Unknown type of input for evt2_files. Please include a single file or a list of files"
        )

    if wavdetect_file is not None:
        if type(wavdetect_file) is str:
            wavdetect_file = [wavdetect_file]
        elif type(wavdetect_file) is not list:
            raise ValueError(
                "Unknown type of input for wavdetect_file. Please include a single file or a list of files"
            )

    # check to make sure the number of evt2 files match the number of wavdetect source lists
    if wavdetect_file is not None and len(wavdetect_file) != len(evt2_file):
        raise ValueError(
            "The number of input evt2_files and wavdetect source fits table files do not match. Please include a wavdetect table for each evt2 file."
        )

    # run wavedetect_match_obsid before the loop starts to ensure input files are in correct order. Make wavdetect_file
    # a list of [None]s so it can work per obsID in CrissCross loop below.
    if wavdetect_file is not None:
        wavdetect_file = wavedetect_match_obsid(
            fits_list_par=evt2_file, wavdetect_list_par=wavdetect_file
        )
    else:
        wavdetect_file = [None] * len(evt2_file)

    # Start major CrissCross loop for all input evt2 files
    for k in range(len(evt2_file)):
        # ardlib.punlearn()

        # start the time logger for printing steps to the screen
        time_log_start, time_log_counter = time_logger(mode="start")

        # print the tweakable paramters to the screen and then record them near the end along with the time it took to run.
        print("\n")
        print("This run is for observation %s" % evt2_file[k])
        if wavdetect_file[k] is not None:
            print("This run is using the wavedetect file %s" % wavdetect_file[k])
        print(
            "The contamination offset threshold is set to %s pixels." % max_pntsrc_dist
        )
        print(
            "The counts threshold to be considered a spectrum of interest is set to %s counts."
            % min_spec_counts
        )
        print(
            "The counts threshold to be considered a potential contaminating spectral source is %s counts."
            % min_spec_confuser_counts
        )
        print(
            "The counts threshold to be considered a potential 0th order point source contaminating source is %s counts."
            % min_pntsrc_counts
        )
        print(
            "The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is %s pixels"
            % max_arm_dist
        )
        print(
            "The fraction of the OSIP window to include when considering two arm overlaps is set at %s percent "
            % (osip_frac * 100)
        )
        print(
            "The minimum counts in Src Bs 0th order to assess total arm confusion in source A is %s "
            % (min_arm_counts)
        )

        # set a few obsid_specific parameters
        obsid = get_header_par(fits_file=evt2_file[k], keyword_par="obs_id")
        roll_nom = float(get_header_par(fits_file=evt2_file[k], keyword_par="ROLL_NOM"))
        grating_rotang = read_file(
            f"{evt2_file[k]}[REGION]"
        )  # always reads the region block because the block number is variable
        heg_ang = np.radians(grating_rotang.ROTANG.values[1])  # tg_part = 1
        meg_ang = np.radians(grating_rotang.ROTANG.values[2])  # tg_part = 2
        # It is physically arbitrary which direction are positive and negative. The minus
        # signs are here to match the Chandra convention.
        norm_vec_heg = -np.array([np.cos(heg_ang), np.sin(heg_ang)])
        norm_vec_meg = -np.array([np.cos(meg_ang), np.sin(meg_ang)])

        print(
            "The HEG/MEG angles for this observation are %s and %s degrees."
            % (heg_ang, meg_ang)
        )

        print("The roll angle of this observation is %s" % roll_nom)

        # create the output files directory but if clobber=False and it exists then stop CrissCross
        output_dir, dir_exists = make_output_dir(
            cc_outdir, obsid, clobber_par=clobber_par
        )
        if dir_exists and not clobber_par:
            print(
                f"\nClobber set to false and output directory {output_dir} exists. If you wish to overwrite files please set clobber=True\n"
            )
            continue

        # run wavdetect if the user did not input a wavdetect source table.
        run_wave = False
        if wavdetect_file[k] is None:
            run_wave = True  # set so end_of_run_cleanup knows to make output dir and move wavdetect files
            wavdetect_file[k] = run_wavdetect(
                evt2_file[k], outdir=output_dir, outroot=f"wavdetect_obsid_{obsid}"
            )
            # wavdetect_file[k] = [wavdetect_file]

        # save the RA, DEC and SRCID from the main input list
        RA_wcs, DEC_wcs, srcID = load_sourcelist(filename=main_list)

        # save the RA, DEC from the subset input list or the user input individual source
        if clean_single_RA is None and clean_single_DEC is None:
            subset_RA, subset_DEC = load_sourcelist(
                filename=subset_src_list, subset_list=True
            )
        else:
            subset_RA = [float(clean_single_RA)]
            subset_DEC = [float(clean_single_DEC)]

        # match the element number of the subset list to the main list using RA and DEC to 6 digits accuracy.
        subset_list = match_subset_to_main(
            RA_main=RA_wcs, DEC_main=DEC_wcs, RA_sub=subset_RA, DEC_sub=subset_DEC
        )

        # convert from RA/DEC in degrees to Chandra Sky physical coordinates and determine off-axis angle in arcsec
        src_pos_x, src_pos_y, src_off_axis = calc_physical_coords(
            fits_par=evt2_file[k], RA_par=RA_wcs, DEC_par=DEC_wcs
        )
        src_pos = np.array([src_pos_x, src_pos_y]).T

        time_message = "Finished converting RA/DEC into chandra coords"
        time_log_counter = time_logger(
            mode="update",
            time_started=time_log_start,
            time_counter=time_log_counter,
            message=time_message,
        )

        # match input source list to wavedetect table to catalog 0th order counts for each source in each obsid
        final_match_arr, final_dist_arr, counts = find_closest_source(
            src_x=src_pos_x,
            src_y=src_pos_y,
            wave_file=wavdetect_file[k],
            max_offset=3.0,
        )

        # create an output file of the input source list with the wave-detect-matched 0th order counts
        write_matched_file(
            srcid_par=srcID,
            ra_par=RA_wcs,
            dec_par=DEC_wcs,
            counts_par=counts,
            fileroot=f"{output_dir}/src_list_{obsid}",
        )

        # Print to the screen the number of sources that satisfy the above conditions as well as the total number of
        # sources in input list.
        src_num = len(src_pos_x)

        counts_intercept_num = len(
            counts[counts > min_spec_counts]
        )  # will count the number of sources that are above the threshold

        print("The total number of sources input is %s." % (src_num))
        print(
            "The number of sources above the contamination intercept threshold of %s counts for ObsID %s is %s."
            % (min_spec_counts, obsid, counts_intercept_num)
        )

        # calculate relevant parameters for when two lines intersect in the Chandra FOV
        k_heg, k_meg = determine_line_intersect_values(
            src_pos, norm_vec_heg, norm_vec_meg
        )
        heg_meg_intersects = (
            src_pos[:, np.newaxis, :] + k_heg[:, :, np.newaxis] * norm_vec_heg
        )

        orders = np.arange(-highest_order, highest_order + 1)
        orders = orders[orders != 0]  # exclude 0 order
        intersect_info = {
            "orders": orders,
            "heg_meg_intersects": heg_meg_intersects,
        }
        intersect_info["distance_along"] = {"heg": k_heg, "meg": k_meg}
        intersect_info["mwave"] = {
            "heg": k_heg * mm_per_pix / X_R * Period["heg"],
            "meg": k_meg * mm_per_pix / X_R * Period["meg"],
        }
        time_message = (
            "Finished calculating XY intercepts for all sources in the field of view."
        )
        time_log_counter = time_logger(
            mode="update",
            time_started=time_log_start,
            time_counter=time_log_counter,
            message=time_message,
        )

        cutoff = {
            "heg": [heg_cutoff_low, heg_cutoff_high],
            "meg": [meg_cutoff_low, meg_cutoff_high],
        }
        osip = OSIP(evt2_file[k])
        skyconverter = Sky2Chandra(evt2_file[k])
        evtcrates = read_file(evt2_file[k])
        records = []

        #########SPECTRAL CONFUSION START ############
        for arm in ["heg", "meg"]:
            records.append(
                spec_confuse_wave(
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
                    counts=counts,
                    min_spec_counts=min_spec_counts,
                    min_spec_confuser_counts=min_spec_confuser_counts,
                    width_mask_pixel=120,
                    obsid_par=obsid,
                    outdir=output_dir,
                    osip_frac=osip_frac,
                    arf_ratios_dir=arf_ratios_dir,
                    cutoff=cutoff,
                    osip=osip,
                    skyconverter=skyconverter,
                    evtcrates=evtcrates,
                    spec_confuse_limit=spec_confuse_limit,
                )
            )

        time_message = "Finished calculating spectral confusion."
        time_log_counter = time_logger(
            mode="update",
            time_started=time_log_start,
            time_counter=time_log_counter,
            message=time_message,
        )

        #########POINT SOURCE CONFUSION START ############
        dist_along_heg, point_to_heg = pntsrc_dist_to_spec(src_pos, norm_vec_heg)
        dist_along_meg, point_to_meg = pntsrc_dist_to_spec(src_pos, norm_vec_meg)
        intersect_info["point2arm"] = {"heg": point_to_heg, "meg": point_to_meg}

        for arm in ["heg", "meg"]:
            records.append(
                pntsrc_confuse_wave(
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
                    src_off_axis_par=src_off_axis,
                    zero_order_counts=counts,
                    max_pntsrc_dist=max_pntsrc_dist,
                    min_spec_counts=min_spec_counts,
                    min_pntsrc_counts=min_pntsrc_counts,
                    cutoff=cutoff,
                    osip=osip,
                    skyconverter=skyconverter,
                    evtcrates=evtcrates,
                    logfile_par=f"{output_dir}/pnt_src_confuse_{obsid}_log.txt",
                    evt_frac_thresh=0.1,
                )
            )

        time_message = "Finished assigning point source confusion."
        time_log_counter = time_logger(
            mode="update",
            time_started=time_log_start,
            time_counter=time_log_counter,
            message=time_message,
        )

        ##########ARM CONFUSION START ############################
        for arm in ["heg", "meg"]:
            records.append(
                arm_confuse_wave(
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
                    src_off_axis_par=src_off_axis,
                    zero_counts=counts,
                    min_arm_counts=min_arm_counts,
                    max_arm_dist=max_arm_dist,
                    nsig_par=arm_nsig,
                )
            )

        time_message = "Finished assigning arm confusion."
        time_log_counter = time_logger(
            mode="update",
            time_started=time_log_start,
            time_counter=time_log_counter,
            message=time_message,
        )

        ##### Table writing and cleanup ############
        records = rfn.stack_arrays(records)

        for i in subset_list:
            # If users run cc with just a single source, allow them to name the confusion file. Otherwise a single root
            #  will get clobbered when looped over multiple sources.
            if (
                clean_single_RA is not None
                and clean_single_DEC is not None
                and clean_single_root is not None
            ):
                cc_table_root = clean_single_root
            else:
                cc_table_root = None
            write_full_conf_table(
                records=records,
                output_dir=output_dir,
                obsid=obsid,
                src_id=i,
                RA=RA_wcs[i],
                DEC=DEC_wcs[i],
                cc_table_root=cc_table_root,
                level=writing_level,
                add_description=True,
            )

        # move output files into final directories and cleanup
        end_of_run_cleanup(
            output_dir_list_par=output_dir, obsid_par=obsid, wavdetect_par=run_wave
        )

        time_message = "Finished Running CrissCross!."
        time_log_counter = time_logger(
            mode="update",
            time_started=time_log_start,
            time_counter=time_log_counter,
            message=time_message,
        )

        log_file = open(f"{output_dir}/LOG_{obsid}.txt", "w")
        total_time = time_logger(mode="end", time_started=time_log_start)
        log_file.write(
            f"""This run is for observation {evt2_file[k]}.
The wavdetect source list used for this observation is {wavdetect_file[k]}.
The roll angle of this observation is {roll_nom:.2f} degrees.
MEG angle = {meg_ang:.2f} degrees and HEG angle = {heg_ang:.2f} degrees.
The contamination offset threshold is set to {max_pntsrc_dist} pixels.
The counts threshold to be considered a spectrum of interest is set to {min_spec_counts} counts.
The counts threshold to be considered a potential contaminating spectral source is {min_spec_confuser_counts} counts.
The counts threshold to be considered a potential 0th order point source contaminating source is {min_pntsrc_counts} counts.
The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is {max_arm_dist} pixels.
The fraction of the OSIP window to include when considering two arm overlaps is set at {osip_frac * 100} percent.
The total number of sources input is {src_num}.
The number of sources above the contamination intercept threshold of {min_spec_counts} counts for ObsID {obsid} is {counts_intercept_num}.
The minimum counts in Src Bs 0th order to assess total arm confusion in source A is {min_arm_counts}.
The HEG/MEG angles for this observation are {heg_ang:.2f} and {meg_ang:.2f} degrees.
The total elapsed time for obsID {obsid} is {total_time} minutes."""
        )
        log_file.close()
