# See README.me for general info about CrissCross

# List of things I still need to do:
# - add back in ds9 figure generation so users can see where confusion occurs on the evt2 fits image.
# - add functionality for user to calculate confusion between two selected sources in a field of view and print results to screen.
# - width_of_exclusion_region has hardcoded parameters for the extraction. Should be read from file.
# - Write parameters values used to run into header (either as history or as keywords)
# - output "0th_order_confused_counts" is really CONFUSER counts in the original version. What do we want? Also doesn't take OSIP into account. Do we want that?
##########################################################################################
##########################################################################################
##########################################################################################
import glob
import os
import shutil
import time

import numpy as np
from numpy.lib import recfunctions as rfn

from pycrates import (
    read_file,
    write_file,
    set_key,
)
from crates_contrib.utils import make_table_crate
from ciao_contrib import runtool as rt
from .iocaldb import OSIP, Sky2Chandra, Cel2Chandra
from ciao_contrib.psf_contrib import PSF
from .widthofexclusion import counts_circle_band, pnt_src_masking_region
from .constants import X_R, Period, mm_per_pix, arcsec_per_pix, hc, Alpha
import ciao_contrib.logger_wrapper as lw

TOOLNAME = 'crisscross'
__revision__  = '28 May 2026'

lw.initialize_logger(TOOLNAME)
v1 = lw.make_verbose_level(TOOLNAME, 1)
v2 = lw.make_verbose_level(TOOLNAME, 2)
v3 = lw.make_verbose_level(TOOLNAME, 3)


##### FLAG DEFINITIONS #####
# Which flag do they get if the intersection point is outside the CCD?
flags_spec = {
    "outside_osip_range": 1,
    "confuser_has_no_0th_order_counts": 2,
    "confuser_has_0_disp_counts_in_order": 4,
    "confusion_smaller_than_conf_ratio": 8,
    "confused_has_0_disp_counts_and_confuser_gtr_0": 16,
    "confusion_above_conf_ratio": 32,
}
flags_spec_levels = {"clean": -1, "warn": 0, "confused": 16}

flags_pnt = {
    "confusing_pntsrc_but_no_counts": 1,
    "confusing_pntsrc_but_relatively_few_counts": 2,
    "confusing_pntsrc_too_weak_and_too_far": 4,
    "pntsrc_conf_outside_resp_region": 8,
    "pntsrc_confusion": 16,
}
flags_pnt_levels = {"clean": 0, "warn": 2, "confused": 16}

flags_arm = flags_spec
flags_arm_levels = flags_spec_levels

flags = {
    "spec": (flags_spec, flags_spec_levels),
    "pnt": (flags_pnt, flags_pnt_levels),
    "strk": (flags_pnt, flags_pnt_levels),
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
        ("flag_id", "<i8"),
    ]
)

#############FUNCTION DEFINITIONS###############
def on_chip(chipx, chipy):
    return (0 < chipx) & (chipx < 1024) & (0 < chipy) & (chipy < 1024)


def calc_off_axis_modifier(theta_arcmin):
    """

    At larger off-axis angles, the PSF gets larger and thus point sources and grating arms
    look wider.

    Parameters
    ----------
    theta_arcmin : float
        off-axis angle in arcminutes

    Returns
    -------
    modifier : float
        multiplier to apply to distances
    """
    out = np.ones_like(theta_arcmin)
    out[theta_arcmin > 3] = 2
    out[theta_arcmin > 6] = 3
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
        "If you wish to use other wavdetect parameters please run wavdetect and provide a wavdetect source fits table with parameter 'wavdetect_file'.\n"
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
    rt.wavdetect.scales = "1 2 4 8 16"
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
    wave_obsid = [
        get_header_par(fits_file=f, keyword_par="obs_id") for f in wavdetect_list_par
    ]
    fits_obsid = [
        get_header_par(fits_file=f, keyword_par="obs_id") for f in fits_list_par
    ]
    if not set(wave_obsid) == set(fits_obsid):
        raise ValueError(
            f"The obsIDs in the wavdetect source tables {wave_obsid} do not match the obsIDs in the evt2 files {fits_obsid}."
        )

    wavedetect_sorted = []

    for i in range(0, len(fits_list_par)):
        for j in range(0, len(wave_obsid)):
            if fits_obsid[i] == wave_obsid[j]:
                wavedetect_sorted.append(wavdetect_list_par[j])
                continue

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
        #catch the case of reading a subset_list and do not generate ids
        elif crate_len == 2 and subset_list is True:
            gen_id = False
            
        else:
            print(
                f'File "{filename}" may contain more than three columns and the rest will be ignored.'
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

def match_subset_to_main(RA_main, DEC_main, RA_sub, DEC_sub, match_offset=0.5):
    """
    Matches sources from the subset_list to the main_list by RA and DEC. All sources in the subset list MUST be also in
    the main list and matched via the element number of the input main_list array. For example, if source number 10 in
    the subset_list (row 10) is the same source as row 200 in the main_list, then source 10 will be matched with
    element 200 and CrissCross will use e.g. src_pos_x[200], src_pos_y[200] when handling subset_list source 10. If
    no or multiple matches are found for a single source then error is thrown. Every source must be unique.

    Parameters
    ----------
    RA_main : np.array
        Right Ascension of main_list source in degrees
    DEC_main : np.array
        Declination of main_list source in degrees
    RA_sub : np.array
        Right Ascension of subset_list source in degrees
    DEC_sub : np.array
        Declination of subset_list source in degrees
    match_offset : float, arcsec
        Maximum offset for matching sources between the main and subset lists.

    Returns
    -------
    match : np.array
        Array of indices with the one main source list that corresponds to each source in the subset list.

    On a sphere, the distance between points is given by the haversine formula, which
    works well numerically except for point that are almost exactly opposites,
    which is not the case here [1].

    Notes
    -----
    This implementation simply calculates all pairwise distances. A KD-Tree or
    similar structure would be more efficient, but we expect that this will
    be used for no more than a few thousand sources and thus the brute-force
    approach is sufficient.

    References
    ----------
    [1] https://en.wikipedia.org/wiki/Haversine_formula
    """
    dlon = RA_main[None, :] - RA_sub[:, None]
    dlat = DEC_main[None, :] - DEC_sub[:, None]
    hav_theta = (1 / 2) * (
        np.sin(np.deg2rad(dlat) / 2) ** 2
        + np.cos(np.deg2rad(DEC_sub[:, None]))
        * np.cos(np.deg2rad(DEC_main[None, :]))
        * np.sin(np.deg2rad(dlon) / 2) ** 2
    )
    theta = 2 * np.arcsin(np.sqrt(hav_theta))
    min_theta = np.min(theta, axis=1)
    if np.any(min_theta > np.deg2rad(match_offset / 3600)):
        ind = min_theta > np.deg2rad(match_offset / 3600)
        raise ValueError(
            f"No match in main list found for the sources with RA={RA_sub[ind]} and DEC={DEC_sub[ind]} with min distance {min_theta[ind]} arcsec. Please make sure RA and DEC value of source to clean matches a source in main_list."
        )
    ind = theta < np.deg2rad(match_offset / 3600)
    if np.any(ind.sum(axis=1) > 1):
        ind_multi = ind.sum(axis=1) > 1
        raise ValueError(
            f"Multiple matches in main list found for the sources with RA={RA_sub[ind_multi]} and DEC={DEC_sub[ind_multi]}. Please make sure there are no duplicate entries in main list or subset_list."
        )
    return np.argmin(theta, axis=1)


def calc_physical_coords(fits_par, RA, DEC):
    """
    Converts from RA and DEC in WCS degrees to Chandra physical coordinates. This also determines the off-axis angle
    in arcmin and the size of the PSF at the off-axis angle.

    Parameters
    ----------
    fits_par : str
        evt2 fits file.
    RA : ndarray
        Right ascension in degrees.
    DEC : ndarray
        Declination in degrees.
    """
    cel_convert = Cel2Chandra(fits_par)
    src = cel_convert(RA, DEC)
    for key, value in src.items():
        if isinstance(value, list):
            src[key] = np.array(value)
    src["RA"] = RA
    src["DEC"] = DEC
    src["pos"] = np.stack([src["x"], src["y"]], axis=-1)
    src["n"] = len(src["x"])
    src["ID"] = np.arange(0, src["n"])

    psf = PSF()
    psf_size = np.zeros(src["n"])
    for i in range(0,src["n"]):
        psf_size[i] = psf.psfSize(
            energy_keV=2.0,
            theta_arcmin=src["theta"][i],
            phi_deg=src["phi"][i],
            ecf=0.9,
        )
    src["psf_size"] = psf_size

    return src


def find_closest_source(src, wave_file, max_offset=3.0):
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
    src : dict
        Dictionary with source properties including positions in Chandra physical units.
    wave_file : str
        path to wavdetect output source fits table.
    max_offset : float
        The max distance in arcsec two sources can be before they are no longer considered matchable between the source
        list and the wavdetect table. All sources are treated the same regardless of off-axis angle which is generally
        ok because centroids should be relatively good as determined by wavdetect.
    """
    # read in and assign relevant wavdetect columns
    wave_data = read_file(wave_file)

    src_wave_x_arr = wave_data.POS.X.values
    src_wave_y_arr = wave_data.POS.Y.values
    counts_wave = wave_data.NET_COUNTS.values

    closest_dist_arr = np.empty(
        src["n"], dtype="float"
    )  # holds the distance in arcsec to the closest matching source from the wavedetect table
    closest_match_arr = np.empty(
        src["n"], dtype="int"
    )  # holds the index value from the wavedetect table that is the closest match to a source in the source list.

    # these will hold the values above for the matched source AFTER you remove double matches and sources > max_offset.
    final_match_arr = np.empty(src["n"], dtype=object)
    final_dist_arr = np.empty(src["n"], dtype=object)

    matched_0th_counts_arr = np.empty(
        src["n"], dtype="float"
    )  # the final 0th_order counts array (NET_COUNTS) from the wavedetect table MATCHED to the user-provided source list.

    # this loop determines the distance from the user-provided source to ALL the sources in the wavedetect table and
    # only saves a non-bogus value if there is a source with separation < max_offset.
    for i in range(0, src["n"]):
        dist_arr = []
        dist_arr = np.sqrt(
            (src["x"][i] - src_wave_x_arr) ** 2 + (src["y"][i] - src_wave_y_arr) ** 2
        )  # This calculates the physical distance from source [i] in the user-provided table to ALL sources in the
        # wavedetect table. This is just the hypotenuse in the xy plane. Note, calculating the ENTIRE array here for
        #  each [i] source and NOT each [i] and each [j] individually.

        closest_dist = []
        closest_dist = (
            np.min(dist_arr) * arcsec_per_pix
        )  # converted from sky coords to arsec

        # if distance is > max offset then assign values of 99999 (bogus) and filter out in next loop. Otherwise,
        # assign matched values.
        if closest_dist <= src['psf_size'][i]:
            closest_dist_arr[i] = closest_dist
            closest_match_arr[i] = np.where(dist_arr == np.min(dist_arr))[0][0]  #
        else:
            closest_dist_arr[i] = 99999
            closest_match_arr[i] = 99999

    # this loop will remove 'double counting' where a single user-provided source might match to multiple wavedetect
    #  sources. This will only match to the closest one and remove that from the pool of potential matches for other sources.
    for i in range(0, src["n"]):
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
            (closest_dist_arr[i] <= src['psf_size'][i])
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
    src,
    fileroot="matched_source_list",
    output_type="txt",
):
    """
    Creates a csv or txt file to save SrcID, RA, Dec and wave_detect_matched 0th order counts.

    Parameters
    ----------
    src : dict
        Dictionary the source information.
    fileroot : str
        root for naming purposes
    output_type : str
        text file output type to save. Can be 'txt' or 'csv'.
    """
    filestack = np.column_stack((src["ID"], src["RA"], src["DEC"], src["counts"]))
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

### Vector arithmetic ###


def perpendicular_vector(vec):
    """Calculate a perpendicular vector in 2D.

    Parameters
    ----------
    vec : np.ndarray
        A (2,) array representing a vector in 2D.

    Returns
    -------
    perp_vec : np.ndarray
        A (2,) array representing a vector that is perpendicular to the input vector.
    """
    if len(vec) != 2:
        raise ValueError("Input vector must be of length 2.")
    return np.array([-vec[1], vec[0]])


def line_line_intersect(src_pos, norm_arm1, norm_arm2):
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

    With this definition, you can obtain the x,y coordinates of all intersection points with:

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
def arf_ratio(ratio_pycrates, order, bin_start, bin_end):
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
    avg_ratio_value : float
        The average spectral response in the bin_start, bin_end bandpass.
    """
    bin_lo = ratio_pycrates.BIN_LO.values
    #handle rare-ish error where wave_low and high values were equal leading to an 'average' of an empty list.
    if bin_start == bin_end:
        bin_end = (
            bin_end + 0.01
        )  # may need to increase 0.01 to guarantee multiple elements are selected.
        v3(
            f"Warning: arf_ratio calculation was estimated because wave_low and wave_high were equal."
        )
    in_range = (bin_start <= bin_lo) & (bin_lo < bin_end)
    order_data = ratio_pycrates.get_column(order)
    avg_ratio_value = np.average(order_data.values[in_range])

    return avg_ratio_value


def counts_scaled_by_arf(pos, order, band, evtcrates, skyconverter, arf, psffrac=0.9):
    """Estimate the number of counts in a spectral arm from 0th order counts and wavelength range.

    This function extracts the number of counts in a given wavelength range at a given position
    and scales that number by ratios of an ARF relative to 0th order.

    Parameters
    ----------
    pos : list
        The x and y position of the source in Chandra physical coordinates.
    order : int
        The order of the spectral arm for which to calculate the counts.
    band : list
        The first and last wavelength in Angstrom where mean response is taken in the ARF tables.
    evtcrates : `pycrates.tablecrate.TABLECrate`
        A crates object holding an event file.
    skyconverter : `ciao_contrib.criss_cross.iocaldb.Sky2Chandra`
        Object that can convert Chandra coordiantes for the event file used.
    arf : fits table
        CrissCross table of typical ARF ratios for different orders based on a single on-axis HETG observation. Note, since this takes the ratio of different orders, the buildup of ACIS contamination over time should not affect this calculation.
    psffrac : float
        The encircled energy fraction to use when calculating the counts in the band. This should be the same as the value used for wavdetect if wavdetect is used to determine 0th order counts.

    Returns
    -------
    counts : float
        The number of counts in the spectral arm given the number of 0th order counts and the ARF ratio.
    arf_counts : float
        The number of counts in the spectral arm scaled by the ARF ratio.
    """
    counts = counts_circle_band(
        evtcrates,
        pos,
        band,
        skyconverter,
        psffrac=psffrac,
    )
    arf_counts = counts * arf_ratio(
        ratio_pycrates=arf,
        order=f"{'p' if order > 0 else 'm'}{abs(order)}_to_0",
        bin_start=band[0],
        bin_end=band[1],
    )
    return counts, arf_counts


def spec_confuse_wave(
    sources,
    subset_sources,
    intersect_info,
    arm,
    min_spec_counts,
    min_spec_confuser_counts,
    width_mask_pixel,
    osip_frac,
    arf_ratios_dir,
    cutoff,
    osip,
    skyconverter,
    evtcrates,
    spec_confuse_limit,
):
    """Determine spectral arm confusion.

    This function analyses spectral confusion where the dispersed soectrum from one
    source is intersected by the dispersed spectrum of another source (a HEG and an MEG
    arm are corssing). Starting from the simple geometrical intersection, it checks if
    order sorting would resolve the two arms separately and estimates the number of
    counts expected in the confusing spectrum to decide if the spectral confusion is
    relevant.

    Parameters
    ----------
    sources : dict
        Dictionary with source properties including positions in Chandra physical units and 0th order counts.
    subset_sources : list of int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    interset_info : dict
        Holding information aboout the source locations, arm locations, and arm intersection points.
    arm : str
        HETG arm type of 'heg' or 'meg'.
    min_spec_counts: int
        Confusion is only calcualted for sources with more 0th order counts than "min_spec_count".
        This parameters saves time to prevent long calculations for sources that are too faint
        to be used scientifically anyway.
    min_spec_confuser_counts : int
        Only sources with more 0th order counts than this threshold are considered a potenital source
        consider a source for spectral confusion. This speeds up the calculation because no
        zero order spectra need to be extra cted for these sources.
    width_mask_pixel : float
        Full width in pixels of the region that is marked as bad when confusion occurs.
         It is no recommended to go smaller than the default values as they are determined based on the intstrument.
    obsid_par : str
        obsID value of the observation.
    outdir : str
        Output directory used to create the log file assocaited with running the osip function.
    osip_frac: float
        CrissCross parameter which controls the size of the OSIP window. A value of 1.0 keep 100% of the OSIP window.
        This parameter can be tweaked lower to make the confusion estimate less conservative.
    arf_ratios_dir : str
        Path to CrissCross arf ratios tables necessary to account for efficiencies between orders.
    osip : `ciao_contrib.criss_cross.iocaldb.OSIP`
        Object that can retrieve OSIP information for the event file used.
    skyconverter : `ciao_contrib.criss_cross.iocaldb.Sky2Chandra`
        Object that can convert Chandra coordiantes for the event file used.
    evtcrates : `pycrates.tablecrate.TABLECrate`
        A crates object holding an event file.
    spec_confuse_limit : float
        Ratio of counts in the confusing/confused grating spectrum that triggers a
        "confused" flag. This number should be conservative, because the estimate of
        the confusing and confused counts are just that - estimates - based on what is
        seen in zeroth order with a simplified instrumental model (e.g. an interpolated
        version of a typical ARF).

    Returns
    -------
    spec_conf : numpy.rec.array
        Information about each occurance of confusion.
        Only valid confusion is listed, all sources and arm combinations
        processed that are not listed are to be considered unconfused.

    Notes
    -----
    In this function we first assume that all sources are confused in every order then
    remove confusion candidates step by step.

    - If a source has fewer than "min_spec_counts" then we ignore it. It's specturm is not useful anyway.
    - If a confuser has fewer than "min_spec_confuser" counts, then its dispersed spectrum will be so weak that we ignore it.
    - If the confuser source intersects the arm of the (potentially) confused source outside of the heg/meg
      cutoff energies (<1 A or >~ 16, 32 A) te spectrum is not confused.
    - If the confuser's m order wavelength is outside the bounds of HEG/MEG it's not confused.
    - If the confuser's m order is outside the wavelength range that the confused source is
      expecting at the location of the intersection (i.e., the OSIP window of the confused source at the
      intersection location), it's not confused.
    - Using the OSIP and the confuser's zero's order, estimate the number of confusing counts.
      If the expected ratio between confusing and confused spectra is below "spec_confuse_limit"
      that it's not confused (but a warkign can be logged).
      This calculation should account for the heg/meg order efficiencies and ARFs BUT assumes an on-axis source at
      the pointing location. This WILL be slightly different for any other source but to first order it should be ok.
      This calculation uses the AVERAGE response ratio in the calculated OSIP range. If OSIP range is large then
      it is washing out some details in the arfs but for estimation purposes it should be ok.

    A few notes on the implementation that help to read the code:

    We now build up the intersections and orders where confusion occurs
    with a series of step of filtering, each one removing more and more
    "confusion" candidates, setting more and more of the "confusion" array to False.
    The first few steps can be done on simple matrix equations, the
    laters ones are more computationally expensive and so we loop them only
    over sources and orders where confusion is possible.
    Arrays that deal with the confuser (e.g. the wavelength at each intersection are
    of shape (n_confused_sources, n_confuser_sources, n_orders_confused)
    and arrays that deal with the confuser are
    of shape (n_confused_sources, n_confuser_sources, n_orders_confuser).
    The shape of a flag array for all possible confusions cases is:
    (n_confused_sources, n_confuser_sources, n_orders_confused, n_orders_confuser)
    so 3D arrays need to be broadcast to the right shape.
    """
    # For the meg we need to transpose the first two axis
    intersect = intersect_info["heg_meg_intersects"]
    orders = intersect_info["orders"]

    if arm == "meg":
        intersect = np.moveaxis(intersect, 1, 0)
    secondary_arm = "meg" if arm == "heg" else "heg"
    mask_interval = width_mask_pixel * mm_per_pix / X_R[arm] * Period[arm]
    primary_arf = read_file(
        f"{arf_ratios_dir}/{arm.upper()}_Nth_0th_order_ratios_mkarf.fits"
    )
    secondary_arf = read_file(
        f"{arf_ratios_dir}/{secondary_arm.upper()}_Nth_0th_order_ratios_mkarf.fits"
    )

    intersect = intersect[subset_sources, :, :]
    srcpos_subset = sources["pos"][subset_sources, :]

    mwave = intersect_info["mwave"][arm][subset_sources, :]
    mwave2 = intersect_info["mwave"][secondary_arm][:, subset_sources].T
    # divide by order number to get wavelength for each order
    wave = mwave[..., np.newaxis] / orders
    wave2 = mwave2[..., np.newaxis] / orders

    # Step 1: Select spectra and confusers with enough counts to be relevant.
    confusion = (sources["counts"] > min_spec_counts)[subset_sources, np.newaxis] & (
        sources["counts"] > min_spec_confuser_counts
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
    confusion &= wave[:, :, :, np.newaxis] > 0
    confusion &= wave2[:, :, np.newaxis, :] > 0

    # Step 3: Arms that intersect so close in or so far out that confusion would be
    # at undetectable wavelengths can be ignored.
    # That's true if either the confused or the confuser spectrum is in the range of
    # energies that can't be detected with ACIS or the grating's don't disperse them.
    far_out_confused = (wave <= cutoff[arm][0]) | (wave >= cutoff[arm][1])
    confusion &= ~far_out_confused[:, :, :, np.newaxis]
    far_out_confuser = (wave2 < cutoff[secondary_arm][0]) | (
        wave2 >= cutoff[secondary_arm][1]
    )
    confusion &= ~far_out_confuser[:, :, np.newaxis, :]

    # Step 4: Is the confusing arm within the OSIP?

    # For all vallues we consider below, the initial value will be overwritten.
    # Setting the initial value to 1 avoids "devide by zero" errors for elements we don't care about.
    energy_low = np.ones_like(wave, dtype=float)
    energy_high = np.ones_like(wave, dtype=float)

    for i, j in np.ndindex(mwave.shape):
        if confusion[i, j].any():
            result = osip(
                intersect[i, j, 0],
                intersect[i, j, 1],
                (hc / wave[i, j, :]),
            )
            energy_low[i, j, :] = result[0]
            energy_high[i, j, :] = result[1]

    # Intersection points that do not fall on any chip are listed as nan
    confusion &= np.isfinite(energy_low[:, :, :, np.newaxis])

    # convert osip from energy to angstrom and account for user parameter osip_frac (fractional size
    # of osip window of choice --e.g., user could want smaller than large osip window)
    mask_width = (1 - osip_frac) * (hc / energy_low - hc / energy_high)
    osip_low = hc / energy_high + mask_width / 2
    osip_high = hc / energy_low - mask_width / 2

    outside_osip = (wave2[:, :, np.newaxis, :] < osip_low[:, :, :, np.newaxis]) | (
        wave2[:, :, np.newaxis, :] > osip_high[:, :, :, np.newaxis]
    )
    flag[confusion & outside_osip] += flags_spec["outside_osip_range"]
    confusion &= ~outside_osip

    # Step 5: Do we expect any signal from the confuser within the OSIP range?
    confuser_0th_counts = np.full_like(wave2, -1)
    for i, j, o in np.ndindex(wave.shape):
        if confusion[i, j, o, :].any():
            confuser_0th_counts[i, j, o] = counts_circle_band(
                evtcrates,
                sources["pos"][j],
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
    confusion &= (confuser_0th_counts > 0)[:, :, :, np.newaxis]

    # Step 6: See if confuser contributes any counts.
    confuser_counts_secondary = np.full_like(confusion, -1, dtype=float)

    for i, j, m1, m2 in np.ndindex(confusion.shape):
        if confusion[i, j, m1, m2]:
            order = orders[m2]
            counts = confuser_0th_counts[i, j, m1]
            confuser_counts_secondary[i, j, m1, m2] = counts * arf_ratio(
                ratio_pycrates=secondary_arf,
                order=f"{'p' if order > 0 else 'm'}{abs(order)}_to_0",
                bin_start=osip_low[i, j, m1],
                bin_end=osip_high[i, j, m1],
            )

    flag[confusion & (confuser_counts_secondary == 0)] += flags_spec[
        "confuser_has_0_disp_counts_in_order"
    ]

    confusion &= confuser_counts_secondary > 0

    # Step 7: Get counts for confused source and calculate confusion ratio.
    confused_0th_counts = np.zeros_like(wave)
    confused_counts_primary = np.zeros_like(wave)

    for i, j, o in np.ndindex(wave.shape):
        if confusion[i, j, o, :].any():
            counts, arf_counts = counts_scaled_by_arf(
                srcpos_subset[i],
                orders[o],
                [
                    osip_low[i, j, o],
                    osip_high[i, j, o],
                ],
                evtcrates,
                skyconverter,
                primary_arf,
            )
            confused_0th_counts[i, j, o] = counts
            confused_counts_primary[i, j, o] = arf_counts

    flag[confusion & (confused_counts_primary == 0)[:, :, :, np.newaxis]] += flags_spec[
        "confused_has_0_disp_counts_and_confuser_gtr_0"
    ]
    confusion &= confused_counts_primary[:, :, :, np.newaxis] > 0

    # This will raise a "devide by 0" warning for sources where confused_counts_primary == 0
    # Above, we already marked those as not-confused and we will never need those values.
    # So, we just hide the error message.
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = confuser_counts_secondary / confused_counts_primary[:, :, :, np.newaxis]
    flag[confusion & (ratio < spec_confuse_limit)] += flags_spec[
        "confusion_smaller_than_conf_ratio"
    ]
    confusion &= ratio >= spec_confuse_limit

    flag[confusion] += flags_spec["confusion_above_conf_ratio"]

    wave_extracted = np.extract(
        flag > 0, np.broadcast_to(wave[:, :, :, None], flag.shape)
    )

    result = {
        "src_id": np.extract(
            flag > 0,
            np.broadcast_to(
                sources["ID"][subset_sources, None, None, None], flag.shape
            ),
        ),
        "confuser_srcid": np.extract(
            flag > 0,
            np.broadcast_to(sources["ID"][None, :, None, None], flag.shape),
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
        "flag_id": np.extract(flag > 0, flag),
    }
    return np.rec.fromarrays([result[n] for n in rec_type.names], dtype=rec_type)


####POINT SOURCE CONFUSION FUNCTIONS####
def pntsrc_confuse_wave(
    sources,
    subset_sources,
    intersect_info,
    arm,
    max_pntsrc_dist,
    min_spec_counts,
    min_pntsrc_counts,
    cutoff,
    osip,
    skyconverter,
    evtcrates,
    logfile_par,
    evt_frac_thresh=0.1,
    min_tg_d=-6.6e-4,
    max_tg_d=6.6e-4,
    mode="point",
):
    r"""Identify point source confusion

    If a 0th order source is sufficiently bright and close to the dispersed
    spectrum of another source then it will be identified as having point
    source confusion. A single confusing point source can only confuse a single arm for
    each 'confused' source.

    Parameters
    ----------
    sources : dict
        Dictionary with source properties including positions in Chandra physical units and 0th order counts.
    subset_sources : list of int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    interset_info : dict
        Holding information aboout the source locations, arm locations, and arm intersection points.
    arm : str
        HETG arm type of 'heg' or 'meg'.
    pntsrc_dict : dictionary
        Point source confusion dict which holds all possible pntsrc confusion entries for every source in main_list.
        This dictionary is modified in place by this function.
    max_pntsrc_dist : float
        CrissCross parameter threshold in number of pixels for how far a point source can be perpendicular to a
        disperssed spectrum before it is no longer considered in the confusion calculation. This number can be increased
        to reduce the number of potentially confusing point sources.
    min_spec_counts : int
        CrissCross parameter threshold in counts above which a confused source is considered bright enough for point
        source confusion estimation.
    min_pntsrc_counts : int
        CrissCross parameter threshold in counts above which a 0th order source is bright enough to be
        considered as a confuser source of another source's spectrum.
    cutoff : dict
        Minimum and maximum wavelength that will be considered.
    osip : `ciao_contrib.criss_cross.iocaldb.OSIP`
        Object that can retrieve OSIP information for the event file used.
    skyconverter : `ciao_contrib.criss_cross.iocaldb.Sky2Chandra`
        Object that can convert Chandra coordiantes for the event file used.
    evtcrates : `pycrates.tablecrate.TABLECrate`
        A crates object holding an event file.
    logfile_par : str
        Name of the logfile for capturing pnt_src_masking_region() log output.
    evt_frac_thresh : float
        Fraction of events allowed by confuser before considering confusion occurs (0.1 = 10%)
    min_tg_d, max_tg_d : float
        Lower and upper bounds of the spectral extraction of a dispersed spectrum in cross-dispersion direction in degrees.
        These parameters should be set to the same values used in `tg_extract` and they default
        to the default used in `tg_extract`. Crisscross assumes rectangular extraction regions.
    mode : str
        Select between "point" source confusion or "streak" confusion.

    Returns
    -------
    pnt_conf : numpy.rec.array
        Information about each occurance of confusion.
        Only valid confusion is listed, all sources and arm combinations
        processed that are not listed are to be considered unconfused.
    """
    orders = intersect_info["orders"]
    mwave = intersect_info["mwave"][arm][subset_sources, :]
    inter_pos = intersect_info["intersects"][arm][subset_sources, :]

    cross_disp_pixel = (max_tg_d - min_tg_d) * 3600 / arcsec_per_pix

    # Array shape is (n_confused_sources, n_confuser_sources).
    confusion = np.ones_like(mwave, dtype=bool)
    confusion &= (sources["counts"][subset_sources] > min_spec_counts)[:, None]
    confusion &= (sources["counts"] > min_pntsrc_counts)[np.newaxis, :]

    off_axis_limit = max_pntsrc_dist * sources["off_axis_modifier"]
    distance2line = intersect_info["point2arm"][arm][subset_sources, :]

    if mode == "point":
        confusion &= distance2line < off_axis_limit
        # A source does not confuse itself, i.e. distance to source is > 0:
        confusion &= distance2line > 0
    elif mode == "streak":
        # Confuser is not so close that it would be counted as point source confusion
        confusion &= distance2line >= off_axis_limit
        # confusion is less than 1024 so it *could* be on the same chip
        confusion &= distance2line < 1024
        # Confuser is on a chip (list of sources could include sources where the 0th
        # order is not on a CCD)
        confusion &= on_chip(sources["chipx"], sources["chipy"])[None, :]
        # Check if confuser and intersection are on the same chip.
        # We start with a simple check based on the
        # distance in pixels (fast) and then use the full Chandra coordinate
        # conversion for all remaining potential intersections (slower).
        dist_to_edge = np.maximum(sources["chipy"], 1023 - sources["chipy"])
        d_arm = intersect_info["point2arm"][arm][subset_sources, :]
        confusion &= d_arm < dist_to_edge[None, :]
        chipx = np.zeros_like(mwave)
        chipy = np.zeros_like(mwave)
        ccd_id = np.zeros_like(mwave)
        # Find with source/confuser pairs are still suspected of confusion.
        # We will run the skyconverter only for those because it can be slow.
        # Since skyconverter takes only 1D arrays, we ravel the 2D arrays to 1D.
        pos = skyconverter(
            inter_pos[:, :, 0].ravel()[confusion.ravel()],
            inter_pos[:, :, 1].ravel()[confusion.ravel()],
        )
        chipx.ravel()[confusion.ravel()] = pos["chipx"]
        chipy.ravel()[confusion.ravel()] = pos["chipy"]
        ccd_id.ravel()[confusion.ravel()] = pos["chip_id"]
        # Intersection between streak and spectrum is on a chip...
        confusion &= on_chip(chipx, chipy)
        # ... and it's actually on the same chip
        confusion &= ccd_id == sources["chip_id"][np.newaxis, :]
    else:
        raise ValueError("mode parameter needs to be either 'point' or 'streak'.")

    # So far, this was all about geometry. Now, we look at which orders are
    # affected by confusion.
    # Array shape is now (n_confused_sources, n_confuser_sources, n_orders_confused).
    wave = mwave[..., np.newaxis] / orders
    flag = np.zeros_like(wave, dtype=int)

    # Wavelength of real photons are always positive
    confusion = confusion[:, :, np.newaxis] & (wave > 0)

    pntsrc_confuse_log_file = open(f"{logfile_par}", "w")

    wave_low = np.zeros_like(wave)
    wave_high = np.zeros_like(wave)
    for i, j, o in np.ndindex(wave.shape):
        if confusion[i, j, o]:  # only calculate for potential sources of confusion
            wave_low[i, j, o], wave_high[i, j, o] = pnt_src_masking_region(
                evtcrates,
                osip,
                skyconverter,
                sources["pos"][subset_sources[i]],
                sources["pos"][j],
                intersect_info["point2arm"][arm][subset_sources[i], j]
                if mode == "point"
                else 0.0,
                wave[i, j, o],
                arm,
                cross_disp_pixel,
                evt_frac_thresh,
                pntsrc_confuse_log_file,
            )
    pntsrc_confuse_log_file.close()

    # Intersection points that do not fall on any chip are listed as nan
    confusion &= np.isfinite(wave_low)

    flag[confusion & (wave_low == 9999.0)] = flags_pnt["confusing_pntsrc_but_no_counts"]
    confusion &= wave_low != 9999.0

    outside_range = (wave <= cutoff[arm][0]) | (wave >= cutoff[arm][1])
    flag[confusion & outside_range] = flags_pnt["pntsrc_conf_outside_resp_region"]
    confusion &= ~outside_range

    flag[confusion & (wave_low == 9998.0)] = flags_pnt[
        "confusing_pntsrc_but_relatively_few_counts"
    ]
    confusion &= wave_low != 9998.0

    flag[confusion & (wave_low == 9997.0)] = flags_pnt[
        "confusing_pntsrc_too_weak_and_too_far"
    ]
    confusion &= wave_low != 9997.0

    flag[confusion] = flags_pnt["pntsrc_confusion"]

    result = {
        "src_id": np.extract(
            flag > 0,
            np.broadcast_to(sources["ID"][subset_sources, None, None], flag.shape),
        ),
        "confuser_srcid": np.extract(
            flag > 0,
            np.broadcast_to(sources["ID"][None, :, None], flag.shape),
        ),
        "0_order_confused_counts": np.extract(
            flag > 0,
            np.broadcast_to(sources["counts"][subset_sources, None, None], flag.shape),
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
        "flag_id": np.extract(flag > 0, flag),
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
    # but to make plots look nice, we fix it to the max of the resolving power.
    res_power[ccd_lam_arm < 1] = np.max(res_power)
    return res_power, ccd_lam_arm


def arm_confuse_wave(
    sources,
    subset_sources,
    intersect_info,
    arm,
    min_arm_counts,
    max_arm_dist,
    arf_ratios_dir,
    cutoff,
    skyconverter,
    evtcrates,
    arm_confuse_limit,
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
    sources : dict
        Dictionary with source properties including positions in Chandra physical units and 0th order counts.
    subset_sources : list of int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    interset_info : dict
        Holding information aboout the source locations, arm locations, and arm intersection points.
    arm : str
        HETG arm type of 'heg' or 'meg'.
    min_arm_counts : float
        Only consider sources with more zero order counts than `min_arm_counts`.
    arm_dist : float
        Maximal distance perpendicular to the dispersion direction that a source can
        have to be considered for confusion. For sources at some distance from the
        optical axis is number is scaled up.
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
    arf = read_file(f"{arf_ratios_dir}/{arm.upper()}_Nth_0th_order_ratios_mkarf.fits")

    distance2line = intersect_info["point2arm"][arm]
    orders = intersect_info["orders"]

    # Array shape is (n_confused_sources, n_confuser_sources).
    confuser_close_enough = (
        distance2line
        < max_arm_dist
        * sources["off_axis_modifier"][np.newaxis, :]
        * sources["off_axis_modifier"][:, np.newaxis]
    ) & (sources["counts"] > min_arm_counts)[np.newaxis, :]
    # A source has distance=0 from itself, but that's not confusion.
    np.fill_diagonal(confuser_close_enough, False)

    # Many sources are too faint to confuse anything.
    # To keep arrays from getting too big in memory, we don't consider those faint
    # source any further for arm confusion and we also don't need to consider
    # sources as potentially confused if they are not in subset_sources.
    # Because we will need the index array of potentially confusing sources often
    # we give it a shorthand name "iconf" for "index_of_confusers"
    iconf = np.any(confuser_close_enough, axis=0)
    confuser_close_enough = confuser_close_enough[subset_sources, :][:, iconf]
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
        # If there are no confusers, we still run though all of this loop.
        # That generates an empty table with the right datatype to stack all the outputs later.
        # We *could* just skip here and only make an empty table,
        # but the rest of the code is fast so it's not worth it to write a separate code path.

        # the dimension of "confused" will be
        # (n_wavelengths, n_confusers, n_orders_m1, n_orders_m2)
        # Note that `None` has the same meaning as `np.newaxis` but is shorter to type
        term1 = wave_arr[:, None, None] * (
            1 - m1[:, None] / m2[None, :]
        )  # shape (n_wavelengths, n_orders_m1, n_orders_m2)
        term2 = mwave[i, :, None] / m2  # shape (n_confusers, n_orders_m2)

        # Step 1:The wavelength difference between the confused and confuser arm is smaller than sigma * resolution (rhs)
        lhs = np.abs(term1[:, None, :, :] + term2[None, :, None, :])
        confused = lhs < rhs[:, None, None, None]
        wav_low = np.min(wave_arr4d, axis=0, where=confused, initial=np.inf)
        wav_high = np.max(wave_arr4d, axis=0, where=confused, initial=0)

        confusion = confused.sum(axis=0) > 0
        # Step 2: And the source is close enough in cross-dispersion direction
        confusion &= confuser_close_enough[i, :, None, None]

        # 0 mean "clean". All flags start clean and flages are added step by step.
        flag = np.zeros_like(confusion, dtype=int)

        # For m1=m2, the arms meet asymptocially at infinity.
        # Intersection of a source with itself, gives 0/0, but those cases are
        # filtered out by setting the diagonal of confuser_close_enough to False above.
        # So, we simply suppress warninges here.
        with np.errstate(divide="ignore", invalid="ignore"):
            intersect_wav = mwave[i, :, None, None] / (
                m1[None, :, None] - m2[None, None, :]
            )

        # Step 3: Arms where the masking area only covers very short or very long wanvelengths
        # are not really confused because the user would likely ignore those wavelengths anyway.
        far_out_confused = (wav_high <= cutoff[arm][0]) | (
            wav_low >= cutoff[arm][1] / np.abs(m1[None, :, None])
        )
        confusion &= ~far_out_confused
        # We are not scaling the inner edge, since that's more about the max energy
        # that the CCD can detect, so we don't have to repeat the "< cutoff[arm][0]" test.
        far_out_confused = wav_low >= cutoff[arm][1] / np.abs(m2[None, None, :])
        confusion &= ~far_out_confused

        # Step 4: Determine how important suspected arm confusion is
        confused_counts = np.full_like(wav_low, -1)
        confused_zero_counts = np.full_like(wav_low, -1)
        confuser_counts = np.full_like(wav_low, -1)
        confuser_zero_counts = np.full_like(wav_low, -1)
        for j, m, n in np.ndindex(confusion.shape):
            if confusion[j, m, n]:
                counts, arf_counts = counts_scaled_by_arf(
                    sources["pos"][iconf.nonzero()[0][j]],
                    m2[m],
                    [wav_low[j, m, n], wav_high[j, m, n]],
                    evtcrates,
                    skyconverter,
                    arf,
                )
                confuser_counts[j, m, n] = arf_counts
                confuser_zero_counts[j, m, n] = counts

        flag[confusion & (confuser_zero_counts == 0)] += flags_arm[
            "confuser_has_no_0th_order_counts"
        ]
        confusion &= confuser_zero_counts > 0
        flag[confusion & (confuser_counts == 0)] += flags_arm[
            "confuser_has_0_disp_counts_in_order"
        ]
        confusion &= confuser_counts > 0

        for j, m, n in np.ndindex(confusion.shape):
            if confusion[j, m, n]:
                counts, arf_counts = counts_scaled_by_arf(
                    sources["pos"][subset_sources[i]],
                    m1[m],
                    [wav_low[j, m, n], wav_high[j, m, n]],
                    evtcrates,
                    skyconverter,
                    arf,
                )
                confused_counts[j, m, n] = arf_counts
                confused_zero_counts[j, m, n] = counts

        flag[confusion & (confused_counts == 0)] += flags_arm[
            "confused_has_0_disp_counts_and_confuser_gtr_0"
        ]
        confusion &= confused_counts > 0

        with np.errstate(divide="ignore", invalid="ignore"):
            conf_ratio = confuser_counts / confused_counts

        flag[confusion & (conf_ratio < arm_confuse_limit)] += flags_arm[
            "confusion_smaller_than_conf_ratio"
        ]
        confusion &= conf_ratio >= arm_confuse_limit

        intersect_wav = np.clip(
            intersect_wav, a_min=cutoff[arm][0], a_max=cutoff[arm][1]
        )

        flag[confusion] += flags_arm["confusion_above_conf_ratio"]
        confuser_srcid_numbers = np.arange(sources["n"])[iconf]
        confuser_srcid = np.extract(
            flag > 0,
            np.broadcast_to(confuser_srcid_numbers[:, None, None], confusion.shape),
        )

        result = {
            "src_id": np.full((flag > 0).sum(), subset_sources[i]),
            "confuser_srcid": confuser_srcid,
            "0_order_confused_counts": sources["counts"][confuser_srcid],
            "grating_type": np.full((flag > 0).sum(), arm),
            "order": np.extract(
                flag > 0, np.broadcast_to(m1[None, :, None], confusion.shape)
            ),
            "confusing_order": np.extract(
                flag > 0, np.broadcast_to(m2[None, None, :], confusion.shape)
            ),
            "confusion_type": np.full((flag > 0).sum(), "arm"),
            "confusion_wave": np.abs(np.extract(flag > 0, intersect_wav)),
            "wave_low": np.abs(np.extract(flag > 0, wav_low)),
            "wave_high": np.abs(np.extract(flag > 0, wav_high)),
            "flag_id": np.extract(flag > 0, flag),
        }
        arm_conf.append(
            np.rec.fromarrays([result[n] for n in rec_type.names], dtype=rec_type)
        )

    return rfn.stack_arrays(arm_conf)


def streak_confuse_wave(
    sources,
    subset_sources,
    intersect_info,
    arm,
    max_pntsrc_dist,
    min_spec_counts,
    min_pntsrc_counts,
    cutoff,
    osip,
    skyconverter,
    evtcrates,
    logfile_par,
    evt_frac_thresh=0.1,
    min_tg_d=-6.6e-04,
    max_tg_d=6.6e-04,
):
    r"""Identify streak source confusion

    If a 0th order source is sufficiently bright on the same chip as a dispersed
    spectrum of another source then it will be identified as having streak
    source confusion.

    Parameters
    ----------
    sources, subset_sources, intersect_info, arm, max_pntsrc_dist, min_spec_counts, min_pntsrc_counts, cutoff,
    osip, skyconverter, evtcrates, logfile_par, evt_frac_thresh : see `pntsrc_confuse_wave()``
        These parameters are passed to `pntsrc_confuse_wave()` with a scaling to account for the
        relative fraction of the exposure spend in out-of-time events that cross a dispersed spectrum.
    min_tg_d, max_tg_d : float
        Lower and upper bounds of the spectral extraction of a dispersed spectrum in cross-dispersion direction in degrees.
        These parameters should be set to the same values used in `tg_extract` and they default
        to the default used in `tg_extract`. Crisscross assumes rectangular extraction regions.

    Returns
    -------
    streak_conf : numpy.rec.array
        Information about each occurance of confusion.
        Only valid confusion is listed, all sources and arm combinations
        processed that are not listed are to be considered unconfused.
    """
    n_rows = (max_tg_d - min_tg_d) * 3600 / arcsec_per_pix
    frac_outoftime = 4e-5 * n_rows / evtcrates.get_key_value("EXPTIME")

    streak_conf = pntsrc_confuse_wave(
        sources=sources,
        subset_sources=subset_sources,
        intersect_info=intersect_info,
        arm=arm,
        max_pntsrc_dist=max_pntsrc_dist,
        min_spec_counts=min_spec_counts,
        min_pntsrc_counts=min_pntsrc_counts / frac_outoftime,
        cutoff=cutoff,
        osip=osip,
        skyconverter=skyconverter,
        evtcrates=evtcrates,
        logfile_par=logfile_par,
        evt_frac_thresh=evt_frac_thresh / frac_outoftime,
        mode="streak",
    )

    streak_conf["confusion_type"][:] = "strk"
    return streak_conf


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
            records["flag_id"] >= levels[level]
        )

    if src_id is not None:
        to_write = to_write & (records["src_id"] == src_id)

    if cc_table_root is not None and len(set(records["src_id"])) == 1:
        filename = (
            f"{output_dir}/confused_{cc_table_root}_consolidated_obsID_{obsid}.fits"
        )
    else:
        filename = f"{output_dir}/confused_src_{src_id}_consolidated_obsID_{obsid}.fits"

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
                    & (records["flag_id"] >= levels[lev])
                ] = lev

        # Get a reverse lookup from flag values to strings.
        # This simple reversing of dicts works because we don't add flag values together
        # e.g. no intersection is ever flag 2 and 4 = 6.
        flags_lookup = {}
        for conf_type, d in flags.items():
            flags_lookup[conf_type] = {v: k for k, v in d[0].items()}
        descr = [flags_lookup[row["confusion_type"]][row["flag_id"]] for row in records]
        records = rfn.rec_append_fields(
            records, ["flag", "flag_comment"], [severity, descr]
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

    # for i in range(len(output_table_full)):
    #     file_size_table = os.stat(output_table_full[i])
    #     if (
    #         file_size_table.st_size == 46080
    #     ):  # note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the
    #         # number of columns!
    #         os.remove(output_table_full[i])

    # for i in range(len(output_table_consolidated)):
    #     file_size_table = os.stat(output_table_consolidated[i])
    #     if (
    #         file_size_table.st_size == 5760
    #     ):  # note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the
    #         # number of columns!
    #         os.remove(output_table_consolidated[i])

    # move the remaining table files to the table directory
    files_to_move = glob.glob(
        f"{output_dir_list_par}/confused_*_obsID_{obsid_par}.fits"
    )
    # check that some files exist after removing the tables that have no confusion.
    if len(files_to_move) == 0:
        print(
            "WARNING -- No confusion tables exist. No confusion identified with input source(s) or something went wrong in CrissCross."
        )
    else:
        for i in files_to_move:
            shutil.move(i, table_dir)

    return ()


class TimeLogger:
    """Class for logging time at different steps of the CrissCross process.

    Can be used as a context manager and also allows for logging time at different steps.

    Examples
    --------
    Use as a contect manager:
    >>> with TimeLogger() as tl:
    ...     # some code here
    ...     tl("Finished step 1")
    ...     # some more code here
    ...     tl("Finished step 2")

    Or use without context manager and call end() at the end of the process:
    >>> tl = TimeLogger()
    ... # some code here
    ... tl("Finished step 1")
    ... # some more code here
    ... tl("Finished step 2")
    ... end_time = tl.end()
    """

    def __init__(self):
        self.start = time.time()
        self.counter = 0

        print("\n")
        print("CrissCross Time Start:")
        print(time.asctime(time.localtime()))
        #print("\n")

    def __enter__(self):
        return self

    def __call__(self, message):
        self.counter += 1
        elapsed = round((time.time() - (self.start)) / 60, 2)

        print("\n")
        print(f"TIME LOG #{self.counter}  -- {message}")
        print(time.asctime(time.localtime()))
        print(f"{elapsed} minutes have elapsed")
        print("\n")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.total_time = round((time.time() - self.start) / 60, 2)
        print()
        print(f"total elapsed time has been {self.total_time} minutes.")
        print()

    def end(self):
        self.__exit__(None, None, None)
        return self.total_time





######### MAIN CrissCross RUN FUNCTION ##############


def run_crisscross(
    evt2_file=None,
    cc_outdir=None,
    main_list=None,
    subset_src_list=None,
    single_src_pos=None,
    single_src_root=None,
    wavdetect_file=None,
    conf_table_level="confused",
    arf_ratios_dir=".",
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
    arm_confuse_limit=0.1,
    meg_cutoff_low=1.0,
    meg_cutoff_high=32.0,
    heg_cutoff_low=1.0,
    heg_cutoff_high=16.0,
    highest_order=3,
    min_tg_d=-6.6e-04,
    max_tg_d=6.6e-04,
):
    """
    Main function for running criss cross. CrissCross identifies portions of a sources spectrum where events from other
    field sources may be errouneously assigned to the extracted source with standard CIAO processing. CrissCross
    produces a fits table for each source which tabulates the wavelength location where confusion occurs for all HETG
    arms (heg+meg) and orders -3 to +3. CrissCross requires the evt2 file that was used to extract a source's spectra
    and a list of RA+DEC (main_list) for every X-ray source in the field of view. A list of sources in the field of
    view can often be obtained by running wavdetect on the same field if there are non-HETG archival Chandra
    observations. CrissCross can create spectral confusion tables for all sources present in a secondary
    (subset_src_list) list or can be run for a single source using the 'single_src_pos' parameter.

    If users have PHA files extracted using the relevant evt2 file they can run the complimentary CIAO tool clean_spec()
    using the CrissCross confusion tables as input to remove confused counts from their spectra and associated ARFs
    before performing their spectral analysis.

    Parameters
    ----------
    evt2_file : str
        A single evt2 file or a list of evt2 files which contain sources in main_list and subset_src_list.
    cc_outdir : str
        A directory for holding the output of CrissCross. If it does not exist then it will be made.
    main_list : str
        A tsv or ascii file with columns RA, DEC, ID of source positions. This is used to distinguish real sources in a
        wavdetect source table from false sources (identified from the dispersed spectra). This can include sources
        outside of an individual chandra obsID FOV.
    subset_src_list : str
        A tsv or ascii file of sources to create confusion tables for. This should be a subset of main_list and include
        sources bright enough for HETG spectral extraction. The table format requires columns RA, and DEC.
    single_src_pos : string
        RA and DEC position in degrees to calculate confusion for only a single source. The source coordinates must
        also be in the main_list file. Format must be J2000 degrees in format e.g., '83.8186447, -5.3896515'.
    single_src_root : string
        Root name for single_src_pos confusion table. If None then element number of main_list is used in table name.
    wavdetect_file : str, None
        A single wavdetect source fits table or a list of wavdetect source fits tables. This is the '*src.fits' file
        output from wavdetect. If no files are included (e.g., wavdetect_file=None) then wavdetect will be run during
        execution of CrissCross.
    conf_table_level : str, 'confused', 'warn', or 'clean'
        Determines the output saved in the confusion tables. 'confused': includes only the locations of confusion.
        'warn': includes confusion and 'warn' locations where confusion could have occured but detection is marginal
        typically due to source brightness (see warn flag in table). 'clean': includes 'confused', 'warn' and 'clean'
        where 'clean' represents locations where there should be no confusion. (default is 'confused')
    highest_order : int
        The highest order of the HETG spectra to consider for confusion. Default is 3 which means orders -3, -2, -1, 1, 2, and
        3 are included in the confusion calculations.
    arf_ratios_dir : str
        The directory which holds the ARF response ratios fits tables necessary for Crisscross.
    clobber_par : bool
        If clobber_par = True then CrissCross overwrites previous CrissCross run if output directory already exists.

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
        Two bright sources whose 0th order distance, measured in ACIS pixels perpendicular from one source to the
        dispersed spectrum of an extracted source, is less than this will be considered as potential arm confusion.
        Users can increase this parameter if they believe spectra are unfairly being flagged as arm confused. Note: an
        on-axis spectrum has a width of approximately 5 pixels and thus if two on-axis sources are within 10 pixels
        then it is possible they can contaminate eachother (default: 8.0).
    arm_nsig : float
        Approximation for how wide the OSIP range is for order sorting when determining which events are part of the
        Nth order spectrum. This parameter is for arm confusion only and increasing it will cause larger portions of a
        spectrum to be considered confused by arm confusion (default: 6.0).
    arm_confuse_limit : float
        The fraction of dispersed events allowed in an arm confusion region before deciding the region is contaminated.
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
    min_tg_d, max_tg_d : float
        Lower and upper bounds of the spectral extraction of a dispersed spectrum in cross-dispersion direction in degrees.
        These parameters should be set to the same values used in `tg_extract` and they default
        to the default used in `tg_extract`. Crisscross assumes rectangualr extraction regions.
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
        timelogger = TimeLogger()

        #print parameters to screen if verbose is > 0
        v1("\n")
        v1(f'This run is for observation "{evt2_file[k]}".')
        v2(
            f'The list of X-ray field sources to assess as potential sources of confusion is "{main_list}".'
        )
        if single_src_pos is not None:
            v2(
                f"The HETG-bright source for which confusion tables will be generated is RA,DEC = ({single_src_pos})."
            )
        else:
            v2(
                f'The list of HETG-bright sources for which confusion tables will be generated is "{subset_src_list}".'
            )
        if wavdetect_file[k] is not None:
            v1(
                f'0th order counts are estimated using the wavdetect file "{wavdetect_file[k]}"'
            )
        v2(
            f"The max distance in pixels perpendicular to confused spectra to be considered a potential point source confuser is {max_pntsrc_dist}."
        )
        v2(
            f"The min number of counts for a 0th order field source to be considered a potential confuser is {min_pntsrc_counts}."
        )
        v2(
            f"The min number of 0th order counts required to calculate confusion for sources in subset_src list is {min_spec_counts}."
        )
        v2(
            f"The min number of 0th order counts required for field sources to be considered a source of spectral confusion is {min_spec_confuser_counts}."
        )
        v2(
            f"Fraction of the OSIP window to use in spectral intersection calculation is {osip_frac}."
        )
        v2(
            f"The fraction of dispersed counts allowed in a subset_src spectral confusion region before flagging as confused is {spec_confuse_limit}."
        )
        v2(
            f"The max distance, in pixels perpendicular to a subset_src spectrum, to be considered a potential arm confuser is {max_arm_dist}."
        )
        v2(
            f"The min number of 0th order counts before a field source is considered a potential arm confuser is {min_arm_counts}."
        )
        v2(
            f"The approximate OSIP range for arm confusion is {arm_nsig}. Higher values will ignore more of a spectrum for arm confusion."
        )
        v2(
            f"The fraction of events allowed in subset_src arm confusion regions before flagging as confusion is {arm_confuse_limit}."
        )
        v2(
            f"The MEG and HEG cutoff wavelengths are {meg_cutoff_low, meg_cutoff_high} A and {heg_cutoff_low, heg_cutoff_high} A , respectively."
        )


        # set a few obsid_specific parameters
        obsid = get_header_par(fits_file=evt2_file[k], keyword_par="obs_id")
        roll_nom = float(get_header_par(fits_file=evt2_file[k], keyword_par="ROLL_NOM"))

        norm_vec = {}
        for arm in ["heg", "meg", "leg"]:
            norm_vec[arm] = np.array(
                [
                    np.cos(np.deg2rad(roll_nom + Alpha[arm])),
                    -np.sin(np.deg2rad(roll_nom + Alpha[arm])),
                ]
            )

        v2(f"The roll angle of this observation is {roll_nom}")

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
        if single_src_pos is None:
            subset_RA, subset_DEC = load_sourcelist(
                filename=subset_src_list, subset_list=True
            )
        else:
            #convert user input string 'ra,dec'.
            single_RA, single_DEC = [float(x.strip()) for x in single_src_pos.split(',')]
            subset_RA = np.array([single_RA])
            subset_DEC = np.array([single_DEC])

        # match the element number of the subset list to the main list using RA and DEC to 6 digits accuracy.
        subset_list = match_subset_to_main(
            RA_main=RA_wcs, DEC_main=DEC_wcs, RA_sub=subset_RA, DEC_sub=subset_DEC
        )

        # convert from RA/DEC in degrees to Chandra Sky physical coordinates
        src = calc_physical_coords(evt2_file[k], RA_wcs, DEC_wcs)

        #timelogger("Finished converting RA/DEC into chandra coords")

        # match input source list to wavedetect table to catalog 0th order counts for each source in each obsid
        final_match_arr, final_dist_arr, counts = find_closest_source(
            src=src,
            wave_file=wavdetect_file[k],
            max_offset=3.0,
        )
        src["counts"] = counts
        src["off_axis_modifier"] = calc_off_axis_modifier(src["theta"])

        # create an output file of the input source list with the wave-detect-matched 0th order counts
        write_matched_file(src, fileroot=f"{output_dir}/src_list_{obsid}")

        # Print to the screen the number of sources that satisfy the above conditions as well as the total number of
        # sources in input list.

        v1(
            f"The total number of X-ray field sources input is {src['n']}. These will be assessed as potential sources of confusion for sources in 'subset_src_list' or 'single_src_pos'."
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
        # calculate relevant parameters for when two lines intersect in the Chandra FOV
        k_heg, k_meg = line_line_intersect(src["pos"], norm_vec["heg"], norm_vec["meg"])
        heg_meg_intersects = (
            src["pos"][:, np.newaxis, :] + k_heg[:, :, np.newaxis] * norm_vec["heg"]
        )

        orders = np.arange(-highest_order, highest_order + 1)
        orders = orders[orders != 0]  # exclude 0 order
        intersect_info = {
            "orders": orders,
            "heg_meg_intersects": heg_meg_intersects,
        }
        intersect_info["mwave"] = {
            "heg": k_heg * mm_per_pix / X_R["heg"] * Period["heg"],
            "meg": k_meg * mm_per_pix / X_R["meg"] * Period["meg"],
        }

        for arm in ["heg", "meg"]:
            records.append(
                spec_confuse_wave(
                    sources=src,
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
                    min_spec_counts=min_spec_counts,
                    min_spec_confuser_counts=min_spec_confuser_counts,
                    width_mask_pixel=120,
                    osip_frac=osip_frac,
                    arf_ratios_dir=arf_ratios_dir,
                    cutoff=cutoff,
                    osip=osip,
                    skyconverter=skyconverter,
                    evtcrates=evtcrates,
                    spec_confuse_limit=spec_confuse_limit,
                )
            )

        #timelogger("Finished calculating spectral confusion.")

        ######### Perpendicular distance
        # Point, arm, and streak confusion all depend on the distance of
        # a source perpendicular to the arm, so we can set up the same
        # intersect info for all of them.
        intersect_info = {
            "orders": orders,
            "intersects": {},
            "mwave": {},
            "point2arm": {},
        }
        for arm in ["heg", "meg"]:
            k_arm, k_src = line_line_intersect(
                src["pos"], norm_vec[arm], perpendicular_vector(norm_vec[arm])
            )
            intersect_info["intersects"][arm] = (
                src["pos"][:, np.newaxis, :] + k_arm[:, :, np.newaxis] * norm_vec[arm]
            )
            intersect_info["mwave"][arm] = k_arm * mm_per_pix / X_R[arm] * Period[arm]
            intersect_info["point2arm"][arm] = np.abs(k_src)

        #########POINT SOURCE CONFUSION START ############

        for arm in ["heg", "meg"]:
            records.append(
                pntsrc_confuse_wave(
                    sources=src,
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
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
        for arm in ["heg", "meg"]:
            records.append(
                streak_confuse_wave(
                    sources=src,
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
                    max_pntsrc_dist=max_pntsrc_dist,
                    min_spec_counts=min_spec_counts,
                    min_pntsrc_counts=min_pntsrc_counts,
                    cutoff=cutoff,
                    osip=osip,
                    skyconverter=skyconverter,
                    evtcrates=evtcrates,
                    logfile_par=f"{output_dir}/streak_confuse_{obsid}_log.txt",
                    evt_frac_thresh=0.1,
                    min_tg_d=min_tg_d,
                    max_tg_d=max_tg_d,
                )
            )

        #timelogger("Finished calculating point source confusion.")

        ##########ARM CONFUSION START ############################
        for arm in ["heg", "meg"]:
            records.append(
                arm_confuse_wave(
                    sources=src,
                    subset_sources=subset_list,
                    intersect_info=intersect_info,
                    arm=arm,
                    min_arm_counts=min_arm_counts,
                    max_arm_dist=max_arm_dist,
                    arf_ratios_dir=arf_ratios_dir,
                    cutoff=cutoff,
                    skyconverter=skyconverter,
                    evtcrates=evtcrates,
                    arm_confuse_limit=arm_confuse_limit,
                    nsig_par=arm_nsig,
                )
            )

        #timelogger("Finished assigning arm confusion.")

        ##### Table writing and cleanup ############
        records = rfn.stack_arrays(records)

        for i in subset_list:
            # If users run cc with just a single source, allow them to name the confusion file. Otherwise a single root
            #  will get clobbered when looped over multiple sources.
            if (
                single_src_pos is not None
                and single_src_root is not None
            ):
                cc_table_root = single_src_root
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
                level=conf_table_level,
                add_description=True,
            )

        # move output files into final directories and cleanup
        end_of_run_cleanup(
            output_dir_list_par=output_dir, obsid_par=obsid, wavdetect_par=run_wave
        )

        #timelogger("Finished Running CrissCross!")

        log_file = open(f"{output_dir}/crisscross_obsID_{obsid}_log.txt", "w")
        total_time = timelogger.end()
#         log_file.write(
#             f"""This run is for observation {evt2_file[k]}.
# The wavdetect source list used for this observation is {wavdetect_file[k]}.
# The roll angle of this observation is {roll_nom:.2f} degrees.
# The contamination offset threshold is set to {max_pntsrc_dist} pixels.
# The counts threshold to be considered a spectrum of interest is set to {min_spec_counts} counts.
# The counts threshold to be considered a potential contaminating spectral source is {min_spec_confuser_counts} counts.
# The counts threshold to be considered a potential 0th order point source contaminating source is {min_pntsrc_counts} counts.
# The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is {max_arm_dist} pixels.
# The fraction of the OSIP window to include when considering two arm overlaps is set at {osip_frac * 100} percent.
# The total number of sources input is {src["n"]}.
# The number of sources above the contamination intercept threshold of {min_spec_counts} counts for ObsID {obsid} is {counts_intercept_num}.
# The minimum counts in Src Bs 0th order to assess total arm confusion in source A is {min_arm_counts}.
# The total elapsed time for obsID {obsid} is {total_time} minutes."""
#         )
        log_file.write(
            f"""
This run is for observation {evt2_file[k]}.

0th order counts are estimated using the wavdetect file {wavdetect_file[k]}.
The list of X-ray field sources to assess as potential sources of confusion is "{main_list}".
The list of HETG-bright sources for which confusion tables will be generated is "{subset_src_list}" or single src = {single_src_pos}.
The max distance in pixels perpendicular to confused spectra to be considered a potential point source confuser is {max_pntsrc_dist}.
The min number of counts for a 0th order field source to be considered a potential confuser is {min_pntsrc_counts}.
The min number of 0th order counts required to calculate confusion for sources in subset_src list is {min_spec_counts}.
The min number of 0th order counts required for field sources to be considered a source of spectral confusion is {min_spec_confuser_counts}.
Fraction of the OSIP window to use in spectral intersection calculation is {osip_frac}.
The fraction of dispersed counts allowed in a subset_src spectral confusion region before flagging as confused is {spec_confuse_limit}.
The max distance, in pixels perpendicular to a subset_src spectrum, to be considered a potential arm confuser is {max_arm_dist}.
The min number of 0th order counts before a field source is considered a potential arm confuser is {min_arm_counts}.
The approximate OSIP range for arm confusion is {arm_nsig}. Higher values will ignore more of a spectrum for arm confusion.
The fraction of events allowed in subset_src arm confusion regions before flagging as confusion is {arm_confuse_limit}.
The MEG and HEG cutoff wavelengths are {meg_cutoff_low, meg_cutoff_high} A and {heg_cutoff_low, heg_cutoff_high} A , respectively.

The total elapsed time for obsID {obsid} is {total_time} minutes.
            """
        )
        log_file.close()
